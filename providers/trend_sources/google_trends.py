"""Google Trends provider — deterministic placeholder until live API wiring."""

from __future__ import annotations

from providers.trend_sources._demo import make_trend
from providers.trend_sources.base import TrendSourceProvider


class GoogleTrendsProvider(TrendSourceProvider):
    key = "google_trends"
    label = "Google Trends (placeholder)"
    platform = "google"

    def discover(self, topic, category="general", country="US", language="en", limit=3):
        return [
            make_trend(
                self.key, self.platform, topic, i,
                category=category, country=country, language=language,
                base_volume=50_000, base_confidence=0.7,
            )
            for i in range(limit)
        ]
