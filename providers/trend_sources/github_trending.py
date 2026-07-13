"""GitHub trending provider — deterministic placeholder until live wiring.

Repository/star-velocity signals: what developers are adopting right now —
a leading indicator for technology content 2-6 weeks before it goes
mainstream.
"""

from __future__ import annotations

from providers.trend_sources._demo import make_trend
from providers.trend_sources.base import TrendSourceProvider


class GithubTrendingProvider(TrendSourceProvider):
    key = "github_trending"
    label = "GitHub Trending (placeholder)"
    platform = "github"

    def discover(self, topic, category="general", country="US", language="en", limit=3):
        return [
            make_trend(
                self.key, self.platform, topic, i,
                category=category, country=country, language=language,
                base_volume=9_000, base_confidence=0.7,
            )
            for i in range(limit)
        ]
