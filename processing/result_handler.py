"""processing/result_handler.py — 整合搜尋結果，找相關筆記、分類主題"""
import json
from dataclasses import dataclass
from pathlib import Path

from llm.base import LLMClient
from search.base import SearchResult


@dataclass
class ProcessedResult:
    topic:       str
    sources:     list[SearchResult]
    related:     list[str]          # vault 中相關筆記的標題
    domain:      str
    subcategory: str                # domain 內的子分類（用於 MOC 分組）
    tags:        list[str]
    followups:   list[str]          # 建議的延伸探索主題


class ResultHandler:
    def __init__(self, llm: LLMClient, vault: Path):
        self._llm   = llm
        self._vault = vault

    def process(self, topic: str, sources: list[SearchResult]) -> ProcessedResult:
        related   = self._find_related(topic)
        meta      = self._classify(topic)
        followups = self._suggest_followups(topic)
        return ProcessedResult(
            topic       = topic,
            sources     = sources,
            related     = related,
            domain      = meta.get("domain", "知識"),
            subcategory = meta.get("subcategory", "一般"),
            tags        = meta.get("tags", [topic]),
            followups   = followups,
        )

    def process_fleeting(self, topic: str) -> dict:
        """為隨手筆記分類並建議清晰的檔名。回傳 dict: title, domain, subcategory, tags"""
        raw = self._llm.complete_json(
            f"使用者寫了一則隨手筆記，主題為：{topic}\n\n"
            '回傳 JSON：{"title": "建議的檔名（簡潔明確，可對主題稍作修改）", '
            '"domain": "領域", "subcategory": "子分類", "tags": ["tag1","tag2"]}\n'
            "domain 例子：健康、財經、心理學、科技、歷史、飲食、環境、社會\n"
            "subcategory 是 domain 內更細的分類，例如 domain=飲食 時可為 咖啡、烘焙等"
        )
        try:
            raw = raw.strip().strip("```json").strip("```").strip()
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"title": topic, "domain": "知識", "subcategory": "一般", "tags": [topic]}

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

    def suggest_aspects(self, topic: str) -> list[str]:
        resp = self._llm.complete(
            f"主題：{topic}\n\n"
            "請建議 4-6 個可以聚焦研究的不同面向（例如：「咖啡」→「如何沖泡」、「咖啡豆種類」、「咖啡的歷史」）。\n"
            "每個面向用簡短的詞組描述。只回傳清單，每行一個，不加說明、不加編號、不加符號。",
            max_tokens=150,
        )
        return [l.strip() for l in resp.text.strip().splitlines() if l.strip()]

    def _suggest_followups(self, topic: str) -> list[str]:
        resp = self._llm.complete(
            f"主題：{topic}\n\n"
            "請建議 4-6 個延伸研究的主題，以簡單的名詞為主，涵蓋：上位概念（更大的知識框架）、"
            "下位概念（可深入的子主題）、橫向概念（跨領域的相關概念），盡量以生活化的角度切入。\n"
            "只回傳主題名稱清單，每行一個，不加說明、不加編號、不加符號。",
            max_tokens=150,
        )
        return [l.strip() for l in resp.text.strip().splitlines() if l.strip()]

    def _classify(self, topic: str) -> dict:
        raw = self._llm.complete_json(
            f"主題：{topic}\n"
            '回傳 JSON：{"domain": "領域", "subcategory": "子分類", "tags": ["tag1","tag2","tag3"]}\n'
            "domain 例子：健康、財經、心理學、科技、歷史、飲食、環境、社會\n"
            "subcategory 是 domain 內更細的分類，例如 domain=飲食 時可為 咖啡、茶、烘焙等"
        )
        try:
            raw = raw.strip().strip("```json").strip("```").strip()
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"domain": "", "subcategory": "一般", "tags": []}
