"""Quality gates — reject placeholder universes."""

from __future__ import annotations

from typing import Any

from services.character_world_studio.models import STYLE_IDENTITY


def review_studio_package(package: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    warnings: list[str] = []
    questions = {
        "viewers_would_recognize_characters": False,
        "audience_would_remember_world": False,
        "want_another_episode_for_characters": False,
        "every_scene_feels_alive": False,
        "feels_like_original_series": False,
    }

    cast = list(package.get("cast") or [])
    location = package.get("location") if isinstance(package.get("location"), dict) else {}
    plates = package.get("character_plates") if isinstance(package.get("character_plates"), dict) else {}
    scenes = list(package.get("scene_bindings") or [])
    style = package.get("visual_identity") or STYLE_IDENTITY

    if not cast:
        failures.append("no_cast")
    else:
        for h in cast:
            if not h.get("facial_range") or not h.get("signature_clothing") or not h.get("silhouette"):
                failures.append(f"incomplete_host_{h.get('id')}")
            if "stick" in str(h.get("role") or "").lower():
                failures.append("stick_figure_host_rejected")
        questions["viewers_would_recognize_characters"] = not any("incomplete_host" in f for f in failures)
        questions["want_another_episode_for_characters"] = len(cast) >= 1 and bool(cast[0].get("personality"))

    if not location.get("id") or not location.get("ambient_life") or not location.get("detail_dressing"):
        failures.append("empty_or_generic_location")
    else:
        questions["audience_would_remember_world"] = True

    if not plates:
        failures.append("missing_character_plates")
    else:
        for cid, path in plates.items():
            if not path:
                failures.append(f"empty_plate_{cid}")

    if not scenes:
        warnings.append("no_scene_bindings")
    else:
        lifeless = 0
        for s in scenes:
            if not s.get("studio_character_id") or not s.get("studio_expression"):
                lifeless += 1
        if lifeless:
            failures.append("expressionless_or_unassigned_scenes")
        questions["every_scene_feels_alive"] = lifeless == 0 and bool(location.get("environmental_animation"))

    if style.get("character_style") != "expressive_stylized":
        warnings.append("style_identity_drift")

    weak_scenes = [
        s.get("scene_number")
        for s in scenes
        if not s.get("studio_character_id") or not s.get("studio_expression")
    ]

    # Soft-attach Visual Foundation V1 constitution (feature-film cinematic realism)
    foundation_review: dict[str, Any] = {}
    try:
        from services.visual_foundation import review_visual_foundation

        foundation_review = review_visual_foundation(package=package)
        for f in foundation_review.get("failures") or []:
            if f not in failures:
                failures.append(f"visual_foundation:{f}")
        for w in foundation_review.get("warnings") or []:
            warnings.append(f"visual_foundation:{w}")
    except Exception:  # noqa: BLE001
        foundation_review = {"skipped": True}

    # Soft-attach Human Realism PerformancePlan coverage
    human_realism_review: dict[str, Any] = {}
    try:
        from services.human_realism import validate_scene_bindings

        human_realism_review = validate_scene_bindings(scenes)
        for f in human_realism_review.get("failures") or []:
            if f not in failures:
                failures.append(f"human_realism:{f}")
        for w in human_realism_review.get("warnings") or []:
            warnings.append(f"human_realism:{w}")
    except Exception:  # noqa: BLE001
        human_realism_review = {"skipped": True}

    facial_review: dict[str, Any] = {}
    env_review: dict[str, Any] = {}
    try:
        from services.character_performance import validate_scene_facial_plans
        from services.environment_department import validate_environment_package

        facial_review = validate_scene_facial_plans(scenes)
        for f in facial_review.get("failures") or []:
            if f not in failures:
                failures.append(f"facial_performance:{f}")
        for w in facial_review.get("warnings") or []:
            warnings.append(f"facial_performance:{w}")
        # Validate first scene environment package if present
        env_pkg = None
        for s in scenes:
            if isinstance(s.get("environment_package"), dict):
                env_pkg = s["environment_package"]
                break
        env_review = validate_environment_package(env_pkg) if env_pkg else {"skipped": True, "warnings": ["no_environment_package"]}
        for f in env_review.get("failures") or []:
            if f not in failures:
                failures.append(f"environment:{f}")
        for w in env_review.get("warnings") or []:
            warnings.append(f"environment:{w}")
        warnings.append(
            "plan_validation_is_not_mp4_quality_proof:inspect_rendered_frames"
        )
    except Exception:  # noqa: BLE001
        facial_review = {"skipped": True}
        env_review = {"skipped": True}

    questions["feels_like_original_series"] = (
        questions["viewers_would_recognize_characters"]
        and questions["audience_would_remember_world"]
        and questions["every_scene_feels_alive"]
        and not failures
    )

    approved = not failures
    return {
        "approved": approved,
        "decision": "APPROVE" if approved else "REJECT",
        "visual_foundation": foundation_review,
        "human_realism": human_realism_review,
        "facial_performance": facial_review,
        "environment_construction": env_review,
        "failures": failures,
        "warnings": warnings,
        "questions": questions,
        "improve_scenes": weak_scenes,
        "reject_signals": list(STYLE_IDENTITY.get("forbid") or []),
    }
