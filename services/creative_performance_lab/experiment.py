"""Create and manage Creative Performance Lab experiments."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from services.creative_performance_lab.models import CONTROLLED_VARIABLES, CreativeExperiment
from services.creative_performance_lab.store import load_experiment, save_experiment


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_experiment(
    *,
    topic: str,
    platform: str = "youtube_shorts",
    audience: str = "general_public",
    video_length_sec: int = 45,
    variables_tested: list[str] | None = None,
    variables_held_constant: list[str] | None = None,
    hypothesis: str = "",
    success_metric: str = "completion_rate_pct",
    minimum_observation_period_hours: int = 48,
    number_of_variants: int = 3,
    exploratory: bool = False,
    meta: dict | None = None,
) -> dict[str, Any]:
    tested = list(variables_tested or ["hook_structure"])
    for v in tested:
        if v not in CONTROLLED_VARIABLES:
            raise ValueError(f"Unknown variable '{v}'. Allowed: {CONTROLLED_VARIABLES}")
    if len(tested) > 1 and not exploratory:
        raise ValueError("Controlled experiments test one primary variable unless exploratory=True")

    held = list(
        variables_held_constant
        or [
            "core_factual_content",
            "approximate_runtime",
            "narrator_voice",
            "music_style",
            "caption_style",
            "overall_visual_identity",
            "call_to_action",
            "export_settings",
        ]
    )
    exp = CreativeExperiment(
        experiment_id=f"cpl_{uuid.uuid4().hex[:12]}",
        topic=topic,
        platform=platform,
        audience=audience,
        video_length_sec=int(video_length_sec),
        number_of_variants=int(number_of_variants),
        variables_tested=tested,
        variables_held_constant=held,
        hypothesis=hypothesis
        or f"Changing {tested[0]} improves {success_metric} on {platform} for '{topic}'.",
        success_metric=success_metric,
        minimum_observation_period_hours=int(minimum_observation_period_hours),
        status="draft",
        exploratory=bool(exploratory),
        created_at=_now(),
        updated_at=_now(),
        meta=dict(meta or {}),
    )
    data = exp.to_dict()
    save_experiment(data)
    return data


def update_experiment(experiment_id: str, **patches: Any) -> dict[str, Any]:
    data = load_experiment(experiment_id)
    if not data:
        raise FileNotFoundError(experiment_id)
    data.update(patches)
    data["updated_at"] = _now()
    save_experiment(data)
    return data
