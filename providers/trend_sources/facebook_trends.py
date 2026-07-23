"""Facebook trends provider — deterministic placeholder until live API wiring."""

from __future__ import annotations

from providers.trend_sources._demo import make_trend
from providers.trend_sources.base import TrendSourceProvider


class FacebookTrendsProvider(TrendSourceProvider):
    key = "facebook_trends"
    label = "Facebook Trends (placeholder)"
    platform = "facebook"

    def discover(self, topic, category="general", country="US", language="en", limit=3):
        return [
            make_trend(
                self.key, self.platform, topic, i,
                category=category, country=country, language=language,
                base_volume=25_000, base_confidence=0.55,
            )
            for i in range(limit)
        ]
