"""Wikipedia trending pages — modular discovery provider.

Uses Wikimedia pageview demo seeds until a live API key/path is configured.
Drop-in replacement: swap discover() body; keep Trend contract.
"""

from __future__ import annotations

from providers.trend_sources._demo import make_trend
from providers.trend_sources.base import TrendSourceProvider


class WikipediaTrendingProvider(TrendSourceProvider):
    key = "wikipedia_trending"
    label = "Wikipedia Trending (placeholder)"
    platform = "wikipedia"

    def is_available(self) -> bool:
        return True

    def discover(self, topic, category="general", country="US", language="en", limit=3):
        # Prefer educational angles for Generational
        edu_category = category if category != "general" else "education"
        return [
            make_trend(
                self.key,
                self.platform,
                topic,
                i,
                category=edu_category,
                country=country,
                language=language,
                base_volume=18_000,
                base_confidence=0.72,
            )
            for i in range(min(limit, 3))
        ]
