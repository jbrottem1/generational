"""Research provider interface."""

from __future__ import annotations

from abc import abstractmethod

from providers.base import Provider


class ResearchProvider(Provider):
    @abstractmethod
    def research(self, command: str, niche: str, subject: str, model: str) -> "dict | None":
        """Returns a research brief dict or None to fall back to heuristics."""
