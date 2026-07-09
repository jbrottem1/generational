"""Publishing Scheduler — timezone-aware publish-time decisions per platform.

Supports immediate publish, explicit scheduled publish, and optimal-window
scheduling from the Optimization Engine's ranked `publish_windows`
(services/seo/windows.py contract). Windows carry local hours per country;
this module resolves them to concrete UTC timestamps using the country's
audience timezone (LOCALIZATION_TARGETS offsets), so multiple brands,
channels, and countries schedule independently.

Extension point: `region_offset_hours()` is the single place a real
timezone database (zoneinfo, per-channel audience analytics) plugs in.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from services.publishing.models import PUBLISH_SCHEDULE_ENTRY_FIELDS  # noqa: F401 - contract re-export
from services.publishing.targets import LOCALIZATION_TARGETS

_WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")

PUBLISH_MODES = ("immediate", "scheduled")


def region_offset_hours(country: str) -> int:
    """UTC offset of a country's main audience timezone (0 if unknown)."""
    target = next((t for t in LOCALIZATION_TARGETS if t[0] == country), None)
    return target[2] if target else 0


def format_utc_offset(offset_hours: int) -> str:
    sign = "+" if offset_hours >= 0 else "-"
    return f"UTC{sign}{abs(offset_hours):02d}:00"


def next_window_occurrence(window: dict, now: "datetime | None" = None) -> datetime:
    """The next UTC datetime that falls inside a ranked publish window.

    Windows describe local hours in the target country; the result is the
    window's start hour on its next occurrence, converted to UTC.
    """
    now = now or datetime.now(timezone.utc)
    offset = region_offset_hours(window.get("country", ""))
    local_tz = timezone(timedelta(hours=offset))
    local_now = now.astimezone(local_tz)

    day = str(window.get("day", "")).lower()
    target_weekday = _WEEKDAYS.index(day) if day in _WEEKDAYS else local_now.weekday()
    start_hour = int(window.get("start_hour_local", 17))

    days_ahead = (target_weekday - local_now.weekday()) % 7
    candidate = (local_now + timedelta(days=days_ahead)).replace(
        hour=start_hour, minute=0, second=0, microsecond=0
    )
    if candidate <= local_now:
        candidate += timedelta(days=7)
    return candidate.astimezone(timezone.utc)


class PublishingScheduler:
    """Decides when each (item × platform) publish should happen."""

    def __init__(self, now: "datetime | None" = None) -> None:
        self._now = now  # injectable clock for deterministic tests

    def _clock(self) -> datetime:
        return self._now or datetime.now(timezone.utc)

    def schedule(
        self,
        package: dict,
        platform: str,
        mode: str = "scheduled",
        publish_time: "str | None" = None,
    ) -> dict:
        """One schedule entry (see PUBLISH_SCHEDULE_ENTRY_FIELDS).

        - `mode="immediate"` → publish now.
        - explicit `publish_time` (ISO-8601) → publish at that instant.
        - otherwise → the best ranked optimization window for the platform,
          falling back to the country's default peak hour, then to now.
        """
        now = self._clock()
        country = package.get("country", "US")
        language = package.get("language", "en")
        offset = region_offset_hours(country)
        window: dict = {}

        if mode == "immediate":
            slot = now
        elif publish_time:
            slot = datetime.fromisoformat(publish_time)
            if slot.tzinfo is None:
                slot = slot.replace(tzinfo=timezone.utc)
        else:
            window = self._best_window(package, platform)
            if window:
                slot = next_window_occurrence(window, now=now)
            else:
                slot = self._default_peak_slot(country, now)

        local_tz = timezone(timedelta(hours=offset))
        return {
            "project_id": package.get("project_id", ""),
            "platform": platform,
            "country": country,
            "language": language,
            "mode": "immediate" if mode == "immediate" else "scheduled",
            "publish_time": slot.astimezone(timezone.utc).isoformat(),
            "timezone": format_utc_offset(offset),
            "local_time": slot.astimezone(local_tz).isoformat(),
            "window": dict(window),
        }

    def _best_window(self, package: dict, platform: str) -> dict:
        """Highest-ranked optimization window matching the platform."""
        from providers.publishing import resolve_platform_key

        windows = package.get("publish_windows") or []
        canonical = resolve_platform_key(platform)
        for window in sorted(windows, key=lambda w: w.get("rank", 999)):
            if resolve_platform_key(window.get("platform", "")) == canonical:
                return window
        return {}

    def _default_peak_slot(self, country: str, now: datetime) -> datetime:
        """Fallback: the country's next default peak local posting hour."""
        offset = region_offset_hours(country)
        target = next((t for t in LOCALIZATION_TARGETS if t[0] == country), None)
        peak_start = target[3][0] if target else 17
        local_tz = timezone(timedelta(hours=offset))
        local_now = now.astimezone(local_tz)
        candidate = local_now.replace(hour=peak_start, minute=0, second=0, microsecond=0)
        if candidate <= local_now:
            candidate += timedelta(days=1)
        return candidate.astimezone(timezone.utc)
