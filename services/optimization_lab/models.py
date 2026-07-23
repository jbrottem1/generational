"""Autonomous Optimization & Experimentation — contracts (V4.0)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

OPTIMIZATION_PASS_THRESHOLD = 98
DEFAULT_VARIANT_COUNT = 5
MAX_REVISION_ROUNDS = 4
VARIANT_LABELS = ("A", "B", "C", "D", "E")

SCORE_DIMENSIONS = (
    "hook_quality",
    "psychology",
    "retention",
    "educational_value",
    "entertainment",
    "seo",
    "visual_quality",
    "narration",
    "professional_appearance",
    "platform_readiness",
)

VARIANT_AXES = (
    "hook",
    "narration",
    "scene_order",
    "visual_style",
    "music",
    "camera_movement",
    "caption_style",
    "thumbnail",
    "title",
    "description",
    "seo",
)


@dataclass
class OptimizationPackage:
    version: str = "4.0.0"
    overall_score: int = 0
    passed: bool = False
    revision_rounds: int = 0
    variants: list[dict[str, Any]] = field(default_factory=list)
    leaderboard: list[dict[str, Any]] = field(default_factory=list)
    winner: dict[str, Any] = field(default_factory=dict)
    critique: dict[str, Any] = field(default_factory=dict)
    revisions: list[dict[str, Any]] = field(default_factory=list)
    predictions: dict[str, Any] = field(default_factory=dict)
    knowledge_applied: list[dict[str, Any]] = field(default_factory=list)
    experiment_id: str = ""
    human_review: dict[str, Any] = field(default_factory=dict)
    improvements_vs_baseline: dict[str, float] = field(default_factory=dict)
    lessons_learned: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
