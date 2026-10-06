import numpy as np
import pytest

from app.llm.router import LLMRouter
from app.rag.pipeline import Done, PdfRagPipeline, Token
from app.rag.prompts import PDF_NOT_FOUND_MESSAGE
from tests.test_llm_router import DummyRouterSettings, MockLLM


class DummyStore:
    def __init__(self, scores: list[float]):
        self.scores = scores

    def search(self, q, k):
        return [(i, s) for i, s in enumerate(self.scores[:k])]


class DummyCache:
    def __init__(self, store, chunks):
        self.store = store
        self.chunks = chunks

    def get(self, session_id):
        return self.store, self.chunks


class DummyEmbedder:
    async def embed_query(self, text: str):
        return np.zeros((32,), dtype="float32")


@pytest.mark.asyncio
async def test_pipeline_off_topic_zero_llm_calls():
    # Store with scores all below 0.40
    store = DummyStore([0.25, 0.15])
    chunks = [{"id": 0, "text": "Foo"}, {"id": 1, "text": "Bar"}]
    cache = DummyCache(store, chunks)

    mock_ollama = MockLLM("ollama", "llama3.1:8b", ["Never called"])
    router = LLMRouter(mock_ollama, None, DummyRouterSettings())

    pipeline = PdfRagPipeline(embedder=DummyEmbedder(), cache=cache, router=router)
    events = [e async for e in pipeline.answer_stream("sess-1", "What is soccer?", history=[])]

    # Must NOT call any LLM
    assert mock_ollama.call_count == 0

    tokens = [e.text for e in events if isinstance(e, Token)]
    assert "".join(tokens) == PDF_NOT_FOUND_MESSAGE

    done = [e for e in events if isinstance(e, Done)][0]
    assert done.grounded is False
    assert done.model_used is None
    assert done.cited == []


@pytest.mark.asyncio
async def test_pipeline_sentinel_split_across_token_boundaries():
    # Good hit so retrieval passes
    store = DummyStore([0.85])
    chunks = [{"id": 0, "page_start": 1, "page_end": 1, "text": "Relevant contract text", "regions": []}]
    cache = DummyCache(store, chunks)

    # LLM outputs NOT_IN_DOCUMENT split across tokens
    mock_ollama = MockLLM(
        "ollama",
        "llama3.1:8b",
        ["NOT_IN_", "DOCUMENT", " because the text lacks that detail."],
    )
    router = LLMRouter(mock_ollama, None, DummyRouterSettings())

    pipeline = PdfRagPipeline(embedder=DummyEmbedder(), cache=cache, router=router)
    events = [e async for e in pipeline.answer_stream("sess-1", "Who is CEO?", history=[])]

    assert mock_ollama.call_count == 1
    tokens = [e.text for e in events if isinstance(e, Token)]
    assert "".join(tokens) == PDF_NOT_FOUND_MESSAGE

    done = [e for e in events if isinstance(e, Done)][0]
    assert done.grounded is False
    assert done.cited == []


@pytest.mark.asyncio
async def test_pipeline_valid_answer_with_citations():
    store = DummyStore([0.85, 0.80])
    chunks = [
        {"id": 0, "page_start": 2, "page_end": 2, "text": "Fee is INR 450,000.", "regions": []},
        {"id": 1, "page_start": 3, "page_end": 3, "text": "Termination is 45 days.", "regions": []},
    ]
    cache = DummyCache(store, chunks)

    mock_ollama = MockLLM(
        "ollama",
        "llama3.1:8b",
        ["The monthly fee is INR 450,000 [S1]. Notice period is 45 days [S2]. Unknown [S99]."],
    )
    router = LLMRouter(mock_ollama, None, DummyRouterSettings())

    pipeline = PdfRagPipeline(embedder=DummyEmbedder(), cache=cache, router=router)
    events = [e async for e in pipeline.answer_stream("sess-1", "What is fee and notice?", history=[])]

    done = [e for e in events if isinstance(e, Done)][0]
    assert done.grounded is True
    assert done.cited == ["S1", "S2"]
    # Unknown citation [S99] must be removed from final message_text
    assert "[S99]" not in done.message_text
    assert "[S1]" in done.message_text
    assert "[S2]" in done.message_text
