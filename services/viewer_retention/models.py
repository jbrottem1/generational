"""Viewer Retention & Cinematic Excellence — contracts (V2.0)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

# Export gate for this engine — quality always wins over speed.
EXCELLENCE_PASS_THRESHOLD = 98
MAX_POLISH_ROUNDS = 4

HOOK_STYLES_V2 = (
    "question",
    "shock_statistic",
    "contradiction",
    "visual_mystery",
    "impossible_statement",
    "common_myth",
    "immediate_payoff",
    "open_loop",
    "pattern_interrupt",
    "high_energy",
)

CINEMATIC_MOTIONS_V2 = (
    "slow_push",
    "macro_push",
    "orbit",
    "parallax",
    "whip_pan",
    "rack_focus",
    "crash_zoom",
    "dolly",
    "tilt",
    "reveal",
    "tracking",
    "drone_simulation",
    "ken_burns",
    "handheld_documentary",
)

# Map V2 motion labels → existing cinematography vocabulary when possible.
MOTION_TO_LEGACY = {
    "slow_push": "slow_push_in",
    "macro_push": "macro_push_in",
    "orbit": "orbit",
    "parallax": "parallax",
    "whip_pan": "horizontal_pan",
    "rack_focus": "rack_focus",
    "crash_zoom": "macro_push_in",
    "dolly": "slow_push_in",
    "tilt": "vertical_pan",
    "reveal": "reveal",
    "tracking": "tracking",
    "drone_simulation": "establishing_wide",
    "ken_burns": "slow_push_in",
    "handheld_documentary": "tracking",
}

PREFERRED_IMAGE_SOURCES = (
    "NASA",
    "NOAA",
    "ESA",
    "USGS",
    "NIH",
    "government",
    "museum",
    "wikimedia",
    "scientific",
)

QUALITY_DIMENSIONS = (
    "hook",
    "visuals",
    "narration",
    "psychology",
    "retention",
    "sound_design",
    "captions",
    "animation",
    "education",
    "entertainment",
    "seo",
)


@dataclass
class HookCandidate:
    style: str
    text: str
    score: int
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ScenePacing:
    scene_id: str
    duration_sec: float
    pacing_label: str  # cut_2s | cut_3s | dramatic_pause | montage | zoom_rhythm | motion_rhythm
    attention_score: int
    information_density: int
    movement_intensity: int
    importance: int
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CameraDirective:
    scene_id: str
    motion: str
    legacy_movement: str
    intensity: float
    reason: str
    narration_cue: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RetentionCheckpoint:
    at_sec: float
    label: str
    retention_probability: float
    risk: str
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PolishIssue:
    kind: str
    severity: str  # low | medium | high
    scene_id: str = ""
    message: str = ""
    fix: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExcellenceReport:
    """Unified V2 package attached to each candidate."""

    version: str = "2.0.0"
    overall_score: int = 0
    passed: bool = False
    polish_rounds: int = 0
    selected_hook: dict[str, Any] = field(default_factory=dict)
    hook_candidates: list[dict[str, Any]] = field(default_factory=list)
    pacing_plan: list[dict[str, Any]] = field(default_factory=list)
    camera_plan: list[dict[str, Any]] = field(default_factory=list)
    narration_plan: dict[str, Any] = field(default_factory=dict)
    sound_design: dict[str, Any] = field(default_factory=dict)
    caption_plan: dict[str, Any] = field(default_factory=dict)
    visual_ranking: list[dict[str, Any]] = field(default_factory=list)
    retention_curve: list[dict[str, Any]] = field(default_factory=list)
    polish_issues: list[dict[str, Any]] = field(default_factory=list)
    polish_fixes: list[str] = field(default_factory=list)
    quality_scores: dict[str, int] = field(default_factory=dict)
    predictions: dict[str, float] = field(default_factory=dict)
    improvements_vs_baseline: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
