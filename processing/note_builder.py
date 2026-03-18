"""processing/note_builder.py — Template Method Pattern: 固定筆記生成流程"""
import re
from datetime import date

from llm.base import LLMClient
from processing.result_handler import ProcessedResult


_PROMPT_TEMPLATE = """\
你是一位善於整理知識的研究者，使用卡片盒筆記法（Zettelkasten）。

請根據以下資料，為主題「{topic}」撰寫一張 Atomic Permanent Note。

## 搜尋資料
{sources}

## Vault 中可能相關的筆記（可插入 [[連結]]）
{related}

## 寫作要求
- 聚焦在**一個**最核心的洞察或機制，不要面面俱到
- 用有洞察力的角度寫，讀完要有「原來如此」的感覺
- 在正文中自然插入 [[相關筆記]] 連結（只用提供的清單）
- 正文 100-200 字，繁體中文
- 最後列出 2-3 個來源

## 輸出格式（只輸出 markdown，不加任何說明）
---
title: "{topic}"
type: permanent
tags: {tags}
created: {today}
related:
{related_yaml}
---

（正文）

## 延伸探索
{followups_md}

## 來源
（格式：- [標題](url)）
"""


class NoteBuilder:
    def __init__(self, llm: LLMClient):
        self._llm = llm

    def build(self, result: ProcessedResult) -> str:
        """Template Method: 組裝 prompt → 呼叫 LLM → 清理輸出"""
        prompt = self._build_prompt(result)
        raw    = self._llm.complete(prompt, max_tokens=2000)
        return self._clean(raw.text)

    # ── private ──────────────────────────────────────────────────────────────

    def _build_prompt(self, r: ProcessedResult) -> str:
        sources_text = "\n\n---\n\n".join(
            f"### {s.title}\n{s.url}\n\n{s.content}" for s in r.sources
        )
        related_yaml = "\n".join(f'  - "[[{n}]]"' for n in r.related) or "  []"
        followups_md = "\n".join(f"- [[{t}]]" for t in r.followups) if r.followups else "（待探索）"
        return _PROMPT_TEMPLATE.format(
            topic        = r.topic,
            sources      = sources_text,
            related      = ", ".join(r.related) or "（無）",
            related_yaml = related_yaml,
            followups_md = followups_md,
            domain       = r.domain,
            tags         = str(r.tags),
            today        = date.today(),
        )

    def _clean(self, raw: str) -> str:
        match = re.search(r"(---\s*\ntitle:.*)", raw, re.DOTALL)
        return match.group(1).strip() if match else raw.strip()
