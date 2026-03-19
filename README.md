# NoteBoi

An automated research and note-taking system built on the [Zettelkasten](https://en.wikipedia.org/wiki/Zettelkasten) methodology.

Given a topic, it asks which aspect you want to focus on, searches curated web sources, summarizes each source into a literature note, synthesizes everything into a permanent note with proper vault links, and commits it all to Git — accessible via CLI or Telegram bot.

## Note Types

The vault is organized into four folders:

| Folder | Type | Description |
|---|---|---|
| `00-MOC/` | Map of Contents | Auto-updated index per domain, grouped by sub-category |
| `10-Fleeting/` | Fleeting note | Raw user input, verbatim — auto-classified by LLM |
| `20-Literature/` | Literature note | One note per web source: LLM summary + original URL |
| `30-Permanent/` | Permanent note | Synthesized Zettelkasten note, links to literature notes |

## Features

- **Aspect-first research** — before searching, asks which angle of the topic to focus on (e.g. coffee → brewing methods / bean varieties / history); aspect is stored in frontmatter, not the filename
- **Literature notes** — each web source becomes its own `20-Literature/` note with an LLM-written summary; inaccessible or paywalled sources are automatically skipped
- **Permanent notes** — 400–600 word synthesis in Traditional Chinese; `## 來源` links to literature notes, not raw URLs
- **Fleeting notes** — capture raw thoughts via `/fleeting`; LLM suggests a clean filename and classifies domain/subcategory without touching content
- **Knowledge linking** — scans existing vault notes and inserts `[[wikilinks]]` to related notes
- **MOC sub-categories** — domain Maps of Contents are organized under `## sub-category` headings (e.g. `## 咖啡` inside `飲食 MOC.md`)
- **Duplicate handling** — if a note for the same topic already exists, saves as `topic 2.md`, `topic 3.md`, etc.
- **Git sync** — commits and pushes after every write
- **Swappable LLMs** — switch between Claude and Gemini via one env variable

## Architecture

```
ResearchAgent.run(topic, focus?)
  ├─ TavilySearchHandler      web search (curated domains) + full-text fetch
  ├─ ResultHandler             LLM: domain, subcategory, tags, related notes, followups
  ├─ LiteratureBuilder         LLM: summarize each source → 20-Literature/
  ├─ NoteBuilder               LLM: synthesize permanent note, inject [[lit]] links
  ├─ VaultWriter               write files, update MOC with subcategory grouping
  └─ GitSyncer                 git add / commit / push

ResearchAgent.add_fleeting(topic, content)
  ├─ ResultHandler.process_fleeting()   LLM: clean filename, domain, subcategory
  ├─ VaultWriter.write_fleeting()       10-Fleeting/{domain}/
  └─ GitSyncer
```

## Requirements

- Python 3.12+
- [uv](https://github.com/astral-sh/uv)
- An [Obsidian](https://obsidian.md/) vault (should be a Git repo for sync)
- API keys: [Anthropic](https://console.anthropic.com/) or [Google Gemini](https://aistudio.google.com/), and [Tavily](https://tavily.com/)
- Optional: a [Telegram bot token](https://core.telegram.org/bots#botfather)

## Installation

```bash
git clone <repo-url>
cd research-agent

cp .env.example .env
# Fill in your API keys and vault path

uv sync
```

## Configuration

| Variable | Required | Default | Description |
|---|---|---|---|
| `ANTHROPIC_KEY` | if Claude | — | Anthropic API key |
| `GEMINI_KEY` | if Gemini | — | Google Gemini API key |
| `LLM_PROVIDER` | no | `claude` | `claude` or `gemini` |
| `LLM_MODEL` | no | `claude-sonnet-4-6` | Model name |
| `TAVILY_KEY` | yes | — | Tavily search API key |
| `VAULT_PATH` | yes | `~/obsidian-vault` | Absolute path to your Obsidian vault |
| `TELEGRAM_TOKEN` | bot mode | — | Telegram bot token |
| `ALLOWED_USERS` | no | `0` | Comma-separated Telegram user IDs |

## Usage

### CLI

```bash
# Research a topic (prompts for aspect focus interactively)
python main.py --topic "複利效應"

# Save a fleeting note
python main.py --fleeting
```

### Telegram Bot

```bash
python main.py --bot
```

| Action | How |
|---|---|
| Research a topic | Send any text message |
| Pick a focus aspect | Tap one of the suggested buttons (or type your own) |
| Explore follow-ups | Tap one of the follow-up suggestion buttons after a note is saved |
| Save a fleeting note | Send `/fleeting`, then follow the prompts |

### Note structure

**Permanent note frontmatter:**
```yaml
---
title: "複利效應"
type: permanent
focus: "投資中的實際應用"   # set when a focus aspect was chosen
domain: 財經
subcategory: 投資
tags: [複利, 投資, 財務自由]
created: 2026-03-19
related:
  - "[[時間價值]]"
  - "[[指數成長]]"
---
```

**Sources chain:**
```
Permanent note  →  ## 來源
                     - [[複利效應的數學基礎]]     ← literature note link
                     - [[長期投資的複利優勢]]

Literature note →  ## 摘要  (LLM summary, 150–250 words)
                   ## 來源
                   - [Original Article Title](https://...)   ← actual URL
```

## Project Structure

```
research-agent/
├── main.py                       Entry point & composition root
├── config.py                     Environment-based configuration
├── agent/
│   └── research_agent.py         Orchestrator: run() and add_fleeting()
├── llm/
│   ├── base.py                   Abstract LLMClient
│   ├── claude.py                 Anthropic Claude
│   └── gemini.py                 Google Gemini
├── search/
│   ├── tavily_handler.py         Two-stage Tavily search + full-text fetch
│   ├── fetcher.py                HTTP page content extractor
│   └── base.py                   SearchResult dataclass
├── processing/
│   ├── result_handler.py         Domain/subcategory classification, related notes, followups
│   ├── literature_builder.py     Per-source literature note generation
│   └── note_builder.py           Permanent note generation + source link injection
├── storage/
│   ├── vault_writer.py           File writer, MOC updater, duplicate handling
│   └── git_syncer.py             git add / commit / push
└── interfaces/
    ├── cli.py                    Interactive CLI
    └── telegram_bot.py           Telegram bot with inline keyboards
```
