"""Color & Lighting — the production's complete visual-light design.

Generates one color & lighting plan (COLOR_LIGHTING_FIELDS): the master
palette, per-scene lighting setups, contrast strategy, visual hierarchy,
brand color integration, accessibility guidance, and an emotional color
map that translates each scene's emotion into a color treatment.
"""

from __future__ import annotations

# Emotion → color treatment. The emotional grammar of the grade.
EMOTIONAL_COLOR_MAP = {
    "curiosity": "cool teal shadows, one warm highlight pulling the eye",
    "interest": "neutral balance, saturation slightly lifted on the subject",
    "engagement": "full palette, midtone warmth, honest contrast",
    "tension": "desaturated field, deepening shadows, cold edge light",
    "surprise": "sudden warm flare against the established cool field",
    "awe": "expansive deep blues with luminous highlights",
    "satisfaction": "golden warmth, lifted shadows, gentle contrast release",
}

_DEFAULT_TREATMENT = "neutral balance, saturation slightly lifted on the subject"

# Lighting recipe by scene purpose.
_LIGHTING_BY_PURPOSE = {
    "hook": "hard key, crushed fill — maximum first-frame contrast",
    "setup": "soft key with ambient fill — orientation, not drama",
    "development": "motivated practicals, balanced three-point",
    "escalation": "narrowing key, rising contrast ratio",
    "revelation": "new light source enters with the reveal",
    "payoff": "warm broad key, open fill — resolution reads as relief",
}


def _accessibility(style: dict) -> dict:
    """Accessibility guidance every render must honor. Guidance, not
    enforcement — the render engine applies it, QC surfaces it."""
    return {
        "caption_contrast": "captions at >= 4.5:1 contrast against background at all times",
        "caption_safe_zone": "keep captions inside the platform safe zone (bottom third, inset)",
        "flash_safety": "no full-frame flashes faster than 3 per second",
        "color_independence": "never encode meaning in color alone — pair with shape or label",
        "text_size": "on-screen text legible at 20% preview size (mobile feeds)",
        "palette_note": f"verify palette '{style.get('color_palette', '')}' holds contrast in compression",
    }


def build_color_lighting_plan(
    storyboard: "list[dict]", blueprint: dict, style: dict, item: "dict | None" = None
) -> dict:
    """One color & lighting plan for one production."""
    item = item or {}
    brand_colors = list(item.get("brand_colors", []))

    lighting_setups = [
        {
            "scene_id": scene.get("scene_id", ""),
            "setup": _LIGHTING_BY_PURPOSE.get(scene.get("purpose", ""), "balanced three-point"),
            "style_lighting": scene.get("lighting", ""),
        }
        for scene in storyboard
    ]

    emotional_map = [
        {
            "scene_id": scene.get("scene_id", ""),
            "emotion": scene.get("emotion", ""),
            "treatment": EMOTIONAL_COLOR_MAP.get(scene.get("emotion", ""), _DEFAULT_TREATMENT),
        }
        for scene in storyboard
    ]

    return {
        "color_palette": style.get("color_palette", ""),
        "lighting_setups": lighting_setups,
        "contrast_strategy": (
            "highest contrast on the hook, easing through development, "
            "rising again into the revelation, releasing at the payoff"
        ),
        "visual_hierarchy": (
            "1) the scene's visual_emphasis subject, 2) supporting characters, "
            "3) overlay text, 4) environment — never let the background outshout the subject"
        ),
        "brand_colors": brand_colors or ["derive from brand kit when Agent 10 lands"],
        "accessibility": _accessibility(style),
        "emotional_color_map": emotional_map,
    }
