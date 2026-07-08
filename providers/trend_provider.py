"""Trend / topic signal provider interface."""

from __future__ import annotations

from abc import abstractmethod

from providers.base import Provider


class TrendProvider(Provider):
    @abstractmethod
    def trend_strength(self, subject: str, niche: str) -> "int | None":
        ...
