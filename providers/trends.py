"""Trends research provider."""

from __future__ import annotations

from providers._research_demo import make_document
from providers.research_source import ResearchSourceProvider


class TrendsProvider(ResearchSourceProvider):
    key = "trends"
    label = "Trends"

    def is_available(self) -> bool:
        return True

    def search(self, topic: str, niche: str = "", limit: int = 3) -> list:
        return [
            make_document(
                topic, self.key, "Google Trends", i, "trend",
                "https://trends.google.com/trends/explore?q={slug}",
                citation_count=0,
                popularity=0.85,
            )
            for i in range(min(limit, 2))
        ]
