"""PubMed research provider."""

from __future__ import annotations

from providers._research_demo import make_document
from providers.research_source import ResearchSourceProvider


class PubMedProvider(ResearchSourceProvider):
    key = "pubmed"
    label = "PubMed"

    def is_available(self) -> bool:
        return True

    def search(self, topic: str, niche: str = "", limit: int = 3) -> list:
        return [
            make_document(
                topic, self.key, "PubMed", i, "scientific",
                "https://pubmed.ncbi.nlm.nih.gov/{index}/",
                citation_count=50 + i * 30,
                popularity=0.6,
            )
            for i in range(min(limit, 3))
        ]
