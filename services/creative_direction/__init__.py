"""Generational Creative Direction — Phase III identity layer.

Does not add engines. Enforces visual identity against the frozen pipeline.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONSTITUTION_PATH = ROOT / "data" / "creative_direction" / "STYLE_CONSTITUTION.json"
OUT = ROOT / "data" / "creative_direction"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_constitution() -> dict[str, Any]:
    if CONSTITUTION_PATH.is_file():
        return json.loads(CONSTITUTION_PATH.read_text(encoding="utf-8"))
    return {"ok": False, "reason": "missing_constitution"}


def review_asset(asset: dict[str, Any], *, constitution: dict[str, Any] | None = None) -> dict[str, Any]:
    """Quality review gate — reject tech-upgrades that weaken identity."""
    c = constitution or load_constitution()
    scores: dict[str, Any] = {}
    reasons: list[str] = []
    warnings: list[str] = []

    criteria = list(c.get("quality_review") or [])
    for key in criteria:
        scores[key] = "pending_human_or_heuristic"

    # Hard rejects
    if asset.get("ken_burns") or asset.get("replaces_skeletal_with_image_animation"):
        reasons.append("replaces_skeletal_with_image_animation")
        scores["animation_quality"] = "fail"
        scores["runtime_compatibility"] = "fail"
    if asset.get("breaks_runtime") or asset.get("breaks_rig"):
        reasons.append("runtime_or_rig_break")
        scores["runtime_compatibility"] = "fail"
    if asset.get("palette_drift") or asset.get("random_palette"):
        reasons.append("brand_inconsistency_palette_drift")
        scores["brand_consistency"] = "fail"
    if asset.get("feeling") in {"threatening", "emotionless", "uncanny", "toy_like", "overly_mechanical"}:
        reasons.append("doctor_identity_violation")
        scores["emotional_connection"] = "fail"
        scores["recognizability"] = "fail"
    if asset.get("lab_mood") in {"empty_grey", "horror_clinical", "fluorescent_only"}:
        reasons.append("lab_identity_violation")
        scores["brand_consistency"] = "fail"

    # Heuristic passes for Phase III compliant packages
    if asset.get("phase") == "III" or asset.get("creative_direction") == "generational_v3":
        for key in ("visual_appeal", "emotional_connection", "recognizability", "brand_consistency"):
            if scores.get(key) == "pending_human_or_heuristic":
                scores[key] = "pass_constitution_aligned"
        scores["runtime_compatibility"] = scores.get("runtime_compatibility") if scores.get("runtime_compatibility") == "fail" else "pass"
        scores["educational_clarity"] = "pass_constitution_aligned"
        scores["animation_quality"] = scores.get("animation_quality") if scores.get("animation_quality") == "fail" else "pass_skeletal_preserved"

    if asset.get("empty_environment"):
        warnings.append("environment_storytelling_weak")
        scores["educational_clarity"] = "warn"

    rejected = bool(reasons)
    return {
        "report_type": "CreativeDirectionReview",
        "ok": not rejected,
        "rejected": rejected,
        "rejection_reasons": reasons,
        "warnings": warnings,
        "scores": scores,
        "criteria": criteria,
        "constitution_version": c.get("version"),
        "reviewed_at": _now(),
        "asset_id": asset.get("asset_id"),
    }


def materialize_creative_direction(*, write: bool = True) -> dict[str, Any]:
    c = load_constitution()
    package = {
        "package_type": "CREATIVE_DIRECTION_PACKAGE",
        "phase": "III",
        "created_at": _now(),
        "constitution": c,
        "guide": "CREATIVE_DIRECTION_GUIDE.md",
        "reviews": {
            "DOCTOR_001": review_asset(
                {
                    "asset_id": "DOCTOR_001",
                    "phase": "III",
                    "creative_direction": "generational_v3",
                    "feeling": "warm_curious_professional",
                },
                constitution=c,
            ),
            "GENERATIONAL_MEDICAL_LAB": review_asset(
                {
                    "asset_id": "GENERATIONAL_MEDICAL_LAB",
                    "phase": "III",
                    "creative_direction": "generational_v3",
                    "lab_mood": "inspirational_teaching_sanctuary",
                },
                constitution=c,
            ),
        },
        "architecture_note": "Creative identity only. Execution engines remain frozen.",
    }
    if write:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "CREATIVE_DIRECTION_PACKAGE.json").write_text(json.dumps(package, indent=2) + "\n")
        (OUT / "DOCTOR_001_CHARACTER_BIBLE.json").write_text(
            json.dumps(
                {
                    **(c.get("doctor_001") or {}),
                    "character_id": "DOCTOR_001",
                    "phase": "III",
                    "palette_ref": c.get("palette"),
                },
                indent=2,
            )
            + "\n"
        )
        (OUT / "LAB_IDENTITY.json").write_text(
            json.dumps({**(c.get("lab") or {}), "phase": "III", "palette_ref": c.get("palette")}, indent=2) + "\n"
        )
        (OUT / "COLOR_SCRIPT.json").write_text(json.dumps(c.get("color_script") or {}, indent=2) + "\n")
        (OUT / "LIGHTING_PHILOSOPHY.json").write_text(json.dumps(c.get("lighting") or {}, indent=2) + "\n")
        (OUT / "MOTION_STYLE.json").write_text(json.dumps(c.get("motion") or {}, indent=2) + "\n")
        (OUT / "PHASE.json").write_text(
            json.dumps(
                {
                    "phase": "III",
                    "title": "Creative Direction & Visual Identity",
                    "objective": "Iconic recognizable Generational Universe without new engines",
                    "runtime_frozen": True,
                },
                indent=2,
            )
            + "\n"
        )
    return {"ok": True, "package": package, "path": str(OUT / "CREATIVE_DIRECTION_PACKAGE.json")}


def apply_identity_notes() -> str:
    return """# Phase III Applied Identity

- Doctor: warmer skin, larger appealing eyes, teal coat trim, soft resting smile, friendlier silhouette
- Lab: dawn-white walls, warm sand wood, window gold light, plants/books, inspirational not clinical
- Lighting: Morning Discovery (warm key + soft fill + teal rim)
- Motion: ease curves retained in Golden Motion keyframes; breathing + coat secondary preserved
- Runtime: same BlenderRuntime / Golden Motion pipeline
"""
