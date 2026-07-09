"""TransitionPlanner — normalized, render-ready transition instructions.

The Director annotates scenes with free-form transition language ("hard
cut", "match cut on motion", ...). The renderer needs a closed vocabulary,
so this module maps whatever the planning layer produced onto supported
transition types plus timing and an optional sound cue. Unknown language
degrades to a cut (never a crash) and is reported as a warning.
"""

from __future__ import annotations

# The closed transition vocabulary this renderer supports.
SUPPORTED_TRANSITIONS = (
    "cut",
    "fade",
    "push",
    "zoom",
    "whip_pan",
    "glitch",
    "flash",
    "documentary_slow_zoom",
    "cinematic_push_in",
    "quick_cut",
)

# Default on-screen duration per transition type (seconds). Cuts are
# instant; everything else is a short social-media-paced move.
TRANSITION_DURATIONS = {
    "cut": 0.0,
    "quick_cut": 0.0,
    "fade": 0.4,
    "push": 0.35,
    "zoom": 0.4,
    "whip_pan": 0.25,
    "glitch": 0.3,
    "flash": 0.15,
    "documentary_slow_zoom": 0.8,
    "cinematic_push_in": 0.6,
}

# Transition sound cues the AudioMixer schedules on the transitions track.
TRANSITION_SOUNDS = {
    "whip_pan": "whoosh",
    "glitch": "glitch stutter",
    "flash": "impact hit",
    "push": "soft whoosh",
    "zoom": "riser",
    "cinematic_push_in": "low swell",
}

# Free-form planning language → supported transition type. Matched as
# substrings, most specific first.
_LANGUAGE_MAP = (
    ("whip", "whip_pan"),
    ("glitch", "glitch"),
    ("flash", "flash"),
    ("push-in", "cinematic_push_in"),
    ("push in", "cinematic_push_in"),
    ("push", "push"),
    ("slow zoom", "documentary_slow_zoom"),
    ("zoom", "zoom"),
    ("fade", "fade"),
    ("dissolve", "fade"),
    ("quick cut", "quick_cut"),
    ("hard cut", "cut"),
    ("smash cut", "quick_cut"),
    ("match cut", "cut"),
    ("cut", "cut"),
    ("none", "cut"),
)


def normalize_transition(raw: str) -> "tuple[str, bool]":
    """Map planning language to a supported type. Returns (type, recognized)."""
    text = (raw or "").strip().lower()
    if not text:
        return "cut", True
    if text in SUPPORTED_TRANSITIONS:
        return text, True
    for fragment, transition in _LANGUAGE_MAP:
        if fragment in text:
            return transition, True
    return "cut", False


class TransitionPlanner:
    """Plans the transition between every pair of adjacent scenes."""

    def plan(self, scenes: list) -> dict:
        """Render-ready transition plan: one entry per scene boundary."""
        transitions = []
        warnings = []
        for scene, following in zip(scenes, scenes[1:]):
            raw = scene.get("transition_out") or following.get("transition_in") or "cut"
            transition, recognized = normalize_transition(str(raw))
            if not recognized:
                warnings.append(
                    f"Unrecognized transition {raw!r} after scene "
                    f"{scene.get('scene_number', 0)} — defaulted to cut."
                )
            transitions.append(
                {
                    "from_scene": scene.get("scene_number", 0),
                    "to_scene": following.get("scene_number", 0),
                    "type": transition,
                    "duration_sec": TRANSITION_DURATIONS.get(transition, 0.0),
                    "sound_cue": TRANSITION_SOUNDS.get(transition, ""),
                    "source_language": str(raw),
                }
            )
        return {
            "supported_types": list(SUPPORTED_TRANSITIONS),
            "transitions": transitions,
            "warnings": warnings,
        }
