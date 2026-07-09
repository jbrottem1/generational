"""Character consistency — persistent characters look identical everywhere.

Consistency comes from data, not model memory: the Creative Studio's cast
(`creative_package.character_plan.cast`, CHARACTER_FIELDS dicts) carries a
stable `visual_signature` and `color_anchor` per character, and this
module compiles them into reference blocks the Prompt Compiler embeds
VERBATIM in every prompt featuring that character — appearance, wardrobe,
facial features, age markers, hair, accessories, body type, and style stay
identical across every generation, forever.

This module reads character dicts from the package data — it never
imports the Creative Studio (department boundaries stay clean).
"""

from __future__ import annotations


def character_reference(character: dict) -> str:
    """One canonical reference sentence for one character.

    Deterministic: the same character dict always compiles to the same
    reference text, so prompts (and therefore cache fingerprints) are
    stable across runs.
    """
    parts = []
    name = str(character.get("name", "")).strip()
    signature = str(character.get("visual_signature", "")).strip()
    if name and signature:
        parts.append(f"{name}: {signature}")
    elif signature:
        parts.append(signature)
    elif name:
        parts.append(name)

    wardrobe = str(character.get("wardrobe", "")).strip()
    if wardrobe:
        parts.append(f"wearing {wardrobe}")
    color_anchor = str(character.get("color_anchor", "")).strip()
    if color_anchor:
        parts.append(f"signature color {color_anchor}")
    accessories = character.get("accessories") or []
    if accessories:
        parts.append("accessories: " + ", ".join(str(a) for a in accessories))
    return "; ".join(parts)


def build_character_index(item: dict) -> "dict[str, dict]":
    """character_id → character dict, from the item's creative package."""
    cast = (item.get("creative_package") or {}).get("character_plan", {}).get("cast", [])
    return {
        str(character.get("character_id", "")): character
        for character in cast
        if character.get("character_id")
    }


def character_references_for(character_ids: "list[str]", index: "dict[str, dict]") -> "list[str]":
    """Reference blocks for the characters present in one request, in a
    stable order. Unknown ids are skipped (never a failure)."""
    references = []
    for character_id in character_ids or []:
        character = index.get(str(character_id))
        if character:
            reference = character_reference(character)
            if reference:
                references.append(reference)
    return references


def scene_character_map(item: dict) -> "dict[str, list]":
    """scene_id → character_ids, from the creative storyboard."""
    storyboard = (item.get("creative_package") or {}).get("storyboard", [])
    return {
        str(scene.get("scene_id", "")): list(scene.get("characters", []) or [])
        for scene in storyboard
        if scene.get("scene_id")
    }
