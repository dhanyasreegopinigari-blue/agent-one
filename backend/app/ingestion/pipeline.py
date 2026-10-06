import json
import logging
from dataclasses import asdict
from typing import Any

import anyio

from app.config import get_settings
from app.db import repository
from app.embeddings.base import EmbeddingError
from app.embeddings.ollama_embedder import OllamaEmbedder
from app.ingestion.chunker import chunk
from app.ingestion.cleaner import clean
from app.ingestion.pdf_parser import PyMuPdfParser
from app.ingestion.types import IngestionError
from app.vectorstore.faiss_store import FaissStore
from app.vectorstore.index_cache import get_index_cache

logger = logging.getLogger("app.ingestion.pipeline")
background_tasks = set()


def _get_embedder(override: Any = None):
    if override is not None:
        return override
    return OllamaEmbedder()


async def run_ingestion(session_id: str, embedder_override: Any = None) -> None:
    settings = get_settings()
    session_dir = settings.sessions_dir / session_id
    doc_path = session_dir / "doc.pdf"
    embedder = _get_embedder(embedder_override)

    try:
        # 1. Parsing
        await anyio.to_thread.run_sync(
            repository.update_document_progress,
            session_id,
            "processing",
            "parsing",
            5,
            None,
            None,
            None,
            None,
        )

        parser = PyMuPdfParser()
        parsed = await anyio.to_thread.run_sync(parser.parse, doc_path)

        # Check if session still exists
        if not await anyio.to_thread.run_sync(repository.get_document, session_id):
            return

        # 2. Chunking
        await anyio.to_thread.run_sync(
            repository.update_document_progress,
            session_id,
            "processing",
            "chunking",
            25,
            None,
            None,
            None,
            None,
        )

        cleaned_segs = await anyio.to_thread.run_sync(
            clean, parsed.segments, parsed.page_count
        )
        chunks = await anyio.to_thread.run_sync(
            chunk,
            cleaned_segs,
            settings.chunk_chars,
            settings.chunk_overlap_chars,
            settings.min_chunk_chars,
        )

        chunk_dicts = [asdict(c) for c in chunks]
        texts = [c.text for c in chunks]
        n_chunks = len(chunks)

        # 3. Embedding
        await anyio.to_thread.run_sync(
            repository.update_document_progress,
            session_id,
            "processing",
            "embedding",
            30,
            n_chunks,
            None,
            None,
            None,
        )

        # Embed in batches to update progress between 30 and 95
        batch_size = max(1, settings.embed_batch_size)
        all_vectors = []

        for i in range(0, len(texts), batch_size):
            if not await anyio.to_thread.run_sync(repository.get_document, session_id):
                return

            batch_texts = texts[i : i + batch_size]
            batch_vecs = await embedder.embed_documents(batch_texts)
            all_vectors.append(batch_vecs)

            # Calculate progress 30 -> 95
            frac = min(1.0, (i + len(batch_texts)) / max(1, len(texts)))
            prog = int(30 + frac * 65)
            await anyio.to_thread.run_sync(
                repository.update_document_progress,
                session_id,
                "processing",
                "embedding",
                prog,
                n_chunks,
                None,
                None,
                None,
            )

        import numpy as np

        if all_vectors:
            vectors = np.vstack(all_vectors)
        else:
            vectors = np.empty((0, embedder.dim or 0), dtype="float32")

        # 4. Indexing
        await anyio.to_thread.run_sync(
            repository.update_document_progress,
            session_id,
            "processing",
            "indexing",
            95,
            n_chunks,
            None,
            None,
            None,
        )

        store = await anyio.to_thread.run_sync(FaissStore.build, vectors)
        await anyio.to_thread.run_sync(
            store.save, session_dir, chunk_dicts, embedder.model
        )

        # Done
        await anyio.to_thread.run_sync(
            repository.update_document_progress,
            session_id,
            "ready",
            "done",
            100,
            n_chunks,
            None,
            None,
            embedder.model,
        )
        get_index_cache().invalidate(session_id)

    except IngestionError as e:
        logger.warning("IngestionError on session %s: %s", session_id, e.code)
        await anyio.to_thread.run_sync(
            repository.update_document_progress,
            session_id,
            "failed",
            "failed",
            0,
            None,
            e.code,
            str(e),
            None,
        )
    except EmbeddingError as e:
        logger.warning("EmbeddingError on session %s: %s", session_id, e)
        await anyio.to_thread.run_sync(
            repository.update_document_progress,
            session_id,
            "failed",
            "failed",
            0,
            None,
            "EMBEDDING_UNAVAILABLE",
            "The embedding model is unavailable. Check that Ollama is running and retry.",
            None,
        )
    except Exception:
        logger.exception("Unexpected error during ingestion on session %s", session_id)
        await anyio.to_thread.run_sync(
            repository.update_document_progress,
            session_id,
            "failed",
            "failed",
            0,
            None,
            "INTERNAL",
            "An internal error occurred during document processing.",
            None,
        )


async def reindex_session(session_id: str, embedder_override: Any = None) -> None:
    settings = get_settings()
    session_dir = settings.sessions_dir / session_id
    chunks_path = session_dir / "chunks.json"

    if not chunks_path.exists():
        from app.errors import AppError

        raise AppError(409, "INDEX_INCOMPATIBLE", "Chunks file missing; re-upload the PDF.")

    chunk_dicts = json.loads(chunks_path.read_text(encoding="utf-8"))
    texts = [c["text"] for c in chunk_dicts]
    embedder = _get_embedder(embedder_override)

    await anyio.to_thread.run_sync(
        repository.update_document_progress,
        session_id,
        "processing",
        "embedding",
        30,
        len(chunk_dicts),
        None,
        None,
        None,
    )

    vectors = await embedder.embed_documents(texts)
    store = await anyio.to_thread.run_sync(FaissStore.build, vectors)
    await anyio.to_thread.run_sync(
        store.save, session_dir, chunk_dicts, embedder.model
    )

    await anyio.to_thread.run_sync(
        repository.update_document_progress,
        session_id,
        "ready",
        "done",
        100,
        len(chunk_dicts),
        None,
        None,
        embedder.model,
    )
    get_index_cache().invalidate(session_id)
