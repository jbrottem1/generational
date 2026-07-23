"""Podcast rankings provider — deterministic placeholder until live wiring.

Chart-position and episode-topic signals: long-form audio interest is a
strong predictor of durable (evergreen/educational) video demand.
"""

from __future__ import annotations

from providers.trend_sources._demo import make_trend
from providers.trend_sources.base import TrendSourceProvider


class PodcastRankingsProvider(TrendSourceProvider):
    key = "podcast_rankings"
    label = "Podcast Rankings (placeholder)"
    platform = "podcasts"

    def discover(self, topic, category="general", country="US", language="en", limit=3):
        return [
            make_trend(
                self.key, self.platform, topic, i,
                category=category, country=country, language=language,
                base_volume=15_000, base_confidence=0.65,
            )
            for i in range(limit)
        ]
