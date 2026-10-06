import json
import uuid
from datetime import datetime, timezone
from typing import Any

from app.db.database import connect


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _row_to_session_dict(row: Any) -> dict:
    doc = None
    if "doc_status" in row.keys() and row["doc_status"] is not None:  # noqa: SIM118
        doc = {
            "filename": row["doc_filename"],
            "size_bytes": row["doc_size_bytes"],
            "page_count": row["doc_page_count"],
            "n_chunks": row["doc_n_chunks"],
            "status": row["doc_status"],
            "stage": row["doc_stage"],
            "progress": row["doc_progress"],
            "error_code": row["doc_error_code"],
            "error_message": row["doc_error_message"],
        }
    return {
        "id": row["id"],
        "type": row["type"],
        "title": row["title"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "document": doc,
    }


def create_session(user_id: str, session_type: str, title: str | None = None) -> dict:
    if title is None:
        title = "New PDF chat" if session_type == "pdf" else "New web chat"
    session_id = uuid.uuid4().hex
    now = utc_now_iso()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO sessions (id, user_id, type, title, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (session_id, user_id, session_type, title, now, now),
        )
    return {
        "id": session_id,
        "type": session_type,
        "title": title,
        "created_at": now,
        "updated_at": now,
        "document": None,
    }


def get_session(session_id: str, user_id: str) -> dict | None:
    with connect() as conn:
        row = conn.execute(
            """
            SELECT s.id, s.user_id, s.type, s.title, s.created_at, s.updated_at,
                   d.filename AS doc_filename, d.size_bytes AS doc_size_bytes,
                   d.page_count AS doc_page_count, d.n_chunks AS doc_n_chunks,
                   d.status AS doc_status, d.stage AS doc_stage, d.progress AS doc_progress,
                   d.error_code AS doc_error_code, d.error_message AS doc_error_message
            FROM sessions s
            LEFT JOIN documents d ON s.id = d.session_id
            WHERE s.id = ? AND s.user_id = ?
            """,
            (session_id, user_id),
        ).fetchone()
        if not row:
            return None
        return _row_to_session_dict(row)


def list_sessions(user_id: str) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT s.id, s.user_id, s.type, s.title, s.created_at, s.updated_at,
                   d.filename AS doc_filename, d.size_bytes AS doc_size_bytes,
                   d.page_count AS doc_page_count, d.n_chunks AS doc_n_chunks,
                   d.status AS doc_status, d.stage AS doc_stage, d.progress AS doc_progress,
                   d.error_code AS doc_error_code, d.error_message AS doc_error_message
            FROM sessions s
            LEFT JOIN documents d ON s.id = d.session_id
            WHERE s.user_id = ?
            ORDER BY s.updated_at DESC
            """,
            (user_id,),
        ).fetchall()
        return [_row_to_session_dict(r) for r in rows]


def rename_session(session_id: str, user_id: str, title: str) -> dict | None:
    now = utc_now_iso()
    with connect() as conn:
        cursor = conn.execute(
            """
            UPDATE sessions
            SET title = ?, updated_at = ?
            WHERE id = ? AND user_id = ?
            """,
            (title, now, session_id, user_id),
        )
        if cursor.rowcount == 0:
            return None
    return get_session(session_id, user_id)


def touch_session(session_id: str) -> None:
    now = utc_now_iso()
    with connect() as conn:
        conn.execute(
            "UPDATE sessions SET updated_at = ? WHERE id = ?",
            (now, session_id),
        )


def delete_session(session_id: str, user_id: str) -> bool:
    with connect() as conn:
        cursor = conn.execute(
            "DELETE FROM sessions WHERE id = ? AND user_id = ?",
            (session_id, user_id),
        )
        return cursor.rowcount > 0


def count_sessions(user_id: str) -> int:
    with connect() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM sessions WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        return row["cnt"] if row else 0


def upsert_document(
    session_id: str,
    filename: str,
    size_bytes: int,
    page_count: int | None = None,
    status: str = "processing",
    stage: str = "parsing",
    progress: int = 0,
    n_chunks: int | None = None,
    error_code: str | None = None,
    error_message: str | None = None,
    embed_model: str | None = None,
) -> None:
    now = utc_now_iso()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO documents (
                session_id, filename, size_bytes, page_count, n_chunks,
                status, stage, progress, error_code, error_message, embed_model,
                created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                filename = excluded.filename,
                size_bytes = excluded.size_bytes,
                page_count = excluded.page_count,
                n_chunks = excluded.n_chunks,
                status = excluded.status,
                stage = excluded.stage,
                progress = excluded.progress,
                error_code = excluded.error_code,
                error_message = excluded.error_message,
                embed_model = excluded.embed_model,
                updated_at = excluded.updated_at
            """,
            (
                session_id,
                filename,
                size_bytes,
                page_count,
                n_chunks,
                status,
                stage,
                progress,
                error_code,
                error_message,
                embed_model,
                now,
                now,
            ),
        )


