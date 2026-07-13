"""Industry publications provider — deterministic placeholder until live wiring.

Trade journals and industry outlets are slower but higher-authority
signals: lower volume, higher confidence than general social sources.
"""

from __future__ import annotations

from providers.trend_sources._demo import make_trend
from providers.trend_sources.base import TrendSourceProvider


class IndustryPublicationsProvider(TrendSourceProvider):
    key = "industry_publications"
    label = "Industry Publications (placeholder)"
    platform = "industry"

    def discover(self, topic, category="general", country="US", language="en", limit=3):
        return [
            make_trend(
                self.key, self.platform, topic, i,
                category=category, country=country, language=language,
                base_volume=5_000, base_confidence=0.75,
            )
            for i in range(limit)
        ]
