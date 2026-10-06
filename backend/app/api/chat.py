import asyncio
import logging
import uuid
from collections import defaultdict
from typing import Any

import anyio
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.auth.deps import CurrentUser, current_user
from app.config import get_settings
from app.db import repository
from app.embeddings.base import EmbeddingError
from app.errors import AppError
from app.llm.base import LLMUnavailable
from app.rag.pipeline import PdfRagPipeline
from app.sessions import service
from app.sse import (
    SSE_HEADERS,
    Done,
    Reset,
    Sources,
    Status,
    Token,
    sse,
    with_heartbeat,
)
from app.vectorstore.faiss_store import IndexIncompatible
from app.vectorstore.index_cache import get_index_cache
from app.web_search.base import SearchError

logger = logging.getLogger("app.api.chat")

router = APIRouter(prefix="/sessions", tags=["chat"])

# Generation concurrency semaphore and per-session locks
_semaphore: asyncio.Semaphore | None = None
_session_locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)


def _get_semaphore() -> asyncio.Semaphore:
    global _semaphore
    if _semaphore is None:
        settings = get_settings()
        _semaphore = asyncio.Semaphore(settings.max_concurrent_generations)
    return _semaphore


def get_embedder():
    from app.embeddings.ollama_embedder import OllamaEmbedder

    return OllamaEmbedder()


def get_router():
    from app.llm.gemini_client import GeminiClient
    from app.llm.ollama_client import OllamaClient
    from app.llm.router import LLMRouter

    settings = get_settings()
    ollama = OllamaClient()
    gemini = GeminiClient() if settings.gemini_api_key else None
    return LLMRouter(ollama, gemini, settings)


def get_search_provider():
    settings = get_settings()
    if settings.web_search_provider == "searxng":
        from app.web_search.searxng import SearxngProvider

        return SearxngProvider()
    else:
        from app.web_search.tavily import TavilyProvider

        return TavilyProvider()


class ChatRequest(BaseModel):
    message: str


@router.post("/{id}/chat")
async def chat_endpoint(
    id: str,
    body: ChatRequest,
    user: CurrentUser = Depends(current_user),
    embedder: Any = Depends(get_embedder),
    llm_router: Any = Depends(get_router),
    search_provider: Any = Depends(get_search_provider),
):
    session = await service.get_session(id, user.id)

    # Message validation
    clean_msg = body.message.strip()
    if not clean_msg or len(clean_msg) > 4000:
        raise AppError(
            422,
            "VALIDATION_ERROR",
            "Message must be between 1 and 4000 characters.",
        )

    # Per-session lock: if held -> 409 BUSY
    sess_lock = _session_locks[id]
    if sess_lock.locked():
        raise AppError(409, "BUSY", "Please wait for the current answer to finish.")

    # PDF session checks
    if session["type"] == "pdf":
        doc = await anyio.to_thread.run_sync(repository.get_document, id)
        if not doc:
            raise AppError(
                409, "DOCUMENT_NOT_READY", "No document uploaded for this session."
            )
        if doc["status"] == "processing":
            raise AppError(
                409, "DOCUMENT_NOT_READY", "Document is still processing."
            )
        if doc["status"] == "failed":
            raise AppError(
                409,
                "DOCUMENT_NOT_READY",
                doc.get("error_message") or "Document processing failed.",
            )

        # Check index compatibility
        try:
            get_index_cache().get(id)
        except IndexIncompatible:
            raise AppError(
                409,
                "INDEX_INCOMPATIBLE",
                "The search index is incompatible or missing. Run reindex or re-upload the PDF.",
            )

    sem = _get_semaphore()

    async def sse_generator():
        # Acquire lock and semaphore
        await sess_lock.acquire()
        await sem.acquire()
        try:
            # Load history
            history = await anyio.to_thread.run_sync(
                repository.last_messages, id, 8
            )

            if session["type"] == "pdf":
                pipeline = PdfRagPipeline(
                    embedder=embedder,
                    cache=get_index_cache(),
                    router=llm_router,
                )
                pipeline_stream = pipeline.answer_stream(id, clean_msg, history)
            else:
                from app.web_search.pipeline import WebChatPipeline

                web_pipe = WebChatPipeline(
                    provider=search_provider,
                    router=llm_router,
                )
                pipeline_stream = web_pipe.answer_stream(clean_msg, history)

            collected_sources: list[dict] = []
            final_message_text = ""
            model_used = None
            fallback = False
            grounded = None
            cited_list: list[str] = []
            generation_complete = False

            try:
                async for event in pipeline_stream:
                    if isinstance(event, Status):
                        yield sse("status", {"stage": event.stage})
                    elif isinstance(event, Sources):
                        collected_sources = event.sources
                        yield sse("sources", {"sources": event.sources})
                    elif isinstance(event, Token):
                        yield sse("token", {"text": event.text})
                    elif isinstance(event, Reset):
                        yield sse("reset", {})
                    elif isinstance(event, Done):
                        final_message_text = event.message_text
                        model_used = event.model_used
                        fallback = event.fallback
                        grounded = event.grounded
                        cited_list = event.cited
                        generation_complete = True

            except LLMUnavailable as e:
                yield sse("error", {"code": "LLM_UNAVAILABLE", "message": str(e)})
                return
            except EmbeddingError as e:
                yield sse("error", {"code": "EMBEDDING_UNAVAILABLE", "message": str(e)})
                return
            except IndexIncompatible as e:
                yield sse("error", {"code": "INDEX_INCOMPATIBLE", "message": str(e)})
                return
            except SearchError as e:
                yield sse("error", {"code": "SEARCH_UNAVAILABLE", "message": str(e)})
                return
            except Exception:
                logger.exception("Unexpected error in chat stream")
                yield sse(
                    "error",
                    {
                        "code": "INTERNAL",
                        "message": "An error occurred while generating the response.",
                    },
                )
                return

            if generation_complete:
                user_msg_id = uuid.uuid4().hex
                asst_msg_id = uuid.uuid4().hex

                user_msg = {
                    "id": user_msg_id,
                    "content": clean_msg,
                }
                asst_msg = {
                    "id": asst_msg_id,
                    "content": final_message_text,
                    "sources": collected_sources,
                    "model_used": model_used,
                    "fallback": fallback,
                    "grounded": grounded,
                }

                await anyio.to_thread.run_sync(
                    repository.add_message_pair, id, user_msg, asst_msg
                )

                yield sse(
                    "done",
                    {
                        "message_id": asst_msg_id,
                        "model_used": model_used,
                        "fallback": fallback,
                        "grounded": grounded,
                        "cited": cited_list,
                    },
                )

        finally:
            sem.release()
            sess_lock.release()

    return StreamingResponse(
        with_heartbeat(sse_generator()),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )
