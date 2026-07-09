"""Data models for the Visual Intelligence Engine.

A `ScenePlan` is one fully art-directed beat of a video — purpose, emotion,
camera, lighting, environment, motion, overlays, captions, and per-scene
visual psychology scores. A `ThumbnailConcept` is one scored thumbnail
direction. Both are dataclasses that serialize to plain dicts, because the
workflow context (and everything Streamlit touches) speaks JSON-safe dicts.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

# The components every planned scene must carry (mirrors the Script Engine's
# REQUIRED_VARIANT_COMPONENTS convention — tests assert against this tuple).
REQUIRED_SCENE_COMPONENTS = (
    "scene_number",
    "purpose",
    "emotion",
    "length_sec",
    "narration",
    "visual_description",
    "camera_angle",
    "camera_motion",
    "shot_composition",
    "subject_placement",
    "lighting",
    "environment",
    "color_palette",
    "transition_in",
    "transition_out",
    "motion_intensity",
    "zoom",
    "background",
    "overlay",
    "text_overlay",
    "caption_timing",
    "sound_effect",
    "music_style",
    "broll",
    "visual_scores",
    "visual_score",
)


@dataclass
class ScenePlan:
    """One art-directed scene of the storyboard."""

    scene_number: int
    purpose: str
    emotion: str = ""
    length_sec: float = 0.0
    narration: str = ""
    visual_description: str = ""
    camera_angle: str = ""
    camera_motion: str = ""
    shot_composition: str = ""
    subject_placement: str = ""
    lighting: str = ""
    environment: str = ""
    color_palette: str = ""
    transition_in: str = "none"
    transition_out: str = "hard cut"
    motion_intensity: int = 50  # 0-100 — drives video-prompt physics + motion report
    zoom: str = ""
    background: str = ""
    overlay: str = ""
    text_overlay: str = ""
    caption_timing: dict = field(default_factory=dict)  # {"start_sec", "end_sec"}
    sound_effect: str = ""
    music_style: str = ""
    broll: list = field(default_factory=list)
    visual_scores: dict = field(default_factory=dict)  # 12 visual psychology dims
    visual_score: int = 0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ScenePlan":
        known = {key: value for key, value in data.items() if key in cls.__dataclass_fields__}
        return cls(**known)


# The eight dimensions every thumbnail concept is scored on.
THUMBNAIL_SCORE_KEYS = (
    "curiosity",
    "readability",
    "contrast",
    "facial_focus",
    "object_focus",
    "color",
    "emotion",
)


@dataclass
class ThumbnailConcept:
    """One scored thumbnail direction for an idea."""

    concept_id: str
    archetype: str
    label: str
    description: str = ""
    focal_point: str = ""
    text_overlay: str = ""
    color_scheme: str = ""
    composition: str = ""
    scores: dict = field(default_factory=dict)  # THUMBNAIL_SCORE_KEYS → 0-100
    overall: int = 0
    expected_ctr_pct: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ThumbnailConcept":
        known = {key: value for key, value in data.items() if key in cls.__dataclass_fields__}
        return cls(**known)
