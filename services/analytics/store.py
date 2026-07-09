"""AnalyticsStore — durable, append-only storage for analytics records.

The persistent memory of the learning loop: every published piece of
content adds one record per platform, and records are NEVER overwritten or
deleted — cumulative intelligence only grows. Storage is a plain JSON list
(`data/analytics/records.json`), same convention as the publishing queue.

Tests isolate by constructing with `directory=` (or by swapping the module
`_DEFAULT_DIR`, mirroring services/publishing/queue.py).
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone

from core.log import get_logger, log_event

logger = get_logger(__name__)

_DEFAULT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "analytics",
)

_RECORDS_FILE = "records.json"
_REPORTS_DIR = "reports"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AnalyticsStore:
    """Append-only JSON store for structured analytics records."""

    def __init__(self, directory: str = "") -> None:
        self.directory = directory or _DEFAULT_DIR

    # ------------------------------------------------------------ plumbing

    def _path(self) -> str:
        return os.path.join(self.directory, _RECORDS_FILE)

    def _read(self) -> list:
        path = self._path()
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Failed to read analytics records: %s", exc)
            return []

    def _write(self, records: list) -> None:
        os.makedirs(self.directory, exist_ok=True)
        with open(self._path(), "w", encoding="utf-8") as file:
            json.dump(records, file, indent=2)

    # ------------------------------------------------------------- records

    def add_record(self, record: dict) -> dict:
        """Append one analytics record (never mutates existing history)."""
        records = self._read()
        records.append(record)
        self._write(records)
        log_event(
            logger, "analytics.record_added",
            record_id=record.get("record_id", ""),
            platform=record.get("platform", ""),
            status=record.get("metrics_status", ""),
        )
        return record

    def add_records(self, records: list) -> list:
        if not records:
            return []
        existing = self._read()
        existing.extend(records)
        self._write(existing)
        log_event(logger, "analytics.records_added", count=len(records))
        return records

    def list_records(
        self,
        platform: str = "",
        since: str = "",
        metrics_status: str = "",
        limit: "int | None" = None,
    ) -> list:
        """Records newest-first, optionally filtered."""
        records = list(reversed(self._read()))
        if platform:
            records = [r for r in records if r.get("platform") == platform]
        if since:
            records = [r for r in records if r.get("collected_at", "") >= since]
        if metrics_status:
            records = [r for r in records if r.get("metrics_status") == metrics_status]
        return records[:limit] if limit else records

    def record_count(self) -> int:
        return len(self._read())

    def find_by_ref(self, analytics_ref: str) -> "dict | None":
        for record in self._read():
            if record.get("analytics_ref") == analytics_ref:
                return record
        return None

    # ------------------------------------------------------------- reports

    def save_report(self, report: dict) -> str:
        """Archive one performance report to data/analytics/reports/."""
        directory = os.path.join(self.directory, _REPORTS_DIR)
        os.makedirs(directory, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        name = f"{report.get('period', 'report')}-{stamp}-{uuid.uuid4().hex[:6]}.json"
        path = os.path.join(directory, name)
        with open(path, "w", encoding="utf-8") as file:
            json.dump(report, file, indent=2)
        log_event(logger, "analytics.report_saved", path=name, period=report.get("period", ""))
        return path


def get_analytics_store() -> AnalyticsStore:
    """A store bound to the current default directory (test-swappable)."""
    return AnalyticsStore()
