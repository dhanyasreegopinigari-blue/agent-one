import logging
from typing import Any

from app.rag.prompts import CONDENSE_SYSTEM_PROMPT

logger = logging.getLogger("app.rag.query_condenser")


async def condense(question: str, history: list[dict], router: Any) -> str:
    if not history:
        return question

    try:
        from app.llm.base import LLMRequest, Msg

        # Last 4 turns (up to 8 messages)
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
        logger.warning("Query condensation failed, using raw question: %s", e)
        return question
