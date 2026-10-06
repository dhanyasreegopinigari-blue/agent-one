import httpx

from app.config import get_settings
from app.web_search.base import SearchError, SearchResult


class SearxngProvider:
    def __init__(self, base_url: str | None = None):
        settings = get_settings()
        self.base_url = (base_url or settings.searxng_url).rstrip("/")

    async def search(self, query: str, max_results: int) -> list[SearchResult]:
        url = f"{self.base_url}/search"
        params = {
            "q": query,
            "format": "json",
            "language": "auto",
            "safesearch": "1",
        }
        timeout = httpx.Timeout(8.0, connect=3.0)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.get(url, params=params)
                if resp.status_code != 200:
                    raise SearchError(f"SearXNG returned HTTP {resp.status_code}: {resp.text[:200]}")
                data = resp.json()
        except httpx.HTTPError as e:
            raise SearchError(f"Failed to connect to SearXNG: {e}") from e
        except Exception as e:
            raise SearchError(f"Error querying SearXNG: {e}") from e

        raw_results = data.get("results", [])
        results: list[SearchResult] = []
        seen_urls: set[str] = set()

        for r in raw_results:
            link = r.get("url", "")
            if not link.startswith(("http://", "https://")):
                continue
            if link in seen_urls:
                continue
            seen_urls.add(link)

            title = r.get("title", "")
            snippet = r.get("content", "") or ""
            results.append(SearchResult(title=title, url=link, snippet=snippet))
            if len(results) >= max_results:
                break

        return results
