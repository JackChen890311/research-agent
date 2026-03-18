"""search/fetcher.py — 抓完整網頁內文"""
import httpx
from bs4 import BeautifulSoup


class WebFetcher:
    def __init__(self, max_chars: int = 5000, timeout: int = 8):
        self._max_chars = max_chars
        self._timeout   = timeout

    def fetch(self, url: str) -> str | None:
        try:
            r = httpx.get(
                url, timeout=self._timeout, follow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            soup = BeautifulSoup(r.text, "html.parser")
            for tag in soup(["nav", "footer", "script", "style", "aside"]):
                tag.decompose()
            return soup.get_text(separator="\n", strip=True)[:self._max_chars]
        except Exception:
            return None
