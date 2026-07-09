"""Camera Director — the full lens-level camera plan for a storyboard.

Extends every board scene into one directed shot (CAMERA_SHOT_FIELDS):
angle, lens selection, movement, zoom, tracking, depth of field, focus
pulls, motion pacing, shot duration, and composition. Deterministic: the
same board and blueprint always produce the same camera plan.
"""

from __future__ import annotations

# Lens selection by camera angle — professional focal-length grammar.
_LENS_BY_ANGLE = (
    ("wide", "24mm wide — scale and context, mild perspective stretch"),
    ("establishing", "24mm wide — scale and context, mild perspective stretch"),
    ("hero", "35mm — natural drama, room for the subject to breathe"),
    ("medium", "50mm — natural field of view, honest proportions"),
    ("over-shoulder", "50mm — natural field of view, honest proportions"),
    ("close-up", "85mm portrait — flattering compression, intimate"),
    ("detail", "100mm macro — texture-level intimacy"),
    ("insert", "100mm macro — texture-level intimacy"),
)

_DEFAULT_LENS = "50mm — natural field of view, honest proportions"

# Depth of field by shot intimacy.
_DOF_BY_LENS_KEY = {
    "24mm": "deep focus — everything readable",
    "35mm": "moderate — subject separated, world present",
    "50mm": "moderate — subject separated, world present",
    "85mm": "shallow — melt the background away",
    "100mm": "razor thin — one plane of focus",
}

_COMPOSITION_BY_PURPOSE = {
    "hook": "centered subject, negative space for hook text overlay",
    "setup": "rule of thirds, leading lines into the subject",
    "development": "balanced thirds, motivated foreground layers",
    "escalation": "tightening headroom, diagonal tension lines",
    "revelation": "symmetry break — the reveal owns the frame center",
    "payoff": "wide symmetric hero composition, horizon settled",
}


def _lens_for(angle: str) -> str:
    lowered = angle.lower()
    for key, lens in _LENS_BY_ANGLE:
        if key in lowered:
            return lens
    return _DEFAULT_LENS


def _dof_for(lens: str) -> str:
    for key, dof in _DOF_BY_LENS_KEY.items():
        if lens.startswith(key):
            return dof
    return "moderate — subject separated, world present"


def _zoom_for(purpose: str, movement: str) -> str:
    if purpose == "hook":
        return "fast 10% punch-in on the opening beat"
    if "push-in" in movement:
        return "slow creeping zoom riding the push-in"
    if "pull-back" in movement:
        return "widening zoom matched to the pull-back"
    return "none — hold focal length"

def _tracking_for(movement: str) -> str:
    if "track" in movement:
        return "lateral dolly track locked to subject speed"
    if "push-in" in movement or "pull-back" in movement:
        return "straight dolly rail, no lateral drift"
    return "static — locked off with micro-drift only"


def _focus_pull_for(purpose: str) -> str:
    if purpose == "revelation":
        return "rack focus from foreground misdirection to the reveal"
    if purpose == "hook":
        return "snap focus lands with the first word of narration"
    return "hold focus on the subject"


def _motion_pacing(tempo: str, purpose: str) -> str:
    if purpose in ("hook", "escalation"):
        return "accelerated — cuts and moves land on narration stresses"
    if tempo in ("slow", "measured"):
        return "unhurried — moves settle before each cut"
    return "steady — one move per scene, no restlessness"


def build_camera_plan(storyboard: "list[dict]", blueprint: dict) -> dict:
    """The Camera Director's complete plan for one storyboard."""
    tempo = blueprint.get("pacing", {}).get("tempo", "dynamic")
    shots = []
    for number, scene in enumerate(storyboard, start=1):
        angle = scene.get("camera_angle", "")
        movement = scene.get("camera_movement", "")
        purpose = scene.get("purpose", "development")
        lens = _lens_for(angle)
        shots.append(
            {
                "shot_id": f"shot_{number:03d}",
                "scene_id": scene.get("scene_id", ""),
                "angle": angle,
                "lens": lens,
                "movement": movement,
                "zoom": _zoom_for(purpose, movement),
                "tracking": _tracking_for(movement),
                "depth_of_field": _dof_for(lens),
                "focus_pull": _focus_pull_for(purpose),
                "motion_pacing": _motion_pacing(tempo, purpose),
                "duration_sec": scene.get("estimated_duration_sec", 0.0),
                "composition": _COMPOSITION_BY_PURPOSE.get(purpose, "balanced thirds"),
            }
        )
    return {
        "cinematic_language": blueprint.get("cinematic_language", {}),
        "aspect_ratio": blueprint.get("aspect_ratio", "9:16"),
        "lens_kit": sorted({shot["lens"] for shot in shots}),
        "shots": shots,
    }
