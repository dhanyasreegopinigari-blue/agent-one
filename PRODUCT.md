# Agent One — Product Specification

## 1. Product Vision
Agent One is a local-first, private document chat and research platform. It allows knowledge workers, lawyers, analysts, and students to converse with complex PDF documents without uploading sensitive data to third-party AI services, receiving answers that are strictly grounded with verifiable page citations.

## 2. Core Users
- **Legal & Compliance Teams**: Reviewing contracts, agreements, and policies with strict privacy and auditability.
- **Financial Analysts**: Extracting terms, fees, and conditions from reports and statements.
- **Researchers & Academics**: Querying lengthy papers and syntheses with verifiable source tracing.
- **Enterprise Engineers**: Interacting with technical specifications without leaking proprietary IP.

## 3. Product Principles
1. **Strict Document Grounding**: PDF answers must come strictly and exclusively from the uploaded document. If an answer cannot be verified from the retrieved context, the system refuses immediately without invoking the LLM.
2. **Local-First Privacy**: Embedding generation and primary inference run on local hardware via Ollama. Cloud fallback to Gemini is optional and explicitly signaled in the UI.
3. **Traceability**: Every claim in an answer cites its exact origin with clickable `[S#]` markers that navigate the split-screen PDF preview to the source page.
4. **Session Isolation**: Document questions and live web searches are strictly separated into distinct session types that never mix.

## 4. Key Workflows
- **PDF Grounded Chat**: Upload PDF (up to 50 MB, 500 pages) ──▶ Automated PyMuPDF parsing, cleaning, chunking ──▶ Ollama embeddings (`nomic-embed-text`) ──▶ FAISS `IndexFlatIP` ──▶ Question answering with page citations.
- **Web Search Chat**: Search live internet via SearXNG / Tavily with verifiable web source links in dedicated web sessions.
