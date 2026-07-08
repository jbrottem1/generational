"""Wikipedia research provider."""

from __future__ import annotations

from providers._research_demo import make_document
from providers.research_source import ResearchSourceProvider


class WikipediaProvider(ResearchSourceProvider):
    key = "wikipedia"
    label = "Wikipedia"

    def is_available(self) -> bool:
        return True

    def search(self, topic: str, niche: str = "", limit: int = 3) -> list:
        return [
            make_document(
                topic, self.key, "Wikipedia", i, "encyclopedia",
                "https://en.wikipedia.org/wiki/{slug}",
                citation_count=0,
                popularity=0.7,
            )
            for i in range(min(limit, 3))
        ]
