"""Research cache — reuse prior results and refresh only stale sources."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone

from core.log import get_logger, log_event
from services.research.models import ResearchDocument, ResearchSummary

logger = get_logger(__name__)

_DEFAULT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "research_cache",
)


def topic_key(topic: str, niche: str = "") -> str:
    raw = f"{niche.strip().lower()}::{topic.strip().lower()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


class ResearchCache:
    def __init__(self, directory: str = _DEFAULT_DIR) -> None:
        self.directory = directory

    def _path_for(self, key: str) -> str:
        return os.path.join(self.directory, f"{key}.json")

    def get(self, key: str, ttl_hours: int) -> "dict | None":
        path = self._path_for(key)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as file:
                entry = json.load(file)
        except (json.JSONDecodeError, OSError) as exc:
            log_event(logger, "research.cache.read_failed", level=30, key=key, error=str(exc))
            return None
        if self.is_stale(entry, ttl_hours):
            log_event(logger, "research.cache.stale", key=key)
            return None
        log_event(logger, "research.cache.hit", key=key, docs=len(entry.get("documents", [])))
        return entry

    @staticmethod
    def is_stale(entry: dict, ttl_hours: int) -> bool:
        cached_at = entry.get("cached_at", "")
        if not cached_at:
            return True
        try:
            then = datetime.fromisoformat(cached_at)
            age_hours = (datetime.now(timezone.utc) - then).total_seconds() / 3600
            return age_hours > ttl_hours
        except ValueError:
            return True

    def set(self, key: str, documents: list[ResearchDocument], summary: ResearchSummary) -> None:
        os.makedirs(self.directory, exist_ok=True)
        entry = {
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "documents": [d.to_dict() for d in documents],
            "summary": summary.to_dict(),
        }
        with open(self._path_for(key), "w", encoding="utf-8") as file:
            json.dump(entry, file, indent=2)
        log_event(logger, "research.cache.stored", key=key, docs=len(documents))

    def load_documents(self, entry: dict) -> list[ResearchDocument]:
        return [ResearchDocument.from_dict(d) for d in entry.get("documents", [])]

    def load_summary(self, entry: dict) -> ResearchSummary:
        return ResearchSummary.from_dict(entry.get("summary", {}))

    def clear(self) -> None:
        if not os.path.isdir(self.directory):
            return
        for filename in os.listdir(self.directory):
            if filename.endswith(".json"):
                os.remove(os.path.join(self.directory, filename))


_cache = ResearchCache()


def get_research_cache(directory: str = "") -> ResearchCache:
    if directory:
        return ResearchCache(directory=directory)
    return _cache
