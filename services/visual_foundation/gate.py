"""Soft QC checklist against Visual Foundation V1 — not a new renderer."""

from __future__ import annotations

from typing import Any

from services.visual_foundation.standards import load_foundation


def review_visual_foundation(candidate: dict[str, Any] | None = None, *, package: dict[str, Any] | None = None) -> dict[str, Any]:
    """Score a production candidate / studio package against the constitution.

    Soft gate: informs Character & World Studio / ops reports. Does not invent pixels.
    """
    cand = dict(candidate or {})
    pkg = dict(package or cand.get("CHARACTER_WORLD_STUDIO_PACKAGE") or cand.get("character_world_studio") or {})
    foundation = load_foundation()
    failures: list[str] = []
    warnings: list[str] = []

    # Style mode
    style_mode = str(
        cand.get("style_mode")
        or (cand.get("constraints") or {}).get("style_mode")
        or foundation.get("default_style_mode")
        or "cinematic_realism"
    )
    if style_mode not in set(foundation.get("style_modes") or []):
        warnings.append(f"undeclared_style_mode:{style_mode}")

    # Cast / continuity
    cast = list(pkg.get("cast") or cand.get("studio_cast") or [])
    if not cast and not cand.get("studio_character_id") and not cand.get("permanent_studio_asset"):
        failures.append("no_recurring_character_reference")
    for h in cast:
        if "stick" in str(h.get("role") or "").lower() and not str(h.get("id") or "").startswith("CHAR-DASH"):
            failures.append("stick_figure_outside_dash_ip")
        if not h.get("silhouette") and not h.get("permanent_ip"):
            warnings.append(f"weak_silhouette_{h.get('id')}")

    # Location living world
    loc = pkg.get("location") if isinstance(pkg.get("location"), dict) else cand.get("studio_location") or {}
    if isinstance(loc, dict):
        if not loc.get("ambient_life") and not loc.get("detail_dressing"):
            failures.append("empty_or_unpopulated_environment")
        if loc.get("forbid_empty") is False:
            warnings.append("location_allows_empty")
    else:
        warnings.append("no_studio_location")

    # Scene liveliness
    scenes = list(
        pkg.get("scene_bindings")
        or (cand.get("visual_package") or {}).get("scenes")
        or cand.get("scenes")
        or []
    )
    lifeless = 0
    for s in scenes:
        if not isinstance(s, dict):
            continue
        if not s.get("studio_expression") and not s.get("emotion") and not s.get("studio_character_id"):
            lifeless += 1
    if scenes and lifeless == len(scenes):
        failures.append("lifeless_facial_or_unassigned_scenes")

    # Forbidden keywords in briefs / mocks
    blob = " ".join(
        [
            str(cand.get("topic") or ""),
            str(cand.get("visual_style") or ""),
            json_safe(cand.get("render_package")),
        ]
    ).lower()
    for bad in ("powerpoint", "clip art", "stick figure host", "solid color bed", "ken burns only"):
        if bad in blob:
            failures.append(f"forbidden_visual_language:{bad.replace(' ', '_')}")

    questions = {
        "viewers_would_recognize_characters": bool(cast) and "no_recurring_character_reference" not in failures,
        "audience_would_remember_world": "empty_or_unpopulated_environment" not in failures,
        "every_scene_feels_alive": lifeless == 0 and bool(scenes),
        "feels_like_original_series": False,
        "want_another_episode_for_world": bool(loc.get("id")) if isinstance(loc, dict) else False,
        "cinematic_realism_not_photoreal_uncanny": style_mode in {"cinematic_realism", "stylized_realism", "realistic"},
    }
    questions["feels_like_original_series"] = (
        questions["viewers_would_recognize_characters"]
        and questions["audience_would_remember_world"]
        and questions["every_scene_feels_alive"]
        and not failures
    )

    approved = not failures
    return {
        "foundation_version": foundation.get("version") or "1.0.0",
        "visual_target": foundation.get("visual_target"),
        "style_mode": style_mode,
        "approved": approved,
        "decision": "APPROVE" if approved else "REJECT",
        "failures": failures,
        "warnings": warnings,
        "questions": questions,
        "reject_catalog": list((foundation.get("quality_gates") or {}).get("reject_if") or []),
        "philosophy": {
            "no_new_renderer": True,
            "no_pipeline_redesign": True,
            "feature_film_cinematic_realism": True,
        },
    }


def json_safe(value: Any) -> str:
    try:
        import json

        return json.dumps(value, default=str)[:2000]
    except Exception:  # noqa: BLE001
        return str(value)[:500]
