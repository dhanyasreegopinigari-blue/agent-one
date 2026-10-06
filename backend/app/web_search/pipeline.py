import logging
import re
from collections.abc import AsyncIterator
from typing import Any

from app.config import get_settings
from app.llm.base import LLMRequest, Msg
from app.llm.router import Done as RouterDone
from app.llm.router import Reset as RouterReset
from app.llm.router import Token as RouterToken
from app.web_search.base import SearchProvider
from app.web_search.prompts import (
    CONDENSE_SYSTEM_PROMPT,
    WEB_NO_RESULTS_MESSAGE,
    build_web_user_message,
    get_web_system_prompt,
)

logger = logging.getLogger("app.web_search.pipeline")


from app.sse import Done, PipelineEvent, Reset, Sources, Status, Token


async def _condense_web(question: str, history: list[dict[str, Any]], router: Any) -> str:
    if not history:
        return question

    try:
        recent_history = history[-8:]
        messages = [
            Msg(role=m["role"], content=m["content"][:1200])
            for m in recent_history
        ]
        messages.append(Msg(role="user", content=question))

        req = LLMRequest(
            system=CONDENSE_SYSTEM_PROMPT,
            messages=messages,
            temperature=0.0,
            max_tokens=128,
        )

        res_text, _, _ = await router.complete(req, allow_fallback=False)
        cleaned = res_text.strip()
        if not cleaned or len(cleaned) > 500:
            return question
        return cleaned
    except Exception as e:
        logger.warning("Web query condensation failed: %s", e)
        return question


class WebChatPipeline:
    def __init__(self, provider: SearchProvider, router: Any):
        self.provider = provider
        self.router = router

    async def answer_stream(
        self,
        question: str,
        history: list[dict[str, Any]],
    ) -> AsyncIterator[PipelineEvent]:
        settings = get_settings()

        # 1. Search
        yield Status("searching")
        standalone = await _condense_web(question, history, self.router)

        results = await self.provider.search(standalone, settings.web_max_results)
        if not results:
            yield Sources([])
            yield Token(WEB_NO_RESULTS_MESSAGE)
            yield Done(
                message_text=WEB_NO_RESULTS_MESSAGE,
                model_used=None,
                fallback=False,
                grounded=False,
                cited=[],
            )
            return

        # 2. Sources
        sources_list = [
            {
                "id": f"W{idx}",
                "title": r.title,
                "url": r.url,
                "snippet": r.snippet,
            }
            for idx, r in enumerate(results, 1)
        ]
        yield Sources(sources_list)
        yield Status("generating")

        # 3. Build messages
        history_msgs: list[Msg] = []
        turns_to_take = settings.history_turns * 2
        for h in history[-turns_to_take:]:
            content = h["content"]
            if h["role"] == "assistant" and len(content) > 1200:
                content = content[:1200]
            history_msgs.append(Msg(role=h["role"], content=content))

        user_content = build_web_user_message(question, results)
        messages = history_msgs + [Msg(role="user", content=user_content)]

        req = LLMRequest(
            system=get_web_system_prompt(),
            messages=messages,
            temperature=settings.temperature,
            max_tokens=settings.max_output_tokens,
        )

        # 4. Stream tokens
        labels = {s["id"] for s in sources_list}
        full_text = ""
        model_used = None
        fallback = False

        async for event in self.router.stream(req, allow_fallback=True):
            if isinstance(event, RouterReset):
                full_text = ""
                yield Reset()
            elif isinstance(event, RouterToken):
                full_text += event.text
                yield Token(event.text)
            elif isinstance(event, RouterDone):
                model_used = event.model
                fallback = event.fallback

        cited = sorted({m for m in re.findall(r"\[(W\d+)\]", full_text) if m in labels})
        final_text = re.sub(
            r"\[(W\d+)\]",
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
