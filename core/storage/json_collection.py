"""Generic JSON collection store — named records, one file per record.

Reused by any service that needs simple local persistence of named records
(channels today, more later). Like the project store, this is deliberately
swappable: services take the directory as a constructor argument, so a
database-backed equivalent can replace it without touching service logic.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone

from core.log import get_logger

logger = get_logger(__name__)


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "record"


class JsonCollectionStore:
    def __init__(self, directory: str) -> None:
        self.directory = directory

    def _ensure_dir(self) -> None:
        os.makedirs(self.directory, exist_ok=True)

    def _path_for(self, name: str) -> str:
        return os.path.join(self.directory, f"{slugify(name)}.json")

    def save(self, record: dict) -> str:
        """Create or update a record keyed by record['name']."""
        self._ensure_dir()
        now = datetime.now(timezone.utc).isoformat()
        record["updated_at"] = now
        record.setdefault("created_at", now)
        path = self._path_for(record["name"])
        with open(path, "w", encoding="utf-8") as file:
            json.dump(record, file, indent=2)
        return path

    def load(self, name: str) -> "dict | None":
        path = self._path_for(name)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Failed to load record '%s' from %s: %s", name, self.directory, exc)
            return None

    def list_all(self) -> list:
        self._ensure_dir()
        records = []
        for filename in sorted(os.listdir(self.directory)):
            if not filename.endswith(".json"):
                continue
            try:
                with open(os.path.join(self.directory, filename), "r", encoding="utf-8") as file:
                    records.append(json.load(file))
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Skipping unreadable record file %s: %s", filename, exc)
        records.sort(key=lambda record: record.get("updated_at", ""), reverse=True)
        return records

    def delete(self, name: str) -> bool:
        path = self._path_for(name)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    def count(self) -> int:
        self._ensure_dir()
        return len([f for f in os.listdir(self.directory) if f.endswith(".json")])
