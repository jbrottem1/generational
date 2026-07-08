"""YouTube research provider — YouTube Trends placeholder."""

from __future__ import annotations

from providers._research_demo import make_document
from providers.research_source import ResearchSourceProvider


class YouTubeProvider(ResearchSourceProvider):
    key = "youtube"
    label = "YouTube Trends"

    def is_available(self) -> bool:
        return True

    def search(self, topic: str, niche: str = "", limit: int = 3) -> list:
        return [
            make_document(
                topic, self.key, "YouTube", i, "video",
                "https://youtube.com/watch?v={slug}{index}",
                citation_count=0,
                popularity=0.8,
            )
            for i in range(min(limit, 2))
        ]
