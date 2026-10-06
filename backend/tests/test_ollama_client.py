import json

import httpx
import pytest
import respx

from app.llm.base import LLMRequest, Msg
from app.llm.ollama_client import OllamaClient, OllamaError


@pytest.mark.asyncio
@respx.mock
async def test_ollama_client_success_and_num_ctx(temp_settings):
    ndjson_body = (
        json.dumps({"message": {"content": "Hello "}, "done": False})
        + "\n"
        + json.dumps({"message": {"content": "world!"}, "done": True})
        + "\n"
    )

    route = respx.post(f"{temp_settings.ollama_base_url}/api/chat").mock(
        return_value=httpx.Response(200, text=ndjson_body)
    )

    client = OllamaClient()
    req = LLMRequest(system="System instructions", messages=[Msg("user", "Hi")], temperature=0.1)

    result = await client.complete(req)
    assert result == "Hello world!"
    assert route.called
    last_req = json.loads(route.calls.last.request.content)
    assert last_req["options"]["num_ctx"] == temp_settings.ollama_num_ctx
    assert last_req["options"]["temperature"] == 0.1


@pytest.mark.asyncio
@respx.mock
async def test_ollama_client_error_line_raises(temp_settings):
    ndjson_body = json.dumps({"error": "model 'nonexistent' not found"}) + "\n"

    respx.post(f"{temp_settings.ollama_base_url}/api/chat").mock(
        return_value=httpx.Response(200, text=ndjson_body)
    )

    client = OllamaClient()
    req = LLMRequest(system="System", messages=[Msg("user", "Hi")], temperature=0.1)

    with pytest.raises(OllamaError, match="model 'nonexistent' not found"):
        await client.complete(req)


@pytest.mark.asyncio
@respx.mock
async def test_ollama_client_http_404_raises(temp_settings):
    respx.post(f"{temp_settings.ollama_base_url}/api/chat").mock(
        return_value=httpx.Response(404, text="Not Found")
    )

    client = OllamaClient()
    req = LLMRequest(system="System", messages=[Msg("user", "Hi")], temperature=0.1)

    with pytest.raises(OllamaError, match="HTTP 404"):
        await client.complete(req)


@pytest.mark.asyncio
@respx.mock
async def test_ollama_client_zero_tokens_raises(temp_settings):
    ndjson_body = json.dumps({"message": {"content": ""}, "done": True}) + "\n"

    respx.post(f"{temp_settings.ollama_base_url}/api/chat").mock(
        return_value=httpx.Response(200, text=ndjson_body)
    )

    client = OllamaClient()
    req = LLMRequest(system="System", messages=[Msg("user", "Hi")], temperature=0.1)

    with pytest.raises(OllamaError, match="zero tokens"):
        await client.complete(req)
