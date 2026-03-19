from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    # LLM
    ANTHROPIC_KEY  = os.getenv("ANTHROPIC_KEY", "")
    GEMINI_KEY     = os.getenv("GEMINI_KEY", "")
    LLM_PROVIDER   = os.getenv("LLM_PROVIDER", "claude")  # "claude" | "gemini"
    LLM_MODEL      = os.getenv("LLM_MODEL", "claude-sonnet-4-6")

    # Search
    TAVILY_KEY     = os.getenv("TAVILY_KEY", "")
    SEARCH_DOMAINS = [
        # 百科 / 知識
        "wikipedia.org",
        "zh.wikipedia.org",
        "wikihow.com",
        "britannica.com",

        # 英文新聞
        "bbc.com",
        "reuters.com",
        "apnews.com",
        "theguardian.com",
        "nytimes.com",
        "techcrunch.com",
        "wired.com",

        # 中文新聞（台灣）
        "udn.com",
        "ltn.com.tw",
        "cna.com.tw",
        "ithome.com.tw",

        # 學術 / 研究 / 技術 / 開發
        "arxiv.org",
        "stackoverflow.com",

        # 生活 / 健康 / 財經 / 心理學 / 自我成長
        "healthline.com",
        "mayoclinic.org",
        "investopedia.com",
        "money.udn.com",
        "commonhealth.com.tw",
        "twreporter.org",
        "scientificamerican.com",
        "hbr.org", "theatlantic.com",
    ]

    # Vault
    VAULT_PATH     = Path(os.getenv("VAULT_PATH", "~/obsidian-vault")).expanduser()

    # Telegram
    TELEGRAM_TOKEN  = os.getenv("TELEGRAM_TOKEN", "")
    ALLOWED_USERS   = set(map(int, os.getenv("ALLOWED_USERS", "0").split(",")))