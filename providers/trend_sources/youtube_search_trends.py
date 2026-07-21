"""YouTube search trends — live Search Intelligence when API key set, else demo."""

from __future__ import annotations

from providers.trend_sources._demo import make_trend
from providers.trend_sources.base import TrendSourceProvider
from services.trends.models import Trend


class YoutubeSearchTrendsProvider(TrendSourceProvider):
    key = "youtube_search_trends"
    label = "YouTube Search Intelligence"
    platform = "youtube"

    def is_available(self) -> bool:
        try:
            from services.providers.youtube_provider import get_youtube_provider

            return get_youtube_provider().is_configured()
        except Exception:  # noqa: BLE001
            return True

    def discover(self, topic, category="general", country="US", language="en", limit=3):
        try:
            from services.providers.youtube_search_intelligence import (
                get_youtube_search_intelligence,
                signals_to_trends,
            )

            intel = get_youtube_search_intelligence()
            if intel.is_configured():
                report = intel.analyze_topic(
                    topic,
                    category=category,
                    country=country,
                    language=language,
                    limit=max(limit, 5),
                )
                trends = signals_to_trends(report.videos, category=category, country=country)
                if trends:
                    return trends[:limit]
        except Exception:  # noqa: BLE001
            pass
        return [
            make_trend(
                self.key,
                self.platform,
                topic,
                i,
                category=category,
                country=country,
                language=language,
                base_volume=40_000,
                base_confidence=0.68,
            )
            for i in range(min(limit, 3))
        ]
