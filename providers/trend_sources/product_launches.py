"""Product launches provider — deterministic placeholder until live wiring.

Launch-tracker signals (Product Hunt-style): bursty, fresh, mid
confidence — early warning for breaking tech/product topics.
"""

from __future__ import annotations

from providers.trend_sources._demo import make_trend
from providers.trend_sources.base import TrendSourceProvider


class ProductLaunchesProvider(TrendSourceProvider):
    key = "product_launches"
    label = "Product Launches (placeholder)"
    platform = "launches"

    def discover(self, topic, category="general", country="US", language="en", limit=3):
        return [
            make_trend(
                self.key, self.platform, topic, i,
                category=category, country=country, language=language,
                base_volume=12_000, base_confidence=0.6,
            )
            for i in range(limit)
        ]
