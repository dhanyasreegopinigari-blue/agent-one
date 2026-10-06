from fastapi import APIRouter, Depends, Response, status

from app.auth.deps import CurrentUser, current_user
from app.sessions import service
from app.sessions.models import (
    CreateSessionRequest,
    MessageResponse,
    SessionResponse,
    UpdateSessionRequest,
)

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse)
async def create_session(
    body: CreateSessionRequest,
    user: CurrentUser = Depends(current_user),
):
    session = await service.create_session(user.id, body.type, body.title)
    return session


@router.get("", response_model=list[SessionResponse])
async def list_sessions(
    user: CurrentUser = Depends(current_user),
):
    sessions = await service.list_sessions(user.id)
    return sessions


@router.get("/{id}", response_model=SessionResponse)
async def get_session(
    id: str,
    user: CurrentUser = Depends(current_user),
):
    session = await service.get_session(id, user.id)
    return session


@router.patch("/{id}", response_model=SessionResponse)
async def update_session(
    id: str,
    body: UpdateSessionRequest,
    user: CurrentUser = Depends(current_user),
):
    session = await service.rename_session(id, user.id, body.title)
    return session


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    id: str,
    user: CurrentUser = Depends(current_user),
):
    await service.delete_session(id, user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{id}/messages", response_model=list[MessageResponse])
async def list_messages(
    id: str,
    user: CurrentUser = Depends(current_user),
):
    messages = await service.list_messages(id, user.id)
    return messages
