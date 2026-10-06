import asyncio
import time
from dataclasses import asdict
from pathlib import Path

import yaml

from app.config import get_settings
from app.embeddings.ollama_embedder import OllamaEmbedder
from app.ingestion.chunker import chunk
from app.ingestion.cleaner import clean
from app.ingestion.pdf_parser import PyMuPdfParser
from app.llm.gemini_client import GeminiClient
from app.llm.ollama_client import OllamaClient
from app.llm.router import Done, LLMRouter, Token
from app.rag.pipeline import PdfRagPipeline
from app.vectorstore.faiss_store import FaissStore


class LocalCache:
    def __init__(self, store, chunks):
        self.store = store
        self.chunks = chunks

    def get(self, _session_id, _expected_model=None):
        return self.store, self.chunks


async def main():
    settings = get_settings()
    eval_dir = Path(__file__).parent.parent / "eval"
    sample_pdf = eval_dir / "sample.pdf"
    questions_file = eval_dir / "questions.yaml"

    if not sample_pdf.exists():
        print(f"Error: {sample_pdf} not found. Run make_sample_pdf.py first.")
        return

    data = yaml.safe_load(questions_file.read_text(encoding="utf-8"))
    questions = data.get("questions", [])

    print(f"--- Ingesting {sample_pdf.name} ---")
    parser = PyMuPdfParser()
    parsed = parser.parse(sample_pdf)
    cleaned = clean(parsed.segments, parsed.page_count)
    chunks = chunk(
        cleaned,
        settings.chunk_chars,
        settings.chunk_overlap_chars,
        settings.min_chunk_chars,
    )
    chunk_dicts = [asdict(c) for c in chunks]

    embedder = OllamaEmbedder()
    try:
        vectors = await embedder.embed_documents([c.text for c in chunks])
    except Exception as e:
        print(f"Cannot connect to Ollama embedder: {e}")
        print("Please ensure Ollama is running and models are pulled to run live eval.")
        return

    store = FaissStore.build(vectors)
    cache = LocalCache(store, chunk_dicts)

    ollama = OllamaClient()
    gemini = GeminiClient() if settings.gemini_api_key else None
    router = LLMRouter(ollama, gemini, settings)
    pipeline = PdfRagPipeline(embedder=embedder, cache=cache, router=router)

    print(f"Index built with {len(chunks)} chunks, dim={store.dim}.\n")
    print("--- Evaluating Questions ---")

    in_doc_scores = []
    off_topic_scores = []
    hits_at_k = 0
    in_doc_count = 0
    off_topic_refusals = 0
    off_topic_count = 0
    ttft_list = []

    for q_item in questions:
        q = q_item["question"]
        in_doc = q_item["in_doc"]
        expected_pages = set(q_item.get("expected_pages", []))

        # Raw top search for score checking
        q_vec = await embedder.embed_query(q)
        raw_hits = store.search(q_vec, settings.top_k)
        top_score = raw_hits[0][1] if raw_hits else 0.0

        if in_doc:
            in_doc_count += 1
            in_doc_scores.append(top_score)
            retrieved_pages = set()
            for idx, _s in raw_hits:
                c = chunk_dicts[idx]
                for p in range(c["page_start"], c["page_end"] + 1):
                    retrieved_pages.add(p)
            if expected_pages.intersection(retrieved_pages):
                hits_at_k += 1
        else:
            off_topic_count += 1
            off_topic_scores.append(top_score)

        # Run pipeline
        start_time = time.perf_counter()
        first_token_time = None
        done_event = None

        try:
            async for ev in pipeline.answer_stream("eval_sess", q, []):
                if isinstance(ev, Token) and first_token_time is None:
                    first_token_time = time.perf_counter() - start_time
                elif isinstance(ev, Done):
                    done_event = ev
        except Exception as e:
            print(f"Error on question '{q}': {e}")
            continue

        if first_token_time:
            ttft_list.append(first_token_time)

        is_refusal = (done_event is not None and not done_event.grounded)
        if not in_doc and is_refusal:
            off_topic_refusals += 1

        print(
            f"[{'IN-DOC' if in_doc else 'OFF-TOPIC'}] "
            f"top_score={top_score:.4f} | "
            f"refusal={is_refusal} | "
            f"Q: {q}"
        )

    hit_rate = hits_at_k / max(1, in_doc_count)
    refusal_rate = off_topic_refusals / max(1, off_topic_count)
    avg_ttft = sum(ttft_list) / max(1, len(ttft_list))

    print("\n--- Evaluation Summary ---")
    print(f"Hit@k (in-doc questions): {hit_rate * 100:.1f}%")
    print(f"Off-topic refusal rate:   {refusal_rate * 100:.1f}%")
    print(f"Avg Time-to-First-Token:  {avg_ttft:.2f}s")

    if in_doc_scores and off_topic_scores:
        min_in = min(in_doc_scores)
        max_off = max(off_topic_scores)
        recommended_min_score = (max_off + min_in) / 2.0
        print(f"Min in-doc score:         {min_in:.4f}")
        print(f"Max off-topic score:      {max_off:.4f}")
        print(f"Recommended MIN_SCORE:    {recommended_min_score:.2f}")
        if max_off >= min_in:
            print("WARNING: Score overlap detected between in-doc and off-topic questions.")


if __name__ == "__main__":
    asyncio.run(main())
