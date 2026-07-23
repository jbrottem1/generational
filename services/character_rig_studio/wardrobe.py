"""Wardrobe — clothing separated from body; reusable outfits."""

from __future__ import annotations

from typing import Any


def build_wardrobe(
    character_id: str,
    *,
    outfits: list[str] | None = None,
    default_outfit: str = "default",
    existing_wardrobe: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cid = str(character_id).upper()
    outfit_list = list(outfits or [default_outfit])
    slots = []
    for name in outfit_list:
        slots.append(
            {
                "id": name,
                "layers": _layers_for(name, cid),
                "separated_from_body": True,
                "cloth_sim": True,
            }
        )

    return {
        "character_id": cid,
        "architecture": "clothing_separated_from_body",
        "default_outfit": default_outfit or outfit_list[0],
        "outfits": slots,
        "outfit_ids": outfit_list,
        "simulate_as_fabric": bool((existing_wardrobe or {}).get("simulate_as_fabric", True)),
        "responds_to": list(
            (existing_wardrobe or {}).get("responds_to")
            or ["walk", "run", "arm_move", "sit", "wind", "gravity", "turn"]
        ),
        "forbid": list(
            (existing_wardrobe or {}).get("forbid")
            or ["frozen_fabric", "fabric_leads_body", "limb_clipping"]
        ),
        "inheritable_architecture": True,
        "existing_ref": "WARDROBE_PROFILE.json" if existing_wardrobe else None,
        "reusable": True,
    }


def _layers_for(outfit: str, character_id: str) -> list[str]:
    o = outfit.lower()
    if "lab" in o or "coat" in o and character_id == "DOCTOR_001":
        return ["base_chassis", "undershirt", "lab_coat", "accent_trim"]
    if "emergency" in o:
        return ["base", "utility_layer", "emergency_vest"]
    if "research" in o:
        return ["base", "research_smock"]
    if "scrub" in o:
        return ["scrubs_top", "scrubs_bottom"]
    if "travel" in o:
        return ["base_layer", "travel_coat", "boots"]
    if "gown" in o:
        return ["soft_gown"]
    return ["base_garment", outfit]
