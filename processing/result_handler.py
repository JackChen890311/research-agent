"""processing/result_handler.py — 整合搜尋結果，找相關筆記、分類主題"""
import json
from dataclasses import dataclass
from pathlib import Path

from llm.base import LLMClient
from search.base import SearchResult


@dataclass
class ProcessedResult:
    topic:    str
    sources:  list[SearchResult]
    related:  list[str]          # vault 中相關筆記的標題
    domain:   str
    tags:     list[str]


class ResultHandler:
    def __init__(self, llm: LLMClient, vault: Path):
        self._llm   = llm
        self._vault = vault

    def process(self, topic: str, sources: list[SearchResult]) -> ProcessedResult:
        related = self._find_related(topic)
        meta    = self._classify(topic)
        return ProcessedResult(
            topic   = topic,
            sources = sources,
            related = related,
            domain  = meta.get("domain", "知識"),
            tags    = meta.get("tags", [topic]),
        )

    # ── private ──────────────────────────────────────────────────────────────

    def _find_related(self, topic: str, top_k: int = 8) -> list[str]:
        all_notes = [p.stem for p in self._vault.rglob("*.md") if p.stem != topic]
        if not all_notes:
            return []
        resp = self._llm.complete(
            f"主題：{topic}\n\n"
            f"以下是 Obsidian vault 中現有筆記標題：\n" + "\n".join(all_notes) + "\n\n"
            f"請從中挑出最相關的最多 {top_k} 個。只回傳標題清單，每行一個，不加說明。",
            max_tokens=200,
        )
        return [l.strip() for l in resp.text.strip().splitlines() if l.strip()]

    def _classify(self, topic: str) -> dict:
        raw = self._llm.complete_json(
            f"主題：{topic}\n"
            '回傳 JSON：{"domain": "領域", "tags": ["tag1","tag2","tag3"]}\n'
            "domain 例子：健康、財經、心理學、科技、歷史、飲食、環境、社會"
        )
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"domain": "知識", "tags": [topic]}
