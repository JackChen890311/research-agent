"""llm/__init__.py — Factory Pattern: 根據 config 決定用哪個 LLM"""
from config import Config
from llm.base import LLMClient
from llm.claude import ClaudeClient
from llm.gemini import GeminiClient


def create_llm_client() -> LLMClient:
    match Config.LLM_PROVIDER:
        case "claude":
            return ClaudeClient(api_key=Config.ANTHROPIC_KEY, model=Config.LLM_MODEL)
        case "gemini":
            return GeminiClient(api_key=Config.GEMINI_KEY, model=Config.LLM_MODEL)
        case _:
            raise ValueError(f"Unknown LLM provider: {Config.LLM_PROVIDER}")
