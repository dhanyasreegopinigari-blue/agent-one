import pytest

from app.config import get_settings
from tests.conftest import make_jwt


def test_auth_valid_token(client, temp_settings):
    token = make_jwt(temp_settings.supabase_jwt_secret, sub="user-123")
    resp = client.get("/sessions", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json() == []


def test_auth_missing_header(client):
    resp = client.get("/sessions")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "UNAUTHENTICATED"


def test_auth_invalid_header_format(client):
    resp = client.get("/sessions", headers={"Authorization": "Basic dXNlcjpwYXNz"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "UNAUTHENTICATED"


def test_auth_expired_token(client, temp_settings):
    token = make_jwt(temp_settings.supabase_jwt_secret, sub="user-123", exp_delta=-60)
    resp = client.get("/sessions", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "UNAUTHENTICATED"


def test_auth_wrong_audience(client, temp_settings):
    token = make_jwt(temp_settings.supabase_jwt_secret, sub="user-123", aud="wrong-audience")
    resp = client.get("/sessions", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "UNAUTHENTICATED"


def test_auth_wrong_secret(client, temp_settings):
    token = make_jwt("another-secret-key-32-chars-long-1234", sub="user-123")
    resp = client.get("/sessions", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "UNAUTHENTICATED"


def test_production_refuses_auth_disabled(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("AUTH_DISABLED", "true")
    get_settings.cache_clear()
    with pytest.raises(RuntimeError, match="AUTH_DISABLED must be false when ENV=production"):
        get_settings()
    get_settings.cache_clear()
