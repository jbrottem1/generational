"""Module 5 — Visual Effects (only when appropriate)."""

from __future__ import annotations

from services.studio_render.models import VFX_TYPES


def build_visual_effects(candidate: dict, color_grade: dict | None = None) -> list[dict]:
    profile = (color_grade or {}).get("profile") or "educational"
    scenes = list((candidate.get("visual_package") or {}).get("scenes") or [])
    if not scenes:
        scenes = [{"scene_id": "s1", "narration": str(candidate.get("title") or "")}]

    effects: list[dict] = []
    for i, scene in enumerate(scenes):
        sid = str(scene.get("scene_id") or f"s{i+1}")
        text = str(scene.get("narration") or "").lower()
        chosen: list[tuple[str, str, float]] = []

        # Subtle film grain on documentary profiles
        if profile in ("science_documentary", "historical", "educational"):
            chosen.append(("film_grain", "Documentary texture", 0.18))
        if profile == "space" or any(w in text for w in ("space", "star", "galaxy")):
            chosen.append(("particles", "Cosmic particle field", 0.35))
            chosen.append(("bloom", "Star bloom", 0.25))
        if any(w in text for w in ("sun", "light", "glow", "bright", "laser")):
            chosen.append(("glow", "Narration light emphasis", 0.3))
            chosen.append(("light_rays", "God rays for emphasis", 0.22))
        if any(w in text for w in ("fog", "mist", "atmosphere", "cloud")):
            chosen.append(("atmosphere", "Atmospheric depth", 0.28))
            chosen.append(("fog", "Soft fog layer", 0.2))
        if any(w in text for w in ("focus", "macro", "tiny", "detail", "notice")):
            chosen.append(("depth_of_field", "Macro DOF", 0.4))
        if profile == "technology" and i % 2 == 0:
            chosen.append(("ambient_lighting", "Tech ambient", 0.2))
        if any(w in text for w in ("lens", "camera", "flare")):
            chosen.append(("lens_flare", "Lens flare accent", 0.15))

        # Never spam — max 2 effects per scene unless space profile
        limit = 3 if profile == "space" else 2
        for name, reason, intensity in chosen[:limit]:
            assert name in VFX_TYPES
            effects.append(
                {
                    "scene_id": sid,
                    "type": name,
                    "intensity": intensity,
                    "reason": reason,
                }
            )
    return effects
