"""AI research provider — deterministic placeholder until live wiring.

Model releases, benchmarks, and lab announcements: high-velocity,
high-confidence signals for the technology/AI content market.
"""

from __future__ import annotations

from providers.trend_sources._demo import make_trend
from providers.trend_sources.base import TrendSourceProvider


class AiResearchProvider(TrendSourceProvider):
    key = "ai_research"
    label = "AI Research (placeholder)"
    platform = "ai_research"

    def discover(self, topic, category="general", country="US", language="en", limit=3):
        return [
            make_trend(
                self.key, self.platform, topic, i,
                category=category, country=country, language=language,
                base_volume=18_000, base_confidence=0.75,
            )
            for i in range(limit)
        ]
