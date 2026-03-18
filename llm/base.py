"""llm/base.py — Strategy Pattern: LLM 可任意替換"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    text: str
    model: str


class LLMClient(ABC):
    """所有 LLM 實作的共同介面"""

    @abstractmethod
    def complete(self, prompt: str, max_tokens: int = 2000) -> LLMResponse:
        ...

    def complete_json(self, prompt: str) -> str:
        """語法糖：要求 LLM 只回傳 JSON"""
        resp = self.complete(prompt + "\n\nOnly return valid JSON, no explanation.", max_tokens=300)
        return resp.text.strip()
