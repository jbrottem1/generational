"""Trend source provider interface.

Every trend provider — Google Trends, YouTube, TikTok, Reddit, RSS, news,
keyword APIs, or future custom sources — implements exactly this contract
and returns only universal `Trend` objects. Nothing downstream may depend
on a specific vendor.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.trends.models import Trend


class TrendSourceProvider(ABC):
    """Contract for all trend discovery providers."""

    key: str = ""       # unique registry key, e.g. "google_trends"
    label: str = ""     # human-readable name for UI/logs
    platform: str = ""  # platform the signals come from, e.g. "tiktok"

    def is_available(self) -> bool:
        """Whether the provider can currently serve requests (keys, quota)."""
        return True

    @abstractmethod
    def discover(
        self,
        topic: str,
        category: str = "general",
        country: str = "US",
        language: str = "en",
        limit: int = 3,
    ) -> "list[Trend]":
        """Return normalized trends related to the topic."""
        raise NotImplementedError