def update_document_progress(
    session_id: str,
    status: str,
    stage: str,
    progress: int,
    n_chunks: int | None = None,
    error_code: str | None = None,
    error_message: str | None = None,
    embed_model: str | None = None,
) -> None:
    now = utc_now_iso()
    with connect() as conn:
        conn.execute(
            """
            UPDATE documents
            SET status = ?,
                stage = ?,
                progress = ?,
                n_chunks = COALESCE(?, n_chunks),
                error_code = ?,
                error_message = ?,
                embed_model = COALESCE(?, embed_model),
                updated_at = ?
            WHERE session_id = ?
            """,
            (
                status,
                stage,
                progress,
                n_chunks,
                error_code,
                error_message,
                embed_model,
                now,
                session_id,
            ),
        )


def get_document(session_id: str) -> dict | None:
    with connect() as conn:
        row = conn.execute(
            """
            SELECT session_id, filename, size_bytes, page_count, n_chunks,
                   status, stage, progress, error_code, error_message, embed_model,
                   created_at, updated_at
            FROM documents
            WHERE session_id = ?
            """,
            (session_id,),
        ).fetchone()
        if not row:
            return None
        return dict(row)


def delete_document(session_id: str) -> None:
    with connect() as conn:
        conn.execute("DELETE FROM documents WHERE session_id = ?", (session_id,))


def add_message_pair(
    session_id: str,
    user_msg: dict,
    assistant_msg: dict,
) -> None:
    user_id = user_msg.get("id") or uuid.uuid4().hex
    user_created_at = user_msg.get("created_at") or utc_now_iso()

    asst_id = assistant_msg.get("id") or uuid.uuid4().hex
    asst_created_at = assistant_msg.get("created_at") or utc_now_iso()

    sources_json = (
        json.dumps(assistant_msg["sources"], ensure_ascii=False)
        if "sources" in assistant_msg and assistant_msg["sources"] is not None
        else None
    )

    with connect() as conn:
        conn.execute(
            """
            INSERT INTO messages (id, session_id, role, content, sources_json, model_used, fallback, grounded, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                session_id,
                "user",
                user_msg["content"],
                None,
                None,
                0,
                None,
                user_created_at,
            ),
        )
        conn.execute(
            """
            INSERT INTO messages (id, session_id, role, content, sources_json, model_used, fallback, grounded, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                asst_id,
                session_id,
                "assistant",
                assistant_msg["content"],
                sources_json,
                assistant_msg.get("model_used"),
                1 if assistant_msg.get("fallback") else 0,
                1 if assistant_msg.get("grounded") else (0 if assistant_msg.get("grounded") is False else None),
                asst_created_at,
            ),
        )
        conn.execute(
            "UPDATE sessions SET updated_at = ? WHERE id = ?",
            (asst_created_at, session_id),
        )


def list_messages(session_id: str) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, role, content, sources_json, model_used, fallback, grounded, created_at
            FROM messages
            WHERE session_id = ?
            ORDER BY created_at ASC
            """,
            (session_id,),
        ).fetchall()
        result = []
        for r in rows:
            sources = []
            if r["sources_json"]:
                try:
                    sources = json.loads(r["sources_json"])
                except Exception:
                    sources = []
            result.append(
                {
                    "id": r["id"],
                    "role": r["role"],
                    "content": r["content"],
                    "sources": sources,
                    "model_used": r["model_used"],
                    "fallback": bool(r["fallback"]),
                    "grounded": (
                        bool(r["grounded"])
                        if r["grounded"] is not None
                        else None
                    ),
                    "created_at": r["created_at"],
                }
            )
        return result


def last_messages(session_id: str, n: int) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, role, content, created_at
            FROM messages
            WHERE session_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (session_id, n),
        ).fetchall()
        # Return chronological order
        return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]


def fail_stale_documents() -> int:
    now = utc_now_iso()
    with connect() as conn:
        cursor = conn.execute(
            """
            UPDATE documents
            SET status = 'failed',
                stage = 'failed',
                error_code = 'INTERRUPTED',
                error_message = 'Operation interrupted by server shutdown.',
                updated_at = ?
            WHERE status = 'processing'
            """,
            (now,),
        )
        return cursor.rowcount
