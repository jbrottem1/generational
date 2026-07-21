"""Reject assets that break the frozen runtime / rig / skeletal contract."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from services.production_asset_studio.models import REJECTION_RULES, empty_validation

ROOT = Path(__file__).resolve().parents[2]


def validate_production_asset(asset: dict[str, Any]) -> dict[str, Any]:
    result = empty_validation()
    reasons: list[str] = []
    warnings: list[str] = []

    asset_type = str(asset.get("asset_type") or asset.get("type") or "")
    if asset.get("replaces_skeletal_with_image_animation") or asset.get("ken_burns"):
        reasons.append("replaces_skeletal_with_image_animation")
    if asset.get("requires_new_architecture"):
        reasons.append("requires_new_architecture")
    if asset.get("breaks_runtime"):
        reasons.append("breaks_runtime")
    if asset.get("breaks_rig"):
        reasons.append("breaks_rig")
    if asset.get("flat_image_background") is True and asset_type in {"world", "environment"}:
        reasons.append("breaks_runtime")
        warnings.append("flat_image_background rejected for environments")

    # Runtime path contract for primary Golden Motion assets
    runtime_path = asset.get("runtime_path")
    if runtime_path:
        p = Path(str(runtime_path))
        if not p.is_absolute():
            p = ROOT / p
        if p.suffix.lower() not in {".blend", ".glb", ".gltf", ".fbx", ".json", ""}:
            warnings.append(f"unusual_suffix:{p.suffix}")

    if asset.get("character_id") == "DOCTOR_001":
        bones = set(asset.get("required_bones") or asset.get("bones") or [])
        # If bones listed, require core set
        core = {"root", "pelvis", "chest", "head", "hand_R", "foot_L", "foot_R"}
        if bones and not core.issubset(bones):
            reasons.append("breaks_rig")
            warnings.append(f"missing_core_bones:{sorted(core - bones)}")

    result["rejection_reasons"] = reasons
    result["warnings"] = warnings
    result["rejected"] = bool(reasons)
    result["ok"] = not reasons
    result["runtime_compatible"] = "breaks_runtime" not in reasons
    result["rig_compatible"] = "breaks_rig" not in reasons
    result["skeletal_animation_preserved"] = "replaces_skeletal_with_image_animation" not in reasons
    result["rules"] = REJECTION_RULES
    return result
