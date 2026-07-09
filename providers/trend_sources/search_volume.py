"""Search volume provider — deterministic placeholder until live wiring.

Raw query-volume signals (complements `keyword_api`'s keyword-database
angle): the highest-volume demand indicator, high confidence.
"""

from __future__ import annotations

from providers.trend_sources._demo import make_trend
from providers.trend_sources.base import TrendSourceProvider


class SearchVolumeProvider(TrendSourceProvider):
    key = "search_volume"
    label = "Search Volume (placeholder)"
    platform = "search"

    def discover(self, topic, category="general", country="US", language="en", limit=3):
        return [
            make_trend(
                self.key, self.platform, topic, i,
                category=category, country=country, language=language,
                base_volume=80_000, base_confidence=0.75,
            )
            for i in range(limit)
        ]
