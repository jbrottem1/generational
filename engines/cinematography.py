"""Cinematography Engine — professionally directed camera motion.

Receives completed scenes from Evidence & Visual Intelligence.
Chooses movement that reinforces narration (never random).
Outputs camera plan, timeline, motion graph, focus, easing, pacing,
and attention score — passed directly to the Animation Engine.
"""

from __future__ import annotations

from core.log import get_logger, log_event
from engines.base import Engine
from services.cinematography.director import (
    apply_cinematography_to_visual_scenes,
    build_cinematography_plan,
)
from services.cinematography.models import animation_handoff_payload

logger = get_logger(__name__)


class CinematographyEngine(Engine):
    key = "cinematography"
    label = "Cinematography"
    icon = "🎬"
    description = (
        "Direct camera angle, framing, zoom, pan, parallax, easing, and transitions "
        "so every educational scene moves like a documentary — then hand off to Animation."
    )
    version = "1.0.0"

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        candidates = list(context.get("candidates") or [])
        if not candidates:
            return {}

        plans: list[dict] = []
        for candidate in candidates:
            plan = build_cinematography_plan(
                candidate,
                topic=str(candidate.get("title") or context.get("subject") or ""),
            )
            data = plan.to_dict()
            candidate["cinematography_plan"] = data
            candidate["animation_handoff"] = animation_handoff_payload(plan)
            candidate["cinematography_attention_score"] = plan.overall_attention_score

            # Enrich visual package scenes when present (additive)
            if candidate.get("visual_package"):
                candidate["visual_package"] = apply_cinematography_to_visual_scenes(
                    candidate["visual_package"], plan
                )

            plans.append(data)

        avg = int(
            sum(p.get("overall_attention_score") or 0 for p in plans) / max(1, len(plans))
        )
        summary = {
            "candidates": len(candidates),
            "scenes_directed": sum(len(p.get("scenes") or []) for p in plans),
            "average_attention_score": avg,
            "animation_ready": True,
        }
        log_event(
            logger,
            "cinematography.completed",
            candidates=len(candidates),
            scenes=summary["scenes_directed"],
            attention=avg,
        )
        return {
            "candidates": candidates,
            "cinematography_summary": summary,
            "cinematography_plans": plans,
            "animation_handoff": candidates[0].get("animation_handoff") if candidates else {},
        }
