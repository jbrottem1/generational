"""Analytics provider interface."""

from __future__ import annotations

from abc import abstractmethod

from providers.base import Provider


class AnalyticsProvider(Provider):
    @abstractmethod
    def fetch_metrics(self, content_id: str, platform: str) -> dict:
        ...
