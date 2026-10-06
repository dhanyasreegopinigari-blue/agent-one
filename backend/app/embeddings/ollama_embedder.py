import asyncio

import faiss
import httpx
import numpy as np

from app.config import get_settings
from app.embeddings.base import EmbeddingError


class OllamaEmbedder:
    def __init__(self, model: str | None = None, base_url: str | None = None):
        settings = get_settings()
        self.model = model or settings.ollama_embed_model
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.dim: int | None = None

    async def _post_embed(self, client: httpx.AsyncClient, inputs: list[str]) -> list[list[float]]:
        settings = get_settings()
        url = f"{self.base_url}/api/embed"
        payload = {
            "model": self.model,
            "input": inputs,
            "keep_alive": settings.ollama_keep_alive,
        }
        resp = await client.post(url, json=payload)
        if resp.status_code != 200:
            raise EmbeddingError(
                "EMBEDDING_UNAVAILABLE",
                f"Ollama returned HTTP {resp.status_code}: {resp.text[:200]}",
            )
        data = resp.json()
        if "embeddings" not in data or not isinstance(data["embeddings"], list):
            raise EmbeddingError(
                "EMBEDDING_UNAVAILABLE",
                "Ollama response missing 'embeddings' array.",
            )
        return data["embeddings"]

    async def embed_documents(self, texts: list[str]) -> np.ndarray:
        if not texts:
            dim = self.dim or 0
            return np.empty((0, dim), dtype="float32")

        settings = get_settings()
        prefix = settings.embed_doc_prefix
        prefixed_texts = [f"{prefix}{t}" for t in texts]

        batch_size = max(1, settings.embed_batch_size)
        all_embeddings: list[list[float]] = []

        timeout = httpx.Timeout(120.0, connect=3.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            for i in range(0, len(prefixed_texts), batch_size):
                batch = prefixed_texts[i : i + batch_size]
                batch_embeddings = None
                last_error: Exception | None = None

                for attempt in range(3):  # initial + up to 2 retries
                    try:
                        batch_embeddings = await self._post_embed(client, batch)
                        break
                    except (httpx.HTTPError, EmbeddingError) as e:
                        last_error = e
                        if attempt < 2:
                            backoff = 1.0 if attempt == 0 else 3.0
                            await asyncio.sleep(backoff)

                if batch_embeddings is None:
                    raise EmbeddingError(
                        "EMBEDDING_UNAVAILABLE",
                        f"Failed to embed document batch: {last_error}",
                    )

                all_embeddings.extend(batch_embeddings)

        arr = np.ascontiguousarray(all_embeddings, dtype="float32")
        if self.dim is None and arr.shape[0] > 0:
            self.dim = arr.shape[1]
        faiss.normalize_L2(arr)
        return arr

    async def embed_query(self, text: str) -> np.ndarray:
        settings = get_settings()
        prefixed = f"{settings.embed_query_prefix}{text}"

        timeout = httpx.Timeout(120.0, connect=3.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                embeddings = await self._post_embed(client, [prefixed])
            except (httpx.HTTPError, EmbeddingError) as e:
                raise EmbeddingError(
                    "EMBEDDING_UNAVAILABLE",
                    f"Failed to embed query: {e}",
                ) from e

        if not embeddings:
            raise EmbeddingError("EMBEDDING_UNAVAILABLE", "Empty query embedding returned.")

        arr = np.ascontiguousarray(embeddings[0], dtype="float32")
        if self.dim is None:
            self.dim = arr.shape[0]
        faiss.normalize_L2(arr.reshape(1, -1))
        return arr
