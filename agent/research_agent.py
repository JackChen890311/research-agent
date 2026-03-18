"""
agent/research_agent.py — Facade Pattern

ResearchAgent 是唯一對外的介面，
所有內部元件（搜尋、處理、寫入、sync）都藏在裡面。
CLI 和 Telegram Bot 只需要呼叫 run()，不需要知道細節。
"""
import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from llm.base import LLMClient
from search.base import SearchHandler
from processing.result_handler import ResultHandler
from processing.note_builder import NoteBuilder
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


class ResearchAgent:
    def __init__(
        self,
        llm:     LLMClient,
        search:  SearchHandler,
        vault:   Path,
    ):
        self._search  = search
        self._handler = ResultHandler(llm, vault)
        self._builder = NoteBuilder(llm)
        self._writer  = VaultWriter(vault)
        self._syncer  = GitSyncer(vault)

    async def run(
        self,
        topic: str,
        on_progress: ProgressCallback = None,
    ) -> ResearchOutput:
        """
        非同步主流程，每個步驟完成後呼叫 on_progress 回報進度。
        所有同步的 I/O 操作都用 asyncio.to_thread() 包起來，
        確保不阻塞 event loop（Telegram Bot 需要）。
        """
        prog = _make_progress(on_progress)

        await prog("🔍 搜尋資料中...")
        sources = await asyncio.to_thread(self._search.search, topic)

        await prog("🔗 掃描 vault 找相關筆記...")
        result = await asyncio.to_thread(self._handler.process, topic, sources)

        await prog("✍️ 整理筆記...")
        content = await asyncio.to_thread(self._builder.build, result)

        await prog("💾 寫入 Obsidian...")
        path = await asyncio.to_thread(self._writer.write, result, content)

        await prog("🔄 Git sync...")
        synced = await asyncio.to_thread(self._syncer.sync, f"add: {topic}")

        return ResearchOutput(
            topic     = topic,
            domain    = result.domain,
            path      = path,
            synced    = synced,
            followups = result.followups,
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
