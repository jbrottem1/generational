"""Visual psychology heuristics — the Director's attention model.

Where `engines/psychology.py` scores what a concept *says*, this module
scores what each frame will *do to a scrolling viewer*: twelve perceptual
attention triggers plus a per-scene **predicted retention** — the Director's
estimate of how much of the audience is still watching when the scene ends.

The twelve triggers the Director optimizes for:

Curiosity · Pattern Interrupts · Contrast · Novelty · Human Faces ·
Eye Contact · Motion · Scale · Speed · Emotional Color Theory ·
Negative Space · Visual Hierarchy

Scoring is deterministic text-feature analysis (word-bank hits, scene
structure, camera/shot metadata) so it is fast, free, reproducible in every
mode, and fully unit-testable without an API key. Swapping in a learned
vision model later only requires changing `score_scene_visuals()` and
`predict_scene_retention()` — the report shapes stay the same.
"""

from __future__ import annotations

from engines.heuristics import (
    CURIOSITY_WORDS,
    NOVELTY_WORDS,
    clamp,
    count_hits,
    stable_jitter,
)

VISUAL_DIMENSION_KEYS = [
    "curiosity",
    "pattern_interrupt",
    "contrast",
    "novelty",
    "human_faces",
    "eye_contact",
    "motion",
    "scale",
    "speed",
    "emotional_color",
    "negative_space",
    "visual_hierarchy",
]

VISUAL_DIMENSION_LABELS = {
    "curiosity": "Curiosity",
    "pattern_interrupt": "Pattern Interrupt",
    "contrast": "Contrast",
    "novelty": "Novelty",
    "human_faces": "Human Faces",
    "eye_contact": "Eye Contact",
    "motion": "Motion",
    "scale": "Scale",
    "speed": "Speed",
    "emotional_color": "Emotional Color Theory",
    "negative_space": "Negative Space",
    "visual_hierarchy": "Visual Hierarchy",
}

# How much each perceptual trigger contributes to a scene's Visual Score
# (0-100). Data, not code — the Learning Engine can retune these from real
# retention curves without touching scoring logic. Sum == 1.0.
# Curiosity, motion, and pattern interrupts carry the most weight because
# they are the strongest scroll-stop signals in short-form feeds; faces and
# eye contact follow (the human visual system prioritizes them reflexively).
VISUAL_SCORE_WEIGHTS = {
    "curiosity": 0.13,
    "pattern_interrupt": 0.11,
    "contrast": 0.10,
    "novelty": 0.09,
    "human_faces": 0.09,
    "eye_contact": 0.07,
    "motion": 0.11,
    "scale": 0.07,
    "speed": 0.07,
    "emotional_color": 0.06,
    "negative_space": 0.05,
    "visual_hierarchy": 0.05,
}

# Visual-specific word banks — they describe what appears ON SCREEN, not what
# the narration argues. The perceptual complement to engines/heuristics.py.
PATTERN_INTERRUPT_VISUAL_WORDS = [
    "whip", "hard cut", "jarring", "reversal", "freeze", "snap", "sudden",
    "glitch", "smash cut", "record scratch", "dutch", "tilted", "flip",
]

CONTRAST_VISUAL_WORDS = [
    "before and after", "split", "side by side", "versus", "against",
    "black and white", "high contrast", "silhouetted", "backlit", "rim light",
    "neon", "dark background", "single accent",
]

FACE_VISUAL_WORDS = [
    "face", "eyes", "expression", "reaction", "gasp", "smile", "brow",
    "close-up of a person", "portrait", "stunned", "staring", "mouth",
]

EYE_CONTACT_VISUAL_WORDS = [
    "eye contact", "direct-to-camera", "direct address", "looking at the lens",
    "into the camera", "locks eyes", "direct eye", "facing the viewer",
    "addresses the lens", "direct-to-viewer",
]

MOTION_VISUAL_WORDS = [
    "explosion", "collapse", "rushing", "spinning", "shattering", "colliding",
    "time-lapse", "slow motion", "whip", "racing", "falling", "erupting",
    "transforming", "morphing", "swirling",
]

SCALE_VISUAL_WORDS = [
    "massive", "tiny", "towering", "microscopic", "giant", "colossal",
    "aerial", "bird's-eye", "wide shot", "dwarfed", "enormous", "miniature",
    "planet", "skyline", "horizon", "drone",
]

SPEED_VISUAL_WORDS = [
    "fast", "rapid", "instant", "hyperlapse", "blur", "streaking", "velocity",
    "accelerating", "blink", "flash", "in seconds", "crash zoom",
]

EMOTIONAL_COLOR_WORDS = [
    "golden", "warm", "amber", "crimson", "cold blue", "teal", "neon",
    "desaturated", "saturated", "glow", "sunrise", "candlelight", "palette",
]

NEGATIVE_SPACE_WORDS = [
    "negative space", "minimal", "empty", "isolated", "clean background",
    "single subject", "vast emptiness", "alone in frame", "whitespace",
    "defocused backdrop",
]

HIERARCHY_WORDS = [
    "rule of thirds", "center", "leading", "focal", "layered", "foreground",
    "framing", "diagonal", "symmetrical", "eye toward", "hero framing",
]

