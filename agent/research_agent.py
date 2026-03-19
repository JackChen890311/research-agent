"""
agent/research_agent.py — Facade Pattern

ResearchAgent 是唯一對外的介面，
所有內部元件（搜尋、處理、寫入、sync）都藏在裡面。
CLI 和 Telegram Bot 只需要呼叫 run()，不需要知道細節。
"""
import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from llm.base import LLMClient
from search.base import SearchHandler
from processing.result_handler import ResultHandler
from processing.note_builder import NoteBuilder
from processing.literature_builder import LiteratureBuilder
from storage.vault_writer import VaultWriter
from storage.git_syncer import GitSyncer


ProgressCallback = Callable[[str], None] | None


@dataclass
class ResearchOutput:
    topic:     str
    domain:    str
    path:      Path
    synced:    bool
    followups: list[str]


@dataclass
class FleetingOutput:
    title:   str
    domain:  str
    path:    Path
    synced:  bool


class ResearchAgent:
    def __init__(
        self,
        llm:     LLMClient,
        search:  SearchHandler,
        vault:   Path,
    ):
        self._search      = search
        self._handler     = ResultHandler(llm, vault)
        self._builder     = NoteBuilder(llm)
        self._lit_builder = LiteratureBuilder(llm)
        self._writer      = VaultWriter(vault)
        self._syncer      = GitSyncer(vault)

    async def suggest_aspects(self, topic: str) -> list[str]:
        """用 LLM 產生該主題可聚焦的研究面向建議"""
        return await asyncio.to_thread(self._handler.suggest_aspects, topic)

    async def run(
        self,
        topic: str,
        focus: str | None = None,
        on_progress: ProgressCallback = None,
    ) -> ResearchOutput:
        """
        非同步主流程，每個步驟完成後呼叫 on_progress 回報進度。
        所有同步的 I/O 操作都用 asyncio.to_thread() 包起來，
        確保不阻塞 event loop（Telegram Bot 需要）。

        focus: 使用者選擇的研究面向（若有），加入 frontmatter 但不影響筆記標題。
        """
        prog = _make_progress(on_progress)

        search_query = f"{topic} {focus}" if focus else topic

        await prog("🔍 搜尋資料中...")
        sources = await asyncio.to_thread(self._search.search, search_query)

        await prog("🔗 掃描現有相關筆記...")
        result = await asyncio.to_thread(self._handler.process, topic, sources)

        await prog("📚 建立文獻筆記...")
        lit_titles = await asyncio.to_thread(self._save_literature, topic, result.domain, sources)

        await prog("✍️  整理筆記...")
        content = await asyncio.to_thread(self._builder.build, result, lit_titles)
        if focus:
            content = _inject_focus(content, focus)

        await prog("💾 寫入筆記軟體（Obsidian）...")
        path = await asyncio.to_thread(self._writer.write, result, content)

        await prog("🔄 同步筆記（Git）...")
        synced = await asyncio.to_thread(self._syncer.sync, f"add: {topic}")

        return ResearchOutput(
            topic     = path.stem,  # 使用實際檔名（可能含編號）
            domain    = result.domain,
            path      = path,
            synced    = synced,
            followups = result.followups,
        )

    async def add_fleeting(
        self,
        topic:   str,
        content: str,
        on_progress: ProgressCallback = None,
    ) -> FleetingOutput:
        """
        儲存隨手筆記。LLM 會建議一個清晰的檔名和分類，但內容原文保留。
        """
        prog = _make_progress(on_progress)

        await prog("🗂️ 分類筆記...")
        meta = await asyncio.to_thread(self._handler.process_fleeting, topic)

        title       = meta.get("title", topic)
        domain      = meta.get("domain", "知識")
        subcategory = meta.get("subcategory", "一般")
        tags        = meta.get("tags", [topic])

        note_content = _build_fleeting_content(title, domain, subcategory, tags, content)

        await prog("💾 寫入筆記...")
        path = await asyncio.to_thread(self._writer.write_fleeting, domain, title, note_content)

        await prog("🔄 同步筆記（Git）...")
        synced = await asyncio.to_thread(self._syncer.sync, f"fleeting: {title}")

        return FleetingOutput(title=title, domain=domain, path=path, synced=synced)

    # ── private ──────────────────────────────────────────────────────────────

    def _save_literature(self, topic: str, domain: str, sources) -> list[str]:
        """
        為每個來源建立文獻筆記（同步，供 asyncio.to_thread 使用）。
        回傳成功儲存的簡化標題清單，供永久筆記的來源區段使用。
        """
        titles = []
        for source in sources:
            try:
                result = self._lit_builder.build_one(topic, source)
                if result is None:
                    continue  # LLM 判斷內容無法取得，略過此來源
                title, lit_content = result
                self._writer.write_literature(domain, title, lit_content)
                titles.append(title)
            except Exception:
                pass  # 單一來源失敗不中斷整體流程
        return titles


def _inject_focus(content: str, focus: str) -> str:
    """在 frontmatter 的 type: permanent 後插入 focus 屬性。"""
    return content.replace(
        "type: permanent\n",
        f"type: permanent\nfocus: \"{focus}\"\n",
        1,
    )


def _build_fleeting_content(
    title: str,
    domain: str,
    subcategory: str,
    tags: list[str],
    content: str,
) -> str:
    return (
        f"---\n"
        f'title: "{title}"\n'
        f"type: fleeting\n"
        f"domain: {domain}\n"
        f"subcategory: {subcategory}\n"
        f"tags: {tags}\n"
        f"created: {date.today()}\n"
        f"---\n\n"
        f"{content}\n"
    )


def _make_progress(cb: ProgressCallback):
    """把同步/非同步/None 的 callback 統一包成 async callable"""
    async def _noop(_): pass

    if cb is None:
        return _noop
    if asyncio.iscoroutinefunction(cb):
        return cb
    # 同步 callback（CLI print）包成 async
    async def _wrapped(msg: str):
        cb(msg)
    return _wrapped
