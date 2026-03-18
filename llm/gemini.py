"""llm/gemini.py"""
from google import genai
from google.genai import types
from llm.base import LLMClient, LLMResponse


class GeminiClient(LLMClient):
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        self._client     = genai.Client(api_key=api_key)
        self._model_name = model

    def complete(self, prompt: str, max_tokens: int = 2000) -> LLMResponse:
        resp = self._client.models.generate_content(
            model=self._model_name,
            contents=prompt,
            config=types.GenerateContentConfig(max_output_tokens=max_tokens),
        )
        return LLMResponse(text=resp.text, model=self._model_name)