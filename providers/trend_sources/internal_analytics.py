"""Internal historical analytics provider — our own performance data as a
trend source.

Mines the Knowledge Base `performance` category (written by the Analytics
& Continuous Learning Engine after publishing) for topics that match the
query, and turns proven winners into high-confidence trend signals: what
already worked for THIS system is the strongest predictor of what will
work again.

Falls back to a deterministic low-confidence demo signal while the
Knowledge Base has no performance history, so the provider is always
exercisable and testable.
"""

from __future__ import annotations

import json

from providers.trend_sources._demo import make_trend
from providers.trend_sources.base import TrendSourceProvider
from services.trends.models import Trend


class InternalAnalyticsProvider(TrendSourceProvider):
    key = "internal_analytics"
    label = "Internal Historical Analytics"
    platform = "internal"

    def _matching_history(self, topic: str, limit: int) -> list:
        """Knowledge Base performance entries mentioning the topic. Never raises."""
        try:
            from services.knowledge import CATEGORY, get_knowledge_base

            entries = get_knowledge_base().list_entries(CATEGORY.PERFORMANCE, limit=100)
        except Exception:  # noqa: BLE001 - a broken KB must not break discovery
            return []
        needle = topic.lower()
        return [e for e in entries if needle in json.dumps(e.get("content", "")).lower()][:limit]

    def discover(self, topic, category="general", country="US", language="en", limit=3):
        trends: "list[Trend]" = []
        for entry in self._matching_history(topic, limit):
            content = entry.get("content")
            content = content if isinstance(content, dict) else {}
            if "performance" in content:
                score = float(content["performance"])          # already 0-1
            else:
                score = float(content.get("score", 50)) / 100  # 0-100 → 0-1
            score = min(1.0, max(0.0, score))
            trends.append(
                Trend(
                    topic=str(content.get("topic", topic)),
                    keywords=[topic.lower(), category, "proven performer"],
                    growth_pct=round(score * 100, 1),
                    search_volume=int(content.get("views", 20_000)),
                    velocity=round(score * 0.8, 2),
                    competition=0.4,
                    freshness=0.6,
                    category=category,
                    country=country,
                    language=language,
                    platform=self.platform,
                    source=self.key,
                    confidence=0.85,   # our own data — highest-trust source
                )
            )

        # Demo fallback keeps the provider deterministic and testable until
        # real performance history accumulates.
        for i in range(len(trends), limit):
            trends.append(
                make_trend(
                    self.key, self.platform, topic, i,
                    category=category, country=country, language=language,
                    base_volume=15_000, base_confidence=0.65,
                )
            )
        return trends
