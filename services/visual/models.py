"""Data models for the Visual Intelligence Engine (Cinematic AI Director).

A `ScenePlan` is one fully directed beat of a video — purpose, emotion,
attention level, shot/lens/depth-of-field, lighting, style, motion,
overlays, captions, asset sourcing, AI prompts, and per-scene visual
psychology + predicted retention. A `ThumbnailConcept` is one scored
thumbnail direction. Both are dataclasses that serialize to plain dicts,
because the workflow context (and everything Streamlit touches) speaks
JSON-safe dicts.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

# The components every directed scene must carry (mirrors the Script
# Engine's REQUIRED_VARIANT_COMPONENTS convention — tests assert this tuple).
REQUIRED_SCENE_COMPONENTS = (
    "scene_number",
    "purpose",
    "emotion",
    "length_sec",
    "attention_level",
    "visual_style",
    "narration",
    "visual_description",
    "shot_type",
    "camera_angle",
    "camera_motion",
    "lens_recommendation",
    "depth_of_field",
    "shot_composition",
    "subject_placement",
    "lighting",
    "environment",
    "color_palette",
    "transition_in",
    "transition_out",
    "motion_intensity",
    "motion_recommendation",
    "zoom",
    "background",
    "asset_type",
    "ai_image_prompt",
    "ai_video_prompt",
    "stock_footage_query",
    "overlay",
    "text_overlay",
    "caption_placement",
    "caption_timing",
    "sound_effect",
    "sfx_timing",
    "music_style",
    "broll",
    "thumbnail_candidate",
    "visual_scores",
    "visual_score",
    "predicted_retention",
)


@dataclass
class ScenePlan:
    """One directed scene of the storyboard."""

    scene_number: int
    purpose: str
    emotion: str = ""
    length_sec: float = 0.0
    attention_level: str = "medium"  # high / medium / low — Director's demand on this beat
    visual_style: str = "cinematic"  # style preset key (services/visual/styles.py)
    narration: str = ""
    visual_description: str = ""
    shot_type: str = "medium"  # professional shot vocabulary key (shots.py)
    camera_angle: str = ""
    camera_motion: str = ""
    lens_recommendation: str = ""
    depth_of_field: str = ""
    shot_composition: str = ""
    subject_placement: str = ""
    lighting: str = ""
    environment: str = ""
    color_palette: str = ""
    transition_in: str = "none"
    transition_out: str = "hard cut"
    motion_intensity: int = 50  # 0-100 — drives video-prompt physics + motion report
    motion_recommendation: str = ""
    zoom: str = ""
    background: str = ""
    asset_type: str = "ai_image"  # recommended source adapter key (sources.py)
    ai_image_prompt: str = ""  # base prompt; per-model dialects live in the package
    ai_video_prompt: str = ""
    stock_footage_query: str = ""
    overlay: str = ""
    text_overlay: str = ""
    caption_placement: str = "bottom third, safe zone"
    caption_timing: dict = field(default_factory=dict)  # {"start_sec", "end_sec"}
    sound_effect: str = ""
    sfx_timing: dict = field(default_factory=dict)  # {"at_sec", "cue"}
    music_style: str = ""
    broll: list = field(default_factory=list)
    thumbnail_candidate: bool = False  # frame worth extracting as a thumbnail
    visual_scores: dict = field(default_factory=dict)  # 12 perceptual triggers
    visual_score: int = 0
    predicted_retention: int = 0  # % of viewers predicted still watching at scene end

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ScenePlan":
        known = {key: value for key, value in data.items() if key in cls.__dataclass_fields__}
        return cls(**known)


# The seven dimensions every thumbnail concept is scored on.
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
    focal_subject: str = ""
    eye_direction: str = ""  # where the subject's gaze points the viewer
    emotion: str = ""
    title_overlay: str = ""
    color_strategy: str = ""
    composition: str = ""
    scores: dict = field(default_factory=dict)  # THUMBNAIL_SCORE_KEYS → 0-100
    contrast_score: int = 0
    overall: int = 0
    click_probability_pct: float = 0.0
    # Back-compat aliases (pre-Cinematic-Director field names) — the audio
    # engine and UI read these; keep them mirrored.
    focal_point: str = ""
    text_overlay: str = ""
    color_scheme: str = ""
    expected_ctr_pct: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ThumbnailConcept":
        known = {key: value for key, value in data.items() if key in cls.__dataclass_fields__}
        return cls(**known)
