"""RSS feed trend provider — deterministic placeholder until feed wiring."""

from __future__ import annotations

from providers.trend_sources._demo import make_trend
from providers.trend_sources.base import TrendSourceProvider


class RssFeedsProvider(TrendSourceProvider):
    key = "rss_feeds"
    label = "RSS Feeds (placeholder)"
    platform = "rss"

    def discover(self, topic, category="general", country="US", language="en", limit=3):
        return [
            make_trend(
                self.key, self.platform, topic, i,
                category=category, country=country, language=language,
                base_volume=5_000, base_confidence=0.5,
            )
            for i in range(min(limit, 2))
        ]
