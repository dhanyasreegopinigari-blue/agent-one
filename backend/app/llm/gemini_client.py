from collections.abc import AsyncIterator

from google import genai
from google.genai import types

from app.config import get_settings
from app.llm.base import LLMRequest


class GeminiError(Exception):
    pass


class GeminiClient:
    name = "gemini"

    def __init__(self, model: str | None = None, api_key: str | None = None):
        settings = get_settings()
        self.model = model or settings.gemini_model
        key = api_key or settings.gemini_api_key
        if not key:
            raise GeminiError("Gemini API key is not configured")
        self.client = genai.Client(api_key=key)

    async def stream(self, req: LLMRequest) -> AsyncIterator[str]:
        contents = [
            types.Content(
                role="user" if m.role == "user" else "model",
                parts=[types.Part.from_text(text=m.content)],
            )
            for m in req.messages
        ]
        cfg = types.GenerateContentConfig(
            system_instruction=req.system,
            temperature=req.temperature,
            max_output_tokens=req.max_tokens,
        )

        token_emitted = False
        try:
            stream_result = await self.client.aio.models.generate_content_stream(
                model=self.model,
                contents=contents,
                config=cfg,
            )
            async for chunk in stream_result:
                if chunk.text:
                    token_emitted = True
                    yield chunk.text
        except Exception as e:
            raise GeminiError(f"Gemini streaming failed: {e}") from e

        if not token_emitted:
            raise GeminiError("Gemini stream returned zero tokens.")

    async def complete(self, req: LLMRequest) -> str:
        parts = []
        async for t in self.stream(req):
            parts.append(t)
        return "".join(parts)
