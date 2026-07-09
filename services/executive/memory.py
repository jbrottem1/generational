"""ExecutiveMemory — JSON store under data/executive/.

Separate from analytics and creative memory. Persists goals, decisions,
loop history, and strategy snapshots across runs.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from core.log import get_logger, log_event
from services.executive.models import new_id

logger = get_logger(__name__)

_DEFAULT_DIR = os.path.join("data", "executive")
_MEMORY_FILE = "memory.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ExecutiveMemory:
    """Append-friendly executive knowledge store."""

    def __init__(self, directory: str = "") -> None:
        self.directory = directory or _DEFAULT_DIR

    def _path(self) -> str:
        return os.path.join(self.directory, _MEMORY_FILE)

    def _read(self) -> dict:
        path = self._path()
        if not os.path.exists(path):
            return {"entries": [], "updated_at": _now_iso()}
        try:
            with open(path, "r", encoding="utf-8") as file:
                data = json.load(file)
                if isinstance(data, list):
                    return {"entries": data, "updated_at": _now_iso()}
                return data
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Failed to read executive memory: %s", exc)
            return {"entries": [], "updated_at": _now_iso()}

    def _write(self, data: dict) -> None:
        os.makedirs(self.directory, exist_ok=True)
        data["updated_at"] = _now_iso()
        with open(self._path(), "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)

    def remember(self, category: str, content: dict, source: str = "executive") -> dict:
        """Append one memory entry."""
        data = self._read()
        entry = {
            "entry_id": new_id("mem"),
            "category": category,
            "content": content,
            "source": source,
            "created_at": _now_iso(),
        }
        data.setdefault("entries", []).append(entry)
        self._write(data)
        log_event(logger, "executive.memory_added", category=category, entry_id=entry["entry_id"])
        return entry

    def recall(self, category: str = "", limit: "int | None" = None) -> list:
        entries = self._read().get("entries", [])
        if category:
            entries = [e for e in entries if e.get("category") == category]
        entries = list(reversed(entries))
        return entries[:limit] if limit else entries

    def count(self, category: str = "") -> int:
        entries = self._read().get("entries", [])
        if category:
            return len([e for e in entries if e.get("category") == category])
        return len(entries)

    def snapshot(self, key: str, payload: dict) -> None:
        """Persist a named snapshot (strategy, health, loop state)."""
        data = self._read()
        data.setdefault("snapshots", {})[key] = {
            "payload": payload,
            "saved_at": _now_iso(),
        }
        self._write(data)

    def load_snapshot(self, key: str) -> dict:
        return self._read().get("snapshots", {}).get(key, {}).get("payload", {})


def get_executive_memory() -> ExecutiveMemory:
    return ExecutiveMemory()
