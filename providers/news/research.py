"""News research provider — placeholder until news API integration."""

from __future__ import annotations

from providers._research_demo import make_document
from providers.research_source import ResearchSourceProvider


class NewsProvider(ResearchSourceProvider):
    key = "news"
    label = "News"

    def is_available(self) -> bool:
        return True

    def search(self, topic: str, niche: str = "", limit: int = 3) -> list:
        return [
            make_document(
                topic, self.key, "NewsWire", i, "news",
                "https://news.example.com/{slug}-report-{index}",
                citation_count=0,
                popularity=0.75,
            )
            for i in range(min(limit, 3))
        ]
