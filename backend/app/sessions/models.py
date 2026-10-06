from typing import Any, Literal

from pydantic import BaseModel, Field


class CreateSessionRequest(BaseModel):
    type: Literal["pdf", "web"]
    title: str | None = Field(default=None, max_length=80)


class UpdateSessionRequest(BaseModel):
    title: str = Field(min_length=1, max_length=80)


class DocumentInfo(BaseModel):
    filename: str
    size_bytes: int
    page_count: int | None = None
    n_chunks: int | None = None
    status: Literal["processing", "ready", "failed"]
    stage: str
    progress: int
    error_code: str | None = None
    error_message: str | None = None


class SessionResponse(BaseModel):
    id: str
    type: Literal["pdf", "web"]
    title: str
    created_at: str
    updated_at: str
    document: DocumentInfo | None = None


class MessageResponse(BaseModel):
    id: str
    role: Literal["user", "assistant"]
    content: str
    sources: list[dict[str, Any]] = Field(default_factory=list)
    model_used: str | None = None
    fallback: bool = False
    grounded: bool | None = None
    created_at: str
