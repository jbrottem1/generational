"""MotionPlanner — per-scene motion effects as structured render instructions.

Still images need motion to survive on vertical feeds; video assets need
their camera intent restated in renderer vocabulary. This module converts
the Director's camera_motion / zoom / motion_intensity annotations into a
closed set of motion effects (ken burns, slow zoom, push-in, pan, ...)
with numeric parameters a renderer can execute directly. No pixels are
moved here — these are instructions.
"""

from __future__ import annotations

# The closed motion-effect vocabulary this renderer supports.
MOTION_EFFECTS = (
    "static",
    "ken_burns",
    "slow_zoom_in",
    "slow_zoom_out",
    "cinematic_push_in",
    "documentary_slow_zoom",
    "pan_left",
    "pan_right",
    "whip_pan",
    "handheld_drift",
    "quick_punch_in",
)

# Free-form camera/zoom planning language → motion effect (substring match,
# most specific first). Prefer cinematic verbs over ken_burns.
_LANGUAGE_MAP = (
    ("whip", "whip_pan"),
    ("push-in", "cinematic_push_in"),
    ("push in", "cinematic_push_in"),
    ("push_in", "cinematic_push_in"),
    ("punch", "quick_punch_in"),
    ("handheld", "handheld_drift"),
    ("orbit", "handheld_drift"),
    ("parallax", "pan_right"),
    ("tracking", "pan_right"),
    ("reveal", "cinematic_push_in"),
    ("crane", "slow_zoom_out"),
    ("drift", "handheld_drift"),
    ("pan left", "pan_left"),
    ("pan right", "pan_right"),
    ("pan", "pan_right"),
    ("ken burns", "ken_burns"),
    ("zoom out", "slow_zoom_out"),
    ("slow zoom", "documentary_slow_zoom"),
    ("zoom", "slow_zoom_in"),
    ("dolly", "cinematic_push_in"),
    ("static", "static"),
    ("locked", "static"),
)


def _effect_for(scene: dict) -> str:
    text = " ".join(
        str(scene.get(key, ""))
        for key in ("camera_motion", "camera_preset", "zoom", "motion_recommendation", "camera")
    ).lower()
    for fragment, effect in _LANGUAGE_MAP:
        if fragment in text:
            return effect
    # Prefer push-in over ken_burns for stills — ken_burns is legacy slideshow default
    if scene.get("asset_type", "ai_image") == "ai_image":
        return "cinematic_push_in"
    return "static"


def _zoom_range_for(effect: str, intensity: int) -> "tuple[float, float]":
    """Start/end scale factors for zoom-family effects (1.0 = no zoom)."""
    depth = round(1.0 + (0.04 + (intensity / 100) * 0.14), 3)
    if effect in ("slow_zoom_in", "documentary_slow_zoom", "cinematic_push_in", "ken_burns"):
        return 1.0, depth
    if effect == "quick_punch_in":
        return 1.0, round(depth + 0.05, 3)
    if effect == "slow_zoom_out":
        return depth, 1.0
    return 1.0, 1.0


class MotionPlanner:
    """Plans one motion effect (with parameters) per scene."""

    def plan_scene(self, scene: dict) -> dict:
        """Structured motion instruction for one scene."""
        intensity = int(scene.get("motion_intensity", 50))
        effect = _effect_for(scene)
        zoom_start, zoom_end = _zoom_range_for(effect, intensity)
        pan = {"pan_left": "left", "pan_right": "right", "whip_pan": "right"}.get(effect, "none")
        return {
            "scene_id": scene.get("scene_number", 0),
            "effect": effect,
            "intensity": intensity,
            "duration_sec": float(scene.get("length_sec", 0.0)),
            "zoom": {"start_scale": zoom_start, "end_scale": zoom_end},
            "pan": {"direction": pan, "amount_pct": round(intensity * 0.12, 1) if pan != "none" else 0.0},
            "ken_burns": effect == "ken_burns",
            "easing": "ease_in_out" if intensity < 70 else "ease_out",
        }

    def plan(self, scenes: list) -> list:
        return [self.plan_scene(scene) for scene in scenes]