# Motion intensity contribution per camera motion — grounds the motion score
# in how the camera itself moves, not just the subject.
CAMERA_MOTION_INTENSITY = {
    "locked-off": 15,
    "slow push-in": 35,
    "slow pull-back": 35,
    "micro slider": 30,
    "handheld drift": 45,
    "first-person handheld": 60,
    "slow lateral drift": 30,
    "orbit": 60,
    "pan": 45,
    "tilt": 40,
    "crash zoom": 85,
    "whip pan": 90,
    "tracking": 65,
    "dolly": 55,
    "drone rise": 70,
    "slow-motion settle": 50,
    "hyperlapse": 95,
}

# Scene purposes engineered as deliberate pattern interrupts.
INTERRUPT_PURPOSES = {"hook", "pattern_interrupt"}


def _scene_text(scene: dict) -> str:
    return " ".join(
        str(scene.get(key, ""))
        for key in (
            "narration",
            "visual_description",
            "text_overlay",
            "environment",
            "background",
            "shot_composition",
            "subject_placement",
            "lighting",
            "color_palette",
            "camera_angle",
        )
    )


def score_scene_visuals(scene: dict) -> dict:
    """Score one scene dict across all 12 perceptual attention triggers (0-100)."""
    text = _scene_text(scene)
    jitter = stable_jitter(text)
    motion_intensity = int(scene.get("motion_intensity", 50) or 50)
    camera_motion = str(scene.get("camera_motion", "")).lower()
    camera_kick = CAMERA_MOTION_INTENSITY.get(camera_motion, 40)
    purpose = scene.get("purpose", "story_beat")

    raw = {
        "curiosity": 40 + 14 * min(count_hits(text, CURIOSITY_WORDS), 3) + (8 if "?" in text else 0),
        "pattern_interrupt": 30 + 14 * min(count_hits(text, PATTERN_INTERRUPT_VISUAL_WORDS), 3)
        + (20 if purpose in INTERRUPT_PURPOSES else 0),
        "contrast": 36 + 15 * min(count_hits(text, CONTRAST_VISUAL_WORDS), 3),
        "novelty": 38 + 15 * min(count_hits(text, NOVELTY_WORDS), 3),
        "human_faces": 30 + 15 * min(count_hits(text, FACE_VISUAL_WORDS), 3),
        "eye_contact": 28 + 18 * min(count_hits(text, EYE_CONTACT_VISUAL_WORDS), 3),
        "motion": 20 + motion_intensity * 0.45 + camera_kick * 0.35
        + 8 * min(count_hits(text, MOTION_VISUAL_WORDS), 3),
        "scale": 34 + 16 * min(count_hits(text, SCALE_VISUAL_WORDS), 3),
        "speed": 26 + 14 * min(count_hits(text, SPEED_VISUAL_WORDS), 3) + motion_intensity * 0.2,
        "emotional_color": 34 + 15 * min(count_hits(text, EMOTIONAL_COLOR_WORDS), 3),
        "negative_space": 32 + 16 * min(count_hits(text, NEGATIVE_SPACE_WORDS), 3),
        "visual_hierarchy": 34 + 15 * min(count_hits(text, HIERARCHY_WORDS), 3),
    }
    return {key: clamp(value + jitter) for key, value in raw.items()}


def scene_visual_score(scores: dict) -> int:
    """Single weighted 0-100 Visual Score from the 12 perceptual triggers."""
    return clamp(
        sum(scores[key] * weight for key, weight in VISUAL_SCORE_WEIGHTS.items()),
        low=0,
        high=100,
    )


# --- Predicted retention -------------------------------------------------------

# Baseline audience decay per scene position (short-form retention curves
# drop steepest right after the hook, then flatten). Data, not code.
POSITION_DECAY_PER_SCENE = 4.0
IDEAL_SCENE_SEC = 6.0
LENGTH_PENALTY_PER_SEC = 2.5


def predict_scene_retention(
    scene: dict,
    *,
    scene_index: int,
    total_scenes: int,
    attention: "dict | None" = None,
) -> int:
    """Predict % of viewers still watching at the END of this scene (0-100).

    Blends the scene's own visual pull, its position in the video (natural
    decay), its length (overlong scenes bleed viewers), and — when the
    Attention Graph has run — the concept-level hook and retention signals.
    """
    visual_score = int(scene.get("visual_score") or scene_visual_score(score_scene_visuals(scene)))
    base = 96 - scene_index * POSITION_DECAY_PER_SCENE

    # Strong visuals slow the decay; weak visuals accelerate it.
    visual_adjust = (visual_score - 50) * 0.25

    length = float(scene.get("length_sec", IDEAL_SCENE_SEC) or IDEAL_SCENE_SEC)
    length_penalty = max(0.0, length - IDEAL_SCENE_SEC * 1.5) * LENGTH_PENALTY_PER_SEC

    interrupt_bonus = 3 if scene.get("purpose") in INTERRUPT_PURPOSES else 0

    attention_adjust = 0.0
    if attention:
        scores = attention.get("scores", {})
        hook = scores.get("first_3_second_hook", 50)
        rewatch = scores.get("rewatch_probability", 50)
        if scene_index == 0:
            attention_adjust = (hook - 50) * 0.2
        else:
            attention_adjust = (rewatch - 50) * 0.1

    raw = base + visual_adjust - length_penalty + interrupt_bonus + attention_adjust
    return clamp(raw, low=5, high=98)


def attention_level_for(retention: int) -> str:
    """Bucket a predicted retention into the Director's attention level."""
    if retention >= 75:
        return "high"
    if retention >= 50:
        return "medium"
    return "low"
