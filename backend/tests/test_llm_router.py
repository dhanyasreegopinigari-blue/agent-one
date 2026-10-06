from collections.abc import AsyncIterator

import pytest

from app.llm.base import LLMRequest, LLMUnavailable, Msg
from app.llm.gemini_client import GeminiError
from app.llm.ollama_client import OllamaError
from app.llm.router import Done, LLMRouter, Reset, Token


class MockLLM:
    def __init__(self, name: str, model: str, output: list[str] | Exception):
        self.name = name
        self.model = model
        self.output = output
        self.call_count = 0

    async def stream(self, req: LLMRequest) -> AsyncIterator[str]:
        self.call_count += 1
        if isinstance(self.output, Exception):
            raise self.output
        for item in self.output:
            if isinstance(item, Exception):
                raise item
            yield item

    async def complete(self, req: LLMRequest) -> str:
        parts = []
        async for t in self.stream(req):
            parts.append(t)
        return "".join(parts)


class DummyRouterSettings:
    ollama_retries = 1
    ollama_breaker_fails = 3
    ollama_breaker_cooldown_s = 30
    allow_gemini_fallback = True


@pytest.mark.asyncio
async def test_router_ollama_ok_gemini_never_called():
    ollama = MockLLM("ollama", "llama3.1:8b", ["Hello", " world"])
    gemini = MockLLM("gemini", "gemini-3-flash", ["Fallback"])
    router = LLMRouter(ollama, gemini, DummyRouterSettings())

    events = [e async for e in router.stream(LLMRequest("sys", [Msg("user", "hi")], 0.1))]
    assert ollama.call_count == 1
    assert gemini.call_count == 0
    tokens = [e.text for e in events if isinstance(e, Token)]
    assert "".join(tokens) == "Hello world"
    done = [e for e in events if isinstance(e, Done)][0]
    assert done.model == "llama3.1:8b"
    assert done.fallback is False


@pytest.mark.asyncio
async def test_router_connect_error_falls_back_to_gemini():
    ollama = MockLLM("ollama", "llama3.1:8b", OllamaError("conn fail", is_connect_error=True))
    gemini = MockLLM("gemini", "gemini-3-flash", ["Gemini answer"])
    router = LLMRouter(ollama, gemini, DummyRouterSettings())

    events = [e async for e in router.stream(LLMRequest("sys", [Msg("user", "hi")], 0.1))]
    # retried once on connect error => 2 calls
    assert ollama.call_count == 2
    assert gemini.call_count == 1
    tokens = [e.text for e in events if isinstance(e, Token)]
    assert "".join(tokens) == "Gemini answer"
    done = [e for e in events if isinstance(e, Done)][0]
    assert done.model == "gemini-3-flash"
    assert done.fallback is True


@pytest.mark.asyncio
async def test_router_midstream_failure_yields_reset_then_gemini():
    ollama = MockLLM("ollama", "llama3.1:8b", ["Partial start", OllamaError("crash mid-stream")])
    gemini = MockLLM("gemini", "gemini-3-flash", ["Complete answer"])
    router = LLMRouter(ollama, gemini, DummyRouterSettings())

    events = [e async for e in router.stream(LLMRequest("sys", [Msg("user", "hi")], 0.1))]
    assert any(isinstance(e, Reset) for e in events)
    done = [e for e in events if isinstance(e, Done)][0]
    assert done.model == "gemini-3-flash"
    assert done.fallback is True


@pytest.mark.asyncio
async def test_router_both_fail_raises_unavailable():
    ollama = MockLLM("ollama", "llama3.1:8b", OllamaError("ollama down"))
    gemini = MockLLM("gemini", "gemini-3-flash", GeminiError("gemini down"))
    router = LLMRouter(ollama, gemini, DummyRouterSettings())

    with pytest.raises(LLMUnavailable):
        async for _ in router.stream(LLMRequest("sys", [Msg("user", "hi")], 0.1)):
            pass


@pytest.mark.asyncio
async def test_router_fallback_disabled_raises_unavailable():
    ollama = MockLLM("ollama", "llama3.1:8b", OllamaError("ollama down"))
    gemini = MockLLM("gemini", "gemini-3-flash", ["Never reached"])
    settings = DummyRouterSettings()
    settings.allow_gemini_fallback = False
    router = LLMRouter(ollama, gemini, settings)

    with pytest.raises(LLMUnavailable):
        async for _ in router.stream(LLMRequest("sys", [Msg("user", "hi")], 0.1)):
            pass
    assert gemini.call_count == 0


@pytest.mark.asyncio
async def test_router_circuit_breaker():
    current_time = 100.0

    def fake_clock():
        return current_time

    ollama = MockLLM("ollama", "llama3.1:8b", OllamaError("down"))
    gemini = MockLLM("gemini", "gemini-3-flash", ["Fallback"])
    settings = DummyRouterSettings()
    settings.ollama_breaker_fails = 3
    settings.ollama_breaker_cooldown_s = 30
    router = LLMRouter(ollama, gemini, settings, clock=fake_clock)

    req = LLMRequest("sys", [Msg("user", "hi")], 0.1)

    # 3 failures open the breaker
    for _ in range(3):
        async for _ in router.stream(req):
            pass

    call_count_after_3 = ollama.call_count

    # 4th call: during cooldown, breaker is open, skips Ollama completely
    current_time += 10.0  # 10s < 30s cooldown
    async for _ in router.stream(req):
        pass
    assert ollama.call_count == call_count_after_3  # did not call Ollama!

    # 5th call: after cooldown (35s), breaker half-open, tries Ollama
    current_time += 25.0  # now 35s since open
    async for _ in router.stream(req):
        pass
    assert ollama.call_count > call_count_after_3
