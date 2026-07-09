"""Character memory system — the permanent record of what each character
has lived through.

Memories are appended into the character record's `memory` slot
(CHARACTER_MEMORY_FIELDS categories) with timestamps and optional content
references. When a category exceeds the configured `memory_size`, the
OLDEST entries are compacted into a single summary entry — long-term
growth is preserved, detail is bounded.
"""

from __future__ import annotations

from services.character_universe.config import get_character_universe_config
from services.character_universe.models import CHARACTER_MEMORY_FIELDS, _now_iso
from services.character_universe.registry import CharacterUniverseRegistry, get_character_universe_registry

MEMORY_CATEGORIES = CHARACTER_MEMORY_FIELDS


class CharacterMemorySystem:
    def __init__(self, registry: "CharacterUniverseRegistry | None" = None) -> None:
        self.registry = registry or get_character_universe_registry()

    def remember(self, character_id: str, category: str, summary: str, **details) -> "dict | None":
        """Append one memory entry; returns the entry (None = unknown character)."""
        if category not in MEMORY_CATEGORIES:
            raise ValueError(f"unknown memory category '{category}' — use one of {MEMORY_CATEGORIES}")
        character = self.registry.get("characters", character_id)
        if character is None:
            return None

        entry = {"at": _now_iso(), "summary": summary, **details}
        memory = character.setdefault("memory", {})
        entries = memory.setdefault(category, [])
        entries.append(entry)
        self._compact(entries)
        self.registry.store.save("characters", character, character_id)
        return entry

    def recall(self, character_id: str, category: str = "", limit: int = 0) -> "list | dict":
        """All memory (no category) or one category's entries, newest last."""
        character = self.registry.get("characters", character_id) or {}
        memory = character.get("memory", {})
        if not category:
            return memory
        entries = list(memory.get(category, []))
        return entries[-limit:] if limit else entries

    def record_evolution(self, character_id: str, trait_change: str, reason: str = "") -> "dict | None":
        """Personality evolution entries also update the live character —
        growth is visible, not just archived."""
        entry = self.remember(character_id, "personality_evolution", trait_change, reason=reason)
        if entry is not None:
            self.remember(character_id, "growth_log", f"evolved: {trait_change}")
        return entry

    def _compact(self, entries: list) -> None:
        limit = get_character_universe_config().memory_size
        if limit <= 0 or len(entries) <= limit:
            return
        overflow = entries[: len(entries) - limit + 1]
        summary = {
            "at": _now_iso(),
            "summary": f"[compacted] {len(overflow)} earlier memories: "
            + "; ".join(str(item.get("summary", "")) for item in overflow[-5:]),
            "compacted_count": len(overflow),
        }
        entries[: len(entries) - limit + 1] = [summary]
