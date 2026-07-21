"""Honest capability audit — do not claim skeletal features without runtime proof."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

# Features required for Golden Motion / true skeletal execution
REQUIRED_FEATURES = (
    "skeletal_animation",
    "joint_transforms",
    "inverse_kinematics",
    "facial_blendshapes_or_bones",
    "lip_synchronization",
    "object_constraints",
    "collision_handling",
    "foot_planting",
    "character_locomotion",
    "cloth_or_secondary_motion",
    "animated_cameras",
    "persistent_3d_environments",
)


def _has_skeletal_assets() -> dict[str, Any]:
    patterns = ("*.glb", "*.gltf", "*.fbx", "*.blend", "*.usd", "*.usda", "*.usdc", "*.vrm")
    found: list[str] = []
    search_roots = [
        ROOT / "data" / "studio_assets",
        ROOT / "data" / "reality",
        ROOT / "assets",
    ]
    for base in search_roots:
        if not base.is_dir():
            continue
        for pat in patterns:
            found.extend(str(p.relative_to(ROOT)) for p in base.rglob(pat))
    return {
        "found": found[:50],
        "count": len(found),
        "has_skinned_mesh": len(found) > 0,
    }


def _external_runtimes() -> dict[str, Any]:
    tools = {
        "blender": shutil.which("blender"),
        "godot": shutil.which("godot"),
        "ffmpeg": shutil.which("ffmpeg"),
    }
    apps = Path("/Applications")
    app_hits = []
    if apps.is_dir():
        for name in ("Blender.app", "Unity Hub.app", "Unity.app", "UE_5", "Maya.app", "Cinema 4D.app"):
            # Unity/Unreal may be versioned folders
            matches = list(apps.glob(f"*{name}*")) + list(apps.glob("Blender*.app"))
            for m in matches:
                app_hits.append(str(m))
    return {
        "cli": {k: bool(v) for k, v in tools.items()},
        "cli_paths": {k: v for k, v in tools.items() if v},
        "applications": app_hits,
        "python_bpy": False,  # bpy only inside Blender
    }


def audit_true_motion() -> dict[str, Any]:
    """Document what true_motion.py actually does."""
    return {
        "renderer_id": "true_motion",
        "module": "services/media_production/true_motion.py",
        "class": "ffmpeg_layered_still_compositor",
        "supports": {
            "skeletal_animation": False,
            "joint_transforms": False,
            "inverse_kinematics": False,
            "facial_blendshapes_or_bones": False,
            "lip_synchronization": False,  # no viseme-driven mesh
            "object_constraints": False,
            "collision_handling": False,
            "foot_planting": False,  # path exprs only; no IK plant
            "character_locomotion": False,  # plate translation ≠ locomotion
            "cloth_or_secondary_motion": False,
            "animated_cameras": True,  # crop/zoom/pan over composite
            "persistent_3d_environments": False,  # plates / procedural 2D bg
        },
        "mechanism": [
            "PNG character plate overlay",
            "environment plate zoompan or procedural lavfi background",
            "ffmpeg overlay x/y expressions (sin drift / linear travel)",
            "post-composite camera crop/scale",
        ],
        "insufficient_for_golden_motion": True,
        "reason": (
            "true_motion animates cameras and layered still images. "
            "It does not drive a skeletal rig, joints, IK, blendshapes, "
            "object constraints, or persistent 3D geometry."
        ),
    }


def audit_planning_packages() -> dict[str, Any]:
    """Planning packages exist — they are not executable meshes."""
    return {
        "director_package": "services/cinematic_direction_studio (plans)",
        "character_performance_package": "services/character_performance_engine (plans)",
        "character_rig_package": "services/character_rig_studio (JSON hierarchy/spec)",
        "world_package": "services/stage_world_simulation (nav/interaction contracts)",
        "interaction_package": "services/physics_interaction (contracts)",
        "doctor_animation_clips": "JSON phase labels — not joint keyframe curves",
        "doctor_rig_specification": "humanoid_ik_fk_hybrid_spec — specification only",
        "executable_skinned_mesh": False,
    }


def audit_capabilities() -> dict[str, Any]:
    assets = _has_skeletal_assets()
    runtimes = _external_runtimes()
    true_motion = audit_true_motion()
    planning = audit_planning_packages()

    feature_matrix: dict[str, dict[str, Any]] = {}
    for feat in REQUIRED_FEATURES:
        tm = true_motion["supports"].get(feat, False)
        feature_matrix[feat] = {
            "true_motion": tm,
            "external_runtime_available": False,
            "skinned_asset_available": assets["has_skinned_mesh"],
            "status": "unavailable" if not tm else "approximated_only",
            "native_execution": False,
        }

    skeletal_ready = (
        assets["has_skinned_mesh"]
        and (runtimes["cli"].get("blender") or bool(runtimes["applications"]))
    )

    return {
        "audit_version": "1.0.0",
        "sufficient_for_golden_motion": False,  # honest: not today
        "skeletal_runtime_ready": skeletal_ready,
        "required_features": list(REQUIRED_FEATURES),
        "feature_matrix": feature_matrix,
        "true_motion": true_motion,
        "planning_packages": planning,
        "skeletal_assets": assets,
        "external_runtimes": runtimes,
        "verdict": (
            "INSUFFICIENT — no skeletal animation runtime and no skinned mesh "
            "assets are available. true_motion is an ffmpeg layered still compositor. "
            "Do not produce a Golden Motion MP4 that fakes skeletal performance."
        ),
        "required_integration": {
            "runtime_options": [
                "Blender (bpy) headless + DOCTOR_001 skinned GLB/FBX",
                "Godot 4 AnimationPlayer + GLTF character",
                "Unreal Engine Sequencer / Control Rig",
                "Unity Timeline + Humanoid Animator",
                "Cloud skeletal provider (e.g. dedicated character animation API) "
                "returning mesh-deformed frame sequences",
            ],
            "asset_gap": (
                "DOCTOR_001 needs a permanent skinned mesh + facial blendshapes/bones "
                "bound to CHARACTER_RIG_PACKAGE hierarchy — not plates alone."
            ),
            "architecture_note": (
                "Frozen architecture keeps planning packages; this layer is the "
                "adapter. A new renderer product is not invented here — an external "
                "skeletal runtime must be selected and integrated via the adapter."
            ),
        },
    }
