import re
from collections.abc import AsyncIterator
from typing import Any

from app.config import get_settings
from app.rag.prompts import (
    PDF_NOT_FOUND_MESSAGE,
    PDF_SYSTEM_PROMPT,
    build_user_message,
)
from app.rag.query_condenser import condense
from app.rag.retriever import hit_to_source, retrieve
from app.sse import Done, PipelineEvent, Reset, Sources, Status, Token


class PdfRagPipeline:
    def __init__(self, embedder: Any, cache: Any, router: Any):
        self.embedder = embedder
        self.cache = cache
        self.router = router

    async def answer_stream(
        self,
        session_id: str,
        question: str,
        history: list[dict[str, Any]],
    ) -> AsyncIterator[PipelineEvent]:
        settings = get_settings()

        # 1. Condense question
        yield Status("retrieving")
        standalone = await condense(question, history, self.router)

        # 2. Retrieve hits
        hits = await retrieve(
            standalone,
            session_id,
            embedder=self.embedder,
            cache=self.cache,
            settings=settings,
        )

        # 3. Gate
        if not hits:
            yield Sources([])
            yield Token(PDF_NOT_FOUND_MESSAGE)
            yield Done(
                message_text=PDF_NOT_FOUND_MESSAGE,
                model_used=None,
                fallback=False,
                grounded=False,
                cited=[],
            )
            return

        # 4. Sources
        sources_list = [hit_to_source(h) for h in hits]
        yield Sources(sources_list)
        yield Status("generating")

        # 5. Build prompt & history
        from app.llm.base import LLMRequest, Msg

        history_msgs: list[Msg] = []
        # last history_turns turns (2 msgs per turn)
        turns_to_take = settings.history_turns * 2
        for h in history[-turns_to_take:]:
            content = h["content"]
            if h["role"] == "assistant" and len(content) > 1200:
                content = content[:1200]
            history_msgs.append(Msg(role=h["role"], content=content))

        user_content = build_user_message(question, hits)
        messages = history_msgs + [Msg(role="user", content=user_content)]

        req = LLMRequest(
            system=PDF_SYSTEM_PROMPT,
            messages=messages,
            temperature=settings.temperature,
            max_tokens=settings.max_output_tokens,
        )

        # 6. Stream and buffer sentinel
        labels = {h.label for h in hits}
        is_buffering = True
        buffer = ""
        full_text = ""
        model_used = None
        fallback = False

        from app.llm.router import Done as RouterDone
        from app.llm.router import Reset as RouterReset
        from app.llm.router import Token as RouterToken

        async for event in self.router.stream(req, allow_fallback=True):
            if isinstance(event, RouterReset):
                is_buffering = True
                buffer = ""
                full_text = ""
                yield Reset()
                continue

            if isinstance(event, RouterToken):
                if is_buffering:
                    buffer += event.text
                    non_ws = len(re.sub(r"\s+", "", buffer))
                    if non_ws >= 16:
                        # Check sentinel
                        if buffer.lstrip().upper().startswith("NOT_IN_DOCUMENT"):
                            yield Token(PDF_NOT_FOUND_MESSAGE)
                            yield Done(
                                message_text=PDF_NOT_FOUND_MESSAGE,
                                model_used=None,
                                fallback=False,
                                grounded=False,
                                cited=[],
                            )
                            return
                        else:
                            is_buffering = False
                            full_text += buffer
                            yield Token(buffer)
                            buffer = ""
                else:
                    full_text += event.text
                    yield Token(event.text)

            elif isinstance(event, RouterDone):
                model_used = event.model
                fallback = event.fallback

        # Check buffer if stream ended while still buffering
        if is_buffering:
            if buffer.lstrip().upper().startswith("NOT_IN_DOCUMENT"):
                yield Token(PDF_NOT_FOUND_MESSAGE)
                yield Done(
                    message_text=PDF_NOT_FOUND_MESSAGE,
                    model_used=None,
                    fallback=False,
                    grounded=False,
                    cited=[],
                )
                return
            elif buffer:
                full_text += buffer
                yield Token(buffer)

        # 7. Post-process citations
        cited = sorted({m for m in re.findall(r"\[(S\d+)\]", full_text) if m in labels})
        # Remove citations to unknown labels
        final_text = re.sub(
            r"\[(S\d+)\]",
            lambda m: m.group(0) if m.group(1) in labels else "",
            full_text,
        )

        yield Done(
            message_text=final_text,
            model_used=model_used,
            fallback=fallback,
            grounded=True,
            cited=cited,
        )
