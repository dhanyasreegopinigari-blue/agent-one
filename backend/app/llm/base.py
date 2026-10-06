from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Literal, Protocol


@dataclass
class Msg:
    role: Literal["user", "assistant"]
    content: str


@dataclass
class LLMRequest:
    system: str
    messages: list[Msg]
    temperature: float
    max_tokens: int | None = None


class LLMUnavailable(Exception):
    pass


class LLMClient(Protocol):
    name: str
    model: str

    def stream(self, req: LLMRequest) -> AsyncIterator[str]: ...

    async def complete(self, req: LLMRequest) -> str: ...
