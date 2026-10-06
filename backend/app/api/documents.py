import asyncio
import re
import urllib.parse
from pathlib import Path

import anyio
import pymupdf
from fastapi import APIRouter, Depends, File, Header, Response, UploadFile, status
from fastapi.responses import FileResponse

from app.auth.deps import CurrentUser, current_user
from app.config import get_settings
from app.db import repository
from app.errors import AppError
from app.ingestion.pipeline import background_tasks, reindex_session, run_ingestion
from app.sessions import service
from app.sessions.models import SessionResponse

router = APIRouter(prefix="/sessions", tags=["documents"])


def _sanitize_filename(name: str) -> str:
    cleaned = Path(name).name
    cleaned = re.sub(r"[^\w\-. ]", "_", cleaned)
    return cleaned[:120] if cleaned else "document.pdf"


@router.post("/{id}/document", response_model=SessionResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    id: str,
    file: UploadFile = File(...),
    content_length: int | None = Header(default=None),
    user: CurrentUser = Depends(current_user),
):
    session = await service.get_session(id, user.id)
    if session["type"] != "pdf":
        raise AppError(409, "WRONG_SESSION_TYPE", "Cannot upload documents to a web chat session.")

    existing_doc = await anyio.to_thread.run_sync(repository.get_document, id)
    if existing_doc:
        if existing_doc["status"] in ("processing", "ready"):
            raise AppError(409, "DOCUMENT_EXISTS", "A document is already uploaded for this session.")
        # If failed, delete old document row to allow retry
        await anyio.to_thread.run_sync(repository.delete_document, id)

    settings = get_settings()
    max_bytes = settings.max_upload_mb * 1024 * 1024

    if content_length and content_length > max_bytes:
        raise AppError(413, "FILE_TOO_LARGE", f"File exceeds maximum upload size of {settings.max_upload_mb} MB.")

    session_dir = settings.sessions_dir / id
    session_dir.mkdir(parents=True, exist_ok=True)
    doc_path = session_dir / "doc.pdf"

    # Stream upload in 1 MiB chunks
    total_bytes = 0
    chunk_size = 1024 * 1024
    first_chunk = bytearray()

    try:
        with open(doc_path, "wb") as out_file:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > max_bytes:
                    out_file.close()
                    if doc_path.exists():
                        doc_path.unlink()
                    raise AppError(
                        413,
                        "FILE_TOO_LARGE",
                        f"File exceeds maximum upload size of {settings.max_upload_mb} MB.",
                    )
                if len(first_chunk) < 1024:
                    first_chunk.extend(chunk[: 1024 - len(first_chunk)])
                out_file.write(chunk)
    except AppError:
        raise
    except Exception as e:
        if doc_path.exists():
            doc_path.unlink()
        raise AppError(500, "INTERNAL", f"Upload failed: {e}") from e

    # Magic byte check: %PDF- in first 1024 bytes
    if b"%PDF-" not in bytes(first_chunk):
        if doc_path.exists():
            doc_path.unlink()
        raise AppError(415, "NOT_A_PDF", "The uploaded file is not a valid PDF document.")

    # Synchronous quick validation via PyMuPDF
    try:
        doc = pymupdf.open(doc_path)
    except Exception as e:
        if doc_path.exists():
            doc_path.unlink()
        raise AppError(422, "PDF_CORRUPT", f"The PDF is corrupt or cannot be opened: {e}") from e

    try:
        if doc.needs_pass:
            if doc_path.exists():
                doc_path.unlink()
            raise AppError(422, "PDF_ENCRYPTED", "This PDF is password-protected.")

        if doc.page_count > settings.max_pages:
            if doc_path.exists():
                doc_path.unlink()
            raise AppError(
                422,
                "PDF_TOO_MANY_PAGES",
                f"PDF has {doc.page_count} pages (maximum allowed is {settings.max_pages}).",
            )
        page_count = doc.page_count
    finally:
        doc.close()

    filename = _sanitize_filename(file.filename or "document.pdf")
    await anyio.to_thread.run_sync(
        repository.upsert_document,
        id,
        filename,
        total_bytes,
        page_count,
        "processing",
        "parsing",
        0,
    )

    # Rename default session title
    if session["title"] == "New PDF chat":
        base_name = Path(filename).stem[:60]
        await service.rename_session(id, user.id, base_name)

    # Start ingestion task
    task = asyncio.create_task(run_ingestion(id))
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)

    updated_session = await service.get_session(id, user.id)
    return updated_session


@router.get("/{id}/status")
async def get_document_status(
    id: str,
    user: CurrentUser = Depends(current_user),
):
    await service.get_session(id, user.id)
    doc = await anyio.to_thread.run_sync(repository.get_document, id)
    if not doc:
        raise AppError(404, "NOT_FOUND", "No document found for this session.")

    return {
        "status": doc["status"],
        "stage": doc["stage"],
        "progress": doc["progress"],
        "error_code": doc["error_code"],
        "error_message": doc["error_message"],
        "n_chunks": doc["n_chunks"],
        "page_count": doc["page_count"],
    }


@router.get("/{id}/document")
async def get_document_bytes(
    id: str,
    user: CurrentUser = Depends(current_user),
):
    await service.get_session(id, user.id)
    doc = await anyio.to_thread.run_sync(repository.get_document, id)
    if not doc:
        raise AppError(404, "NOT_FOUND", "No document found for this session.")

    settings = get_settings()
    doc_path = settings.sessions_dir / id / "doc.pdf"
    if not doc_path.exists():
        raise AppError(404, "NOT_FOUND", "Document file not found on disk.")

    encoded_filename = urllib.parse.quote(doc["filename"])
    return FileResponse(
        path=str(doc_path),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}"
        },
    )


@router.post("/{id}/reindex", status_code=status.HTTP_202_ACCEPTED)
async def trigger_reindex(
    id: str,
    user: CurrentUser = Depends(current_user),
):
    await service.get_session(id, user.id)
    doc = await anyio.to_thread.run_sync(repository.get_document, id)
    if not doc:
        raise AppError(404, "NOT_FOUND", "No document found for this session.")

    task = asyncio.create_task(reindex_session(id))
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)

    return Response(status_code=status.HTTP_202_ACCEPTED)
