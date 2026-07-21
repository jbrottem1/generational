"""Normalize ops + Creative Excellence + Audience Intelligence into program scores."""

from __future__ import annotations

from typing import Any

from services.production_validation.evaluate import evaluate_production
from services.validation_program.catalog import MEASUREMENT_DIMENSIONS


def _f(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _first_positive(*values: Any, default: float = 70.0) -> float:
    """Pick first usable score; treat None/missing/0 as absent (common in sparse CE payloads)."""
    for value in values:
        if value is None:
            continue
        try:
            score = float(value)
        except (TypeError, ValueError):
            continue
        if score > 0:
            return score
    return default


def score_validation_run(
    ops_result: dict[str, Any],
    *,
    category: str = "",
    opportunity_score: float | None = None,
) -> dict[str, Any]:
    """Compose existing evaluators into V1 Validation Program scorecard."""
    base = evaluate_production(ops_result)
    report = ops_result.get("report") or {}
    context = ops_result.get("context") or {}
    status = ops_result.get("status") or {}
    ce = context.get("creative_excellence") or {}
    ai = context.get("audience_intelligence_review") or {}

    # Prefer full CE review if attached on report path later
    ce_score = _f(ce.get("creative_excellence_score"), _f(report.get("creative_excellence_score"), 0))
    v2 = {}
    if isinstance(ce.get("single_recommendation"), dict):
        pass
    # Soft re-pull scorecard if ops only stored summary
    scorecard = ce.get("scorecard") if isinstance(ce.get("scorecard"), dict) else {}
    v2 = (scorecard.get("v2_quality") or {}).get("scores") if scorecard else {}
    if not isinstance(v2, dict):
        v2 = {}

    ai_evals = {}
    # Load AI review file if path present
    ai_path = report.get("audience_intelligence_review_path") or ai.get("path")
    if ai_path:
        try:
            from pathlib import Path
            import json

            payload = json.loads(Path(ai_path).read_text(encoding="utf-8"))
            ai_evals = payload.get("evaluations") or {}
            if not ai.get("highest_impact_improvement"):
                ai["highest_impact_improvement"] = (payload.get("highest_impact_improvement") or {}).get("statement")
        except Exception:  # noqa: BLE001
            ai_evals = {}

    base_scores = dict(base.get("scores") or {})
    candidate0 = (context.get("candidates") or [{}])[0] or {}
    measurements = {
        "research_accuracy": _first_positive(
            base_scores.get("educational_accuracy"), report.get("educational_accuracy"), default=70
        ),
        "psychology_effectiveness": _first_positive(
            ai_evals.get("emotional_impact"), base_scores.get("hook_strength"), default=70
        ),
        "hook_strength": _first_positive(base_scores.get("hook_strength"), v2.get("hook"), default=70),
        "story_flow": _first_positive(v2.get("storytelling"), ai_evals.get("story_clarity"), default=70),
        "educational_clarity": _first_positive(
            v2.get("educational_clarity"), base_scores.get("educational_accuracy"), default=70
        ),
        "world_continuity": _first_positive(
            candidate0.get("world_continuity_score"),
            (_f(v2.get("visual_quality"), 0) * 0.95 if _f(v2.get("visual_quality"), 0) > 0 else None),
            default=65,
        ),
        "visual_quality": _first_positive(base_scores.get("visual_quality"), v2.get("visual_quality"), default=70),
        "cinematic_quality": _first_positive(
            v2.get("motion_quality"), base_scores.get("animation_quality"), default=70
        ),
        "narration_quality": _first_positive(
            base_scores.get("narration_quality"), v2.get("audio_quality"), default=70
        ),
        "caption_accuracy": _first_positive(base_scores.get("caption_quality"), default=75),
        "audio_mix": _first_positive(base_scores.get("audio_mix"), default=75),
        "thumbnail_appeal": _first_positive(
            base_scores.get("thumbnail_quality"), ai_evals.get("shareability_prediction"), default=60
        ),
        "packaging": _first_positive(base_scores.get("seo_quality"), default=65),
        "overall_professionalism": _first_positive(
            v2.get("overall_professionalism"),
            ce_score,
            base_scores.get("overall_production_score"),
            default=70,
        ),
    }
    for k in MEASUREMENT_DIMENSIONS:
        measurements[k] = round(_f(measurements.get(k), 0), 1)

    overall = round(sum(measurements[k] for k in MEASUREMENT_DIMENSIONS) / len(MEASUREMENT_DIMENSIONS), 1)

    # Timing
    stages = status.get("stages") if isinstance(status.get("stages"), list) else []
    stage_ms = {
        str(s.get("key")): int(s.get("duration_ms") or 0)
        for s in stages
        if isinstance(s, dict) and s.get("key")
    }
    elapsed_ms = int(status.get("elapsed_ms") or ops_result.get("elapsed_ms") or sum(stage_ms.values()) or 0)
    render_ms = int(stage_ms.get("rendering") or 0) + int(stage_ms.get("export") or 0)

    failures = []
    for s in stages:
        if not isinstance(s, dict):
            continue
        for err in s.get("errors") or []:
            failures.append({"stage": s.get("key"), "error": str(err)[:240]})
        for w in s.get("warnings") or []:
            if "fail" in str(w).lower() or "unavailable" in str(w).lower():
                failures.append({"stage": s.get("key"), "warning": str(w)[:240]})

    success = bool(status.get("success") or ops_result.get("success"))
    return {
        "category": category or (ops_result.get("brief") or {}).get("domain") or "",
        "topic": (ops_result.get("brief") or {}).get("topic") or report.get("topic") or "",
        "production_id": ops_result.get("production_id") or status.get("production_id") or report.get("production_id"),
        "success": success,
        "measurements": measurements,
        "overall_program_score": overall,
        "legacy_scores": base_scores,
        "creative_excellence_score": ce_score or None,
        "opportunity_score": opportunity_score,
        "viewer_prediction": _f(base_scores.get("retention_prediction"), _f(ai_evals.get("retention_prediction"), 0)),
        "hook_score": measurements["hook_strength"],
        "timing": {
            "elapsed_ms": elapsed_ms,
            "render_ms": render_ms,
            "stage_ms": stage_ms,
        },
        "failures": failures,
        "weaknesses": base.get("weaknesses") or [],
        "creative_recommendation": (
            report.get("creative_recommendation")
            or (
                (ce.get("single_recommendation") or {}).get("recommendation")
                if isinstance(ce.get("single_recommendation"), dict)
                else ce.get("single_recommendation")
            )
        ),
        "audience_lesson": report.get("audience_intelligence_lesson")
        or ai.get("highest_impact_improvement"),
        "publish_ready": bool(base.get("publish_ready")),
        "pipeline_health": status.get("pipeline_health"),
        "validation_score": status.get("validation_score"),
    }
