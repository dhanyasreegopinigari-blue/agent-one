from datetime import datetime, timedelta, timezone

import jwt
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
