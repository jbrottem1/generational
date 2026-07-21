"""YouTube Data API v3 — centralized authenticated client.

Production rules:
- Read credentials only from environment / SecretManager via get_credential
- Never hardcode keys
- Never log or raise the raw API key
- Graceful degradation when the key is missing or quota is exhausted

Usage:
    from services.providers.youtube_provider import get_youtube_provider

    yt = get_youtube_provider()
    status = yt.validate()
    videos = yt.search_videos("axial tilt seasons", max_results=5)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlencode

from core.log import get_logger, log_event
from services.provider_runtime.config import get_credential, has_credential
from services.provider_runtime.http_client import request_json

logger = get_logger(__name__)

API_BASE = "https://www.googleapis.com/youtube/v3"
ENV_VAR = "YOUTUBE_API_KEY"

# Approximate quota units (YouTube Data API v3)
QUOTA_COSTS = {
    "search": 100,
    "videos": 1,
    "channels": 1,
    "videoCategories": 1,
    "commentThreads": 1,
}


def mask_secret(value: str | None, *, visible: int = 4) -> str:
    """Return a masked representation safe for logs / UI."""
    raw = str(value or "")
    if not raw:
        return "(missing)"
    if len(raw) <= visible * 2:
        return "***"
    return f"{raw[:visible]}…{raw[-visible:]} (len={len(raw)})"


def _sanitize_error(message: str, api_key: str = "") -> str:
    """Strip any accidental secret material from error strings."""
    text = str(message or "")
    if api_key and api_key in text:
        text = text.replace(api_key, "***REDACTED***")
    # Common query param leakage
    if "key=" in text:
        parts = []
        for chunk in text.split("&"):
            if chunk.startswith("key=") or "key=" in chunk and chunk.split("key=", 1)[-1]:
                if "key=" in chunk:
                    chunk = chunk.split("key=", 1)[0] + "key=***REDACTED***"
            parts.append(chunk)
        text = "&".join(parts)
    return text[:500]


@dataclass
class YouTubeQuotaTracker:
    """In-process quota accounting for discovery budgeting."""

    units_used: int = 0
    calls: list[dict[str, Any]] = field(default_factory=list)
    daily_budget: int = 10_000  # default YouTube project quota

    def record(self, operation: str, units: int, *, ok: bool) -> None:
        self.units_used += max(0, int(units))
        self.calls.append(
            {
                "operation": operation,
                "units": units,
                "ok": ok,
                "ts": time.time(),
            }
        )

    def remaining(self) -> int:
        return max(0, self.daily_budget - self.units_used)

    def snapshot(self) -> dict[str, Any]:
        return {
            "units_used": self.units_used,
            "daily_budget": self.daily_budget,
            "remaining_estimate": self.remaining(),
            "calls": len(self.calls),
        }


class YouTubeProviderError(RuntimeError):
    """Safe error — never includes the API key."""


class YouTubeProvider:
    """Authenticated YouTube Data API v3 client."""

    name = "youtube_data_api_v3"
    credential_env = ENV_VAR

    def __init__(self, *, api_key: str | None = None, quota: YouTubeQuotaTracker | None = None):
        # api_key=None → resolve from env; api_key="" → explicitly unconfigured (tests)
        self._explicit_key = api_key is not None
        self._api_key = (api_key if api_key is not None else get_credential(ENV_VAR) or "").strip()
        self.quota = quota or YouTubeQuotaTracker()

    # ------------------------------------------------------------------
    # Auth / health
    # ------------------------------------------------------------------

    def is_configured(self) -> bool:
        if self._explicit_key:
            return bool(self._api_key)
        return bool(self._api_key) or has_credential(ENV_VAR)

    def _key(self) -> str:
        if not self._api_key and not self._explicit_key:
            self._api_key = (get_credential(ENV_VAR) or "").strip()
        return self._api_key

    def masked_key(self) -> str:
        return mask_secret(self._key())

    def validate(self) -> dict[str, Any]:
        """Startup / Agent 0 validation — never crashes the process."""
        report: dict[str, Any] = {
            "provider": self.name,
            "env_var": ENV_VAR,
            "detected": False,
            "authenticated": False,
            "quota_accessible": False,
            "trending_search_ok": False,
            "ok": False,
            "error": None,
            "masked_key": "(missing)",
            "quota": self.quota.snapshot(),
        }
        if not self.is_configured():
            report["error"] = (
                f"{ENV_VAR} is missing. Add it to the project .env "
                "(see .env.example) and restart. Never commit the real key."
            )
            return report

        report["detected"] = True
        report["masked_key"] = self.masked_key()

        # Cheap auth probe: videos.list mostPopular (1 unit)
        try:
            probe = self.search_trending(region_code="US", max_results=1, category_id="")
            if probe.get("ok"):
                report["authenticated"] = True
                report["quota_accessible"] = True
                report["trending_search_ok"] = True
                report["ok"] = True
            else:
                report["error"] = _sanitize_error(str(probe.get("error") or "auth_failed"), self._key())
                # Distinguish auth vs quota
                err = (report["error"] or "").lower()
                if "quota" in err:
                    report["authenticated"] = True
                    report["quota_accessible"] = False
                elif "key" in err or "403" in err or "400" in err or "401" in err:
                    report["authenticated"] = False
        except Exception as exc:  # noqa: BLE001
            report["error"] = _sanitize_error(str(exc), self._key())

        report["quota"] = self.quota.snapshot()
        return report

    # ------------------------------------------------------------------
    # Low-level request
    # ------------------------------------------------------------------

    def _request(self, resource: str, params: dict[str, Any]) -> dict[str, Any]:
        key = self._key()
        if not key:
            return {"ok": False, "error": f"{ENV_VAR} not configured", "items": []}

        cost = QUOTA_COSTS.get(resource, 1)
        if self.quota.remaining() < cost:
            return {
                "ok": False,
                "error": "youtube_quota_budget_exhausted",
                "items": [],
                "quota": self.quota.snapshot(),
            }

        query = {k: v for k, v in params.items() if v is not None and v != ""}
        query["key"] = key
        url = f"{API_BASE}/{resource}?{urlencode(query)}"
        # Build a log-safe URL without the key
        safe_params = {**query, "key": "***"}
        safe_url = f"{API_BASE}/{resource}?{urlencode(safe_params)}"

        try:
            resp = request_json("GET", url, timeout_sec=20, retries=1)
        except Exception as exc:  # noqa: BLE001
            self.quota.record(resource, cost, ok=False)
            log_event(logger, "youtube.request_failed", level=30, resource=resource, error=_sanitize_error(str(exc), key))
            return {"ok": False, "error": _sanitize_error(str(exc), key), "items": []}

        ok = resp.ok
        self.quota.record(resource, cost, ok=ok)
        body = resp.body if isinstance(resp.body, dict) else {"raw": str(resp.body)[:200]}

        if not ok:
            err_obj = body.get("error") if isinstance(body, dict) else None
            message = ""
            if isinstance(err_obj, dict):
                message = str(err_obj.get("message") or err_obj)
            else:
                message = f"HTTP {resp.status}"
            log_event(
                logger,
                "youtube.api_error",
                level=30,
                resource=resource,
                status=resp.status,
                error=_sanitize_error(message, key),
                url=safe_url,
            )
            return {
                "ok": False,
                "error": _sanitize_error(message, key),
                "status": resp.status,
                "items": [],
                "quota": self.quota.snapshot(),
            }

        items = list(body.get("items") or [])
        return {
            "ok": True,
            "items": items,
            "page_info": body.get("pageInfo") or {},
            "next_page_token": body.get("nextPageToken"),
            "quota": self.quota.snapshot(),
            "raw_keys": list(body.keys()),
        }

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def search_videos(
        self,
        query: str,
        *,
        max_results: int = 10,
        order: str = "relevance",
        region_code: str = "US",
        published_after: str | None = None,
        video_duration: str | None = None,
        relevance_language: str = "en",
    ) -> dict[str, Any]:
        """Search public videos by keyword."""
        return self._request(
            "search",
            {
                "part": "snippet",
                "type": "video",
                "q": query,
                "maxResults": max(1, min(int(max_results), 50)),
                "order": order,
                "regionCode": region_code,
                "relevanceLanguage": relevance_language,
                "publishedAfter": published_after,
                "videoDuration": video_duration,
            },
        )

    def keyword_search(self, keyword: str, **kwargs: Any) -> dict[str, Any]:
        return self.search_videos(keyword, **kwargs)

    def search_topics(self, topic: str, *, max_results: int = 10, **kwargs: Any) -> dict[str, Any]:
        """Topic search biased toward educational explainers."""
        q = f"{topic} explained OR science OR educational"
        return self.search_videos(q, max_results=max_results, order=kwargs.pop("order", "viewCount"), **kwargs)

    def search_trending(
        self,
        *,
        region_code: str = "US",
        max_results: int = 10,
        category_id: str = "",
    ) -> dict[str, Any]:
        """Most popular videos (chart=mostPopular)."""
        return self._request(
            "videos",
            {
                "part": "snippet,statistics,contentDetails",
                "chart": "mostPopular",
                "regionCode": region_code,
                "maxResults": max(1, min(int(max_results), 50)),
                "videoCategoryId": category_id or None,
            },
        )

    def category_search(
        self,
        category_id: str,
        *,
        region_code: str = "US",
        max_results: int = 10,
    ) -> dict[str, Any]:
        return self.search_trending(
            region_code=region_code,
            max_results=max_results,
            category_id=str(category_id),
        )

    def search_channels(
        self,
        query: str,
        *,
        max_results: int = 5,
        region_code: str = "US",
    ) -> dict[str, Any]:
        return self._request(
            "search",
            {
                "part": "snippet",
                "type": "channel",
                "q": query,
                "maxResults": max(1, min(int(max_results), 50)),
                "regionCode": region_code,
                "order": "relevance",
            },
        )

    def related_videos(self, video_id: str, *, max_results: int = 10) -> dict[str, Any]:
        """Related / similar videos via search (relatedToVideoId deprecated — use topic query fallback)."""
        # relatedToVideoId was deprecated; approximate with video title search when possible
        meta = self.video_statistics(video_id)
        title = ""
        items = meta.get("items") or []
        if items:
            title = str((items[0].get("snippet") or {}).get("title") or "")
        query = title or video_id
        result = self.search_videos(query, max_results=max_results, order="relevance")
        result["seed_video_id"] = video_id
        result["method"] = "title_similarity_search"
        return result

    def video_statistics(self, video_ids: str | list[str]) -> dict[str, Any]:
        if isinstance(video_ids, list):
            ids = ",".join(str(v) for v in video_ids if v)
        else:
            ids = str(video_ids)
        return self._request(
            "videos",
            {
                "part": "snippet,statistics,contentDetails",
                "id": ids,
            },
        )

    def channel_statistics(self, channel_ids: str | list[str]) -> dict[str, Any]:
        if isinstance(channel_ids, list):
            ids = ",".join(str(c) for c in channel_ids if c)
        else:
            ids = str(channel_ids)
        return self._request(
            "channels",
            {
                "part": "snippet,statistics,brandingSettings",
                "id": ids,
            },
        )

    def list_categories(self, *, region_code: str = "US") -> dict[str, Any]:
        return self._request(
            "videoCategories",
            {"part": "snippet", "regionCode": region_code},
        )

    # ------------------------------------------------------------------
    # Discovery helpers — normalize into Trend-friendly dicts
    # ------------------------------------------------------------------

    def discover_opportunities(
        self,
        subject: str,
        *,
        region_code: str = "US",
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Combine trending + topic search into discovery candidates."""
        out: list[dict[str, Any]] = []
        trending = self.search_trending(region_code=region_code, max_results=limit)
        if trending.get("ok"):
            for item in trending.get("items") or []:
                out.append(self._normalize_video_item(item, source="youtube_trending", subject=subject))

        topic = self.search_topics(subject, max_results=limit, region_code=region_code)
        if topic.get("ok"):
            # search results need statistics enrichment
            ids: list[str] = []
            for it in topic.get("items") or []:
                raw_id = it.get("id")
                if isinstance(raw_id, dict):
                    vid = raw_id.get("videoId") or ""
                else:
                    vid = str(raw_id or "")
                if vid:
                    ids.append(vid)
            stats = self.video_statistics(ids) if ids else {"ok": False, "items": []}
            by_id = {str(it.get("id")): it for it in (stats.get("items") or [])}
            for item in topic.get("items") or []:
                raw_id = item.get("id")
                if isinstance(raw_id, dict):
                    vid = raw_id.get("videoId") or ""
                else:
                    vid = str(raw_id or "")
                merged = by_id.get(vid) or {
                    "id": vid,
                    "snippet": item.get("snippet") or {},
                    "statistics": {},
                }
                out.append(self._normalize_video_item(merged, source="youtube_search_trends", subject=subject))

        return out[: max(limit * 2, limit)]

    def _normalize_video_item(self, item: dict[str, Any], *, source: str, subject: str) -> dict[str, Any]:
        from services.providers.youtube_search_intelligence import parse_iso8601_duration, pick_thumbnail

        snippet = item.get("snippet") or {}
        stats = item.get("statistics") or {}
        details = item.get("contentDetails") or {}
        video_id = item.get("id")
        if isinstance(video_id, dict):
            video_id = video_id.get("videoId") or video_id.get("channelId") or ""
        views = int(stats.get("viewCount") or 0)
        likes = int(stats.get("likeCount") or 0)
        comments = int(stats.get("commentCount") or 0)
        engagement = 0.0
        if views > 0:
            engagement = min(1.0, (likes + comments) / views)
        duration_sec = parse_iso8601_duration(str(details.get("duration") or ""))
        thumbs = snippet.get("thumbnails") if isinstance(snippet.get("thumbnails"), dict) else None
        thumbnail = pick_thumbnail(thumbs)
        if not thumbnail and video_id:
            thumbnail = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
        return {
            "video_id": video_id,
            "title": snippet.get("title") or subject,
            "channel_id": snippet.get("channelId") or "",
            "channel_title": snippet.get("channelTitle") or "",
            "description": (snippet.get("description") or "")[:280],
            "published_at": snippet.get("publishedAt") or "",
            "category_id": snippet.get("categoryId") or "",
            "tags": list(snippet.get("tags") or [])[:8],
            "views": views,
            "likes": likes,
            "comments": comments,
            "duration_sec": duration_sec,
            "thumbnail": thumbnail,
            "language": snippet.get("defaultAudioLanguage") or snippet.get("defaultLanguage") or "en",
            "engagement_rate": round(engagement, 5),
            "source": source,
            "url": f"https://www.youtube.com/watch?v={video_id}" if video_id else "",
        }


