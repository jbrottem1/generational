"""Future analytics provider interfaces — no live integrations required yet.

Clean plug-in surface for YouTube Analytics, TikTok Analytics, Instagram Insights,
A/B tests, retention curves, CTR, AVD, comments. Implementation can arrive later
without changing Audience Intelligence architecture.
"""

from __future__ import annotations

from typing import Any, Protocol


class AudienceAnalyticsProvider(Protocol):
    """Contract for real-world analytics feeds into Audience Intelligence."""

    name: str
    platform: str

    def is_available(self) -> bool: ...

    def fetch_video_metrics(self, video_id: str) -> dict[str, Any]: ...

    def fetch_retention_curve(self, video_id: str) -> dict[str, Any]: ...


def _stub(name: str, platform: str, video_id: str, *, feature: str = "metrics") -> dict[str, Any]:
    return {
        "provider": name,
        "platform": platform,
        "video_id": video_id,
        "connected": False,
        "feature": feature,
        "metrics": {},
        "retention_curve": [],
        "ctr": None,
        "average_watch_duration_sec": None,
        "comments": [],
        "engagement": {},
        "ab_test_results": [],
        "error": f"{name} analytics not connected — interface reserved for future integration",
        "note": "Do not invent live metrics. Wire real credentials later.",
    }


class YouTubeAnalyticsInterface:
    name = "youtube_analytics"
    platform = "youtube_shorts"

    def is_available(self) -> bool:
        try:
            from providers.analytics.youtube import YouTubeAnalyticsProvider

            return bool(YouTubeAnalyticsProvider().is_available())
        except Exception:  # noqa: BLE001
            return False

    def fetch_video_metrics(self, video_id: str) -> dict[str, Any]:
        if not self.is_available():
            return _stub(self.name, self.platform, video_id)
        try:
            from providers.analytics.youtube import YouTubeAnalyticsProvider

            raw = YouTubeAnalyticsProvider().fetch_metrics(video_id, "youtube")
            return {
                "provider": self.name,
                "platform": self.platform,
                "video_id": video_id,
                "connected": True,
                "metrics": raw if isinstance(raw, dict) else {"raw": raw},
                "note": "Uses existing YouTube analytics provider when connected",
            }
        except Exception as exc:  # noqa: BLE001
            out = _stub(self.name, self.platform, video_id)
            out["error"] = str(exc)[:200]
            return out

    def fetch_retention_curve(self, video_id: str) -> dict[str, Any]:
        base = self.fetch_video_metrics(video_id)
        base["feature"] = "retention_curve"
        base.setdefault("retention_curve", [])
        if not base.get("connected"):
            base["error"] = "Retention curve reserved — connect YouTube Analytics later"
        return base


class TikTokAnalyticsInterface:
    name = "tiktok_analytics"
    platform = "tiktok"

    def is_available(self) -> bool:
        return False

    def fetch_video_metrics(self, video_id: str) -> dict[str, Any]:
        return _stub(self.name, self.platform, video_id)

    def fetch_retention_curve(self, video_id: str) -> dict[str, Any]:
        return _stub(self.name, self.platform, video_id, feature="retention_curve")


class InstagramInsightsInterface:
    name = "instagram_insights"
    platform = "instagram_reels"

    def is_available(self) -> bool:
        return False

    def fetch_video_metrics(self, video_id: str) -> dict[str, Any]:
        return _stub(self.name, self.platform, video_id)

    def fetch_retention_curve(self, video_id: str) -> dict[str, Any]:
        return _stub(self.name, self.platform, video_id, feature="retention_curve")


class ABTestResultsInterface:
    """Placeholder for future A/B harness results (e.g. Creative Performance Lab outcomes)."""

    name = "ab_test_results"
    platform = "multi"

    def is_available(self) -> bool:
        return True  # can read local CPL results

    def fetch_video_metrics(self, video_id: str) -> dict[str, Any]:
        # Optional: lightly surface CPL experiment ids if present in labs store
        try:
            from services.creative_performance_lab.store import load_knowledge

            kb = load_knowledge()
            return {
                "provider": self.name,
                "platform": self.platform,
                "video_id": video_id,
                "connected": True,
                "metrics": {},
                "ab_test_results": list(kb.get("learnings") or [])[:10],
                "note": "Local Creative Performance Lab learnings only — not live platform A/B",
            }
        except Exception:  # noqa: BLE001
            return _stub(self.name, self.platform, video_id)

    def fetch_retention_curve(self, video_id: str) -> dict[str, Any]:
        return _stub(self.name, self.platform, video_id, feature="retention_curve")


def list_analytics_interfaces() -> list[dict[str, Any]]:
    providers = [
        YouTubeAnalyticsInterface(),
        TikTokAnalyticsInterface(),
        InstagramInsightsInterface(),
        ABTestResultsInterface(),
    ]
    return [
        {
            "name": p.name,
            "platform": p.platform,
            "available": p.is_available(),
            "methods": ["fetch_video_metrics", "fetch_retention_curve"],
        }
        for p in providers
    ]


def get_analytics_provider(name: str = "youtube_analytics") -> AudienceAnalyticsProvider:
    mapping = {
        "youtube_analytics": YouTubeAnalyticsInterface,
        "youtube": YouTubeAnalyticsInterface,
        "tiktok_analytics": TikTokAnalyticsInterface,
        "tiktok": TikTokAnalyticsInterface,
        "instagram_insights": InstagramInsightsInterface,
        "instagram": InstagramInsightsInterface,
        "ab_test_results": ABTestResultsInterface,
        "ab": ABTestResultsInterface,
    }
    cls = mapping.get(name) or YouTubeAnalyticsInterface
    return cls()
