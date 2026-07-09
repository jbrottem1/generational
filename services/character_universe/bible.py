"""Story Bible — the single canonical snapshot of one universe (or the
whole catalog): characters, relationships, locations, organizations,
canon events, franchises, style packs, and open continuity issues.

The bible is generated on demand from the registry — it is a view, never
a second source of truth. Downstream engines receive it through the
shared context (`story_bibles`), never by importing this module.
"""

from __future__ import annotations

from services.character_universe.continuity import ContinuityEngine
from services.character_universe.registry import CharacterUniverseRegistry, get_character_universe_registry
from services.character_universe.world_models import build_story_bible


def build_bible(universe_id: str = "",
                registry: "CharacterUniverseRegistry | None" = None) -> dict:
    registry = registry or get_character_universe_registry()
    continuity = ContinuityEngine(registry)

    if universe_id:
        universe = registry.get("universes", universe_id) or {}
        characters = registry.characters_in_universe(universe_id)
        locations = registry.list("locations", universe_id=universe_id)
        organizations = registry.list("organizations", universe_id=universe_id)
        canon_events = registry.canon_events_for(universe_id)
        franchises = registry.list("franchises", universe_id=universe_id)
        style_packs = registry.list("style_packs", universe_id=universe_id)
    else:
        universe = {}
        characters = registry.list("characters")
        locations = registry.list("locations")
        organizations = registry.list("organizations")
        canon_events = registry.list("canon_events")
        franchises = registry.list("franchises")
        style_packs = registry.list("style_packs")

    character_ids = {character["character_id"] for character in characters}
    relationships = [
        relationship
        for relationship in registry.list("relationships")
        if relationship.get("source_id") in character_ids
        or relationship.get("target_id") in character_ids
    ]

    return build_story_bible(
        {
            "universe_id": universe_id,
            "universe": universe,
            "characters": characters,
            "relationships": relationships,
            "locations": locations,
            "organizations": organizations,
            "canon_events": canon_events,
            "franchises": franchises,
            "style_packs": style_packs,
            "continuity_issues": continuity.validate_all(universe_id),
        }
    )
