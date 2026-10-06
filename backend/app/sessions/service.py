import re
import shutil

import anyio

from app.config import get_settings
from app.db import repository
from app.errors import AppError

SESSION_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")


def validate_session_id(session_id: str) -> None:
    if not SESSION_ID_PATTERN.match(session_id):
        raise AppError(404, "NOT_FOUND", "Session not found")


async def create_session(user_id: str, session_type: str, title: str | None = None) -> dict:
    settings = get_settings()
    count = await anyio.to_thread.run_sync(repository.count_sessions, user_id)
    if count >= settings.max_sessions_per_user:
        raise AppError(403, "SESSION_LIMIT", "Maximum session limit reached")

    return await anyio.to_thread.run_sync(
        repository.create_session, user_id, session_type, title
    )


async def get_session(session_id: str, user_id: str) -> dict:
    validate_session_id(session_id)
    session = await anyio.to_thread.run_sync(repository.get_session, session_id, user_id)
    if not session:
        raise AppError(404, "NOT_FOUND", "Session not found")
    return session


async def list_sessions(user_id: str) -> list[dict]:
    return await anyio.to_thread.run_sync(repository.list_sessions, user_id)


async def rename_session(session_id: str, user_id: str, title: str) -> dict:
    validate_session_id(session_id)
    session = await anyio.to_thread.run_sync(
        repository.rename_session, session_id, user_id, title
    )
    if not session:
        raise AppError(404, "NOT_FOUND", "Session not found")
    return session


async def delete_session(session_id: str, user_id: str) -> None:
    validate_session_id(session_id)
    deleted = await anyio.to_thread.run_sync(
        repository.delete_session, session_id, user_id
    )
    if not deleted:
        raise AppError(404, "NOT_FOUND", "Session not found")

    # Remove session directory
    settings = get_settings()
    session_dir = settings.sessions_dir / session_id
    if session_dir.exists():
        await anyio.to_thread.run_sync(shutil.rmtree, session_dir, True)

    # Invalidate index cache if vectorstore index_cache is available
    try:
        from app.vectorstore.index_cache import get_index_cache
        get_index_cache().invalidate(session_id)
    except (ImportError, AttributeError):
        pass


async def list_messages(session_id: str, user_id: str) -> list[dict]:
    # Ensure session exists and is owned by the user
    await get_session(session_id, user_id)
    return await anyio.to_thread.run_sync(repository.list_messages, session_id)
