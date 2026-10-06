import asyncio
import json
import logging
from collections.abc import AsyncIterator

import httpx

from app.config import get_settings
from app.llm.base import LLMRequest

logger = logging.getLogger("app.llm.ollama_client")


class OllamaError(Exception):
    def __init__(self, message: str, is_connect_error: bool = False):
        super().__init__(message)
        self.is_connect_error = is_connect_error


class OllamaClient:
    name = "ollama"

    def __init__(self, model: str | None = None, base_url: str | None = None):
        settings = get_settings()
        self.model = model or settings.ollama_chat_model
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")

    async def stream(self, req: LLMRequest) -> AsyncIterator[str]:
        settings = get_settings()
        url = f"{self.base_url}/api/chat"

        chat_messages = [{"role": "system", "content": req.system}]
        for m in req.messages:
            chat_messages.append({"role": m.role, "content": m.content})

        options = {
            "temperature": req.temperature,
            "num_ctx": settings.ollama_num_ctx,
        }
        if req.max_tokens is not None:
            options["num_predict"] = req.max_tokens

        payload = {
            "model": self.model,
            "messages": chat_messages,
            "stream": True,
            "keep_alive": settings.ollama_keep_alive,
            "options": options,
        }

        token_emitted = False
        timeout = httpx.Timeout(
            settings.ollama_idle_timeout_s,
            connect=settings.ollama_connect_timeout_s,
        )

        try:
            async with (
                httpx.AsyncClient(timeout=timeout) as client,
                client.stream("POST", url, json=payload) as response,
            ):
                if response.status_code != 200:
                    body = await response.aread()
                    raise OllamaError(
                        f"Ollama returned HTTP {response.status_code}: {body.decode('utf-8', errors='ignore')[:200]}"
                    )

                lines_iter = response.aiter_lines().__aiter__()

                # First token wait timeout
                try:
                    first_line = await asyncio.wait_for(
                        lines_iter.__anext__(),
                        timeout=settings.ollama_first_token_timeout_s,
                    )
                except StopAsyncIteration:
                    raise OllamaError("Stream ended without any response.") from None
                except TimeoutError:
                    raise OllamaError("Timed out waiting for first token from Ollama.") from None

                # Process first line
                token = self._parse_line(first_line)
                if token:
                    token_emitted = True
                    yield token

                # Process remaining lines with idle timeout
                while True:
                    try:
                        line = await asyncio.wait_for(
                            lines_iter.__anext__(),
                            timeout=settings.ollama_idle_timeout_s,
                        )
                    except StopAsyncIteration:
                        break
                    except TimeoutError:
                        raise OllamaError("Ollama stream idle timeout exceeded.") from None

                    token = self._parse_line(line)
                    if token:
                        token_emitted = True
                        yield token

        except httpx.ConnectError as e:
            raise OllamaError(f"Failed to connect to Ollama: {e}", is_connect_error=True) from e
        except httpx.HTTPError as e:
            raise OllamaError(f"HTTP error during Ollama call: {e}") from e

        if not token_emitted:
            raise OllamaError("Ollama returned an empty response with zero tokens.")

    def _parse_line(self, line: str) -> str:
        line = line.strip()
        if not line:
            return ""
        try:
            data = json.loads(line)
        except Exception as e:
            raise OllamaError(f"Failed to parse Ollama NDJSON line: {e}") from e

        if "error" in data:
            raise OllamaError(f"Ollama error: {data['error']}")

        msg = data.get("message", {})
        return msg.get("content", "")

    async def complete(self, req: LLMRequest) -> str:
        parts = []
        async for t in self.stream(req):
            parts.append(t)
        return "".join(parts)


async def warm_models() -> None:
    settings = get_settings()
    base = settings.ollama_base_url.rstrip("/")
    timeout = httpx.Timeout(10.0, connect=3.0)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            # Warm chat model
            await client.post(
                f"{base}/api/chat",
                json={
                    "model": settings.ollama_chat_model,
                    "messages": [],
                    "keep_alive": settings.ollama_keep_alive,
                },
            )
            # Warm embed model
            await client.post(
                f"{base}/api/embed",
                json={
                    "model": settings.ollama_embed_model,
                    "input": ["warmup"],
                    "keep_alive": settings.ollama_keep_alive,
                },
            )
    except Exception as e:
        logger.warning("Failed to warm Ollama models: %s", e)
