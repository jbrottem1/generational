"""Developer communities provider — deterministic placeholder until live wiring.

Forum/Q&A signals (Stack Overflow, Hacker News, Discord-style): what
builders are struggling with and talking about — mid-volume, mid
confidence, good content-gap indicators.
"""

from __future__ import annotations

from providers.trend_sources._demo import make_trend
from providers.trend_sources.base import TrendSourceProvider


class DeveloperCommunitiesProvider(TrendSourceProvider):
    key = "developer_communities"
    label = "Developer Communities (placeholder)"
    platform = "dev_communities"

    def discover(self, topic, category="general", country="US", language="en", limit=3):
        return [
            make_trend(
                self.key, self.platform, topic, i,
                category=category, country=country, language=language,
                base_volume=7_000, base_confidence=0.6,
            )
            for i in range(limit)
        ]
