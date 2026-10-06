# Agent Instructions

<!-- START:nextjs-agent-rules -->
## Next.js Rules
- Next.js 16 with Turbopack and React 19.
- Use App Router.
- Keep client components marked with `'use client'`.
<!-- END:nextjs-agent-rules -->

## Project Commands

### Backend (Python 3.12 / FastAPI)
- Activate venv: `.\backend\.venv\Scripts\Activate.ps1`
- Run dev server: `uvicorn app.main:app --reload --port 8000`
- Run test suite: `pytest -q`
- Run linter: `ruff check app tests scripts`
- Run live eval: `python scripts/eval_live.py`

### Frontend (Next.js 16)
- Dev server: `npm run dev`
- Typecheck: `npm run typecheck`
- Lint: `npm run lint`
- Build: `npm run build`

### Module Dependency Rules
- `api -> sessions/rag/web_search -> llm, embeddings, vectorstore, ingestion, db`
- `app/rag/**` and `app/vectorstore/**` must NEVER import `app.web_search`.
- `app/web_search/**` must NEVER import `app.rag`, `app.vectorstore`, `app.embeddings`, or `app.ingestion`.
