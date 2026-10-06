import time
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from app.llm.base import LLMClient, LLMRequest, LLMUnavailable
from app.llm.gemini_client import GeminiError
from app.llm.ollama_client import OllamaError


@dataclass
class Token:
    text: str


@dataclass
class Reset:
    pass


@dataclass
class Done:
    model: str
    fallback: bool


class LLMRouter:
    def __init__(
        self,
        ollama: LLMClient,
        gemini: LLMClient | None,
        settings: Any,
        clock=time.monotonic,
    ):
        self.ollama = ollama
        self.gemini = gemini
        self.settings = settings
        self.clock = clock
        self.consecutive_fails = 0
        self.breaker_opened_at: float | None = None

    def _breaker_open(self) -> bool:
        if self.breaker_opened_at is None:
            return False
        return (self.clock() - self.breaker_opened_at) < self.settings.ollama_breaker_cooldown_s

    def _breaker_success(self) -> None:
        self.consecutive_fails = 0
        self.breaker_opened_at = None

    def _breaker_failure(self) -> None:
        self.consecutive_fails += 1
        if self.consecutive_fails >= self.settings.ollama_breaker_fails:
            self.breaker_opened_at = self.clock()

    async def stream(
        self, req: LLMRequest, allow_fallback: bool = True
    ) -> AsyncIterator[Token | Reset | Done]:
        emitted = False
        if not self._breaker_open():
            for attempt in range(self.settings.ollama_retries + 1):
                try:
                    async for t in self.ollama.stream(req):
                        emitted = True
                        yield Token(t)
                    self._breaker_success()
                    yield Done(self.ollama.model, fallback=False)
                    return
                except OllamaError as e:
                    if emitted:
                        break
                    if attempt < self.settings.ollama_retries and getattr(e, "is_connect_error", False):
                        continue
                    break
            self._breaker_failure()

        # ---- fallback path ----
        if not (allow_fallback and self.gemini and self.settings.allow_gemini_fallback):
            raise LLMUnavailable("The local model is unavailable and no fallback is configured.")

        if emitted:
            yield Reset()

        try:
            async for t in self.gemini.stream(req):
                yield Token(t)
            yield Done(self.gemini.model, fallback=True)
        except GeminiError as e:
            raise LLMUnavailable(f"Both the local model and the fallback failed: {e}") from e

    async def complete(
        self, req: LLMRequest, allow_fallback: bool = True
    ) -> tuple[str, str, bool]:
        parts: list[str] = []
        model_used = ""
        fallback = False
        async for ev in self.stream(req, allow_fallback=allow_fallback):
            if isinstance(ev, Reset):
                parts.clear()
            elif isinstance(ev, Token):
                parts.append(ev.text)
            elif isinstance(ev, Done):
                model_used = ev.model
                fallback = ev.fallback
        return "".join(parts), model_used, fallback
