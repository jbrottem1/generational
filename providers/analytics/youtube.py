"""YouTube Analytics provider — live when credentials exist, else mock.

Uses ProviderRuntime credentials + the shared HTTP client. Never imports a
vendor SDK. When credentials are missing or the API errors, callers should
fall back to MockAnalyticsProvider via the registry.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from providers.analytics_provider import AnalyticsProvider


class YouTubeAnalyticsProvider(AnalyticsProvider):
    name = "youtube_analytics"
    credential_env = "YOUTUBE_ACCESS_TOKEN"
    api_key_env = "YOUTUBE_API_KEY"

    def is_available(self) -> bool:
        try:
            from services.provider_runtime.config import has_credential

            return has_credential(self.credential_env) or has_credential(self.api_key_env)
        except Exception:  # noqa: BLE001
            return False

    def fetch_metrics(self, content_id: str, platform: str) -> dict:
        if not self.is_available():
            return self._error(content_id, platform, "No YouTube credentials configured")

        try:
            from services.provider_runtime.config import get_credential
            from services.provider_runtime.http_client import request_json
        except Exception as exc:  # noqa: BLE001
            return self._error(content_id, platform, str(exc))

        token = get_credential(self.credential_env) or ""
        api_key = get_credential(self.api_key_env) or ""
        end = datetime.now(timezone.utc).date()
        start = end - timedelta(days=28)
        params = {
            "ids": "channel==MINE",
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
            "metrics": (
                "views,estimatedMinutesWatched,averageViewDuration,"
                "likes,comments,shares,subscribersGained"
            ),
            "dimensions": "video",
        }
        if content_id:
            params["filters"] = f"video=={content_id}"

        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        elif api_key:
            params["key"] = api_key

        url = "https://youtubeanalytics.googleapis.com/v2/reports?" + urlencode(params)
        try:
            resp = request_json("GET", url, headers=headers, timeout_sec=20, retries=1)
        except Exception as exc:  # noqa: BLE001
            return self._error(content_id, platform, str(exc))

        if not resp.ok:
            body = resp.body
            snippet = body if isinstance(body, str) else str(body)[:200]
            return self._error(content_id, platform, f"YouTube Analytics HTTP {resp.status}: {snippet}")

        data = resp.body if isinstance(resp.body, dict) else {}
        return self._parse_report(data, content_id, platform)

    def _parse_report(self, data: dict, content_id: str, platform: str) -> dict:
        headers = [h.get("name", "") for h in (data.get("columnHeaders") or [])]
        rows = data.get("rows") or []
        values = rows[0] if rows else [0] * len(headers)
        mapped = {name: values[i] if i < len(values) else 0 for i, name in enumerate(headers)}

        views = int(mapped.get("views") or 0)
        avg_duration = float(mapped.get("averageViewDuration") or 0)
        watch_min = float(mapped.get("estimatedMinutesWatched") or 0)
        return {
            "views": views,
            "watch_time_sec": int(watch_min * 60) if watch_min else int(views * avg_duration),
            "average_view_duration_sec": avg_duration,
            "audience_retention": 0,
            "ctr": 0,
            "likes": int(mapped.get("likes") or 0),
            "comments": int(mapped.get("comments") or 0),
            "shares": int(mapped.get("shares") or 0),
            "saves": 0,
            "subscriber_growth": int(mapped.get("subscribersGained") or 0),
            "followers_gained": int(mapped.get("subscribersGained") or 0),
            "rpm": 0,
            "cpm": 0,
            "mock": False,
            "provider": self.name,
            "platform": platform,
            "content_id": content_id,
        }

    def _error(self, content_id: str, platform: str, error: str) -> dict:
        return {
            "views": 0,
            "watch_time_sec": 0,
            "average_view_duration_sec": 0,
            "audience_retention": 0,
            "ctr": 0,
            "likes": 0,
            "comments": 0,
            "shares": 0,
            "saves": 0,
            "subscriber_growth": 0,
            "followers_gained": 0,
            "rpm": 0,
            "cpm": 0,
            "mock": False,
            "error": error,
            "provider": self.name,
            "platform": platform,
            "content_id": content_id,
        }