_PROVIDER: YouTubeProvider | None = None


def get_youtube_provider(*, refresh: bool = False) -> YouTubeProvider:
    global _PROVIDER
    if _PROVIDER is None or refresh:
        _PROVIDER = YouTubeProvider()
    return _PROVIDER


def validate_youtube_startup() -> dict[str, Any]:
    """Agent 0 / app boot hook — never raises."""
    try:
        provider = get_youtube_provider(refresh=True)
        report = provider.validate()
        lines = []
        lines.append(("✓" if report["detected"] else "✗") + " YouTube API detected")
        lines.append(("✓" if report["authenticated"] else "✗") + " Authentication successful")
        lines.append(("✓" if report["quota_accessible"] else "✗") + " API quota accessible")
        lines.append(("✓" if report["trending_search_ok"] else "✗") + " Trending search test passed")
        report["lines"] = lines
        for line in lines:
            log_event(logger, "youtube.startup_check", message=line, ok=report.get("ok"))
        if report.get("error"):
            log_event(logger, "youtube.startup_error", level=30, error=report["error"])
        return report
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "detected": False,
            "authenticated": False,
            "quota_accessible": False,
            "trending_search_ok": False,
            "error": _sanitize_error(str(exc)),
            "lines": [
                "✗ YouTube API detected",
                "✗ Authentication successful",
                "✗ API quota accessible",
                "✗ Trending search test passed",
            ],
        }
