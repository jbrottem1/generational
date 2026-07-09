"""Data models and contracts for the Render & Video Production Engine.

Everything the renderer plans is JSON-safe (dataclasses that serialize to
plain dicts), matching every other subsystem. The models here are the
render-side contract: the output format spec, timeline segments, the
render job lifecycle, and the render package version pin so downstream
consumers (Publishing, Agent 7) can detect format changes.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

# Contract version for the Agent 6 render package. Distinct from the
# planning-layer render package inside visual_package (version "1.0") —
# this is the *production* render package written to
# ContentPackage.render_package.
RENDER_PACKAGE_VERSION = "2.0"

RENDER_ENGINE_VERSION = "1.0.0"

# Platforms the vertical short-form output targets.
SUPPORTED_PLATFORMS = (
    "youtube_shorts",
    "tiktok",
    "instagram_reels",
    "facebook_reels",
)

# The one output format this version produces: 9:16 vertical MP4.
OUTPUT_FORMAT = {
    "aspect_ratio": "9:16",
    "resolution": {"width": 1080, "height": 1920},
    "container": "mp4",
    "video_codec": "h264",
    "audio_codec": "aac",
    "fps": 30,
    "orientation": "vertical",
    "platforms": list(SUPPORTED_PLATFORMS),
}

# Sensible runtime window for short-form vertical video (seconds).
MIN_RUNTIME_SEC = 5.0
MAX_RUNTIME_SEC = 180.0


class RenderStatus:
    """Outcome vocabulary for render planning, validation, and mock renders.

    Mirrors the orchestrator's StageStatus so reports compose cleanly.
    """

    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class RenderJobStatus:
    """Lifecycle of one render job."""

    QUEUED = "queued"
    PLANNING = "planning"
    RENDERING = "rendering"
    COMPLETE = "complete"
    FAILED = "failed"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# Every timeline segment carries these components (tests assert this tuple).
TIMELINE_SEGMENT_FIELDS = (
    "scene_id",
    "start_time",
    "end_time",
    "duration",
    "narration_reference",
    "visual_reference",
    "caption_reference",
    "audio_reference",
    "transition_in",
    "transition_out",
    "motion_effect",
    "overlay_text",
    "render_status",
)


@dataclass
class TimelineSegment:
    """One renderable segment of the video timeline (times in seconds)."""

    scene_id: int
    start_time: float = 0.0
    end_time: float = 0.0
    duration: float = 0.0
    narration_reference: str = ""
    visual_reference: str = ""
    caption_reference: str = ""
    audio_reference: str = ""
    transition_in: str = "cut"
    transition_out: str = "cut"
    motion_effect: str = "static"
    overlay_text: str = ""
    render_status: str = "planned"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "TimelineSegment":
        known = {key: value for key, value in data.items() if key in cls.__dataclass_fields__}
        return cls(**known)


# Every scene render plan carries these components (tests assert this tuple).
SCENE_RENDER_PLAN_FIELDS = (
    "scene_id",
    "visual_asset_type",
    "image_prompt",
    "video_prompt",
    "stock_footage_query",
    "user_footage_slot",
    "avatar_footage_slot",
    "reaction_footage_slot",
    "camera_movement",
    "effect",
    "text_overlays",
    "caption_placement",
    "sound_cues",
    "narration",
    "duration_sec",
    "resolved_asset",
)


@dataclass
class RenderJob:
    """One render request through its lifecycle — queued to complete/failed."""

    job_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    title: str = ""
    status: str = RenderJobStatus.QUEUED
    created_at: str = field(default_factory=_now_iso)
    started_at: str = ""
    finished_at: str = ""
    progress_pct: int = 0
    warnings: list = field(default_factory=list)
    log: list = field(default_factory=list)
    output: dict = field(default_factory=dict)

    def advance(self, status: str, message: str = "", progress_pct: "int | None" = None) -> None:
        """Move the job to a new lifecycle state and record it in the log."""
        self.status = status
        if progress_pct is not None:
            self.progress_pct = progress_pct
        if status == RenderJobStatus.PLANNING and not self.started_at:
            self.started_at = _now_iso()
        if status in (RenderJobStatus.COMPLETE, RenderJobStatus.FAILED):
            self.finished_at = _now_iso()
            self.progress_pct = 100 if status == RenderJobStatus.COMPLETE else self.progress_pct
        self.log.append({"at": _now_iso(), "status": status, "message": message})

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "RenderJob":
        known = {key: value for key, value in data.items() if key in cls.__dataclass_fields__}
        return cls(**known)
