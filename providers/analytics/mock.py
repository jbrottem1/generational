"""MockAnalyticsProvider — deterministic platform metrics for development.

Metrics are derived from a hash of (content_id, platform), so the same
content always yields the same numbers: the learning loop, experiments,
and tests all behave reproducibly. Every payload is marked `mock: true`;
real platform APIs swap in behind the same interface.
"""

from __future__ import annotations

import hashlib

from providers.analytics_provider import AnalyticsProvider

# Per-platform baseline scale so mock data resembles real distribution
# differences (shorts platforms skew high-view / low-watch-time).
_PLATFORM_SCALE = {
    "youtube_shorts": 1.0,
    "tiktok": 1.4,
    "instagram_reels": 0.9,
    "facebook_reels": 0.5,
    "youtube": 0.6,
}


def _seed(content_id: str, platform: str) -> int:
    digest = hashlib.sha256(f"{content_id}|{platform}".encode("utf-8")).hexdigest()
    return int(digest[:12], 16)


class MockAnalyticsProvider(AnalyticsProvider):
    name = "mock"

    def is_available(self) -> bool:
        return True

    def fetch_metrics(self, content_id: str, platform: str) -> dict:
        seed = _seed(content_id, platform)
        scale = _PLATFORM_SCALE.get(platform, 0.8)

        views = int((1_000 + seed % 99_000) * scale)
        retention = 35 + seed % 56                      # 35-90 percent
        avg_view_duration = round(10 + (seed % 400) / 10.0, 1)   # 10-50 sec
        ctr = round(2 + (seed % 110) / 10.0, 1)         # 2-13 percent
        engagement_base = max(1, views // 100)

        return {
            "views": views,
            "watch_time_sec": int(views * avg_view_duration),
            "average_view_duration_sec": avg_view_duration,
            "audience_retention": retention,
            "ctr": ctr,
            "likes": engagement_base * (2 + seed % 7),
            "comments": engagement_base // (2 + seed % 5),
            "shares": engagement_base // (1 + seed % 4),
            "saves": engagement_base // (2 + seed % 6),
            "subscriber_growth": (seed % 50) - 5,       # can be negative
            "followers_gained": seed % 120,
            "rpm": 0,                                    # placeholder — no monetization API
            "cpm": 0,                                    # placeholder — no monetization API
            "mock": True,
        }
