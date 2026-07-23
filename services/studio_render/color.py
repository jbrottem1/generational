"""Module 4 — Color Grading with LUT profiles."""

from __future__ import annotations

from services.studio_render.models import GRADE_PROFILES

# Profile → LUT-like grading parameters (deterministic, editable)
LUT_PROFILES: dict[str, dict] = {
    "science_documentary": {
        "lut_id": "gen_science_doc_v3",
        "temperature": -5,
        "contrast": 1.08,
        "saturation": 0.92,
        "shadows": -0.05,
        "highlights": -0.08,
        "teal_orange": 0.15,
    },
    "technology": {
        "lut_id": "gen_tech_v3",
        "temperature": -12,
        "contrast": 1.12,
        "saturation": 0.88,
        "shadows": -0.08,
        "highlights": 0.05,
        "teal_orange": 0.22,
    },
    "space": {
        "lut_id": "gen_space_v3",
        "temperature": -18,
        "contrast": 1.15,
        "saturation": 0.85,
        "shadows": -0.12,
        "highlights": 0.1,
        "teal_orange": 0.05,
    },
    "nature": {
        "lut_id": "gen_nature_v3",
        "temperature": 8,
        "contrast": 1.05,
        "saturation": 1.08,
        "shadows": 0.02,
        "highlights": -0.05,
        "teal_orange": 0.08,
    },
    "medical": {
        "lut_id": "gen_medical_v3",
        "temperature": -2,
        "contrast": 1.06,
        "saturation": 0.9,
        "shadows": -0.03,
        "highlights": 0.0,
        "teal_orange": 0.05,
    },
    "business": {
        "lut_id": "gen_business_v3",
        "temperature": 2,
        "contrast": 1.1,
        "saturation": 0.86,
        "shadows": -0.06,
        "highlights": -0.02,
        "teal_orange": 0.12,
    },
    "finance": {
        "lut_id": "gen_finance_v3",
        "temperature": -4,
        "contrast": 1.11,
        "saturation": 0.84,
        "shadows": -0.07,
        "highlights": 0.02,
        "teal_orange": 0.18,
    },
    "historical": {
        "lut_id": "gen_historical_v3",
        "temperature": 14,
        "contrast": 1.04,
        "saturation": 0.78,
        "shadows": 0.04,
        "highlights": -0.1,
        "teal_orange": 0.0,
    },
    "educational": {
        "lut_id": "gen_educational_v3",
        "temperature": 0,
        "contrast": 1.07,
        "saturation": 0.95,
        "shadows": -0.02,
        "highlights": -0.04,
        "teal_orange": 0.1,
    },
}

_TOPIC_MAP = (
    (("space", "nasa", "planet", "galaxy", "orbit"), "space"),
    (("ai", "chip", "robot", "computer", "software", "tech"), "technology"),
    (("ocean", "forest", "animal", "coral", "wildlife", "plant"), "nature"),
    (("cell", "dna", "medical", "brain", "health", "virus"), "medical"),
    (("market", "stock", "finance", "money", "invest"), "finance"),
    (("business", "startup", "company", "ceo"), "business"),
    (("history", "ancient", "war", "century", "empire"), "historical"),
    (("physics", "chemistry", "biology", "science", "math"), "science_documentary"),
)


def choose_grade_profile(candidate: dict) -> str:
    blob = " ".join(
        str(candidate.get(k) or "")
        for k in ("title", "topic", "niche", "category", "subject")
    ).lower()
    for keys, profile in _TOPIC_MAP:
        if any(k in blob for k in keys):
            return profile
    return "educational"


def build_color_grade(candidate: dict) -> dict:
    profile = choose_grade_profile(candidate)
    assert profile in GRADE_PROFILES
    lut = dict(LUT_PROFILES[profile])
    return {
        "profile": profile,
        "lut": lut,
        "consistency": {
            "locked": True,
            "white_balance_locked": True,
            "scene_variance_max": 0.08,
        },
        "reason": f"Topic-matched LUT profile: {profile}",
    }
