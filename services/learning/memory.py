"""HistoricalMemory — the long-term, append-only strategy knowledge base.

Remembers what worked, what failed, platform trends, evergreen and
seasonal content, and audience preferences across every run. Historical
knowledge is NEVER overwritten: every observation appends a new entry, so
intelligence accumulates over time and old lessons stay auditable.

Storage: `data/analytics/memory.json` (one JSON list). Tests isolate by
constructing with `directory=` or swapping the store module default dir.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone

from core.log import get_logger, log_event
from services.analytics import store as _store_module

logger = get_logger(__name__)

_MEMORY_FILE = "memory.json"


class MEMORY_CATEGORY:
    SUCCESSFUL_STRATEGIES = "successful_strategies"
    FAILED_STRATEGIES = "failed_strategies"
    PLATFORM_TRENDS = "platform_trends"
    EVERGREEN_CONTENT = "evergreen_content"
    SEASONAL_CONTENT = "seasonal_content"
    AUDIENCE_PREFERENCES = "audience_preferences"
    EXPERIMENT_OUTCOMES = "experiment_outcomes"

    ALL = (
        SUCCESSFUL_STRATEGIES,
        FAILED_STRATEGIES,
        PLATFORM_TRENDS,
        EVERGREEN_CONTENT,
        SEASONAL_CONTENT,
        AUDIENCE_PREFERENCES,
        EXPERIMENT_OUTCOMES,
    )


MEMORY_ENTRY_FIELDS = (
    "entry_id",
    "category",           # MEMORY_CATEGORY value
    "content",            # the remembered fact/strategy (str or dict)
    "confidence",         # 0-100 at time of writing
    "evidence",           # supporting data (samples, scores, refs)
    "source",             # what produced the memory (learning|experiment|manual)
    "created_at",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class HistoricalMemory:
    """Append-only cumulative strategy memory."""

    def __init__(self, directory: str = "") -> None:
        # Shares the analytics data directory so one conftest swap
        # isolates the whole Agent 9 persistence layer.
        self.directory = directory or _store_module._DEFAULT_DIR

    def _path(self) -> str:
        return os.path.join(self.directory, _MEMORY_FILE)

    def _read(self) -> list:
        path = self._path()
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Failed to read learning memory: %s", exc)
            return []

    def _write(self, entries: list) -> None:
        os.makedirs(self.directory, exist_ok=True)
        with open(self._path(), "w", encoding="utf-8") as file:
            json.dump(entries, file, indent=2)

    # ------------------------------------------------------------- writes

    def remember(
        self,
        category: str,
        content,
        confidence: int = 50,
        evidence: "dict | None" = None,
        source: str = "learning",
    ) -> dict:
        """Append one memory entry — history is never overwritten."""
        if category not in MEMORY_CATEGORY.ALL:
            raise ValueError(
                f"Unknown memory category '{category}'. Valid: {list(MEMORY_CATEGORY.ALL)}"
            )
        entry = {
            "entry_id": f"mem_{uuid.uuid4().hex[:12]}",
            "category": category,
            "content": content,
            "confidence": int(confidence),
            "evidence": evidence or {},
            "source": source,
            "created_at": _now_iso(),
        }
        entries = self._read()
        entries.append(entry)
        self._write(entries)
        log_event(logger, "learning.memory_added", category=category, entry_id=entry["entry_id"])
        return entry

    # -------------------------------------------------------------- reads

    def recall(self, category: str, limit: "int | None" = None) -> list:
        """Entries in a category, newest first."""
        entries = [e for e in reversed(self._read()) if e.get("category") == category]
        return entries[:limit] if limit else entries

    def search(self, query: str, category: str = "") -> list:
        needle = query.lower()
        return [
            entry
            for entry in reversed(self._read())
            if (not category or entry.get("category") == category)
            and needle in json.dumps(entry.get("content", "")).lower()
        ]

    def count(self, category: str = "") -> int:
        if category:
            return len([e for e in self._read() if e.get("category") == category])
        return len(self._read())

    def counts_by_category(self) -> dict:
        counts = {category: 0 for category in MEMORY_CATEGORY.ALL}
        for entry in self._read():
            category = entry.get("category", "")
            if category in counts:
                counts[category] += 1
        return counts


def get_memory() -> HistoricalMemory:
    """A memory bound to the current default directory (test-swappable)."""
    return HistoricalMemory()
