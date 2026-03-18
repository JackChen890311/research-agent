"""llm/claude.py"""
import anthropic
from llm.base import LLMClient, LLMResponse


class ClaudeClient(LLMClient):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model  = model

    def complete(self, prompt: str, max_tokens: int = 2000) -> LLMResponse:
        resp = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return LLMResponse(text=resp.content[0].text, model=self._model)
