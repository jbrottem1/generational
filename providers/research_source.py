"""Research source provider interface — every data provider implements search()."""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from providers.base import Provider

if TYPE_CHECKING:
    from services.research.models import ResearchDocument


class ResearchSourceProvider(Provider):
    """Unified interface for Wikipedia, PubMed, arXiv, etc."""

    key: str = "base"
    label: str = "Base"

    @abstractmethod
    def search(self, topic: str, niche: str = "", limit: int = 3) -> "list[ResearchDocument]":
        """Return normalized research documents for a topic."""
