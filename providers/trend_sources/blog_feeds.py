"""Blog feeds provider — deterministic placeholder until live crawl wiring."""

from __future__ import annotations

from providers.trend_sources._demo import make_trend
from providers.trend_sources.base import TrendSourceProvider


class BlogFeedsProvider(TrendSourceProvider):
    key = "blog_feeds"
    label = "Blog Feeds (placeholder)"
    platform = "blogs"

    def discover(self, topic, category="general", country="US", language="en", limit=3):
        return [
            make_trend(
                self.key, self.platform, topic, i,
                category=category, country=country, language=language,
                base_volume=8_000, base_confidence=0.5,
            )
            for i in range(limit)
        ]
