"""Asset handoff — request/reference via Asset Intelligence (no duplicate media system)."""

from __future__ import annotations

from typing import Any


def build_asset_requirements(world: dict[str, Any], *, zone_id: str = "", topic: str = "") -> dict[str, Any]:
    """Produce structured asset requirements for the existing media pipeline."""
    requirements = []
    resolved = []
    missing = []

    # Background / environment plates
    requirements.append(
        {
            "kind": "background_loop",
            "purpose": "environment_plate",
            "query": f"{world.get('name') or world.get('world_type')} {zone_id}".strip(),
            "world_id": world.get("world_id"),
            "zone": zone_id,
        }
    )
    for ambience in world.get("sound_ambience") or world.get("ambience") or []:
        requirements.append(
            {
                "kind": "sound_effect" if "effect" in str(ambience).lower() else "music",
                "purpose": "environmental_ambience",
                "query": str(ambience),
                "handoff_to": "sound_design",
                "note": "World specifies context only — final mix is sound system",
            }
        )
    for obj in (world.get("objects") or [])[:8]:
        name = obj.get("name") if isinstance(obj, dict) else str(obj)
        requirements.append(
            {
                "kind": "image",
                "purpose": "prop",
                "query": str(name),
                "object_id": (obj.get("object_id") if isinstance(obj, dict) else ""),
            }
        )

    # Try resolve via Asset Intelligence without regenerating
    try:
        from services.asset_intelligence import semantic_search

        for req in requirements:
            hits = semantic_search(str(req.get("query") or topic or world.get("name") or ""), limit=2)
            if hits:
                top = hits[0]
                resolved.append({**req, "resolved": True, "asset_id": top.get("asset_id"), "uri": top.get("uri"), "score": top.get("rank_score")})
            else:
                missing.append({**req, "resolved": False})
    except Exception:  # noqa: BLE001
        missing = [{**r, "resolved": False, "error": "asset_intelligence_unavailable"} for r in requirements]

    return {
        "world_id": world.get("world_id"),
        "requirements": requirements,
        "resolved": resolved,
        "missing": missing,
        "note": "Does not duplicate Asset Intelligence — references or requests only",
    }
