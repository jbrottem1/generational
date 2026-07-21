"""Creative Performance Lab — experiment contracts (extends Optimization Lab / analytics)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

EXPERIMENT_STATUSES = (
    "draft",
    "variants_ready",
    "awaiting_human_review",
    "awaiting_publishing",
    "awaiting_analytics",
    "evaluating",
    "confirmed_winner",
    "provisional_winner",
    "early_signal",
    "insufficient_data",
    "inconclusive",
    "archived",
)

RESULT_STATUSES = (
    "INSUFFICIENT_DATA",
    "EARLY_SIGNAL",
    "PROVISIONAL_WINNER",
    "CONFIRMED_WINNER",
    "INCONCLUSIVE",
)

CONTROLLED_VARIABLES = (
    "hook_wording",
    "hook_structure",
    "opening_visual",
    "narration_voice",
    "narration_pace",
    "visual_pacing",
    "scene_order",
    "caption_style",
    "music_intensity",
    "thumbnail",
    "title",
    "call_to_action",
    "publish_time",
)

HUMAN_ISSUE_TAGS = (
    "weak_first_three_seconds",
    "robotic_narration",
    "static_visuals",
    "confusing_explanation",
    "weak_payoff",
    "caption_problems",
    "poor_music_choice",
    "thumbnail_weakness",
)


@dataclass
class CreativeExperiment:
    experiment_id: str
    topic: str
    platform: str = "youtube_shorts"
    audience: str = "general_public"
    video_length_sec: int = 45
    number_of_variants: int = 3
    variables_tested: list[str] = field(default_factory=list)
    variables_held_constant: list[str] = field(default_factory=list)
    hypothesis: str = ""
    success_metric: str = "completion_rate_pct"
    minimum_observation_period_hours: int = 48
    status: str = "draft"
    production_ids: list[str] = field(default_factory=list)
    publishing_ids: list[str] = field(default_factory=list)
    final_result: dict[str, Any] = field(default_factory=dict)
    confidence_level: float = 0.0
    exploratory: bool = False
    variants: list[dict[str, Any]] = field(default_factory=list)
    predictions_label: str = "PREDICTION — not real audience results"
    created_at: str = ""
    updated_at: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
