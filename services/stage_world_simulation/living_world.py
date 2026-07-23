"""Living world — the environment is never static."""

from __future__ import annotations

from typing import Any

from services.stage_world_simulation.models import LIVING_CHANNELS


def build_living_world(
    definition: dict[str, Any],
    *,
    world_id: str,
    ambient_from_location: list[str] | None = None,
) -> dict[str, Any]:
    outdoor = bool(definition.get("outdoor"))
    wtype = str(definition.get("world_type") or "")

    channels: list[str] = ["ambient_particles", "lighting_changes"]
    if outdoor or "nature" in wtype or "forest" in world_id.lower() or "park" in world_id.lower():
        channels.extend(["moving_trees", "wind", "birds", "clouds"])
    if "ocean" in world_id.lower() or "ocean" in wtype:
        channels.extend(["flowing_water", "clouds", "birds"])
    if not outdoor:
        channels.extend(["animated_screens", "people_walking", "steam"])
    if "museum" in world_id.lower() or "lecture" in world_id.lower() or "hospital" in world_id.lower():
        channels.append("people_walking")

    for item in ambient_from_location or []:
        token = str(item).lower().replace(" ", "_")
        # Map freeform ambient labels into living channels
        if any(k in token for k in ("tree", "leaf", "sway")):
            channels.append("moving_trees")
        elif "wind" in token or "breeze" in token:
            channels.append("wind")
        elif "water" in token or "caustic" in token or "bubble" in token:
            channels.append("flowing_water")
        elif "screen" in token or "monitor" in token or "holo" in token:
            channels.append("animated_screens")
        elif any(k in token for k in ("people", "visitor", "researcher", "crowd")):
            channels.append("people_walking")
        elif "bird" in token:
            channels.append("birds")
        elif "cloud" in token:
            channels.append("clouds")
        elif "steam" in token or "vapor" in token:
            channels.append("steam")
        elif "particle" in token or "dust" in token or "mote" in token:
            channels.append("ambient_particles")

    # Dedupe preserve order
    seen: set[str] = set()
    ordered: list[str] = []
    for c in channels:
        if c not in seen and c in LIVING_CHANNELS:
            seen.add(c)
            ordered.append(c)
    for c in LIVING_CHANNELS:
        if len(ordered) >= 5:
            break
        if c not in seen:
            ordered.append(c)
            seen.add(c)

    tracks = [
        {
            "id": ch,
            "continuous": True,
            "layer": "background" if ch in {"clouds", "birds", "moving_trees"} else "midground",
            "amplitude": 0.4,
        }
        for ch in ordered
    ]

    return {
        "world_id": world_id,
        "living": True,
        "forbid_static_environment": True,
        "channels": ordered,
        "tracks": tracks,
        "weather": definition.get("default_weather") or "interior_climate",
        "lighting": definition.get("default_lighting") or "soft_daylight",
        "lighting_dynamic": True,
        "philosophy": "The environment is never static.",
    }
