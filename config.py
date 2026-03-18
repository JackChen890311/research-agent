from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    # LLM
    ANTHROPIC_KEY  = os.getenv("ANTHROPIC_KEY", "")
    GEMINI_KEY     = os.getenv("GEMINI_KEY", "")
    LLM_PROVIDER   = os.getenv("LLM_PROVIDER", "claude")  # "claude" | "gemini"
    LLM_MODEL      = os.getenv("LLM_MODEL", "claude-sonnet-4-20250514")

    # Search
    TAVILY_KEY     = os.getenv("TAVILY_KEY", "")
    SEARCH_DOMAINS = [
        "wikipedia.org", "britannica.com",
        "healthline.com", "investopedia.com",
        "psychologytoday.com", "scientificamerican.com",
        "hbr.org", "theatlantic.com",
    ]

    # Vault
    VAULT_PATH     = Path(os.getenv("VAULT_PATH", "~/obsidian-vault")).expanduser()

    # Telegram
    TELEGRAM_TOKEN  = os.getenv("TELEGRAM_TOKEN", "")
    ALLOWED_USERS   = set(map(int, os.getenv("ALLOWED_USERS", "0").split(",")))
    TELEGRAM_PROXY  = os.getenv("TELEGRAM_PROXY", "")  # e.g. http://127.0.0.1:7890
