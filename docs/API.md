# Agent One — API Reference

Base URL: `NEXT_PUBLIC_BACKEND_URL`.
Authentication: All routes except `GET /health` require `Authorization: Bearer <supabase_access_token>`.

Error response schema:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable explanation"
  }
}
```

---

## 1. REST Endpoints

### 1.1 Health Check
- `GET /health`
- **Auth**: None
- **Response**:
  ```json
  {
    "status": "ok",
    "ollama": {
      "status": "ok",
      "available": true,
      "chat_model": "llama3.1:8b",
      "embed_model": "nomic-embed-text"
    },
    "gemini": {
      "status": "configured",
      "available": true,
      "model": "gemini-3-flash-preview"
    },
    "web_search": {
      "provider": "searxng",
      "status": "ok"
    },
    "version": "3.0.0"
  }
  ```

### 1.2 Session Management
- `POST /sessions`
  - Body: `{"type": "pdf" | "web"}`
  - Returns: `200` Session summary
  - Errors: `403 SESSION_LIMIT` (when user exceeds 100 sessions)
- `GET /sessions`
  - Returns: `200` List of sessions for the authenticated user, ordered by `updated_at DESC`.
- `GET /sessions/{id}`
  - Returns: `200` Session summary
  - Errors: `404 NOT_FOUND`
- `PATCH /sessions/{id}`
  - Body: `{"title": "Updated Title"}`
  - Returns: `200` Updated session summary
- `DELETE /sessions/{id}`
  - Returns: `204 No Content` (removes database record and all on-disk artifacts)
- `GET /sessions/{id}/messages`
  - Returns: `200` Array of chat messages with sources and citations.

### 1.3 Document Management (PDF Sessions Only)
- `POST /sessions/{id}/document`
  - Form multipart: `file: <binary PDF>`
  - Returns: `202 Accepted` with initial processing session summary
  - Errors:
    - `409 WRONG_SESSION_TYPE`: Cannot upload a document to a web session.
    - `409 DOCUMENT_EXISTS`: Document already processed and ready.
    - `413 FILE_TOO_LARGE`: PDF exceeds 50 MB.
    - `415 NOT_A_PDF`: Magic bytes do not start with `%PDF-`.
    - `422 PDF_CORRUPT | PDF_ENCRYPTED | PDF_TOO_MANY_PAGES`
- `GET /sessions/{id}/status`
  - Returns: Ingestion progress status:
    ```json
    {
      "status": "processing" | "ready" | "failed",
      "stage": "parsing" | "chunking" | "embedding" | "indexing" | "done",
      "progress": 75,
      "error_code": null,
      "error_message": null,
      "n_chunks": 12,
      "page_count": 8
    }
    ```
- `GET /sessions/{id}/document`
  - Returns: `application/pdf` binary stream.
- `POST /sessions/{id}/reindex`
  - Triggers re-embedding and FAISS index reconstruction from stored PDF binary.

---

## 2. Real-Time Chat Streaming (`POST /sessions/{id}/chat`)

- Request: `{"message": "What is the termination clause?"}`
- Header: `Accept: text/event-stream`
- Protocol: Server-Sent Events (SSE). Frames are separated by `\n\n`. Lines starting with `:` are heartbeats.

### SSE Event Stream Lifecycle
1. `event: status`
   ```json
   {"stage": "retrieving"} // or "searching", "generating"
   ```
2. `event: sources` (sent once, before tokens)
   ```json
   {
     "sources": [
       {
         "id": "S1",
         "chunk_id": 4,
         "page_start": 3,
         "page_end": 3,
         "snippet": "Either party may terminate...",
         "score": 0.74,
         "regions": [{"page": 3, "bbox": [0.08, 0.21, 0.92, 0.34]}]
       }
     ]
   }
   ```
3. `event: token`
   ```json
   {"text": "According"}
   ```
4. `event: reset` (sent only if primary LLM fails mid-stream and fallback is engaged)
   ```json
   {}
   ```
5. `event: done` (terminal event for successful answers)
   ```json
   {
     "message_id": "msg_01...",
     "model_used": "llama3.1:8b",
     "fallback": false,
     "grounded": true,
     "cited": ["S1"]
   }
   ```
6. `event: error` (terminal event for pipeline failure)
   ```json
   {
     "code": "LLM_UNAVAILABLE",
     "message": "Both Ollama and Gemini fallback failed to generate an answer."
   }
   ```
