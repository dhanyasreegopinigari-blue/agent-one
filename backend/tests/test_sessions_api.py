from app.config import get_settings
from tests.conftest import make_jwt


def test_session_crud_flow(client, temp_settings):
    token_a = make_jwt(temp_settings.supabase_jwt_secret, sub="user-a")
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 1. Create PDF session
    res = client.post("/sessions", json={"type": "pdf"}, headers=headers_a)
    assert res.status_code == 200
    sess = res.json()
    assert sess["type"] == "pdf"
    assert sess["title"] == "New PDF chat"
    assert sess["document"] is None
    sess_id = sess["id"]
    assert len(sess_id) == 32

    # 2. Get session
    res = client.get(f"/sessions/{sess_id}", headers=headers_a)
    assert res.status_code == 200
    assert res.json()["id"] == sess_id

    # 3. Rename session
    res = client.patch(f"/sessions/{sess_id}", json={"title": "Updated Title"}, headers=headers_a)
    assert res.status_code == 200
    assert res.json()["title"] == "Updated Title"

    # 4. User B cannot see or touch User A's session (must get 404)
    token_b = make_jwt(temp_settings.supabase_jwt_secret, sub="user-b")
    headers_b = {"Authorization": f"Bearer {token_b}"}
    res_b = client.get(f"/sessions/{sess_id}", headers=headers_b)
    assert res_b.status_code == 404
    assert res_b.json()["error"]["code"] == "NOT_FOUND"

    res_b_patch = client.patch(
        f"/sessions/{sess_id}", json={"title": "Hacked"}, headers=headers_b
    )
    assert res_b_patch.status_code == 404

    res_b_del = client.delete(f"/sessions/{sess_id}", headers=headers_b)
    assert res_b_del.status_code == 404

    # 5. List sessions
    res_list = client.get("/sessions", headers=headers_a)
    assert res_list.status_code == 200
    items = res_list.json()
    assert len(items) == 1
    assert items[0]["id"] == sess_id

    # 6. Delete session
    # Create session directory to verify deletion
    sess_dir = temp_settings.sessions_dir / sess_id
    sess_dir.mkdir(parents=True, exist_ok=True)
    dummy_file = sess_dir / "test.txt"
    dummy_file.write_text("hello")

    res_del = client.delete(f"/sessions/{sess_id}", headers=headers_a)
    assert res_del.status_code == 204
    assert not sess_dir.exists()

    # Get after delete returns 404
    res_after = client.get(f"/sessions/{sess_id}", headers=headers_a)
    assert res_after.status_code == 404


def test_session_id_validation(client, temp_settings):
    token = make_jwt(temp_settings.supabase_jwt_secret, sub="user-a")
    headers = {"Authorization": f"Bearer {token}"}

    # Path traversal or invalid format must return 404
    for bad_id in ["../etc/passwd", "123", "invalid-id-that-is-not-32-hex"]:
        res = client.get(f"/sessions/{bad_id}", headers=headers)
        assert res.status_code == 404


def test_session_limit(client, temp_settings, monkeypatch):
    monkeypatch.setenv("MAX_SESSIONS_PER_USER", "2")
    get_settings.cache_clear()
    token = make_jwt(temp_settings.supabase_jwt_secret, sub="user-limit")
    headers = {"Authorization": f"Bearer {token}"}

    r1 = client.post("/sessions", json={"type": "pdf"}, headers=headers)
    assert r1.status_code == 200

    r2 = client.post("/sessions", json={"type": "web"}, headers=headers)
    assert r2.status_code == 200

    r3 = client.post("/sessions", json={"type": "pdf"}, headers=headers)
    assert r3.status_code == 403
    assert r3.json()["error"]["code"] == "SESSION_LIMIT"
