import numpy as np
import pytest

from app.vectorstore.faiss_store import FaissStore, IndexIncompatible


def test_faiss_store_self_retrieval_and_k_larger_than_total():
    n_chunks = 10
    dim = 64
    rng = np.random.default_rng(42)
    vectors = rng.standard_normal((n_chunks, dim)).astype("float32")

    store = FaissStore.build(vectors)
    assert store.dim == dim

    # Self-retrieval: each vector queried against store must return itself as rank 0 with score ≈ 1.0
    for idx in range(n_chunks):
        hits = store.search(vectors[idx], k=5)
        assert len(hits) == 5
        top_id, top_score = hits[0]
        assert top_id == idx
        assert pytest.approx(top_score, abs=1e-4) == 1.0

    # k > ntotal must be safe and return ntotal items
    large_k_hits = store.search(vectors[0], k=100)
    assert len(large_k_hits) == n_chunks


def test_faiss_store_save_load_roundtrip_and_no_tmp_files(tmp_path):
    n_chunks = 5
    dim = 32
    rng = np.random.default_rng(123)
    vectors = rng.standard_normal((n_chunks, dim)).astype("float32")

    store = FaissStore.build(vectors)
    chunks = [
        {"id": i, "text": f"Chunk text {i}", "page_start": 1, "page_end": 1}
        for i in range(n_chunks)
    ]
    model_name = "nomic-embed-text"

    store_dir = tmp_path / "store"
    store.save(store_dir, chunks, embed_model=model_name)

    # Assert no .tmp files exist
    tmp_files = list(store_dir.glob("*.tmp"))
    assert len(tmp_files) == 0

    # Assert regular files exist
    assert (store_dir / "index.faiss").exists()
    assert (store_dir / "chunks.json").exists()
    assert (store_dir / "meta.json").exists()

    # Load successfully
    loaded_store, loaded_chunks = FaissStore.load(store_dir, expected_model=model_name)
    assert loaded_store.dim == dim
    assert len(loaded_chunks) == n_chunks
    assert loaded_chunks[0]["text"] == "Chunk text 0"

    # Search loaded store
    hits = loaded_store.search(vectors[0], k=1)
    assert hits[0][0] == 0
    assert pytest.approx(hits[0][1], abs=1e-4) == 1.0


def test_faiss_store_model_mismatch_raises(tmp_path):
    n_chunks = 3
    dim = 16
    vectors = np.ones((n_chunks, dim), dtype="float32")
    store = FaissStore.build(vectors)
    chunks = [{"id": i, "text": f"T{i}"} for i in range(n_chunks)]

    store_dir = tmp_path / "store_mismatch"
    store.save(store_dir, chunks, embed_model="model-v1")

    with pytest.raises(IndexIncompatible):
        FaissStore.load(store_dir, expected_model="model-v2")
