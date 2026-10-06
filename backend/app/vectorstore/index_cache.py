import threading
from collections import OrderedDict

from app.config import get_settings
from app.vectorstore.faiss_store import FaissStore


class IndexCache:
    def __init__(self, capacity: int = 8):
        self.capacity = capacity
        self._cache: OrderedDict[str, tuple[FaissStore, list[dict]]] = OrderedDict()
        self._lock = threading.Lock()

    def get(
        self, session_id: str, expected_model: str | None = None
    ) -> tuple[FaissStore, list[dict]]:
        settings = get_settings()
        expected = expected_model or settings.ollama_embed_model

        with self._lock:
            if session_id in self._cache:
                self._cache.move_to_end(session_id)
                return self._cache[session_id]

        session_dir = settings.sessions_dir / session_id
        store, chunks = FaissStore.load(session_dir, expected)

        with self._lock:
            self._cache[session_id] = (store, chunks)
            self._cache.move_to_end(session_id)
            if len(self._cache) > self.capacity:
                self._cache.popitem(last=False)
            return store, chunks

    def set(self, session_id: str, store: FaissStore, chunks: list[dict]) -> None:
        with self._lock:
            self._cache[session_id] = (store, chunks)
            self._cache.move_to_end(session_id)
            if len(self._cache) > self.capacity:
                self._cache.popitem(last=False)

    def invalidate(self, session_id: str) -> None:
        with self._lock:
            self._cache.pop(session_id, None)


_index_cache: IndexCache | None = None


def get_index_cache() -> IndexCache:
    global _index_cache
    if _index_cache is None:
        settings = get_settings()
        _index_cache = IndexCache(capacity=settings.index_cache_size)
    return _index_cache
