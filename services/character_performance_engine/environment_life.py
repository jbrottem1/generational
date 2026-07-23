"""Living environment cues — the world never freezes."""

from __future__ import annotations

from typing import Any

from services.character_performance_engine.models import ENVIRONMENT_LIFE, MIN_ENVIRONMENT_LIFE


def plan_environment_life(
    *,
    location_hint: str = "lab",
    ambient_from_location: list[str] | None = None,
    duration_sec: float = 3.0,
) -> dict[str, Any]:
    loc = (location_hint or "lab").lower()
    base: list[str] = []
    if any(k in loc for k in ("lab", "clinic", "hospital", "medical")):
        base = ["machines_operate", "screens_update", "lights_flicker", "steam_rise", "people_walk", "particles_drift"]
    elif any(k in loc for k in ("outdoor", "forest", "park", "nature")):
        base = ["clouds_move", "trees_sway", "grass_wind", "birds_fly", "particles_drift"]
    elif any(k in loc for k in ("city", "street", "urban")):
        base = ["cars_pass", "people_walk", "clouds_move", "lights_flicker", "particles_drift"]
    else:
        base = ["particles_drift", "lights_flicker", "people_walk", "screens_update"]

    for item in ambient_from_location or []:
        token = str(item).lower().replace(" ", "_")
        if token not in base:
            base.append(token)

    # Ensure minimum living channels
    for token in ENVIRONMENT_LIFE:
        if len(base) >= MIN_ENVIRONMENT_LIFE:
            break
        if token not in base:
            base.append(token)

    tracks = []
    for i, token in enumerate(base[:8]):
        tracks.append(
            {
                "id": token,
                "t_start": 0.0,
                "t_end": float(duration_sec),
                "continuous": True,
                "layer": "background" if i % 2 == 0 else "midground",
                "amplitude": 0.35 + 0.05 * (i % 3),
            }
        )

    return {
        "living": True,
        "forbid_static_background": True,
        "channels": base[:8],
        "tracks": tracks,
        "doors_and_traffic": "people_walk" in base or "doors_open" in base,
        "philosophy": "Nothing is frozen.",
    }
