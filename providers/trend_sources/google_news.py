"""Google News — live RSS intelligence for Agent 0 discovery.

Uses providers.news.google_news_provider (production RSS client).
Falls back to demo seeds only if every live pull fails.
"""

from __future__ import annotations

from providers.trend_sources._demo import make_trend
from providers.trend_sources.base import TrendSourceProvider
from services.trends.models import Trend


class GoogleNewsProvider(TrendSourceProvider):
    key = "google_news"
    label = "Google News"
    platform = "news"

    def is_available(self) -> bool:
        try:
            from providers.news.google_news_provider import get_google_news_provider

            return get_google_news_provider().is_configured()
        except Exception:  # noqa: BLE001
            return True

    def discover(self, topic, category="general", country="US", language="en", limit=3):
        try:
            from providers.news.google_news_provider import (
                discovery_items_to_trends,
                get_google_news_provider,
            )

            gn = get_google_news_provider()
            items = gn.discover_for_topic(
                topic,
                category=category,
                country=country,
                language=language,
                limit=max(1, int(limit)),
            )
            trends = discovery_items_to_trends(items, platform=self.platform)
            if trends:
                return trends[:limit]
        except Exception:  # noqa: BLE001
            pass
        return self._demo(topic, category=category, country=country, language=language, limit=limit)

    def _demo(self, topic, *, category, country, language, limit) -> list[Trend]:
        return [
            make_trend(
                self.key,
                self.platform,
                topic if i else f"breaking: {topic}",
                i,
                category="news" if i == 0 else category,
                country=country,
                language=language,
                base_volume=30_000,
                base_confidence=0.58,
            )
            for i in range(min(limit, 2))
        ]
