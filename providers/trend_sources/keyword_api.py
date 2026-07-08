"""Keyword research API provider — deterministic placeholder until API wiring."""

from __future__ import annotations

from providers.trend_sources._demo import make_trend
from providers.trend_sources.base import TrendSourceProvider


class KeywordApiProvider(TrendSourceProvider):
    key = "keyword_api"
    label = "Keyword APIs (placeholder)"
    platform = "google"

    def discover(self, topic, category="general", country="US", language="en", limit=3):
        return [
            make_trend(
                self.key, self.platform, topic, i,
                category=category, country=country, language=language,
                base_volume=40_000, base_confidence=0.75,
            )
            for i in range(min(limit, 2))
        ]
