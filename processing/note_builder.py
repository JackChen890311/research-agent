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
- 標題要簡潔明確，能夠反映筆記的核心內容
- 筆記應該是獨立且完整的，能夠被未來的自己或他人理解
- 用有洞察力的角度寫，讀完要有「原來如此」的感覺
- 在正文中自然插入 [[相關筆記]] 連結（只用提供的清單）
- 正文 400-600 字，繁體中文
- 來源區段直接使用提供的清單，不要新增或刪減

## 輸出格式（只輸出 markdown，不加任何說明）
---
title: "{topic}"
type: permanent
tags: {tags}
created: {today}
related:
{related_yaml}
---

（正文，可以使用分段、列點或表格輔助）

## 延伸探索
{followups_md}

## 來源
{sources_links}
"""


class NoteBuilder:
    def __init__(self, llm: LLMClient):
        self._llm = llm

    def build(self, result: ProcessedResult, lit_titles: list[str] | None = None) -> str:
        """Template Method: 組裝 prompt → 呼叫 LLM → 清理輸出 → 注入來源連結"""
        prompt  = self._build_prompt(result, lit_titles)
        raw     = self._llm.complete(prompt, max_tokens=2000)
        content = self._clean(raw.text)
        if lit_titles:
            content = self._inject_sources(content, lit_titles)
        return content

    # ── private ──────────────────────────────────────────────────────────────

    def _build_prompt(self, r: ProcessedResult, lit_titles: list[str] | None) -> str:
        sources_text = "\n\n---\n\n".join(
            f"### {s.title}\n{s.url}\n\n{s.content}" for s in r.sources
        )
        related_yaml = "\n".join(f'  - "[[{n}]]"' for n in r.related) or "  []"
        followups_md = "\n".join(f"- [[{t}]]" for t in r.followups) if r.followups else "（待探索）"

        if lit_titles:
            sources_links = "\n".join(f"- [[{t}]]" for t in lit_titles)
        else:
            sources_links = "\n".join(f"- [{s.title}]({s.url})" for s in r.sources[:5])

        return _PROMPT_TEMPLATE.format(
            topic         = r.topic,
            sources       = sources_text,
            related       = ", ".join(r.related) or "（無）",
            related_yaml  = related_yaml,
            followups_md  = followups_md,
            sources_links = sources_links,
            domain        = r.domain,
            tags          = str(r.tags),
            today         = date.today(),
        )

    def _inject_sources(self, content: str, lit_titles: list[str]) -> str:
        """強制將 ## 來源 區段替換為文獻筆記連結，不依賴 LLM 輸出正確格式。"""
        links = "\n".join(f"- [[{t}]]" for t in lit_titles)
        new_section = f"## 來源\n\n{links}"
        # 替換從 ## 來源 到文末的所有內容
        content = re.sub(r"## 來源.*", new_section, content, flags=re.DOTALL)
        return content.rstrip() + "\n"

    def _clean(self, raw: str) -> str:
        match = re.search(r"(---\s*\ntitle:.*)", raw, re.DOTALL)
        return match.group(1).strip() if match else raw.strip()
