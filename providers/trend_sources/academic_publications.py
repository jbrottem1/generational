"""Academic publications provider — deterministic placeholder until live wiring.

Journal/preprint signals: slow-moving, low-volume, very high confidence —
strong early indicators for educational and evergreen content.
"""

from __future__ import annotations

from providers.trend_sources._demo import make_trend
from providers.trend_sources.base import TrendSourceProvider


class AcademicPublicationsProvider(TrendSourceProvider):
    key = "academic_publications"
    label = "Academic Publications (placeholder)"
    platform = "academic"

    def discover(self, topic, category="general", country="US", language="en", limit=3):
        return [
            make_trend(
                self.key, self.platform, topic, i,
                category=category, country=country, language=language,
                base_volume=3_000, base_confidence=0.8,
            )
            for i in range(limit)
        ]
