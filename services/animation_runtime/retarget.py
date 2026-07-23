"""Canonical ↔ runtime bone retargeting layer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.animation_runtime.capability import doctor_asset_paths


def load_resolved_bone_map() -> dict[str, Any]:
    path = doctor_asset_paths()["rig_map"]
    if not path.is_file():
        return {"ok": False, "bones": [], "path": str(path)}
    data = json.loads(path.read_text())
    bones = []
    for b in data.get("bones") or []:
        bones.append(
            {
                "canonical_bone_name": b.get("canonical_bone_name"),
                "runtime_bone_name": b.get("runtime_bone_name") or b.get("canonical_bone_name"),
                "rotation_offset": b.get("rotation_offset") or [0, 0, 0],
                "translation_offset": b.get("translation_offset") or [0, 0, 0],
                "scale_factor": float(b.get("scale_factor") or 1.0),
                "axis_conversion": b.get("axis_conversion") or "blender_z_up",
                "parent_validation": b.get("parent_validation") or b.get("parent"),
            }
        )
    return {
        "ok": True,
        "path": str(path),
        "bones": bones,
        "facial_shape_keys": data.get("facial_shape_keys") or [],
        "supports": {
            "animation_clip_retargeting": True,
            "root_motion_extraction": True,
            "foot_lock_correction": True,
            "hand_ik": True,
            "head_aim": True,
            "eye_aim": "approximated_via_head",
            "prop_attachment": True,
            "facial_channel_mapping": True,
        },
    }


def write_bone_map_copy(dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    resolved = load_resolved_bone_map()
    dest.write_text(json.dumps(resolved, indent=2) + "\n")
    return dest
