"""Golden Motion Validation — execute or honestly refuse."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.animation_execution.capability import audit_capabilities
from services.animation_execution.scene import SPOKEN_LINE, build_executable_animation_scene
from services.animation_execution.select_runtime import select_runtime

ROOT = Path(__file__).resolve().parents[2]
OUT_ROOT = ROOT / "data" / "animation_execution" / "golden_motion"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _assemble_source_packages() -> dict[str, Any]:
    """Pull permanent packages for DOCTOR_001 + GMRI lab."""
    from services.character_performance_engine import build_character_performance
    from services.character_rig_studio import resolve_character_rig
    from services.cinematic_direction_studio import build_director_package
    from services.physics_interaction import build_interaction_package
    from services.stage_world_simulation import resolve_world_package

    world = resolve_world_package("WORLD-GMRI-MEDICAL-LAB")
    rig = resolve_character_rig("DOCTOR_001")
    scene = {
        "scene_number": 1,
        "purpose": "story_beat",
        "length_sec": 14.0,
        "narration": SPOKEN_LINE,
        "studio_character_id": "DOCTOR_001",
    }
    director = build_director_package(
        scene=scene,
        scene_index=0,
        total_scenes=1,
        location="LOC-GMRI",
        topic="Golden Motion Validation",
    )
    performance = build_character_performance(
        character_id="DOCTOR_001",
        scene=scene,
        scene_index=0,
        location=world,
    )
    interactions = [
        build_interaction_package(
            actor="DOCTOR_001",
            target="door_main",
            interaction_type="opening_doors",
            interaction_id="gm_open_door",
            t_start=0.0,
            t_end=1.2,
            world_id="WORLD-GMRI-MEDICAL-LAB",
        ),
        build_interaction_package(
            actor="DOCTOR_001",
            target="sample_container",
            interaction_type="picking_up_objects",
            interaction_id="gm_grasp_sample",
            t_start=6.5,
            t_end=9.5,
            world_id="WORLD-GMRI-MEDICAL-LAB",
        ),
    ]
    return {
        "director_package": director,
        "character_performance_package": performance,
        "character_rig_package": rig,
        "world_package": world,
        "interaction_packages": interactions,
    }


def run_golden_motion_validation(*, write: bool = True) -> dict[str, Any]:
    """Build EXECUTABLE_ANIMATION_SCENE, attempt skeletal execution, write artifacts."""
    sources = _assemble_source_packages()
    executable = build_executable_animation_scene(
        director_package=sources["director_package"],
        character_performance_package=sources["character_performance_package"],
        character_rig_package=sources["character_rig_package"],
        world_package=sources["world_package"],
        interaction_packages=sources["interaction_packages"],
        duration_sec=14.0,
    )
    adapter, selection = select_runtime()
    execution = adapter.execute_scene(executable)
    capability = audit_capabilities()

    passed = bool(
        execution.get("ok")
        and adapter.supports_skeletal
        and execution.get("encode", {}).get("mp4_path")
    )

    # Frame-contact / motion proof cannot be claimed without skeletal frames
    frame_contact = {
        "ok": False,
        "reason": "No skeletal frames rendered — contact checks not executable",
        "required_checks": [
            "foot_floor_contact",
            "hand_object_contact",
            "object_attachment",
            "collision_results",
        ],
        "results": {
            "foot_floor_contact": "unavailable",
            "hand_object_contact": "unavailable",
            "object_attachment": "unavailable",
            "collision_results": "unavailable",
        },
    }

    motion_proof_sheet = {
        "ok": False,
        "reason": "No frame buffer — contact sheet not generated",
        "required_frames": [
            "left_foot_plant",
            "right_foot_plant",
            "reach",
            "grasp",
            "object_lift",
            "facial_expression",
            "speaking_pose",
        ],
        "frames": [],
    }

    honest_capability = {
        "features_executed_natively": [],
        "features_approximated": [],
        "features_unavailable": list(capability.get("required_features") or []),
        "fallback_used": None,
        "fallback_forbidden_for_golden_motion": True,
        "true_motion_explicitly_not_used": True,
        "verdict": capability.get("verdict"),
        "required_integration": capability.get("required_integration"),
    }

    manifest = {
        "test": "GOLDEN_MOTION_VALIDATION",
        "created_at": _now(),
        "passed": passed,
        "refused_misleading_mp4": bool(execution.get("refused_misleading_mp4")),
        "renderer_used": adapter.runtime_id,
        "supports_skeletal": adapter.supports_skeletal,
        "actor_asset_loaded": False,
        "actor_id": "DOCTOR_001",
        "rig_version": (sources["character_rig_package"].get("identity") or {}).get(
            "continuity_version"
        ),
        "world_package": sources["world_package"].get("world_id"),
        "animation_clips": executable.get("animation_clips"),
        "joint_tracks": [j.get("joint") for j in executable.get("joint_tracks") or []],
        "facial_tracks": list((executable.get("facial_tracks") or {}).keys()),
        "interaction_constraints": [
            ix.get("interaction_id") for ix in executable.get("interactions") or []
        ],
        "physics_events": executable.get("physics_state"),
        "camera_tracks": [
            c.get("framing") for c in executable.get("camera_plan") or []
        ],
        "spoken_line": SPOKEN_LINE,
        "voice_intent": "VOICE-0001 Founder ElevenLabs (or Doctor canonical if assigned)",
        "lip_sync": "planned_phoneme_timeline_only — not waveform-aligned without runtime",
        "execution": {
            "ok": execution.get("ok"),
            "encode": execution.get("encode"),
            "log_ops": [x.get("op") for x in execution.get("log") or []],
        },
        "runtime_selection": {
            "selected": selection.get("selected"),
            "note": selection.get("note"),
        },
    }

    gap_report = {
        "title": "Renderer Capability Gap Report — Golden Motion",
        "created_at": _now(),
        "golden_motion_passed": False,
        "mp4_produced": False,
        "current_renderer": capability.get("true_motion"),
        "planning_stack_ready": True,
        "planning_packages_composed": True,
        "executable_animation_scene_built": True,
        "blocking_gaps": [
            "No skinned mesh / GLB / FBX / Blend asset for DOCTOR_001",
            "No Blender / Godot / Unreal / Unity skeletal runtime installed or wired",
            "true_motion is ffmpeg layered still compositing — insufficient",
            "Animation clip JSON files are phase labels, not joint curves",
            "RIG_SPECIFICATION is a contract, not an executable armature",
        ],
        "required_to_pass": capability.get("required_integration"),
        "adapter_status": (
            "AnimationExecutionAdapter interface is implemented. "
            "InsufficientRuntimeAdapter correctly refuses fake MP4 success."
        ),
        "next_integration_step": (
            "1) Author or import DOCTOR_001 skinned mesh + face blendshapes bound to "
            "CHARACTER_RIG_PACKAGE joints. "
            "2) Install Blender (recommended) or Godot/Unreal/Unity. "
            "3) Implement BlenderAdapter (or chosen runtime) behind "
            "services/animation_execution/adapter.py. "
            "4) Re-run scripts/golden_motion_validation.py."
        ),
    }

    result = {
        "ok": passed,
        "golden_motion_passed": passed,
        "mp4_path": (execution.get("encode") or {}).get("mp4_path"),
        "executable_scene": executable,
        "execution_manifest": manifest,
        "frame_contact_report": frame_contact,
        "motion_proof_contact_sheet": motion_proof_sheet,
        "honest_capability_report": honest_capability,
        "capability_gap_report": gap_report,
        "capability_audit": capability,
        "source_package_summaries": {
            "director_ok": (sources["director_package"].get("validation") or {}).get("ok"),
            "performance_ok": (sources["character_performance_package"].get("validation") or {}).get(
                "ok"
            ),
            "rig_ok": (sources["character_rig_package"].get("validation") or {}).get("ok"),
            "world_ok": (sources["world_package"].get("validation") or {}).get("ok"),
        },
    }

    if write:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out = OUT_ROOT / f"GOLDEN_MOTION_{stamp}"
        out.mkdir(parents=True, exist_ok=True)

        def dump(name: str, data: Any) -> str:
            path = out / name
            path.write_text(json.dumps(data, indent=2, default=str) + "\n", encoding="utf-8")
            return str(path)

        paths = {
            "EXECUTABLE_ANIMATION_SCENE.json": dump(
                "EXECUTABLE_ANIMATION_SCENE.json", executable
            ),
            "EXECUTION_MANIFEST.json": dump("EXECUTION_MANIFEST.json", manifest),
            "FRAME_CONTACT_REPORT.json": dump("FRAME_CONTACT_REPORT.json", frame_contact),
            "MOTION_PROOF_CONTACT_SHEET.json": dump(
                "MOTION_PROOF_CONTACT_SHEET.json", motion_proof_sheet
            ),
            "HONEST_CAPABILITY_REPORT.json": dump(
                "HONEST_CAPABILITY_REPORT.json", honest_capability
            ),
            "CAPABILITY_GAP_REPORT.json": dump("CAPABILITY_GAP_REPORT.json", gap_report),
            "CAPABILITY_AUDIT.json": dump("CAPABILITY_AUDIT.json", capability),
        }
        md = out / "GOLDEN_MOTION_REPORT.md"
        md.write_text(_markdown(result, gap_report), encoding="utf-8")
        paths["GOLDEN_MOTION_REPORT.md"] = str(md)
        # Stable pointer
        latest = OUT_ROOT / "LATEST"
        latest.mkdir(parents=True, exist_ok=True)
        for name, src in paths.items():
            (latest / Path(name).name).write_text(
                Path(src).read_text(encoding="utf-8"), encoding="utf-8"
            )
        result["out_dir"] = str(out)
        result["latest_dir"] = str(latest)
        result["artifacts"] = paths

    return result


def _markdown(result: dict[str, Any], gap: dict[str, Any]) -> str:
    lines = [
        "# Golden Motion Validation Report",
        "",
        f"**Passed:** `{result.get('golden_motion_passed')}`",
        f"**MP4:** `{result.get('mp4_path')}`",
        "",
        "## Verdict",
        "",
        "The planning architecture composed successfully into an "
        "`EXECUTABLE_ANIMATION_SCENE`.",
        "",
        "**No skeletal runtime / skinned mesh is available.**",
        "A misleading layered-still MP4 was **refused**.",
        "",
        "## Blocking gaps",
        "",
    ]
    for g in gap.get("blocking_gaps") or []:
        lines.append(f"- {g}")
    lines.extend(
        [
            "",
            "## Next integration step",
            "",
            str(gap.get("next_integration_step") or ""),
            "",
            "## Auto-rejection honored",
            "",
            "- No still-image Doctor presented as animation",
            "- No Ken Burns / plate pan disguised as skeletal motion",
            "- No false capability claims",
            "",
        ]
    )
    return "\n".join(lines)
