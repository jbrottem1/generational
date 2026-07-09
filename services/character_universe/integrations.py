"""Integration payload builders — how the Character & Universe Engine
serves every other department WITHOUT calling any engine (Directive #1).

Each builder returns a JSON-safe dict the engine publishes on a shared
context key. Downstream engines read the key; the orchestrator routes it:

- script_context_for()      → Script Generation (speaking style, dialogue
                              rules, personality, motivation, relationships,
                              story context, canon history)
- creative_context_for()    → Creative Studio (storyboard context, scene
                              participants, world rules, visual references,
                              creative constraints)
- asset_requests_for()      → Universal Asset Generation / Agent 14
                              (definitions, reference prompts, style packs,
                              environments, consistency rules — requests
                              only, never generation)
- optimization_payload()    → Optimization Laboratory (popularity,
                              retention impact, audience preferences,
                              performance history, franchise performance)
"""

from __future__ import annotations

from services.character_universe.bible import build_bible
from services.character_universe.continuity import ContinuityEngine
from services.character_universe.registry import CharacterUniverseRegistry, get_character_universe_registry
from services.character_universe.relationships import RelationshipEngine


def character_prompt_fragment(character: dict) -> str:
    """The exact text every generation prompt embeds for this character —
    the mechanism of cross-provider visual consistency."""
    visual = character.get("visual_profile", {})
    parts = [character.get("name", ""), visual.get("visual_signature", "")]
    wardrobe = visual.get("wardrobe") or []
    if wardrobe:
        parts.append("wearing " + ", ".join(wardrobe[:3]))
    palette = visual.get("color_palette") or []
    if palette:
        parts.append("signature colors " + ", ".join(palette[:3]))
    if visual.get("art_style"):
        parts.append(f"in {visual['art_style']} style")
    return ", ".join(part for part in parts if part)


def script_context_for(character_id: str,
                       registry: "CharacterUniverseRegistry | None" = None) -> dict:
    """Everything the Script Generation Engine needs to write this
    character in-voice and in-canon."""
    registry = registry or get_character_universe_registry()
    character = registry.get("characters", character_id)
    if character is None:
        return {}
    relationships = RelationshipEngine(registry).relationship_context(character_id)
    memory = character.get("memory", {})
    return {
        "character_id": character_id,
        "name": character.get("name", ""),
        "speaking_style": character.get("speech_style", ""),
        "voice_style": character.get("voice_style", ""),
        "vocabulary": character.get("vocabulary", []),
        "humor_style": character.get("humor_style", ""),
        "catchphrases": character.get("catchphrases", []),
        "dialogue_rules": [
            rule for rule in (
                f"stay in {character.get('speech_style')}" if character.get("speech_style") else "",
                f"humor: {character.get('humor_style')}" if character.get("humor_style") else "",
                "never contradict canon history",
            ) if rule
        ],
        "personality": character.get("personality_traits", []),
        "motivation": character.get("motivations", []),
        "goals": character.get("goals", []),
        "emotional_state": character.get("emotional_state", ""),
        "relationship_context": relationships,
        "story_context": character.get("current_arc", {}),
        "canon_history": memory.get("events", [])[-10:],
        "backstory": character.get("backstory", ""),
    }


def creative_context_for(character_ids: list, universe_id: str = "",
                         registry: "CharacterUniverseRegistry | None" = None) -> dict:
    """Storyboard-facing context for the Creative Studio: who is in the
    scene, what they look like, and what the world allows."""
    registry = registry or get_character_universe_registry()
    participants = []
    for character_id in character_ids:
        character = registry.get("characters", character_id)
        if character is None:
            continue
        participants.append(
            {
                "character_id": character_id,
                "name": character.get("name", ""),
                "role": character.get("role", ""),
                "prompt_fragment": character_prompt_fragment(character),
                "visual_references": character.get("visual_profile", {}).get("reference_prompts", []),
                "placement_notes": character.get("visual_profile", {}).get("expressions", []),
            }
        )
    universe = registry.get("universes", universe_id) or {} if universe_id else {}
    return {
        "universe_id": universe_id,
        "scene_participants": participants,
        "world_rules": universe.get("rules", []),
        "creative_constraints": [
            rule for participant in participants for rule in
            (registry.get("characters", participant["character_id"]) or {})
            .get("visual_profile", {}).get("consistency_rules", [])
        ],
        "locations": registry.list("locations", universe_id=universe_id) if universe_id else [],
    }


