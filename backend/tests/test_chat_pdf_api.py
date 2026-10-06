import json
import time

from app.api.chat import get_embedder, get_router
from app.llm.router import LLMRouter
from tests.conftest import HashEmbedder, make_jwt, make_pdf
from tests.test_llm_router import DummyRouterSettings, MockLLM


def _parse_sse(text: str) -> list[tuple[str, dict]]:
    events = []
    blocks = text.split("\n\n")
    for b in blocks:
        if not b.strip() or b.startswith(":"):
            continue
        lines = b.strip().split("\n")
        ev_name = None
        ev_data = None
        for l in lines:
            if l.startswith("event: "):
                ev_name = l[7:].strip()
            elif l.startswith("data: "):
                ev_data = json.loads(l[6:].strip())
        if ev_name and ev_data is not None:
            events.append((ev_name, ev_data))
    return events


def test_chat_pdf_lifecycle_and_events(client, temp_settings, monkeypatch):
    embedder = HashEmbedder()
    monkeypatch.setattr("app.ingestion.pipeline._get_embedder", lambda override=None: embedder)

    token = make_jwt(temp_settings.supabase_jwt_secret, sub="user-1")
    headers = {"Authorization": f"Bearer {token}"}

    sess = client.post("/sessions", json={"type": "pdf"}, headers=headers).json()
    sess_id = sess["id"]

    # 1. Chat before upload or ready -> 409 DOCUMENT_NOT_READY
    r_early = client.post(f"/sessions/{sess_id}/chat", json={"message": "Hello"}, headers=headers)
    assert r_early.status_code == 409
    assert r_early.json()["error"]["code"] == "DOCUMENT_NOT_READY"

    # Upload document
    pdf_text = "The monthly fee is INR 450,000 for all consulting services provided. " * 15
    pdf_bytes = make_pdf([pdf_text])
    client.post(
        f"/sessions/{sess_id}/document",
        files={"file": ("doc.pdf", pdf_bytes, "application/pdf")},
        headers=headers,
    )

    # Wait for ready
    for _ in range(30):
        stat = client.get(f"/sessions/{sess_id}/status", headers=headers).json()
        if stat["status"] == "ready":
            break
        time.sleep(0.1)
    assert stat["status"] == "ready"

    # Dependency overrides for chat
    mock_ollama = MockLLM("ollama", "llama3.1:8b", ["The monthly fee is INR 450,000 [S1]."])
    router = LLMRouter(mock_ollama, None, DummyRouterSettings())

    client.app.dependency_overrides[get_embedder] = lambda: embedder
    client.app.dependency_overrides[get_router] = lambda: router

    try:
        # In-doc question
        res = client.post(
            f"/sessions/{sess_id}/chat",
            json={"message": "What is the monthly fee?"},
            headers=headers,
        )
        assert res.status_code == 200
        events = _parse_sse(res.text)

        event_names = [e[0] for e in events]
        assert "status" in event_names
        assert "sources" in event_names
        assert "token" in event_names
        assert "done" in event_names

        done_event = [e[1] for e in events if e[0] == "done"][0]
        assert done_event["model_used"] == "llama3.1:8b"
        assert done_event["fallback"] is False
        assert done_event["grounded"] is True

        # Verify messages persisted
        msgs = client.get(f"/sessions/{sess_id}/messages", headers=headers).json()
        assert len(msgs) == 2
        assert msgs[0]["role"] == "user"
        assert msgs[0]["content"] == "What is the monthly fee?"
        assert msgs[1]["role"] == "assistant"
        assert msgs[1]["model_used"] == "llama3.1:8b"
        assert len(msgs[1]["sources"]) > 0

    finally:
        client.app.dependency_overrides.clear()


def test_chat_pdf_off_topic_no_llm_call(client, temp_settings, monkeypatch):
    embedder = HashEmbedder()
    monkeypatch.setattr("app.ingestion.pipeline._get_embedder", lambda override=None: embedder)

    token = make_jwt(temp_settings.supabase_jwt_secret, sub="user-1")
    headers = {"Authorization": f"Bearer {token}"}

    sess = client.post("/sessions", json={"type": "pdf"}, headers=headers).json()
    sess_id = sess["id"]

    pdf_text = "This document only discusses deep sea marine biology and corals. " * 15
    pdf_bytes = make_pdf([pdf_text])
    client.post(
        f"/sessions/{sess_id}/document",
        files={"file": ("doc.pdf", pdf_bytes, "application/pdf")},
        headers=headers,
    )

    for _ in range(30):
        stat = client.get(f"/sessions/{sess_id}/status", headers=headers).json()
        if stat["status"] == "ready":
            break
        time.sleep(0.1)

    mock_ollama = MockLLM("ollama", "llama3.1:8b", ["Should not be called!"])
    router = LLMRouter(mock_ollama, None, DummyRouterSettings())

    client.app.dependency_overrides[get_embedder] = lambda: embedder
    client.app.dependency_overrides[get_router] = lambda: router

    try:
        # Off-topic question
        res = client.post(
            f"/sessions/{sess_id}/chat",
            json={"message": "What is quantum computing quantum circuit qubit gate?"},
            headers=headers,
        )
        assert res.status_code == 200
        events = _parse_sse(res.text)

        # Off-topic gate must not call LLM
        assert mock_ollama.call_count == 0

        done_event = [e[1] for e in events if e[0] == "done"][0]
        assert done_event["grounded"] is False
        assert done_event["model_used"] is None

    finally:
        client.app.dependency_overrides.clear()
