import json
import os
from pathlib import Path

import faiss
import numpy as np

SCHEMA_VERSION = 1


class IndexIncompatible(Exception):
    pass


class FaissStore:
    def __init__(self, index: faiss.Index, dim: int):
        self.index = index
        self.dim = dim

    @classmethod
    def build(cls, vectors: np.ndarray) -> "FaissStore":
        vectors = np.ascontiguousarray(vectors, dtype="float32")
        faiss.normalize_L2(vectors)
        index = faiss.IndexFlatIP(vectors.shape[1])
        index.add(vectors)
        return cls(index, vectors.shape[1])

    def search(self, query: np.ndarray, k: int) -> list[tuple[int, float]]:
        k = min(k, self.index.ntotal)
        if k <= 0:
            return []
        q = np.ascontiguousarray(query.reshape(1, -1), dtype="float32")
        faiss.normalize_L2(q)
        scores, ids = self.index.search(q, k)
        return [(int(i), float(s)) for i, s in zip(ids[0], scores[0]) if i != -1]

    def save(self, directory: Path, chunks: list[dict], embed_model: str) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        meta = {
            "schema_version": SCHEMA_VERSION,
            "embed_model": embed_model,
            "dim": self.dim,
            "n_chunks": len(chunks),
        }
        tmp = {n: directory / f"{n}.tmp" for n in ("index.faiss", "chunks.json", "meta.json")}
        faiss.write_index(self.index, str(tmp["index.faiss"]))
        tmp["chunks.json"].write_text(json.dumps(chunks, ensure_ascii=False), encoding="utf-8")
        tmp["meta.json"].write_text(json.dumps(meta), encoding="utf-8")
        for name, t in tmp.items():
            os.replace(t, directory / name)

    @classmethod
    def load(cls, directory: Path, expected_model: str) -> tuple["FaissStore", list[dict]]:
        meta_file = directory / "meta.json"
        index_file = directory / "index.faiss"
        chunks_file = directory / "chunks.json"
        if not (meta_file.exists() and index_file.exists() and chunks_file.exists()):
            raise IndexIncompatible("missing_files")

        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        if meta.get("schema_version") != SCHEMA_VERSION or meta.get("embed_model") != expected_model:
            raise IndexIncompatible(meta.get("embed_model", "unknown"))

        index = faiss.read_index(str(index_file))
        chunks = json.loads(chunks_file.read_text(encoding="utf-8"))
        if index.ntotal != len(chunks) or index.d != meta["dim"]:
            raise IndexIncompatible("corrupt")

        return cls(index, meta["dim"]), chunks
