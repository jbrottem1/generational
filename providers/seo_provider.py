"""SEO provider interface."""

from __future__ import annotations

from abc import abstractmethod

from providers.base import Provider


class SEOProvider(Provider):
    @abstractmethod
    def optimize(self, title: str, hook: str, niche: str, subject: str, model: str) -> "dict | None":
        """Returns SEO packaging dict or None for heuristic fallback."""
