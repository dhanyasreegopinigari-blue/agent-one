import asyncio
import json
from dataclasses import dataclass
from typing import Any

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "X-Accel-Buffering": "no",
    "Connection": "keep-alive",
}


@dataclass
class Status:
    stage: str


@dataclass
class Sources:
    sources: list[dict[str, Any]]


@dataclass
class Token:
    text: str


@dataclass
class Reset:
    pass


@dataclass
class Done:
    message_text: str
    model_used: str | None
    fallback: bool
    grounded: bool | None
    cited: list[str]


PipelineEvent = Status | Sources | Token | Reset | Done


def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def with_heartbeat(agen, interval: float = 15.0):
    """Yield items from agen; emit an SSE comment every `interval`s of silence
    so proxies do not time out during cold model loads."""
    it = agen.__aiter__()
    pending = asyncio.ensure_future(it.__anext__())
    try:
        while True:
            done, _ = await asyncio.wait({pending}, timeout=interval)
            if not done:
                yield ": ping\n\n"
                continue
            try:
                item = pending.result()
            except StopAsyncIteration:
                return
            yield item
            pending = asyncio.ensure_future(it.__anext__())
    finally:
        pending.cancel()
        if hasattr(agen, "aclose"):
            await agen.aclose()
