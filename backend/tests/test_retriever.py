import numpy as np
import pytest

from app.rag.retriever import retrieve


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


class DummySettings:
    top_k = 5
    min_score = 0.40
    score_margin = 0.12
    max_context_chars = 1000


@pytest.mark.asyncio
async def test_retriever_off_topic_returns_empty():
    store = DummyStore([0.35, 0.30, 0.20])  # all below min_score 0.40
    chunks = [{"id": i, "text": f"Chunk {i}"} for i in range(3)]
    cache = DummyCache(store, chunks)

    hits = await retrieve(
        "off topic query",
        "sess-1",
        embedder=DummyEmbedder(),
        cache=cache,
        settings=DummySettings(),
    )
    assert hits == []


@pytest.mark.asyncio
async def test_retriever_margin_filter_and_score_order():
    # top score 0.80, margin 0.12 => cutoff 0.68
    # 0.80, 0.75, 0.65 (filtered by margin), 0.35 (filtered by min_score)
    store = DummyStore([0.80, 0.75, 0.65, 0.35])
    chunks = [{"id": i, "text": f"Chunk {i}"} for i in range(4)]
    cache = DummyCache(store, chunks)

    hits = await retrieve(
        "sample query",
        "sess-1",
        embedder=DummyEmbedder(),
        cache=cache,
        settings=DummySettings(),
    )
    assert len(hits) == 2
    assert hits[0].label == "S1"
    assert hits[0].score == 0.80
    assert hits[0].chunk["id"] == 0
    assert hits[1].label == "S2"
    assert hits[1].score == 0.75
    assert hits[1].chunk["id"] == 1


@pytest.mark.asyncio
async def test_retriever_context_budget():
    store = DummyStore([0.90, 0.88, 0.85])
    # Total budget = 500 chars
    settings = DummySettings()
    settings.max_context_chars = 500

    chunks = [
        {"id": 0, "text": "A" * 300},
        {"id": 1, "text": "B" * 300},  # 300 + 300 = 600 > 500 => dropped
        {"id": 2, "text": "C" * 100},
    ]
    cache = DummyCache(store, chunks)

    hits = await retrieve(
        "query",
        "sess-1",
        embedder=DummyEmbedder(),
        cache=cache,
        settings=settings,
    )
    assert len(hits) == 1
    assert hits[0].label == "S1"
    assert len(hits[0].chunk["text"]) == 300
