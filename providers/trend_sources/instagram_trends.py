"""Instagram trends provider — deterministic placeholder until live API wiring."""

from __future__ import annotations

from providers.trend_sources._demo import make_trend
from providers.trend_sources.base import TrendSourceProvider


class InstagramTrendsProvider(TrendSourceProvider):
    key = "instagram_trends"
    label = "Instagram Trends (placeholder)"
    platform = "instagram"

    def discover(self, topic, category="general", country="US", language="en", limit=3):
        return [
            make_trend(
                self.key, self.platform, topic, i,
                category=category, country=country, language=language,
                base_volume=30_000, base_confidence=0.6,
            )
            for i in range(limit)
        ]
