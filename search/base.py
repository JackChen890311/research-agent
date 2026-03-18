"""search/base.py — Strategy Pattern: 搜尋引擎可替換"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class SearchResult:
    title:   str
    url:     str
    content: str
    score:   float = 0.0
    extra:   dict  = field(default_factory=dict)


class SearchHandler(ABC):
    @abstractmethod
    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        ...
