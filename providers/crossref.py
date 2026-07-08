"""Crossref research provider."""

from __future__ import annotations

from providers._research_demo import make_document
from providers.research_source import ResearchSourceProvider


class CrossrefProvider(ResearchSourceProvider):
    key = "crossref"
    label = "Crossref"

    def is_available(self) -> bool:
        return True

    def search(self, topic: str, niche: str = "", limit: int = 3) -> list:
        return [
            make_document(
                topic, self.key, "Crossref", i, "citation",
                "https://doi.org/10.1000/{slug}.{index}",
                citation_count=100 + i * 40,
                popularity=0.5,
            )
            for i in range(min(limit, 3))
        ]
