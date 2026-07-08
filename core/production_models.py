"""Strongly typed production data models for the Media Production Pipeline.

Every engine accepts and returns these structures (as dicts in the workflow
context for Streamlit compatibility). Typed builders and validators live
here so engines stay small and independently testable.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from typing import Any


def _uid(prefix: str = "") -> str:
    return f"{prefix}{uuid.uuid4().hex[:10]}" if prefix else uuid.uuid4().hex[:12]


# --- Stage status (production dashboard) ---

class StageState:
    WAITING = "waiting"
    RUNNING = "running"
    COMPLETED = "completed"
    RETRYING = "retrying"
    FAILED = "failed"


@dataclass
class StageStatus:
    key: str
    label: str
    state: str = StageState.WAITING
    error: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# --- Scene Planning ---

@dataclass
class Scene:
    scene_id: str
    title: str
    duration_sec: float
    narration: str
    visual_description: str
    emotion: str
    camera_movement: str
    transition: str
    on_screen_text: str
    keywords: list
    timing_start: float = 0.0
    timing_end: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


# --- Visual Planning ---

@dataclass
class VisualPrompt:
    scene_id: str
    subject: str
    environment: str
    mood: str
    lighting: str
    camera_angle: str
    camera_movement: str
    animation_style: str
    color_palette: str
    cinematic_direction: str
    prompt_text: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# --- Voice / Narration ---

VOICE_PROFILES = [
    "documentary",
    "educational",
    "storytelling",
    "science",
    "finance",
    "high_energy",
    "calm",
]

VOICE_MODES = ("ai", "recorded", "clone")


@dataclass
class VoiceSettings:
    speaking_speed: float = 1.0
    energy: float = 0.7
    emotion: str = "neutral"
    pitch: float = 1.0
    pause_style: str = "natural"
    pronunciation_overrides: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class VoiceProfile:
    profile_id: str
    name: str
    style: str
    mode: str = "ai"
    settings: VoiceSettings = field(default_factory=VoiceSettings)
    recording_path: str = ""
    project_attachments: list = field(default_factory=list)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["settings"] = self.settings.to_dict()
        return data


@dataclass
class NarrationTrack:
    scene_id: str
    text: str
    duration_sec: float
    mode: str
    profile_id: str
    asset_id: str = ""
    placeholder: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


# --- Assets ---

ASSET_TYPES = (
    "generated_image",
    "generated_video",
    "uploaded_footage",
    "stock_footage",
    "narration",
    "music",
    "sound_effect",
    "subtitle",
    "thumbnail",
)


@dataclass
class Asset:
    asset_id: str
    asset_type: str
    label: str
    path: str = ""
    metadata: dict = field(default_factory=dict)
    reusable: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


# --- Subtitles ---

@dataclass
class SubtitleCue:
    start_sec: float
    end_sec: float
    text: str
    words: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SubtitleTrack:
    format: str
    platform: str
    cues: list
    srt_content: str = ""
    word_level: bool = False

    def to_dict(self) -> dict:
        return {"format": self.format, "platform": self.platform, "cues": self.cues, "srt_content": self.srt_content, "word_level": self.word_level}


# --- Timeline ---

@dataclass
class TimelineClip:
    clip_id: str
    track: str
    start_sec: float
    end_sec: float
    asset_id: str = ""
    label: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Timeline:
    duration_sec: float
    scene_order: list
    narration_clips: list
    visual_clips: list
    subtitle_clips: list
    music_clips: list
    effect_clips: list
    transitions: list

    def to_dict(self) -> dict:
        return asdict(self)


# --- Render Package ---

@dataclass
class RenderPackage:
    package_id: str
    title: str
    duration_sec: float
    scenes: list
    narration_tracks: list
    visual_prompts: list
    assets: list
    subtitles: dict
    timeline: dict
    thumbnail_concept: str
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


# --- Production package (one per approved script) ---

@dataclass
class ProductionPackage:
    content_id: str
    title: str
    script: str
    niche: str
    publish_score: int
    scenes: list = field(default_factory=list)
    visual_prompts: list = field(default_factory=list)
    narration_tracks: list = field(default_factory=list)
    assets: list = field(default_factory=list)
    subtitles: dict = field(default_factory=dict)
    timeline: dict = field(default_factory=dict)
    render_package: dict = field(default_factory=dict)
    queue_status: str = "queued"

    def to_dict(self) -> dict:
        return asdict(self)


def build_production_package(idea: dict, niche: str) -> ProductionPackage:
    return ProductionPackage(
        content_id=_uid("cnt_"),
        title=idea.get("title", "Untitled"),
        script=idea.get("script", ""),
        niche=niche,
        publish_score=idea.get("scores", {}).get("publish", 0),
    )


def stage_statuses_from_steps(steps: list, stage_defs: list) -> list:
    """Map workflow step results to dashboard StageStatus objects."""
    step_map = {s.get("engine", s.get("key", "")): s for s in steps}
    statuses = []
    for key, label in stage_defs:
        step = step_map.get(key, {})
        status = step.get("status", "")
        if status == "succeeded":
            state = StageState.COMPLETED
        elif status == "failed":
            state = StageState.FAILED
        elif status == "skipped":
            state = StageState.WAITING
        else:
            state = StageState.WAITING
        statuses.append(StageStatus(key=key, label=label, state=state, error=step.get("error", "")))
    return [s.to_dict() for s in statuses]
