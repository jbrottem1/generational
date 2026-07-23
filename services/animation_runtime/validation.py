"""Asset validation for animation runtime ingestion."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.animation_runtime.capability import doctor_asset_paths


SUPPORTED_FORMATS = {".blend", ".fbx", ".glb", ".gltf", ".obj", ".png", ".jpg", ".jpeg", ".hdr", ".exr", ".mp3", ".wav"}


def validate_runtime_assets() -> dict[str, Any]:
    paths = doctor_asset_paths()
    issues: list[dict[str, Any]] = []
    checks: dict[str, Any] = {}

    def fail(code: str, detail: str) -> None:
        issues.append({"code": code, "detail": detail, "severity": True})

    def warn(code: str, detail: str) -> None:
        issues.append({"code": code, "detail": detail, "severity": False})

    runtime_dir = paths["runtime_dir"]
    checks["runtime_dir_exists"] = runtime_dir.is_dir()
    if not runtime_dir.is_dir():
        fail("missing_runtime_dir", f"Expected {runtime_dir}")

    char = paths["character_blend"]
    checks["character_blend_exists"] = char.is_file()
    if not char.is_file():
        fail("missing_mesh", f"Missing skinned character blend: {char}")
        fail("missing_armature", "No armature asset file present")
        fail("mesh_not_skinned", "Cannot verify skinning without character blend")
    else:
        checks["character_format"] = char.suffix.lower()
        if char.suffix.lower() not in {".blend", ".fbx", ".glb", ".gltf"}:
            fail("incompatible_format", f"Unsupported character format {char.suffix}")

    lab = paths["lab_blend"]
    checks["lab_blend_exists"] = lab.is_file()
    if not lab.is_file():
        fail("world_missing", f"Missing lab blend: {lab}")
    else:
        # Image-only worlds are rejected separately if only flat plates exist
        checks["world_is_blend_geometry"] = lab.suffix.lower() == ".blend"

    prop = paths["prop_blend"]
    checks["prop_blend_exists"] = prop.is_file()
    if not prop.is_file():
        fail("prop_missing", f"Missing prop blend: {prop}")

    bone_map = paths["rig_map"]
    checks["rig_map_exists"] = bone_map.is_file()
    bone_count = 0
    facial_keys: list[str] = []
    if bone_map.is_file():
        data = json.loads(bone_map.read_text())
        bones = data.get("bones") or []
        bone_count = len(bones)
        facial_keys = list(data.get("facial_shape_keys") or [])
        required = {
            "root",
            "pelvis",
            "spine_01",
            "chest",
            "neck",
            "head",
            "upper_arm_L",
            "upper_arm_R",
            "forearm_L",
            "forearm_R",
            "hand_L",
            "hand_R",
            "thigh_L",
            "thigh_R",
            "shin_L",
            "shin_R",
            "foot_L",
            "foot_R",
        }
        present = {b.get("canonical_bone_name") for b in bones}
        missing_bones = sorted(required - present)
        if missing_bones:
            fail("broken_bone_mapping", f"Missing bones: {missing_bones}")
        if not data.get("skinned"):
            fail("mesh_not_skinned", "RIG_BONE_MAP marks skinned=false")
        if not data.get("armature"):
            fail("missing_armature", "RIG_BONE_MAP marks armature=false")
        for face in ("jaw_open", "smile", "blink_L", "blink_R", "viseme_A"):
            if face not in facial_keys:
                fail("missing_facial_controls", f"Missing facial control/shape key: {face}")
        if data.get("asset_origin") == "image_slideshow":
            fail("world_is_image", "Asset origin is image slideshow — rejected")
    else:
        fail("broken_bone_mapping", f"Missing {bone_map}")

    checks["bone_count"] = bone_count
    checks["facial_key_count"] = len(facial_keys)

    # Hand attachment / floor contact markers expected in map metadata or defaults
    if bone_map.is_file():
        present = {b.get("canonical_bone_name") for b in json.loads(bone_map.read_text()).get("bones") or []}
        if "hand_R" not in present:
            fail("missing_hand_attachment_points", "hand_R missing")
        if "foot_L" not in present or "foot_R" not in present:
            fail("missing_floor_contact_markers", "foot_L/foot_R missing")

    critical = [i for i in issues if i.get("severity")]
    return {
        "report_type": "AssetValidationReport",
        "ok": len(critical) == 0,
        "checks": checks,
        "issues": issues,
        "supported_formats": sorted(SUPPORTED_FORMATS),
        "paths": {k: str(v) for k, v in paths.items()},
    }
