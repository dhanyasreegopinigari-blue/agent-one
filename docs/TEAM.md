# Team & Project Contributors

> *Describes the legacy v2 architecture; update to reflect the RAG redesign.*

## Core Contributors
- **Agent One Development Team** — Core architecture, RAG pipeline redesign, and multimodal document intelligence.

### Member Contributions Breakdown
- **Architecture & Ingestion**: PyMuPDF two-column layout detection, dehyphenation, header/footer cleaning, deterministic sentence-aware chunking with overlap and bounding box region coordinates.
- **Embeddings & Vector Search**: Ollama embedding client (`nomic-embed-text`), FAISS `IndexFlatIP` exact cosine retrieval, LRU caching, and index persistence.
- **RAG & LLM Orchestration**: Prompt design with strict grounding rules, score & margin gating with canned refusal for off-topic queries, Ollama streaming client, Gemini fallback router, and circuit breaker.
- **Search Provider Isolation**: SearXNG / Tavily provider integration in distinct `web` sessions with zero cross-talk to PDF vector storage.
- **Frontend & App Shell**: Next.js 16 rebuild with Supabase authentication, AppShell with split-screen PDF preview, SSE stream reader, and real-time status popover.
