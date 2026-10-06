import anyio
from fastapi import Header
from pydantic import BaseModel

from app.auth.jwt_verifier import verify_token
from app.config import get_settings
from app.errors import AppError


class CurrentUser(BaseModel):
    id: str
    is_anonymous: bool = False


async def current_user(authorization: str | None = Header(default=None)) -> CurrentUser:
    s = get_settings()
    if s.auth_disabled:
        return CurrentUser(id=s.dev_user_id)
    if not authorization or not authorization.lower().startswith("bearer "):
        raise AppError(401, "UNAUTHENTICATED", "Missing bearer token")
    claims = await anyio.to_thread.run_sync(verify_token, authorization[7:].strip())
    return CurrentUser(id=claims["sub"], is_anonymous=bool(claims.get("is_anonymous", False)))
