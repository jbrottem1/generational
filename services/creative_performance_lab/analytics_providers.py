"""Analytics provider interfaces — YouTube live; TikTok/Instagram stubs for later."""

from __future__ import annotations

from typing import Any, Protocol


class AnalyticsIngestProvider(Protocol):
    name: str
    platform: str

    def is_available(self) -> bool: ...

    def fetch_video_metrics(self, video_id: str) -> dict[str, Any]: ...


class YouTubeLabAnalytics:
    """Thin adapter over existing providers.analytics.youtube."""

    name = "youtube"
    platform = "youtube_shorts"

    def is_available(self) -> bool:
        try:
            from providers.analytics.youtube import YouTubeAnalyticsProvider

            return YouTubeAnalyticsProvider().is_available()
        except Exception:  # noqa: BLE001
            return False

    def fetch_video_metrics(self, video_id: str) -> dict[str, Any]:
        from providers.analytics.youtube import YouTubeAnalyticsProvider

        raw = YouTubeAnalyticsProvider().fetch_metrics(video_id, "youtube")
        return {
            "provider": self.name,
            "platform": self.platform,
            "video_id": video_id,
            "connected": self.is_available(),
            "metrics": raw,
            "note": "Uses existing YouTube analytics provider — never invents metrics",
        }


class TikTokLabAnalyticsStub:
    name = "tiktok"
    platform = "tiktok"

    def is_available(self) -> bool:
        return False

    def fetch_video_metrics(self, video_id: str) -> dict[str, Any]:
        return {
            "provider": self.name,
            "platform": self.platform,
            "video_id": video_id,
            "connected": False,
            "metrics": {},
            "error": "TikTok analytics not connected — interface reserved",
        }


class InstagramLabAnalyticsStub:
    name = "instagram"
    platform = "instagram_reels"

    def is_available(self) -> bool:
        return False

    def fetch_video_metrics(self, video_id: str) -> dict[str, Any]:
        return {
            "provider": self.name,
            "platform": self.platform,
            "video_id": video_id,
            "connected": False,
            "metrics": {},
            "error": "Instagram analytics not connected — interface reserved",
        }


def get_analytics_provider(platform: str = "youtube_shorts") -> AnalyticsIngestProvider:
    p = (platform or "").lower()
    if "tiktok" in p:
        return TikTokLabAnalyticsStub()
    if "instagram" in p or "reel" in p:
        return InstagramLabAnalyticsStub()
    return YouTubeLabAnalytics()
