"""Cinematic Director vocabulary — maps to existing renderer/cinematography fields."""

from __future__ import annotations

from typing import Any

# User-facing camera language → existing cinematography CAMERA_MOVEMENTS + render hints
CAMERA_MOVES: dict[str, dict[str, Any]] = {
    "push_in": {"cinematography": "slow_push_in", "zoom": "in", "static": False},
    "pull_out": {"cinematography": "slow_pull_out", "zoom": "out", "static": False},
    "dolly": {"cinematography": "tracking", "zoom": "none", "static": False},
    "orbit": {"cinematography": "orbit", "zoom": "none", "static": False},
    "handheld": {"cinematography": "camera_3d_move", "zoom": "none", "static": False, "intensity_boost": 12},
    "static": {"cinematography": "static_hold", "zoom": "none", "static": True},
    "macro": {"cinematography": "macro_push_in", "zoom": "in", "static": False},
    "overhead": {"cinematography": "establishing_wide", "angle": "top_down", "zoom": "out", "static": False},
    "tracking": {"cinematography": "tracking", "zoom": "none", "static": False},
}

COMPOSITIONS = (
    "rule_of_thirds",
    "center_composition",
    "close_up",
    "wide",
    "medium",
    "split_screen",
    "macro_details",
)

LIGHTING = (
    "bright",
    "dramatic",
    "high_contrast",
    "soft",
    "rim_lighting",
    "scientific",
    "documentary",
)

TRANSITIONS = (
    "hard_cut",
    "cross_dissolve",
    "whip_transition",
    "match_cut",
    "fade",
    "l_cut",
    "j_cut",
)

# Niche → hex-ish palette suggestions (documentation + grade hint strings for renderer)
COLOR_PALETTES: dict[str, dict[str, Any]] = {
    "science": {
        "label": "Science",
        "primary": "#0B3D91",
        "secondary": "#4FC3F7",
        "accent": "#FFD54F",
        "background": "#071428",
        "grade_hint": "cool_scientific",
    },
    "biology": {
        "label": "Biology",
        "primary": "#1B5E20",
        "secondary": "#81C784",
        "accent": "#FF8A65",
        "background": "#0A1F12",
        "grade_hint": "organic_teal",
    },
    "history": {
        "label": "History",
        "primary": "#5D4037",
        "secondary": "#D7CCC8",
        "accent": "#C9A227",
        "background": "#1A120C",
        "grade_hint": "warm_sepia",
    },
    "psychology": {
        "label": "Psychology",
        "primary": "#4527A0",
        "secondary": "#B39DDB",
        "accent": "#26A69A",
        "background": "#140F28",
        "grade_hint": "violet_calm",
    },
    "finance": {
        "label": "Finance",
        "primary": "#004D40",
        "secondary": "#80CBC4",
        "accent": "#FFC107",
        "background": "#041410",
        "grade_hint": "ledger_green",
    },
    "nature": {
        "label": "Nature",
        "primary": "#33691E",
        "secondary": "#AED581",
        "accent": "#FFF176",
        "background": "#0C1608",
        "grade_hint": "earth_natural",
    },
    "technology": {
        "label": "Technology",
        "primary": "#01579B",
        "secondary": "#00E5FF",
        "accent": "#FF4081",
        "background": "#020B16",
        "grade_hint": "neon_tech",
    },
}

NICHE_ALIASES = {
    "science": "science",
    "biology": "biology",
    "marine": "biology",
    "nature": "nature",
    "history": "history",
    "dark_history": "history",
    "psychology": "psychology",
    "finance": "finance",
    "technology": "technology",
    "tech": "technology",
    "ai": "technology",
    "educational": "science",
}


def resolve_niche(niche: str = "", topic: str = "") -> str:
    raw = f"{niche} {topic}".lower()
    for key, canon in NICHE_ALIASES.items():
        if key in raw.replace("-", "_") or key in raw:
            return canon
    return "science"


def palette_for_niche(niche: str = "", topic: str = "") -> dict[str, Any]:
    return dict(COLOR_PALETTES[resolve_niche(niche, topic)])
