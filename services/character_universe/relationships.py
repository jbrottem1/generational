"""Relationship engine — the social graph between characters (and between
characters and organizations).

Relationships are first-class persisted records; each strength change is
appended to the relationship's own history so evolution is auditable.
Character records carry only `relationship_ids` — the graph itself lives
here.
"""

from __future__ import annotations

from services.character_universe.models import RelationType, _now_iso, build_relationship
from services.character_universe.registry import CharacterUniverseRegistry, get_character_universe_registry


class RelationshipEngine:
    def __init__(self, registry: "CharacterUniverseRegistry | None" = None) -> None:
        self.registry = registry or get_character_universe_registry()

    def link(self, source_id: str, target_id: str, relation_type: str = RelationType.FRIEND, **extra) -> dict:
        """Create a relationship and index it on both characters."""
        relationship = build_relationship(
            {"source_id": source_id, "target_id": target_id, "relation_type": relation_type, **extra}
        )
        relationship["history"].append(
            {"at": _now_iso(), "change": "created", "strength": relationship["strength"]}
        )
        self.registry.store.save("relationships", relationship, relationship["relationship_id"])
        for character_id in (source_id, target_id):
            character = self.registry.get("characters", character_id)
            if character is not None:
                ids = character.setdefault("relationship_ids", [])
                if relationship["relationship_id"] not in ids:
                    ids.append(relationship["relationship_id"])
                    self.registry.store.save("characters", character, character_id)
        return relationship

    def get(self, relationship_id: str) -> "dict | None":
        return self.registry.get("relationships", relationship_id)

    def for_character(self, character_id: str, relation_type: str = "") -> list:
        relationships = [
            relationship
            for relationship in self.registry.list("relationships")
            if character_id in (relationship.get("source_id"), relationship.get("target_id"))
        ]
        if relation_type:
            relationships = [r for r in relationships if r.get("relation_type") == relation_type]
        return relationships

    def between(self, character_a: str, character_b: str) -> list:
        pair = {character_a, character_b}
        return [
            relationship
            for relationship in self.registry.list("relationships")
            if {relationship.get("source_id"), relationship.get("target_id")} == pair
        ]

    def adjust_strength(self, relationship_id: str, delta: int, reason: str = "") -> "dict | None":
        relationship = self.registry.get("relationships", relationship_id)
        if relationship is None:
            return None
        relationship["strength"] = max(0, min(100, int(relationship.get("strength", 50)) + delta))
        relationship.setdefault("history", []).append(
            {"at": _now_iso(), "change": reason or "strength_adjusted",
             "delta": delta, "strength": relationship["strength"]}
        )
        self.registry.store.save("relationships", relationship, relationship_id)
        return relationship

    def end(self, relationship_id: str, reason: str = "") -> "dict | None":
        """Historical relationships are never deleted — they end."""
        relationship = self.registry.get("relationships", relationship_id)
        if relationship is None:
            return None
        relationship["status"] = "ended"
        relationship["ended_at"] = _now_iso()
        relationship.setdefault("history", []).append(
            {"at": relationship["ended_at"], "change": reason or "ended"}
        )
        self.registry.store.save("relationships", relationship, relationship_id)
        return relationship

    def relationship_context(self, character_id: str) -> list:
        """Named, human-readable relationship summaries for script/creative
        integration payloads."""
        context = []
        for relationship in self.for_character(character_id):
            if relationship.get("status") == "ended":
                continue
            other_id = (
                relationship["target_id"]
                if relationship.get("source_id") == character_id
                else relationship["source_id"]
            )
            other = self.registry.get("characters", other_id) or {}
            context.append(
                {
                    "relationship_id": relationship["relationship_id"],
                    "with_character_id": other_id,
                    "with_name": other.get("name", other_id),
                    "relation_type": relationship.get("relation_type", ""),
                    "label": relationship.get("label", ""),
                    "strength": relationship.get("strength", 50),
                }
            )
        return context
