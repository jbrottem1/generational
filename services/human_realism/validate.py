"""Soft validation for Human Realism packages and PerformancePlans."""

from __future__ import annotations

from typing import Any

from services.human_realism.base import base_framework


def validate_performance_plan(plan: dict[str, Any] | None) -> dict[str, Any]:
    failures: list[str] = []
    warnings: list[str] = []
    if not isinstance(plan, dict) or not plan:
        return {"ok": False, "failures": ["missing_performance_plan"], "warnings": []}
    required = base_framework()["performance_plan_required_fields"]
    for field in required:
        if field not in plan or plan.get(field) in (None, "", []):
            failures.append(f"missing_{field}")
    emotion = plan.get("emotion") if isinstance(plan.get("emotion"), dict) else {}
    if not emotion.get("primary"):
        failures.append("emotion_primary_missing")
    if plan.get("foot_contact_required") is False:
        warnings.append("foot_contact_disabled")
    return {"ok": not failures, "failures": failures, "warnings": warnings}


def validate_scene_bindings(scenes: list[dict[str, Any]]) -> dict[str, Any]:
    failures: list[str] = []
    warnings: list[str] = []
    if not scenes:
        warnings.append("no_scenes")
        return {"ok": True, "failures": failures, "warnings": warnings}
    for i, scene in enumerate(scenes):
        review = validate_performance_plan(scene.get("performance_plan"))
        for f in review["failures"]:
            failures.append(f"scene_{i}:{f}")
        for w in review["warnings"]:
            warnings.append(f"scene_{i}:{w}")
    return {"ok": not failures, "failures": failures, "warnings": warnings}
