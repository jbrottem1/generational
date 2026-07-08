"""YouTube Trending provider — deterministic placeholder until Data API wiring."""

from __future__ import annotations

from providers.trend_sources._demo import make_trend
from providers.trend_sources.base import TrendSourceProvider


class YouTubeTrendingProvider(TrendSourceProvider):
    key = "youtube_trending"
    label = "YouTube Trending (placeholder)"
    platform = "youtube_shorts"

    def discover(self, topic, category="general", country="US", language="en", limit=3):
        return [
            make_trend(
                self.key, self.platform, topic, i,
                category=category, country=country, language=language,
                base_volume=80_000, base_confidence=0.65,
            )
            for i in range(limit)
        ]
