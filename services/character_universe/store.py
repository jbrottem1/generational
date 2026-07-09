"""Persistence for the Character & Universe Engine.

One `JsonCollectionStore` per entity kind under `data/character_universe/`
— the same deliberately swappable local-JSON layer channels use. Records
are keyed by their entity id (stored in the record's `name` slot expected
by the collection store) so renames never orphan files.

Tests point `_DEFAULT_DIR` at a tmp dir (see tests/conftest.py).
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from core.storage.json_collection import JsonCollectionStore

_DEFAULT_DIR = os.path.join("data", "character_universe")

COLLECTIONS = (
    "characters", "universes", "relationships", "locations",
    "organizations", "canon_events", "appearances", "franchises",
    "brand_identities", "style_packs",
)


class CharacterUniverseStore:
    """Facade over one JSON collection per entity kind."""

    def __init__(self, base_dir: "str | None" = None) -> None:
        self.base_dir = base_dir or _DEFAULT_DIR
        self._stores = {
            kind: JsonCollectionStore(os.path.join(self.base_dir, kind))
            for kind in COLLECTIONS
        }

    def save(self, kind: str, record: dict, record_id: str) -> dict:
        """Persist by entity id without clobbering the record's display `name`."""
        record = dict(record)
        store = self._stores[kind]
        store._ensure_dir()
        now = datetime.now(timezone.utc).isoformat()
        record["updated_at"] = now
        record.setdefault("created_at", now)
        path = store._path_for(record_id)
        with open(path, "w", encoding="utf-8") as file:
            json.dump(record, file, indent=2)
        return record

    def load(self, kind: str, record_id: str) -> "dict | None":
        return self._stores[kind].load(record_id)

    def list_all(self, kind: str) -> list:
        return self._stores[kind].list_all()

    def delete(self, kind: str, record_id: str) -> bool:
        return self._stores[kind].delete(record_id)

    def count(self, kind: str) -> int:
        return self._stores[kind].count()


_store: "CharacterUniverseStore | None" = None


def get_store() -> CharacterUniverseStore:
    global _store
    if _store is None or _store.base_dir != _DEFAULT_DIR:
        _store = CharacterUniverseStore()
    return _store


def reset_store() -> None:
    """Drop the cached store so the next access re-reads `_DEFAULT_DIR`."""
    global _store
    _store = None
