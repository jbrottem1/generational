"""YouTube Trending — live Data API when YOUTUBE_API_KEY is set, else demo."""

from __future__ import annotations

from providers.trend_sources._demo import make_trend
from providers.trend_sources.base import TrendSourceProvider
from services.trends.models import Trend


# YouTube category most relevant to educational content
_SCIENCE_EDU_CATEGORY = "28"  # Science & Technology
_EDUCATION_CATEGORY = "27"


class YouTubeTrendingProvider(TrendSourceProvider):
    key = "youtube_trending"
    label = "YouTube Trending"
    platform = "youtube_shorts"

    def is_available(self) -> bool:
        try:
            from services.providers.youtube_provider import get_youtube_provider

            return get_youtube_provider().is_configured()
        except Exception:  # noqa: BLE001
            return True  # demo fallback always available

    def discover(self, topic, category="general", country="US", language="en", limit=3):
        try:
            from services.providers.youtube_provider import get_youtube_provider

            yt = get_youtube_provider()
            if yt.is_configured():
                return self._live_discover(yt, topic, category=category, country=country, limit=limit)
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
                base_volume=80_000,
                base_confidence=0.65,
            )
            for i in range(limit)
        ]

    def _live_discover(self, yt, topic: str, *, category: str, country: str, limit: int) -> list[Trend]:
        cat_id = ""
        if "science" in (category or "").lower() or "edu" in (category or "").lower():
            cat_id = _SCIENCE_EDU_CATEGORY
        result = yt.search_trending(region_code=country or "US", max_results=max(limit, 5), category_id=cat_id)
        if not result.get("ok"):
            # Retry without category filter
            result = yt.search_trending(region_code=country or "US", max_results=max(limit, 5))
        trends: list[Trend] = []
        for i, item in enumerate((result.get("items") or [])[:limit]):
            snippet = item.get("snippet") or {}
            stats = item.get("statistics") or {}
            title = str(snippet.get("title") or topic)
            views = int(stats.get("viewCount") or 0)
            likes = int(stats.get("likeCount") or 0)
            comments = int(stats.get("commentCount") or 0)
            engagement = (likes + comments) / views if views else 0.0
            trends.append(
                Trend(
                    topic=title[:120],
                    keywords=[w.lower() for w in title.split()[:5] if len(w) > 2],
                    search_volume=max(views, 1),
                    growth_pct=min(200.0, engagement * 5000),
                    velocity=min(1.0, engagement * 20),
                    competition=0.55,
                    freshness=0.85,
                    category=category or "general",
                    country=country or "US",
                    language="en",
                    platform=self.platform,
                    source=self.key,
                    confidence=0.82,
                )
            )
        if not trends:
            return [
                make_trend(
                    self.key,
                    self.platform,
                    topic,
                    i,
                    category=category,
                    country=country,
                    base_volume=80_000,
                    base_confidence=0.55,
                )
                for i in range(limit)
            ]
        return trends
