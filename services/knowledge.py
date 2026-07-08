"""Knowledge Base — the memory of the content operating system.

Stores winning hooks, titles, scripts, thumbnail concepts, SEO keywords,
publishing history, and performance data. The ideation engine writes into
it on every generation (tagged with its source), and the future learning
engine will mine it to improve prompts and channel strategy.

Entries are stored as JSON lists, one file per category, under
data/knowledge/.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone

from core.log import get_logger, log_event

logger = get_logger(__name__)

_DEFAULT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "knowledge"
)


class CATEGORY:
    HOOKS = "hooks"
    TITLES = "titles"
    SCRIPTS = "scripts"
    THUMBNAILS = "thumbnail_concepts"
    SEO_KEYWORDS = "seo_keywords"
    PUBLISHING_HISTORY = "publishing_history"
    PERFORMANCE = "performance"
    RESEARCH = "research_briefs"

    ALL = [HOOKS, TITLES, SCRIPTS, THUMBNAILS, SEO_KEYWORDS, PUBLISHING_HISTORY, PERFORMANCE, RESEARCH]


class KnowledgeBase:
    def __init__(self, directory: str = _DEFAULT_DIR) -> None:
        self.directory = directory

    def _path_for(self, category: str) -> str:
        if category not in CATEGORY.ALL:
            raise ValueError(f"Unknown knowledge category '{category}'. Valid: {CATEGORY.ALL}")
        return os.path.join(self.directory, f"{category}.json")

    def _read(self, category: str) -> list:
        path = self._path_for(category)
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Failed to read knowledge category '%s': %s", category, exc)
            return []

    def _write(self, category: str, entries: list) -> None:
        os.makedirs(self.directory, exist_ok=True)
        with open(self._path_for(category), "w", encoding="utf-8") as file:
            json.dump(entries, file, indent=2)

    def add_entry(self, category: str, content, metadata: "dict | None" = None) -> dict:
        """Append one entry. `content` may be a string or a dict (e.g. performance rows)."""
        entry = {
            "id": uuid.uuid4().hex[:12],
            "content": content,
            "metadata": metadata or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        entries = self._read(category)
        entries.append(entry)
        self._write(category, entries)
        log_event(logger, "knowledge.entry_added", category=category, entry_id=entry["id"])
        return entry

    def list_entries(self, category: str, limit: "int | None" = None) -> list:
        """Entries in a category, newest first."""
        entries = list(reversed(self._read(category)))
        return entries[:limit] if limit else entries

    def search(self, category: str, query: str) -> list:
        """Case-insensitive substring search over entry content."""
        needle = query.lower()
        return [
            entry
            for entry in self.list_entries(category)
            if needle in json.dumps(entry["content"]).lower()
        ]

    def count(self, category: "str | None" = None) -> int:
        if category:
            return len(self._read(category))
        return sum(len(self._read(cat)) for cat in CATEGORY.ALL)

    def counts_by_category(self) -> dict:
        return {cat: len(self._read(cat)) for cat in CATEGORY.ALL}

    def clear(self, category: str) -> None:
        self._write(category, [])
        log_event(logger, "knowledge.category_cleared", category=category)


_kb = KnowledgeBase()


def get_knowledge_base() -> KnowledgeBase:
    """The app-wide knowledge base singleton."""
    return _kb
