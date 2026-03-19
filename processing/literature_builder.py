"""processing/literature_builder.py — 將每個網頁來源整理成文獻筆記"""
from datetime import date

from llm.base import LLMClient
from search.base import SearchResult


class LiteratureBuilder:
    def __init__(self, llm: LLMClient):
        self._llm = llm

    def build_one(self, research_topic: str, source: SearchResult) -> tuple[str, str] | None:
        """
        根據單一搜尋來源建立文獻筆記。
        回傳 (simplified_title, markdown_content)，
        或 None（當內容無法取得、為錯誤頁面或資訊量不足時）。
        """
        resp = self._llm.complete(
            f"研究主題：{research_topic}\n\n"
            f"以下是一篇文章的內容：\n"
            f"原始標題：{source.title}\n"
            f"網址：{source.url}\n\n"
            f"{source.content}\n\n"
            "請判斷這份內容是否包含與研究主題相關的實質資訊（非錯誤頁面、非存取限制、非空白內容）。\n\n"
            "如果內容無法取得或無實質資訊，只回傳一行：SKIP\n\n"
            "如果有實質內容，請回傳以下兩部分（用 === 分隔）：\n"
            "1. 簡潔筆記標題：6-12 個繁體中文字，反映文章核心論點，不要用原始標題直接翻譯\n"
            "2. 摘要：150-250 字，說明這篇文章與研究主題的關聯及核心論點\n\n"
            "格式：\n"
            "<標題>\n"
            "===\n"
            "<摘要>",
            max_tokens=500,
        ).text.strip()

        if resp.upper().startswith("SKIP"):
            return None

        if "===" in resp:
            parts   = resp.split("===", 1)
            title   = parts[0].strip()
            summary = parts[1].strip()
        else:
            title   = (source.title or source.url).strip()
            summary = resp

        content = (
            f"---\n"
            f'title: "{title}"\n'
            f"type: literature\n"
            f"source: {source.url}\n"
            f"topic: {research_topic}\n"
            f"created: {date.today()}\n"
            f"---\n\n"
            f"## 摘要\n\n"
            f"{summary}\n\n"
            f"## 來源\n\n"
            f"- [{source.title or source.url}]({source.url})\n"
        )
        return title, content
