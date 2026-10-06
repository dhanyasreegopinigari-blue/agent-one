from datetime import datetime, timedelta, timezone

import jwt
import numpy as np
import pymupdf
import pytest
from starlette.testclient import TestClient

from app.config import get_settings
from app.db.database import init_db
from app.main import create_app


def make_jwt(
    secret: str,
    sub: str,
    aud: str = "authenticated",
    exp_delta: int = 3600,
    extra: dict | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "aud": aud,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=exp_delta)).timestamp()),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, secret, algorithm="HS256")


def make_pdf(pages: list[str]) -> bytes:
    doc = pymupdf.open()
    for text in pages:
        p = doc.new_page(width=600, height=800)
        p.insert_textbox(pymupdf.Rect(50, 50, 550, 750), text)
    data = doc.tobytes()
    doc.close()
    return data


class HashEmbedder:
    def __init__(self, dim: int = 64, model: str = "nomic-embed-text"):
        self.dim = dim
        self.model = model

    async def embed_documents(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, self.dim), dtype="float32")
        vectors = []
        for t in texts:
            vec = np.zeros(self.dim, dtype="float32")
            for word in t.lower().split():
                h = abs(hash(word)) % self.dim
                vec[h] += 1.0
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec /= norm
            vectors.append(vec)
        return np.ascontiguousarray(vectors, dtype="float32")

    async def embed_query(self, text: str) -> np.ndarray:
        vec = np.zeros(self.dim, dtype="float32")
        for word in text.lower().split():
            h = abs(hash(word)) % self.dim
            vec[h] += 1.0
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        return np.ascontiguousarray(vec, dtype="float32")


@pytest.fixture
def temp_settings(tmp_path, monkeypatch):
    monkeypatch.setenv("ENV", "test")
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("AUTH_DISABLED", "false")
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "test-secret-key-that-is-at-least-32-chars-long")
    get_settings.cache_clear()
    settings = get_settings()
    init_db()
    yield settings
    get_settings.cache_clear()


@pytest.fixture
def client(temp_settings):
    app = create_app()
    with TestClient(app) as tc:
        yield tc
