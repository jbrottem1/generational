"""TikTok Trends research provider — placeholder until API integration."""

from __future__ import annotations

from providers._research_demo import make_document
from providers.research_source import ResearchSourceProvider


class TikTokProvider(ResearchSourceProvider):
    key = "tiktok"
    label = "TikTok Trends"

    def is_available(self) -> bool:
        return True

    def search(self, topic: str, niche: str = "", limit: int = 3) -> list:
        return [
            make_document(
                topic, self.key, "TikTok Trends", i, "trend",
                "https://tiktok.com/tag/{slug}",
                citation_count=0,
                popularity=0.82,
            )
            for i in range(min(limit, 2))
        ]
