# Agent One

Private, local-first AI document chat and research platform. Ask questions about your PDF documents and receive verifiable answers grounded strictly in the text, accompanied by interactive page citations.

---

## Architecture Overview

```
                         HTTPS                                   HTTPS (api.example.com)
 Browser ───────────────────────────▶ Vercel (Next.js 16 UI)
    │                                         │ (Static + Client pages; zero secrets)
    │
    │  Authorization: Bearer <Supabase JWT>
    ├────────────────────────────────────────▶ Caddy :443 ──▶ FastAPI Backend :8000
    │      (PDF upload, SSE chat stream)                           │        │         │
    │                                                              │        │         └──▶ SearXNG (Web chats)
    └──▶ Supabase Auth (Email, Google, Guest)                      │        └──▶ Gemini API (Fallback)
                                                                   ▼
                                                    Ollama (Chat + Embeddings, private network)
                                                    Storage: SQLite + PDFs + FAISS Indices
```

### PDF Grounded Workflow
```
PDF Upload ──▶ PyMuPDF layout parser ──▶ Cleaner ──▶ Deterministic Chunker (~2400 chars, 15% overlap)
           ──▶ Ollama embeddings (nomic-embed-text) ──▶ FAISS IndexFlatIP (Cosine similarity)
           ──▶ Grounded Prompt ──▶ Ollama (llama3.1:8b) ──▶ Real-time SSE streaming with [S#] citations
```

---

## Quick Start (Local Development)

### 1. Prerequisites
- **Python**: 3.12+
- **Node.js**: >= 20.9 (Next.js 16)
- **Ollama**: Installed and running locally (`http://localhost:11434`)

### 2. Pull Required AI Models
```bash
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

### 3. Start the Backend
```bash
cd backend
python -m venv .venv

# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# On macOS/Linux:
source .venv/bin/activate

pip install -r requirements.lock
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```
Verify: visit `http://localhost:8000/health` (returns status `ok`).

### 4. Start the Frontend
```bash
# In repository root:
npm install
cp .env.example .env.local
npm run dev
```
Open `http://localhost:3000` in your browser.

---

## Configuration Reference

### Backend (`backend/.env`)
| Variable | Default | Description |
|---|---|---|
| `ENV` | `development` | Set `production` on deployment |
| `AUTH_DISABLED` | `false` | Set `true` for local testing without Supabase JWT |
| `SUPABASE_URL` | — | Supabase project URL (`https://<ref>.supabase.co`) |
| `SUPABASE_JWT_SECRET` | — | Leave empty for JWKS asymmetric key verification |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama service endpoint |
| `OLLAMA_CHAT_MODEL` | `llama3.1:8b` | Primary chat LLM |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Primary embeddings model |
| `ALLOW_GEMINI_FALLBACK` | `true` | Fallback to Gemini when Ollama fails/times out |
| `GEMINI_API_KEY` | — | Gemini API key for fallback |
| `MIN_SCORE` | `0.40` | Retrieval threshold score gate |
| `SCORE_MARGIN` | `0.12` | Relative score margin filter |

### Frontend (`.env.local` / Vercel)
| Variable | Description |
|---|---|
| `NEXT_PUBLIC_BACKEND_URL` | Base URL of the backend API (e.g. `http://localhost:8000`) |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase public anon key |

---

## Documentation

- [Architecture Reference](docs/ARCHITECTURE.md) — Detailed component design, isolation rules, and eval benchmarks.
- [Deployment Guide](docs/DEPLOYMENT.md) — Production deployment with Docker Compose, Caddy, and Vercel.
- [API Reference](docs/API.md) — REST endpoints and Server-Sent Events (SSE) chat specification.
- [Team & Contributors](docs/TEAM.md) — Team members and architectural contributions.
- [Product Specification](PRODUCT.md) — Product vision, user personas, and grounding principles.
