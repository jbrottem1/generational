"""arXiv research provider."""

from __future__ import annotations

from providers._research_demo import make_document
from providers.research_source import ResearchSourceProvider


class ArxivProvider(ResearchSourceProvider):
    key = "arxiv"
    label = "arXiv"

    def is_available(self) -> bool:
        return True

    def search(self, topic: str, niche: str = "", limit: int = 3) -> list:
        return [
            make_document(
                topic, self.key, "arXiv", i, "preprint",
                "https://arxiv.org/abs/2401.{index:05d}",
                citation_count=20 + i * 15,
                popularity=0.55,
            )
            for i in range(min(limit, 3))
        ]
