"""AI Cinematic Director — directing layer between script and renderer."""

from __future__ import annotations

from typing import Any

from services.cinematic_director.package import (
    PACKAGE_VERSION,
    apply_cinematic_direction_to_candidate,
    build_cinematic_direction_package,
)
from services.cinematic_director.validate import validate_cinematic_direction
from services.cinematic_director.vocabulary import (
    CAMERA_MOVES,
    COLOR_PALETTES,
    COMPOSITIONS,
    LIGHTING,
    TRANSITIONS,
    palette_for_niche,
)


def direct_candidate(candidate: dict[str, Any], *, script: str = "", niche: str = "") -> dict[str, Any]:
    """Build package, validate, apply onto candidate for existing render path."""
    package = build_cinematic_direction_package(
        candidate,
        script=script or str(candidate.get("script") or ""),
        topic=str(candidate.get("topic") or candidate.get("title") or ""),
        niche=niche or str(candidate.get("niche") or ""),
        platform=str(candidate.get("platform") or "youtube_shorts"),
    )
    try:
        from services.cinematography.director import (
            apply_cinematography_to_visual_scenes,
            build_cinematography_plan,
        )
        from services.cinematography.models import animation_handoff_payload

        working = dict(candidate)
        plan = build_cinematography_plan(working, topic=str(working.get("title") or ""))
        working["cinematography_plan"] = plan.to_dict()
        working["animation_handoff"] = animation_handoff_payload(plan)
        if working.get("visual_package"):
            working["visual_package"] = apply_cinematography_to_visual_scenes(
                working["visual_package"], plan
            )
        candidate = working
    except Exception:  # noqa: BLE001
        pass

    directed = apply_cinematic_direction_to_candidate(candidate, package)
    directed["cinematic_direction_ok"] = bool((package.get("validation") or {}).get("ok"))
    return directed


def direct_context_candidates(context: dict[str, Any]) -> dict[str, Any]:
    """Pipeline-friendly: enrich all candidates in context."""
    candidates = list(context.get("candidates") or [])
    updates = []
    for c in candidates:
        updates.append(direct_candidate(c, niche=str(context.get("niche") or c.get("niche") or "")))
    if updates:
        return {
            "candidates": updates,
            "cinematic_direction_packages": [u.get("cinematic_direction_package") for u in updates],
        }
    return {}
