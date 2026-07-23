"""Environmental physics — wind and rain affect world + actors."""

from __future__ import annotations

from typing import Any

from services.physics_interaction.models import ENV_RAIN_TARGETS, ENV_WIND_TARGETS


def build_environmental_physics(
    *,
    weather: str = "interior_climate",
    outdoor: bool = False,
) -> dict[str, Any]:
    w = str(weather or "").lower()
    wind_on = outdoor or any(k in w for k in ("breeze", "wind", "storm", "swell"))
    rain_on = any(k in w for k in ("rain", "storm", "drizzle"))

    return {
        "weather": weather,
        "outdoor": outdoor,
        "wind": {
            "enabled": wind_on,
            "affects": list(ENV_WIND_TARGETS),
            "base_strength": 0.35 if wind_on else 0.05,
            "gusts": wind_on,
        },
        "rain": {
            "enabled": rain_on,
            "affects": list(ENV_RAIN_TARGETS),
            "wetness": 0.6 if rain_on else 0.0,
            "puddles": rain_on,
            "footprints": rain_on or outdoor,
        },
        "interior_air": not outdoor,
        "particles_drift": True,
    }
