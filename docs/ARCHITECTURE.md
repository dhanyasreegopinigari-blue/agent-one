# Agent One — Architecture Reference

## 1. Overview & Deployment Topology

Agent One uses a clean two-tier decoupled architecture:
- **Frontend**: Next.js 16 (React 19) App Router, hosted on Vercel. Static & client-side rendering with no long-running operations or API secrets.
- **Backend**: Python 3.12 + FastAPI single-worker service running in Docker with Caddy reverse proxy on port 443.
- **Inference & Vector Retrieval**: Private internal network with Ollama (`llama3.1:8b` for chat, `nomic-embed-text` for embeddings), FAISS (`IndexFlatIP` over L2-normalized vectors), and SearXNG for isolated web searches.
- **Fallback**: Gemini API via `google-genai` SDK when Ollama times out or fails (can be disabled via `ALLOW_GEMINI_FALLBACK=false`).
- **Auth & Storage**: Supabase JWT authentication (asymmetric JWKS or HMAC-SHA256) + SQLite WAL database for metadata & messages, local filesystem for PDF binaries and FAISS indices.

```
                         HTTPS                                   HTTPS (api.example.com)
 Browser ───────────────────────────▶ Vercel (Next.js UI only)
    │                                         │ (static + client pages; no AI logic, no secrets)
    │
    │  Authorization: Bearer <Supabase JWT>
    ├────────────────────────────────────────▶ Caddy :443 ──▶ FastAPI backend :8000
    │      (upload PDF, SSE chat, status)                          │        │         │
    │                                                              │        │         └──▶ SearXNG (web chats only)
    └──▶ Supabase Auth (login, tokens)                             │        └──▶ Gemini API (fallback only)
                                                                   ▼
                                                    Ollama (chat + embeddings, private network)
                                                    data volume: SQLite + PDFs + FAISS indexes
```

## 2. Ingestion & Retrieval Pipeline

```
Upload PDF ──▶ validate (magic bytes, size, encryption, pages) ──▶ save doc.pdf
  ──▶ [background task]
        ├── PyMuPDF block parser (2-column layout detection)
        ├── Text cleaner (dehyphenation, header/footer/page number removal)
        ├── Deterministic chunker (~2400 chars, 15% overlap, normalized [0,1] bbox regions)
        ├── Batch embeddings via Ollama (/api/embed)
        └── Build FAISS IndexFlatIP ──▶ atomic disk write (index.faiss, chunks.json, meta.json)
```

```
Question ──▶ Query condenser (if multi-turn; Ollama only)
  ──▶ Query embedder (Ollama /api/embed)
  ──▶ FAISS top-k search (cosine similarity via inner product)
  ──▶ Score gating (min_score=0.40, score_margin=0.12)
        ├── Below threshold ──▶ Canned refusal ("Could not find that in the PDF"), 0 LLM calls
        └── Above threshold ──▶ Grounded system prompt with labeled blocks [S1..Sn]
              ──▶ Router: Ollama (primary) ──(fail/timeout)──▶ Gemini (fallback)
              ──▶ SSE token streaming with sentinel check (NOT_IN_DOCUMENT)
              ──▶ Source citation validation & database persistence
```

## 3. Session Types & Isolation Invariants

| Feature | `pdf` Session | `web` Session |
|---|---|---|
| Document upload | Exactly 1 PDF | Forbidden (HTTP 409) |
| Retrieval engine | FAISS per-session index | None |
| Embeddings | Ollama `nomic-embed-text` | Never invoked |
| Web Search | Never invoked | SearXNG / Tavily |
| Citations format | `[S#]` with page number | `[W#]` with source title & URL |

## 4. Module Dependency Graph

```
api ──▶ sessions, rag, web_search ──▶ llm, embeddings, vectorstore, ingestion, db
```

- `app.rag` and `app.vectorstore` **never** import `app.web_search`.
- `app.web_search` **never** imports `app.rag`, `app.vectorstore`, `app.embeddings`, or `app.ingestion`.
- Invariant verified automatically by `tests/test_isolation_imports.py`.

## 5. Measured Evaluation Benchmarks

Evaluated with `backend/eval/sample.pdf` (Northwind Services Agreement) and `backend/eval/questions.yaml`:
- **In-document Question Hit Rate (Hit@k)**: 100% (target: ≥ 85%)
- **Off-topic Query Refusal Rate**: 100% (target: 100% canned refusal with 0 LLM calls)
- **Calibrated `MIN_SCORE`**: 0.40
- **Calibrated `SCORE_MARGIN`**: 0.12
