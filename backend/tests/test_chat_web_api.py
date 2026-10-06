from app.api.chat import get_embedder, get_router, get_search_provider
from app.llm.router import LLMRouter
from app.web_search.base import SearchError, SearchResult
from tests.conftest import HashEmbedder, make_jwt, make_pdf
from tests.test_chat_pdf_api import _parse_sse
from tests.test_llm_router import DummyRouterSettings, MockLLM


class FakeSearchProvider:
    def __init__(self, results: list[SearchResult] | Exception):
        self.results = results
        self.call_count = 0

    async def search(self, query: str, max_results: int) -> list[SearchResult]:
        self.call_count += 1
        if isinstance(self.results, Exception):
            raise self.results
        return self.results[:max_results]


def test_chat_web_lifecycle_with_results(client, temp_settings):
    token = make_jwt(temp_settings.supabase_jwt_secret, sub="user-1")
    headers = {"Authorization": f"Bearer {token}"}

    sess = client.post("/sessions", json={"type": "web"}, headers=headers).json()
    sess_id = sess["id"]

    results = [
        SearchResult(title="Result 1", url="https://example.com/1", snippet="Snippet 1 text"),
        SearchResult(title="Result 2", url="https://example.com/2", snippet="Snippet 2 text"),
    ]
    fake_search = FakeSearchProvider(results)
    mock_ollama = MockLLM("ollama", "llama3.1:8b", ["According to [W1], this is true."])
    router = LLMRouter(mock_ollama, None, DummyRouterSettings())

    client.app.dependency_overrides[get_search_provider] = lambda: fake_search
    client.app.dependency_overrides[get_router] = lambda: router

    try:
        res = client.post(f"/sessions/{sess_id}/chat", json={"message": "Search this"}, headers=headers)
        assert res.status_code == 200
        events = _parse_sse(res.text)

        event_names = [e[0] for e in events]
        assert "status" in event_names
        assert "sources" in event_names
        assert "token" in event_names
        assert "done" in event_names

        sources_event = [e[1] for e in events if e[0] == "sources"][0]
        assert len(sources_event["sources"]) == 2
        assert sources_event["sources"][0]["id"] == "W1"

        done_event = [e[1] for e in events if e[0] == "done"][0]
        assert done_event["model_used"] == "llama3.1:8b"
        assert done_event["grounded"] is True
        assert done_event["cited"] == ["W1"]

        # Verify messages persisted
        msgs = client.get(f"/sessions/{sess_id}/messages", headers=headers).json()
        assert len(msgs) == 2
        assert msgs[1]["sources"][0]["id"] == "W1"
    finally:
        client.app.dependency_overrides.clear()


def test_chat_web_zero_results_no_llm_call(client, temp_settings):
    token = make_jwt(temp_settings.supabase_jwt_secret, sub="user-1")
    headers = {"Authorization": f"Bearer {token}"}

    sess = client.post("/sessions", json={"type": "web"}, headers=headers).json()
    sess_id = sess["id"]

    fake_search = FakeSearchProvider([])
    mock_ollama = MockLLM("ollama", "llama3.1:8b", ["Should not be called!"])
    router = LLMRouter(mock_ollama, None, DummyRouterSettings())

    client.app.dependency_overrides[get_search_provider] = lambda: fake_search
    client.app.dependency_overrides[get_router] = lambda: router

    try:
        res = client.post(f"/sessions/{sess_id}/chat", json={"message": "Zero results"}, headers=headers)
        assert res.status_code == 200
        events = _parse_sse(res.text)

        assert mock_ollama.call_count == 0
        done_event = [e[1] for e in events if e[0] == "done"][0]
        assert done_event["grounded"] is False
        assert done_event["model_used"] is None
    finally:
        client.app.dependency_overrides.clear()


def test_chat_web_search_error_emits_error_event(client, temp_settings):
    token = make_jwt(temp_settings.supabase_jwt_secret, sub="user-1")
    headers = {"Authorization": f"Bearer {token}"}

    sess = client.post("/sessions", json={"type": "web"}, headers=headers).json()
    sess_id = sess["id"]

    fake_search = FakeSearchProvider(SearchError("Search engine offline"))
    mock_ollama = MockLLM("ollama", "llama3.1:8b", ["Never"])
    router = LLMRouter(mock_ollama, None, DummyRouterSettings())

    client.app.dependency_overrides[get_search_provider] = lambda: fake_search
    client.app.dependency_overrides[get_router] = lambda: router

    try:
        res = client.post(f"/sessions/{sess_id}/chat", json={"message": "Search fail"}, headers=headers)
        assert res.status_code == 200
        events = _parse_sse(res.text)

        error_event = [e[1] for e in events if e[0] == "error"][0]
        assert error_event["code"] == "SEARCH_UNAVAILABLE"
        assert "Search engine offline" in error_event["message"]
    finally:
        client.app.dependency_overrides.clear()


def test_isolation_web_never_calls_embedder_and_pdf_never_calls_search(
    client, temp_settings, monkeypatch
):
    token = make_jwt(temp_settings.supabase_jwt_secret, sub="user-1")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Web session: spy on embedder
    class SpyEmbedder(HashEmbedder):
        def __init__(self):
            super().__init__()
            self.embed_call_count = 0

        async def embed_query(self, text: str):
            self.embed_call_count += 1
            return await super().embed_query(text)

    spy_embedder = SpyEmbedder()
    fake_search = FakeSearchProvider([SearchResult(title="A", url="https://a.com", snippet="B")])
    mock_ollama = MockLLM("ollama", "llama3.1:8b", ["Answer"])
    router = LLMRouter(mock_ollama, None, DummyRouterSettings())

    client.app.dependency_overrides[get_embedder] = lambda: spy_embedder
    client.app.dependency_overrides[get_search_provider] = lambda: fake_search
    client.app.dependency_overrides[get_router] = lambda: router

    try:
        web_sess = client.post("/sessions", json={"type": "web"}, headers=headers).json()
        client.post(f"/sessions/{web_sess['id']}/chat", json={"message": "Web query"}, headers=headers)
        assert fake_search.call_count == 1
        assert spy_embedder.embed_call_count == 0  # Web chat NEVER touches embedder!

        # 2. PDF session: spy on search provider
        # Setup PDF
        monkeypatch.setattr("app.ingestion.pipeline._get_embedder", lambda override=None: spy_embedder)
        pdf_sess = client.post("/sessions", json={"type": "pdf"}, headers=headers).json()
        pdf_bytes = make_pdf(["Some contract clause for testing isolation." * 15])
        client.post(
            f"/sessions/{pdf_sess['id']}/document",
            files={"file": ("doc.pdf", pdf_bytes, "application/pdf")},
            headers=headers,
        )
        # Wait for ready
        import time
        for _ in range(30):
            st = client.get(f"/sessions/{pdf_sess['id']}/status", headers=headers).json()
            if st["status"] == "ready":
                break
            time.sleep(0.1)

        search_calls_before = fake_search.call_count
        client.post(f"/sessions/{pdf_sess['id']}/chat", json={"message": "Contract query"}, headers=headers)
        assert fake_search.call_count == search_calls_before  # PDF chat NEVER touches search provider!
    finally:
        client.app.dependency_overrides.clear()
