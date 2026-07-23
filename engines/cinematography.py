"""Cinematography Engine — professionally directed camera motion.

Receives completed scenes from Evidence & Visual Intelligence.
Chooses movement that reinforces narration (never random).
Outputs camera plan, timeline, motion graph, focus, easing, pacing,
and attention score — then Virtual Film Director stamps the shot plan
consumed by the Animation Engine.
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
    version = "1.1.0"

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        candidates = list(context.get("candidates") or [])
        if not candidates:
            return {}

        # AI Cinematic Director layer (service façade — not a new render engine)
        try:
            from services.cinematic_director import direct_candidate

            directed = []
            for candidate in candidates:
                directed.append(
                    direct_candidate(
                        candidate,
                        niche=str(context.get("niche") or candidate.get("niche") or ""),
                    )
                )
            candidates = directed
        except Exception:  # noqa: BLE001
            pass

        plans: list[dict] = []
        final_candidates: list[dict] = []
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            # Prefer package already attached by cinematic director; still ensure cine plan
            if isinstance(candidate.get("cinematography_plan"), dict):
                data = candidate["cinematography_plan"]
            else:
                plan = build_cinematography_plan(
                    candidate,
                    topic=str(candidate.get("title") or context.get("subject") or ""),
                )
                data = plan.to_dict()
                candidate["cinematography_plan"] = data
                candidate["animation_handoff"] = animation_handoff_payload(plan)
                candidate["cinematography_attention_score"] = plan.overall_attention_score

                if candidate.get("visual_package"):
                    candidate["visual_package"] = apply_cinematography_to_visual_scenes(
                        candidate["visual_package"], plan
                    )
            plans.append(data)

            # Virtual Film Director — directs ABOVE Animation Engine (no new renderer)
            try:
                from services.virtual_film_director import direct_candidate as vfd_direct

                candidate = vfd_direct(
                    candidate,
                    topic=str(
                        candidate.get("topic")
                        or candidate.get("title")
                        or context.get("subject")
                        or ""
                    ),
                    production_id=str(context.get("production_id") or ""),
                    write=True,
                )
            except Exception:  # noqa: BLE001
                pass

            # Character & World Studio — living universe cast + sets
            try:
                from services.character_world_studio import studio_place_candidate

                candidate = studio_place_candidate(
                    candidate,
                    topic=str(
                        candidate.get("topic")
                        or candidate.get("title")
                        or context.get("subject")
                        or ""
                    ),
                    production_id=str(context.get("production_id") or ""),
                    write=True,
                )
            except Exception:  # noqa: BLE001
                pass
            final_candidates.append(candidate)

        candidates = final_candidates
        avg = int(
            sum(p.get("overall_attention_score") or 0 for p in plans if isinstance(p, dict))
            / max(1, len(plans))
        )
        scenes_directed = sum(len(p.get("scenes") or []) for p in plans)
        vfd_count = sum(1 for c in candidates if c.get("directed_by_vfd"))
        log_event(
            logger,
            "cinematography.completed",
            candidates=len(candidates),
            scenes=scenes_directed,
            attention=avg,
            vfd=vfd_count,
        )
        return {
            "candidates": candidates,
            "cinematography_summary": {
                "candidates": len(candidates),
                "scenes_directed": scenes_directed,
                "average_attention_score": avg,
                "animation_ready": True,
                "virtual_film_director": vfd_count,
            },
            "cinematography_plans": plans,
            "cinematography_attention_score": avg,
            "cinematic_direction_packages": [
                c.get("cinematic_direction_package") for c in candidates if c.get("cinematic_direction_package")
            ],
            "virtual_film_director_packages": [
                c.get("VIRTUAL_FILM_DIRECTOR_PACKAGE") for c in candidates if c.get("VIRTUAL_FILM_DIRECTOR_PACKAGE")
            ],
            "animation_handoff": candidates[0].get("animation_handoff") if candidates else {},
        }
