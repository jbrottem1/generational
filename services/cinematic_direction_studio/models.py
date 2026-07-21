"""Frozen vocabulary — Cinematic Direction Studio.

Not an animation engine. Not a renderer.
Directs every shot before rendering begins.
"""

from __future__ import annotations

PACKAGE_TYPE = "DIRECTOR_PACKAGE"
EPISODE_PACKAGE_TYPE = "EPISODE_DIRECTOR_PACKAGE"
PACKAGE_VERSION = "1.0.0"
ENGINE_ID = "cinematic_direction_studio"
LIBRARY_VERSION = "1.0.0"

SHOT_TYPES = (
    "establishing",
    "wide",
    "medium",
    "close_up",
    "extreme_close_up",
    "tracking",
    "follow",
    "orbit",
    "over_the_shoulder",
    "pov",
    "reaction",
    "cutaway",
    "insert",
)

# Emotion → camera language
EMOTION_CAMERA: dict[str, dict[str, str]] = {
    "hope": {"movement": "slow_push_in", "true_motion": "push_in", "shot": "close_up"},
    "discovery": {"movement": "orbit_reveal", "true_motion": "orbit", "shot": "orbit"},
    "conversation": {"movement": "over_the_shoulder", "true_motion": "handheld", "shot": "over_the_shoulder"},
    "reflection": {"movement": "slow_dolly", "true_motion": "pull_out", "shot": "medium"},
    "teaching": {"movement": "tracking_walk_and_talk", "true_motion": "tracking", "shot": "tracking"},
    "curiosity": {"movement": "orbit_reveal", "true_motion": "orbit", "shot": "medium"},
    "understanding": {"movement": "slow_push_in", "true_motion": "push_in", "shot": "close_up"},
    "wonder": {"movement": "orbit_reveal", "true_motion": "orbit", "shot": "wide"},
    "inspiration": {"movement": "slow_push_in", "true_motion": "push_in", "shot": "close_up"},
    "resolution": {"movement": "slow_dolly", "true_motion": "pull_out", "shot": "medium"},
    "urgency": {"movement": "follow", "true_motion": "tracking", "shot": "follow"},
    "mystery": {"movement": "slow_dolly", "true_motion": "orbit", "shot": "medium"},
    "comfort": {"movement": "slow_push_in", "true_motion": "push_in", "shot": "medium"},
    "scientific": {"movement": "tracking_walk_and_talk", "true_motion": "tracking", "shot": "tracking"},
    "focus": {"movement": "slow_push_in", "true_motion": "push_in", "shot": "medium"},
    "joy": {"movement": "orbit_reveal", "true_motion": "orbit", "shot": "medium"},
    "awe": {"movement": "orbit_reveal", "true_motion": "orbit", "shot": "wide"},
}

EMOTIONAL_ARC = (
    "curiosity",
    "understanding",
    "wonder",
    "reflection",
    "inspiration",
    "resolution",
)

LIGHTING_INTENTS = (
    "warm",
    "hopeful",
    "scientific",
    "mysterious",
    "comforting",
    "urgent",
)

LIGHTING_TO_MOOD = {
    "warm": "golden_hour",
    "hopeful": "golden_hour",
    "scientific": "clinical_warm",
    "mysterious": "moonlight",
    "comforting": "soft_daylight",
    "urgent": "cinematic_contrast",
}

TRANSITION_STYLES = (
    "cut",
    "match_cut",
    "dissolve",
    "motivated_whip",
    "hold_then_cut",
    "L_cut",
    "J_cut",
)

REJECT_REASONS = (
    "camera_moves_without_purpose",
    "actors_move_mechanically",
    "editing_feels_random",
    "emotion_unclear",
    "shots_repeat",
    "identical_framing_every_scene",
)
