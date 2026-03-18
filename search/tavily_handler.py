"""search/tavily_handler.py"""
from tavily import TavilyClient
from search.base import SearchHandler, SearchResult
from search.fetcher import WebFetcher
from config import Config


class TavilySearchHandler(SearchHandler):
    """
    Decorator Pattern: 在 Tavily 結果上疊加全文抓取。
    兩段搜尋策略：主搜尋 + 補充深度搜尋，合併去重。
    """

    def __init__(self):
        self._client  = TavilyClient(api_key=Config.TAVILY_KEY)
        self._fetcher = WebFetcher()

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        raw = self._multi_search(query)
        return [self._enrich(r) for r in raw[:max_results]]

    # ── private ──────────────────────────────────────────────────────────────

    def _multi_search(self, query: str) -> list[dict]:
        main = self._client.search(
            query, max_results=5, search_depth="advanced",
            include_domains=Config.SEARCH_DOMAINS,
        )["results"]

        supplement = self._client.search(
            f"{query} explained guide", max_results=3, search_depth="basic",
        )["results"]

        seen, merged = set(), []
        for r in main + supplement:
            if r["url"] not in seen:
                seen.add(r["url"])
                merged.append(r)
        return merged

    def _enrich(self, raw: dict) -> SearchResult:
        full = self._fetcher.fetch(raw["url"])
        return SearchResult(
            title   = raw["title"],
            url     = raw["url"],
            content = full or raw["content"],
            score   = raw.get("score", 0.0),
        )
