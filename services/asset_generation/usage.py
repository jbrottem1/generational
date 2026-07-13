"""Usage tracking — append-only record of every generation attempt.

Persists to `data/asset_generation/usage.json` (same convention as the
asset registry). Every successful, failed, blocked, or cache-hit job can
emit one USAGE_EVENT_FIELDS dict so cost, latency, and provider mix are
auditable without scraping the job history.

Tests isolate by constructing `UsageTracker(directory=...)` or by swapping
the module `_DEFAULT_DIR`.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone

from core.log import get_logger

logger = get_logger(__name__)

_DEFAULT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "asset_generation",
)

_USAGE_FILE = "usage.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class UsageTracker:
    """Append-only JSON store for generation usage events."""

    def __init__(self, directory: str = "") -> None:
        self.directory = directory or _DEFAULT_DIR

    def _path(self) -> str:
        return os.path.join(self.directory, _USAGE_FILE)

    def _read(self) -> list:
        path = self._path()
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as file:
                data = json.load(file)
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Failed to read usage store: %s", exc)
            return []

    def _write(self, events: list) -> None:
        os.makedirs(self.directory, exist_ok=True)
        with open(self._path(), "w", encoding="utf-8") as file:
            json.dump(events, file, indent=2)

    def record(self, job: dict, project_id: str = "") -> dict:
        """Append one USAGE_EVENT_FIELDS dict derived from a generation job."""
        event = {
            "event_id": f"usage_{uuid.uuid4().hex[:10]}",
            "job_id": str(job.get("job_id", "")),
            "asset_id": str(job.get("asset_id", "")),
            "asset_type": str(job.get("asset_type", "")),
            "asset_class": str(job.get("asset_class", "")),
            "provider": str(job.get("provider", "")),
            "status": str(job.get("status", "")),
            "cache_hit": bool(job.get("cache_hit", False)),
            "cost_estimate": float(job.get("cost_estimate", 0.0) or 0.0),
            "latency_ms": int(job.get("latency_ms", 0) or 0),
            "project_id": str(project_id or ""),
            "created_at": str(job.get("created_at", "")) or _now_iso(),
        }
        events = self._read()
        events.append(event)
        self._write(events)
        return event

    def events(self, limit: "int | None" = None, provider: str = "", project_id: str = "") -> list:
        """Newest-first usage events, optionally filtered."""
        rows = list(reversed(self._read()))
        if provider:
            rows = [row for row in rows if row.get("provider") == provider]
        if project_id:
            rows = [row for row in rows if row.get("project_id") == project_id]
        return rows[:limit] if limit else rows

    def summary(self, project_id: str = "") -> dict:
        """Aggregate usage: totals by provider, cost, cache hits, latency."""
        rows = self.events(project_id=project_id)
        by_provider: "dict[str, int]" = {}
        by_status: "dict[str, int]" = {}
        total_cost = 0.0
        total_latency = 0
        cache_hits = 0
        for row in rows:
            provider = str(row.get("provider", "")) or "(none)"
            by_provider[provider] = by_provider.get(provider, 0) + 1
            status = str(row.get("status", "")) or "(none)"
            by_status[status] = by_status.get(status, 0) + 1
            total_cost += float(row.get("cost_estimate", 0.0) or 0.0)
            total_latency += int(row.get("latency_ms", 0) or 0)
            if row.get("cache_hit"):
                cache_hits += 1
        return {
            "events": len(rows),
            "cache_hits": cache_hits,
            "estimated_cost": round(total_cost, 4),
            "average_latency_ms": int(round(total_latency / len(rows))) if rows else 0,
            "by_provider": dict(sorted(by_provider.items())),
            "by_status": dict(sorted(by_status.items())),
        }


_tracker: "UsageTracker | None" = None


def get_usage_tracker() -> UsageTracker:
    global _tracker
    if _tracker is None:
        _tracker = UsageTracker()
    return _tracker


def reset_usage_tracker() -> None:
    """Drop the cached tracker (tests)."""
    global _tracker
    _tracker = None


def summarize_jobs(jobs: "list[dict]") -> dict:
    """In-memory usage summary from a list of generation jobs (no I/O)."""
    by_provider: "dict[str, int]" = {}
    total_cost = 0.0
    total_latency = 0
    cache_hits = 0
    for job in jobs:
        provider = str(job.get("provider", "")) or "(none)"
        by_provider[provider] = by_provider.get(provider, 0) + 1
        total_cost += float(job.get("cost_estimate", 0.0) or 0.0)
        total_latency += int(job.get("latency_ms", 0) or 0)
        if job.get("cache_hit"):
            cache_hits += 1
    return {
        "events": len(jobs),
        "cache_hits": cache_hits,
        "estimated_cost": round(total_cost, 4),
        "average_latency_ms": int(round(total_latency / len(jobs))) if jobs else 0,
        "by_provider": dict(sorted(by_provider.items())),
    }