def asset_requests_for(character_ids: list, universe_id: str = "",
                       registry: "CharacterUniverseRegistry | None" = None) -> list:
    """Structured asset REQUESTS for the Universal Asset Generation Engine
    (Agent 14). This engine never generates media — it hands Agent 14
    definitions, reference prompts, style packs, and consistency rules."""
    registry = registry or get_character_universe_registry()
    requests = []
    for character_id in character_ids:
        character = registry.get("characters", character_id)
        if character is None:
            continue
        visual = character.get("visual_profile", {})
        requests.append(
            {
                "request_type": "character_reference",
                "entity_type": "character",
                "entity_id": character_id,
                "character_definition": {
                    "name": character.get("name", ""),
                    "species": character.get("species", ""),
                    "role": character.get("role", ""),
                    "visual_profile": visual,
                },
                "reference_prompt": character_prompt_fragment(character),
                "reference_prompts": visual.get("reference_prompts", []),
                "style_pack_ids": [
                    pack["style_pack_id"]
                    for pack in registry.list("style_packs", universe_id=universe_id)
                ] if universe_id else [],
                "consistency_rules": visual.get("consistency_rules", []),
            }
        )
    if universe_id:
        for location in registry.list("locations", universe_id=universe_id):
            requests.append(
                {
                    "request_type": "environment_reference",
                    "entity_type": "location",
                    "entity_id": location["location_id"],
                    "environment_definition": {
                        "name": location.get("name", ""),
                        "location_type": location.get("location_type", ""),
                        "description": location.get("description", ""),
                        "lighting_profile": location.get("lighting_profile", ""),
                        "weather": location.get("weather", ""),
                        "architecture": location.get("architecture", ""),
                    },
                    "reference_prompts": location.get("reference_prompts", []),
                    "consistency_rules": location.get("environment_rules", []),
                }
            )
    return requests


def optimization_payload(registry: "CharacterUniverseRegistry | None" = None) -> dict:
    """Character/franchise performance signals for the Optimization
    Laboratory. Metrics originate from Analytics — this engine only
    aggregates what has been recorded back onto its entities."""
    registry = registry or get_character_universe_registry()
    characters = registry.list("characters")
    franchises = registry.list("franchises")
    return {
        "character_popularity": [
            {
                "character_id": character["character_id"],
                "name": character.get("name", ""),
                "popularity_score": character.get("popularity_score", 0),
                "brand_importance": character.get("brand_importance", 0),
                "status": character.get("status", ""),
            }
            for character in characters
        ],
        "franchise_performance": [
            {
                "franchise_id": franchise["franchise_id"],
                "name": franchise.get("name", ""),
                "franchise_type": franchise.get("franchise_type", ""),
                "performance": franchise.get("performance", {}),
            }
            for franchise in franchises
        ],
        "audience_preferences": {
            "most_popular": max(
                characters, key=lambda c: c.get("popularity_score", 0)
            )["character_id"] if characters else "",
        },
    }


def continuity_report(universe_id: str = "",
                      registry: "CharacterUniverseRegistry | None" = None) -> dict:
    registry = registry or get_character_universe_registry()
    issues = ContinuityEngine(registry).validate_all(universe_id)
    return {
        "universe_id": universe_id,
        "issues": issues,
        "errors": sum(1 for issue in issues if issue["severity"] == "error"),
        "warnings": sum(1 for issue in issues if issue["severity"] == "warning"),
        "clean": not issues,
    }


def story_bible(universe_id: str = "",
                registry: "CharacterUniverseRegistry | None" = None) -> dict:
    return build_bible(universe_id, registry)
