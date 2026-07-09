"""Visual psychology heuristics — the perceptual core of Visual Intelligence.

Where `engines/psychology.py` scores what a concept *says*, this module
scores what a scene will *look like*: twelve perceptual triggers that make
a frame stop a scrolling thumb. Every scene in the storyboard receives a
0-100 score per dimension plus one weighted Scene Visual Score.

Scoring is deterministic text-feature analysis (word-bank hits, scene
structure, motion intensity) so it is fast, free, reproducible in every
mode, and fully unit-testable without an API key. Swapping in a learned
vision model later only requires changing `score_scene_visuals()` — the
report shape stays the same.
"""

from __future__ import annotations

from engines.heuristics import (
    CURIOSITY_WORDS,
    FEAR_WORDS,
    HUMOR_WORDS,
    IDENTITY_WORDS,
    NOVELTY_WORDS,
    SATISFACTION_WORDS,
    clamp,
    count_hits,
    stable_jitter,
)

VISUAL_DIMENSION_KEYS = [
    "curiosity",
    "mystery",
    "wonder",
    "fear",
    "beauty",
    "novelty",
    "scale",
    "contrast",
    "motion",
    "satisfaction",
    "humor",
    "identity",
]

VISUAL_DIMENSION_LABELS = {
    "curiosity": "Curiosity",
    "mystery": "Mystery",
    "wonder": "Wonder",
    "fear": "Fear",
    "beauty": "Beauty",
    "novelty": "Novelty",
    "scale": "Scale",
    "contrast": "Contrast",
    "motion": "Motion",
    "satisfaction": "Satisfaction",
    "humor": "Humor",
    "identity": "Identity",
}

# How much each perceptual trigger contributes to a scene's Visual Score
# (0-100). Data, not code — the future Learning Engine can retune these from
# real retention curves without touching scoring logic. Sum == 1.0.
# Curiosity, motion, and contrast carry the most weight because they are the
# strongest scroll-stop signals in short-form feeds.
VISUAL_SCORE_WEIGHTS = {
    "curiosity": 0.14,
    "mystery": 0.09,
    "wonder": 0.08,
    "fear": 0.06,
    "beauty": 0.08,
    "novelty": 0.09,
    "scale": 0.07,
    "contrast": 0.11,
    "motion": 0.12,
    "satisfaction": 0.08,
    "humor": 0.04,
    "identity": 0.04,
}

# Visual-specific word banks. These describe what appears ON SCREEN, not what
# the narration argues — the perceptual complement to engines/heuristics.py.
MYSTERY_VISUAL_WORDS = [
    "shadow", "silhouette", "obscured", "fog", "darkness", "unseen", "hidden",
    "behind", "beneath", "half-lit", "partially", "reveal", "unknown", "veiled",
]

WONDER_VISUAL_WORDS = [
    "vast", "glowing", "cosmic", "aurora", "starfield", "bioluminescent",
    "impossible", "breathtaking", "otherworldly", "infinite", "majestic",
    "shimmering", "floating", "levitating",
]

BEAUTY_VISUAL_WORDS = [
    "golden hour", "symmetry", "elegant", "pristine", "crystalline", "silky",
    "cinematic", "painterly", "lush", "delicate", "graceful", "immaculate",
    "soft focus", "bokeh",
]

SCALE_VISUAL_WORDS = [
    "massive", "tiny", "towering", "microscopic", "giant", "colossal",
    "aerial", "bird's-eye", "wide shot", "dwarfed", "enormous", "miniature",
    "planet", "skyline", "horizon",
]

CONTRAST_VISUAL_WORDS = [
    "before and after", "split", "side by side", "versus", "against",
    "black and white", "high contrast", "silhouetted", "backlit", "rim light",
    "neon", "dark background", "single accent",
]

MOTION_VISUAL_WORDS = [
    "explosion", "collapse", "rushing", "spinning", "shattering", "colliding",
    "time-lapse", "slow motion", "whip", "racing", "falling", "erupting",
    "transforming", "morphing", "swirling",
]

# Motion intensity defaults per camera motion — used when a scene's motion
# score needs grounding in how the camera itself moves, not just the subject.
CAMERA_MOTION_INTENSITY = {
    "locked-off": 15,
    "slow push-in": 35,
    "slow pull-back": 35,
    "handheld drift": 45,
    "orbit": 60,
    "pan": 45,
    "tilt": 40,
    "crash zoom": 85,
    "whip pan": 90,
    "tracking": 65,
    "dolly": 55,
    "drone rise": 70,
}


def _scene_text(scene: dict) -> str:
    return " ".join(
        str(scene.get(key, ""))
        for key in ("narration", "visual_description", "text_overlay", "environment", "background")
    )


def score_scene_visuals(scene: dict) -> dict:
    """Score one scene dict across all 12 visual psychology dimensions (0-100)."""
    text = _scene_text(scene)
    lower = text.lower()
    jitter = stable_jitter(text)
    motion_intensity = int(scene.get("motion_intensity", 50) or 50)
    camera_motion = str(scene.get("camera_motion", "")).lower()
    camera_kick = CAMERA_MOTION_INTENSITY.get(camera_motion, 40)

    raw = {
        "curiosity": 40 + 14 * min(count_hits(text, CURIOSITY_WORDS), 3) + (8 if "?" in text else 0),
        "mystery": 36 + 15 * min(count_hits(text, MYSTERY_VISUAL_WORDS), 3)
        + (8 if "low-key" in lower or "shadow" in lower else 0),
        "wonder": 36 + 15 * min(count_hits(text, WONDER_VISUAL_WORDS), 3),
        "fear": 30 + 16 * min(count_hits(text, FEAR_WORDS), 3),
        "beauty": 36 + 15 * min(count_hits(text, BEAUTY_VISUAL_WORDS), 3)
        + (6 if "lighting" in lower or "light" in lower else 0),
        "novelty": 38 + 15 * min(count_hits(text, NOVELTY_WORDS), 3),
        "scale": 34 + 16 * min(count_hits(text, SCALE_VISUAL_WORDS), 3),
        "contrast": 36 + 15 * min(count_hits(text, CONTRAST_VISUAL_WORDS), 3),
        "motion": 20 + motion_intensity * 0.45 + camera_kick * 0.35
        + 8 * min(count_hits(text, MOTION_VISUAL_WORDS), 3),
        "satisfaction": 36 + 15 * min(count_hits(text, SATISFACTION_WORDS), 3),
        "humor": 30 + 17 * min(count_hits(text, HUMOR_WORDS), 3),
        "identity": 32 + 16 * min(count_hits(text, IDENTITY_WORDS), 3),
    }
    return {key: clamp(value + jitter) for key, value in raw.items()}


def scene_visual_score(scores: dict) -> int:
    """Single weighted 0-100 Visual Score from the 12 perceptual dimensions."""
    return clamp(
        sum(scores[key] * weight for key, weight in VISUAL_SCORE_WEIGHTS.items()),
        low=0,
        high=100,
    )
