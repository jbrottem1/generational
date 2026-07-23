"""Retention-aware visual intensity — elevate first 3s, peaks, reveals, emotion."""

from __future__ import annotations

import re
from typing import Any


def predicted_retention_weight(
    *,
    scene_index: int,
    total_scenes: int,
    narration: str,
    purpose: str = "",
    start_sec: float = 0.0,
) -> dict[str, Any]:
    """Return intensity multipliers labeled as predictions for directing, not audience proof."""
    text = (narration or "").lower()
    purpose = (purpose or "").lower()
    weight = 0.55
    tags: list[str] = []

    if scene_index == 0 or start_sec < 3.0 or purpose in ("hook", "pattern_interrupt"):
        weight = max(weight, 0.95)
        tags.append("first_3_seconds")

    if any(w in text for w in ("stop", "wait", "nobody", "secret", "wrong", "but ", "however")):
        weight = max(weight, 0.88)
        tags.append("curiosity_peak")

    if any(w in text for w in ("reveal", "because", "that's why", "three hearts", "actually", "truth")):
        weight = max(weight, 0.9)
        tags.append("major_reveal")

    if any(w in text for w in ("feel", "afraid", "wonder", "strange", "beautiful", "shock")):
        weight = max(weight, 0.82)
        tags.append("emotional_moment")

    # Mid-story can dip; endings bump for CTA
    if total_scenes > 2 and scene_index == total_scenes - 1:
        weight = max(weight, 0.7)
        tags.append("payoff_or_cta")

    if purpose in ("cta", "call_to_action"):
        weight = max(weight, 0.72)

    motion_floor = 35 if "first_3_seconds" in tags else 28
    motion_target = int(round(motion_floor + weight * 60))
    return {
        "intensity_0_1": round(min(1.0, weight), 3),
        "recommended_motion_score": min(100, motion_target),
        "tags": tags,
        "label": "PREDICTION — directing heuristic, not real audience retention",
    }


def choose_camera_for_intensity(intensity: float, *, avoid_static: bool = True, scene_index: int = 0) -> str:
    """Pick a user-facing camera move from intensity (avoid dead stills by default)."""
    if intensity >= 0.9:
        return ("push_in", "macro", "handheld", "orbit")[scene_index % 4]
    if intensity >= 0.75:
        return ("push_in", "dolly", "tracking", "orbit")[scene_index % 4]
    if intensity >= 0.55:
        return ("dolly", "tracking", "pull_out", "push_in")[scene_index % 4]
    if avoid_static:
        return ("pull_out", "dolly", "tracking")[scene_index % 3]
    return "static"


def choose_composition(narration: str, camera: str) -> str:
    text = (narration or "").lower()
    if camera == "macro" or any(w in text for w in ("detail", "cell", "close", "blood", "heart")):
        return "macro_details" if "cell" in text or "detail" in text else "close_up"
    if any(w in text for w in ("world", "ocean", "planet", "landscape", "facility")):
        return "wide"
    if any(w in text for w in ("versus", "two", "compare", "split")):
        return "split_screen"
    if camera in ("push_in", "macro"):
        return "close_up"
    if camera in ("overhead", "pull_out"):
        return "wide"
    return "rule_of_thirds" if scene_hash(narration) % 2 == 0 else "center_composition"


def scene_hash(text: str) -> int:
    return abs(hash((text or "")[:80])) % 10_000


def choose_lighting(niche: str, intensity: float, narration: str) -> str:
    """V2 quality: prefer motivated documentary / scientific lighting over flat soft fills."""
    text = (narration or "").lower()
    if intensity >= 0.9 or any(w in text for w in ("shock", "stop", "reveal")):
        return "high_contrast" if intensity >= 0.92 else "dramatic"
    if niche in ("science", "technology"):
        # Prefer rim + scientific practicals for depth (documentary grade)
        return "scientific" if intensity >= 0.55 else "rim_lighting"
    if niche in ("biology", "nature"):
        # Soft only for quiet beats; otherwise documentary key for depth
        return "soft" if intensity < 0.55 else "documentary"
    if niche == "history":
        return "dramatic"
    if niche == "psychology":
        return "soft" if intensity < 0.6 else "documentary"
    if niche == "finance":
        return "bright" if intensity < 0.7 else "high_contrast"
    return "documentary"


def choose_transition(prev_camera: str, intensity: float, scene_index: int) -> str:
    if scene_index == 0:
        return "hard_cut"
    if intensity >= 0.9:
        return "whip_transition" if scene_index % 2 else "hard_cut"
    if prev_camera == "macro":
        return "match_cut"
    if intensity < 0.55:
        return "cross_dissolve"
    return ("hard_cut", "l_cut", "j_cut", "hard_cut")[scene_index % 4]


def emphasis_and_hierarchy(narration: str, intensity: float) -> dict[str, Any]:
    words = [w for w in re.findall(r"[A-Za-z0-9']+", narration or "") if len(w) > 2]
    keywords = words[:3]
    return {
        "text_emphasis": keywords,
        "on_screen_priority": "keyword_punch" if intensity >= 0.8 else "caption_support",
        "visual_hierarchy": [
            "subject",
            "motion",
            "caption",
            "atmosphere",
        ]
        if intensity >= 0.75
        else ["subject", "caption", "atmosphere", "motion"],
    }
