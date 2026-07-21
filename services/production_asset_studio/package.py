"""Build PRODUCTION_ASSET_PACKAGE manifests."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from services.production_asset_studio.departments import department_catalog, list_departments
from services.production_asset_studio.models import (
    ENGINE_ID,
    PACKAGE_TYPE,
    PACKAGE_VERSION,
    PHASE,
    RUNTIME_CONTRACT,
)
from services.production_asset_studio.validation import validate_production_asset


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_asset_studio_package(*, focus: str = "golden_motion_phase_ii") -> dict[str, Any]:
    departments = list_departments()
    validated = []
    for dep in departments:
        for asset in dep.get("assets") or []:
            v = validate_production_asset({**asset, "asset_type": dep["department_id"]})
            validated.append({"asset_id": asset.get("asset_id"), "department_id": dep["department_id"], **v})

    rejected = [v for v in validated if v.get("rejected")]
    return {
        "package_type": PACKAGE_TYPE,
        "package_version": PACKAGE_VERSION,
        "engine_id": ENGINE_ID,
        "phase": PHASE,
        "focus": focus,
        "created_at": _now(),
        "runtime_contract": RUNTIME_CONTRACT,
        "departments": departments,
        "validation_summary": {
            "checked": len(validated),
            "rejected": len(rejected),
            "ok": len(rejected) == 0,
        },
        "asset_validations": validated,
        "quality_standard": [
            "visual_realism",
            "animation_quality",
            "facial_performance",
            "lighting",
            "materials",
            "storytelling",
            "runtime_unchanged",
        ],
        "architecture_note": "Assets upgrade only. Execution engines remain frozen.",
    }


def build_department_package(department_id: str) -> dict[str, Any]:
    dep = department_catalog(department_id)
    return {
        "package_type": "PRODUCTION_DEPARTMENT_PACKAGE",
        "package_version": PACKAGE_VERSION,
        "phase": PHASE,
        "created_at": _now(),
        "department": dep,
    }
