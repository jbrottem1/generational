"""Build and export Phase II production assets into RUNTIME contract paths.

Run:
  blender --background --python build_production_assets.py -- --out DIR --runtime-dir DIR
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from production_builders import (  # noqa: E402
    apply_lighting_preset,
    build_production_doctor,
    build_production_lab,
    build_sample_container,
    material_library,
    write_bone_map,
)


def _argv() -> list[str]:
    if "--" in sys.argv:
        return sys.argv[sys.argv.index("--") + 1 :]
    return []


def _parse() -> dict:
    args = _argv()
    out = {"out": str(Path.cwd() / "phase2_out"), "runtime_dir": ""}
    i = 0
    while i < len(args):
        if args[i] == "--out" and i + 1 < len(args):
            out["out"] = args[i + 1]
            i += 2
        elif args[i] == "--runtime-dir" and i + 1 < len(args):
            out["runtime_dir"] = args[i + 1]
            i += 2
        else:
            i += 1
    return out


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (
        bpy.data.meshes,
        bpy.data.armatures,
        bpy.data.materials,
        bpy.data.actions,
        bpy.data.cameras,
        bpy.data.lights,
    ):
        for b in list(block):
            block.remove(b)


def main() -> None:
    cfg = _parse()
    out = Path(cfg["out"])
    out.mkdir(parents=True, exist_ok=True)
    runtime = Path(cfg["runtime_dir"]) if cfg["runtime_dir"] else out / "RUNTIME"
    runtime.mkdir(parents=True, exist_ok=True)

    clear_scene()
    mats = material_library()
    lab = build_production_lab(mats)
    container = build_sample_container(mats)
    arm, mesh = build_production_doctor(mats)
    lights = apply_lighting_preset("morning_discovery")

    scene_blend = out / "PHASE_III_CREATIVE_SCENE.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(scene_blend))

    # Export RUNTIME contract files (full scene copies — Golden Motion consumes same paths)
    import shutil

    char = runtime / "DOCTOR_001_SKINNED.blend"
    lab_b = runtime / "GENERATIONAL_MEDICAL_LAB.blend"
    prop = runtime / "SAMPLE_CONTAINER_001.blend"
    shutil.copy2(scene_blend, char)
    shutil.copy2(scene_blend, lab_b)
    shutil.copy2(scene_blend, prop)

    write_bone_map(runtime / "RIG_BONE_MAP.json", mesh)
    write_bone_map(out / "RIG_BONE_MAP.json", mesh)

    origin = {
        "phase": "III",
        "quality_tier": "phase_iii_iconic_identity",
        "studio": "creative_direction+production_asset_studio",
        "creative_direction": "generational_v3",
        "not_copyrighted_third_party": True,
        "asset_origin": "phase_iii_creative_direction",
        "character": str(char),
        "world": str(lab_b),
        "prop": str(prop),
        "lighting_preset": "morning_discovery",
        "improvements": [
            "iconic_doctor_appeal_silhouette",
            "large_warm_eyes_iris_pupil",
            "soft_resting_smile",
            "teal_coat_identity_trim",
            "inspirational_lab_not_clinical",
            "dawn_white_warm_sand_palette",
            "window_gold_key_light",
            "teal_rim_signature_lighting",
            "brand_mark_panel",
            "lived_in_research_storytelling",
            "constitution_aligned_materials",
        ],
    }
    (runtime / "ASSET_ORIGIN.json").write_text(json.dumps(origin, indent=2) + "\n")
    (out / "ASSET_ORIGIN.json").write_text(json.dumps(origin, indent=2) + "\n")

    # Prop catalog sidecar
    props_catalog = {
        "SAMPLE_CONTAINER_001": {"grasp_point": [0, 0, 0.04], "mass_kg": 0.12, "collision": "cylinder"},
        "MICROSCOPE_001": {"grasp_point": [0, 0, 0.1], "mass_kg": 2.4, "collision": "box"},
        "MEDICAL_SCANNER_001": {"grasp_point": [0, 0, 0.2], "mass_kg": 8.0, "collision": "box"},
        "COFFEE_MUG_001": {"grasp_point": [0.04, 0, 0.04], "mass_kg": 0.25, "collision": "cylinder"},
    }
    (out / "PROP_CATALOG.json").write_text(json.dumps(props_catalog, indent=2) + "\n")
    (runtime.parent.parent / "production_asset_studio" / "library" / "props" / "PROP_CATALOG.json").parent.mkdir(
        parents=True, exist_ok=True
    )

    report = {
        "ok": True,
        "phase": "III",
        "creative_direction": "generational_v3",
        "scene": str(scene_blend),
        "runtime_dir": str(runtime),
        "character": str(char),
        "world": str(lab_b),
        "prop": str(prop),
        "lights": lights,
        "bones": len(arm.data.bones),
        "shape_keys": [k.name for k in mesh.data.shape_keys.key_blocks] if mesh.data.shape_keys else [],
        "lab_objects": list(lab.keys()),
        "container": container.name,
    }
    (out / "PRODUCTION_BUILD_REPORT.json").write_text(json.dumps(report, indent=2) + "\n")
    print("PHASE_III_BUILD_OK", scene_blend)


if __name__ == "__main__":
    main()
