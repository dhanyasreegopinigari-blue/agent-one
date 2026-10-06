import httpx

from app.config import get_settings
from app.web_search.base import SearchError, SearchResult


class TavilyProvider:
    def __init__(self, api_key: str | None = None):
        settings = get_settings()
        self.api_key = api_key or settings.tavily_api_key

    async def search(self, query: str, max_results: int) -> list[SearchResult]:
        if not self.api_key:
            raise SearchError("Tavily API key is not configured.")

        url = "https://api.tavily.com/search"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "query": query,
            "max_results": max_results,
        }
        timeout = httpx.Timeout(8.0, connect=3.0)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code != 200:
                    raise SearchError(f"Tavily returned HTTP {resp.status_code}: {resp.text[:200]}")
                data = resp.json()
        except httpx.HTTPError as e:
            raise SearchError(f"Failed to connect to Tavily: {e}") from e
        except Exception as e:
            raise SearchError(f"Error querying Tavily: {e}") from e

        raw_results = data.get("results", [])
        results: list[SearchResult] = []
        for r in raw_results[:max_results]:
            title = r.get("title", "")
            link = r.get("url", "")
            snippet = r.get("content", "") or ""
            results.append(SearchResult(title=title, url=link, snippet=snippet))

        return results
