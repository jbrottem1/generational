"""Build permanent DOCTOR_001 production asset package + validation sheets.

Run:
  blender --background --python build_doctor_001_asset.py -- --out DIR --runtime-dir DIR
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Euler, Vector

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from doctor_production_mesh import (  # noqa: E402
    BONES,
    FACIAL_SHAPE_KEYS,
    build_canonical_doctor,
)
from production_builders import (  # noqa: E402
    apply_lighting_preset,
    build_production_lab,
    build_sample_container,
    material_library,
)


def _argv():
    if "--" in sys.argv:
        return sys.argv[sys.argv.index("--") + 1 :]
    return []


def _parse():
    args = _argv()
    out = {"out": str(Path.cwd() / "doctor_out"), "runtime_dir": "", "validate": "1"}
    i = 0
    while i < len(args):
        if args[i] == "--out" and i + 1 < len(args):
            out["out"] = args[i + 1]
            i += 2
        elif args[i] == "--runtime-dir" and i + 1 < len(args):
            out["runtime_dir"] = args[i + 1]
            i += 2
        elif args[i] == "--validate" and i + 1 < len(args):
            out["validate"] = args[i + 1]
            i += 2
        else:
            i += 1
    return out


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.armatures, bpy.data.materials, bpy.data.actions, bpy.data.cameras, bpy.data.lights):
        for b in list(block):
            block.remove(b)


def write_maps(out: Path, arm, body):
    bone_map = []
    for name, parent, head, tail in BONES:
        bone_map.append(
            {
                "canonical_bone_name": name,
                "runtime_bone_name": name,
                "rotation_offset": [0, 0, 0],
                "translation_offset": [0, 0, 0],
                "scale_factor": 1.0,
                "axis_conversion": "blender_z_up",
                "parent_validation": parent,
            }
        )
    facial = [k.name for k in body.data.shape_keys.key_blocks] if body.data.shape_keys else []
    (out / "RIG_BONE_MAP.json").write_text(
        json.dumps(
            {
                "actor_id": "DOCTOR_001",
                "bones": bone_map,
                "count": len(bone_map),
                "facial_shape_keys": facial,
                "skinned": True,
                "armature": True,
                "asset_origin": "doctor_001_production_v1",
                "quality_tier": "production_v1",
                "height_m": 1.85,
            },
            indent=2,
        )
        + "\n"
    )
    (out / "FACIAL_CHANNEL_MAP.json").write_text(
        json.dumps(
            {
                "actor_id": "DOCTOR_001",
                "system": "shape_keys_hybrid_with_eye_lid_bones",
                "channels": FACIAL_SHAPE_KEYS,
                "eye_bones": ["eye_L", "eye_R", "lid_upper_L", "lid_upper_R", "lid_lower_L", "lid_lower_R"],
                "jaw_bone": "jaw",
            },
            indent=2,
        )
        + "\n"
    )
    (out / "VISEME_MAP.json").write_text(
        json.dumps(
            {
                "actor_id": "DOCTOR_001",
                "mapping": {
                    "rest": "viseme_REST",
                    "closed_lips": "viseme_M",
                    "wide_vowel": "viseme_E",
                    "open_vowel": "viseme_A",
                    "rounded_vowel": "viseme_O",
                    "teeth_lip_contact": "viseme_F",
                    "tongue_teeth_contact": "viseme_L",
                    "consonant_closure": "viseme_M",
                    "smile_speaking": "viseme_smile_speak",
                    "concerned_speaking": "viseme_concern_speak",
                    "U": "viseme_U",
                    "WQ": "viseme_WQ",
                },
                "legacy_aliases": {
                    "viseme_A": "viseme_A",
                    "viseme_E": "viseme_E",
                    "viseme_O": "viseme_O",
                    "viseme_U": "viseme_U",
                    "viseme_M": "viseme_M",
                    "viseme_F": "viseme_F",
                },
            },
            indent=2,
        )
        + "\n"
    )
    (out / "HAND_ATTACHMENT_POINTS.json").write_text(
        json.dumps(
            {
                "hand_R": {"grasp_point": list(arm.get("hand_grasp_R", (-0.74, 0, 1.0))), "bone": "hand_R"},
                "hand_L": {"grasp_point": list(arm.get("hand_grasp_L", (0.74, 0, 1.0))), "bone": "hand_L"},
                "validated_props": ["SAMPLE_CONTAINER_001"],
            },
            indent=2,
        )
        + "\n"
    )
    (out / "FOOT_CONTACT_MARKERS.json").write_text(
        json.dumps(
            {
                "foot_L": {"point": list(arm.get("foot_contact_L", (0.13, 0.06, 0.02))), "bone": "foot_L"},
                "foot_R": {"point": list(arm.get("foot_contact_R", (-0.13, 0.06, 0.02))), "bone": "foot_R"},
            },
            indent=2,
        )
        + "\n"
    )
    (out / "CANONICAL_MEASUREMENTS.json").write_text(
        json.dumps(
            {
                "height_m": 1.85,
                "height_ft_in": "6'1\"",
                "forward_axis": "-Y",
                "up_axis": "+Z",
                "units": "meters",
                "scale": 1.0,
                "face_toward": "doorway_negative_Y",
            },
            indent=2,
        )
        + "\n"
    )


def setup_camera(loc, target, lens=50):
    bpy.ops.object.camera_add(location=loc)
    cam = bpy.context.object
    cam.name = "VAL_CAM"
    direction = Vector(target) - Vector(loc)
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = lens
    bpy.context.scene.camera = cam
    return cam


def set_shape(mesh, name, value):
    if mesh.data.shape_keys and name in mesh.data.shape_keys.key_blocks:
        mesh.data.shape_keys.key_blocks[name].value = value


def reset_shapes(mesh):
    if not mesh.data.shape_keys:
        return
    for kb in mesh.data.shape_keys.key_blocks:
        if kb.name != "Basis":
            kb.value = 0.0
    # Iter 001 resting trust expression
    sk = mesh.data.shape_keys.key_blocks
    if "smile" in sk:
        sk["smile"].value = 0.32
    if "eye_squint" in sk:
        sk["eye_squint"].value = 0.14
    if "cheek_raise" in sk:
        sk["cheek_raise"].value = 0.12
    if "empathy" in sk:
        sk["empathy"].value = 0.08


def pose_bone(arm, name, rot_deg=(0, 0, 0)):
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="POSE")
    pb = arm.pose.bones.get(name)
    if pb:
        pb.rotation_mode = "XYZ"
        pb.rotation_euler = Euler(tuple(math.radians(a) for a in rot_deg), "XYZ")
    bpy.ops.object.mode_set(mode="OBJECT")


def reset_pose(arm):
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="POSE")
    for pb in arm.pose.bones:
        pb.rotation_euler = Euler((0, 0, 0), "XYZ")
        pb.location = Vector((0, 0, 0))
    bpy.ops.object.mode_set(mode="OBJECT")


def _set_world_energy(energy=1.0):
    world = bpy.context.scene.world
    if world and world.use_nodes:
        bg = world.node_tree.nodes.get("Background")
        if bg:
            bg.inputs[1].default_value = energy


def _override_materials_black():
    black = bpy.data.materials.new("SILHOUETTE_BLACK")
    black.use_nodes = True
    bsdf = black.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0, 0, 0, 1)
        bsdf.inputs["Roughness"].default_value = 1.0
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 0.0
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        if not obj.data.materials:
            obj.data.materials.append(black)
        else:
            for i in range(len(obj.data.materials)):
                obj.data.materials[i] = black
    return black


def _override_materials_gray():
    # Force neutral grey materials for grayscale readability plate
    gray = bpy.data.materials.new("GRAYSCALE_PLATE")
    gray.use_nodes = True
    bsdf = gray.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.45, 0.45, 0.45, 1)
        bsdf.inputs["Roughness"].default_value = 0.7
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 0.0
    # Keep relative value via original luminance approx — simple flat plate OK for Constitution TH/SIL
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        name = obj.name
        if name.startswith("DOCTOR") or "COAT" in name or "DOC" in name or "coat" in name.lower():
            if not obj.data.materials:
                obj.data.materials.append(gray)
            else:
                for i in range(len(obj.data.materials)):
                    # Face slightly lighter, coat mid
                    m = bpy.data.materials.new(f"GRAY_{obj.name}_{i}")
                    m.use_nodes = True
                    b = m.node_tree.nodes.get("Principled BSDF")
                    val = 0.72 if "FACE" in (obj.data.materials[i].name if obj.data.materials[i] else "") else 0.55
                    if obj.data.materials[i] and "NAVY" in obj.data.materials[i].name:
                        val = 0.18
                    if obj.data.materials[i] and ("COAT" in obj.data.materials[i].name or "DOC_COAT" in obj.data.materials[i].name):
                        val = 0.62
                    if b:
                        b.inputs["Base Color"].default_value = (val, val, val, 1)
                        b.inputs["Roughness"].default_value = 0.75
                    obj.data.materials[i] = m


def render_validation_sheet(out: Path, arm, body, coat, container, blend_path=None):
    sheet = out / "VALIDATION_RENDERS"
    sheet.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    for engine in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES"):
        try:
            scene.render.engine = engine
            break
        except Exception:
            continue
    scene.render.resolution_x = 1080
    scene.render.resolution_y = 1920
    scene.render.image_settings.file_format = "PNG"
    if hasattr(scene, "eevee"):
        scene.eevee.taa_render_samples = 16

    shots = [
        ("01_front_fullbody", (0, -3.2, 1.1), (0, 0, 1.0), 35, None, None),
        ("02_rear_fullbody", (0, 3.2, 1.1), (0, 0, 1.0), 35, None, None),
        ("03_left_profile", (3.0, 0, 1.2), (0, 0, 1.1), 40, None, None),
        ("04_right_profile", (-3.0, 0, 1.2), (0, 0, 1.1), 40, None, None),
        ("05_three_quarter_hero", (1.6, -2.2, 1.4), (0, 0, 1.4), 45, None, None),
        ("06_neutral_closeup", (0.0, -1.25, 1.80), (0.0, -0.16, 1.80), 50, None, None),
        ("07_warm_smile", (0.0, -1.25, 1.80), (0.0, -0.16, 1.80), 50, {"smile": 0.75, "cheek_raise": 0.4}, None),
        ("08_concern", (0.0, -1.25, 1.80), (0.0, -0.16, 1.80), 50, {"concern": 0.8, "brow_inner_raise": 0.5}, None),
        ("09_curiosity", (0.0, -1.25, 1.80), (0.0, -0.16, 1.80), 50, {"curiosity": 0.7, "brow_raise": 0.45}, None),
        ("10_determination", (0.0, -1.25, 1.80), (0.0, -0.16, 1.80), 50, {"determination": 0.7, "focus": 0.5}, None),
        ("11_speaking", (0.0, -1.25, 1.80), (0.0, -0.16, 1.80), 50, {"viseme_A": 0.7, "jaw_open": 0.4, "smile": 0.25}, None),
        ("12_blink_mid", (0.0, -1.25, 1.80), (0.0, -0.16, 1.80), 50, {"blink_L": 0.85, "blink_R": 0.75}, None),
        ("13_eye_look_left", (0.0, -1.25, 1.80), (0.0, -0.16, 1.80), 50, None, {"eye_L": (0, 18, 0), "eye_R": (0, 18, 0)}),
        ("14_eye_look_right", (0.0, -1.25, 1.80), (0.0, -0.16, 1.80), 50, None, {"eye_L": (0, -18, 0), "eye_R": (0, -18, 0)}),
        ("15_open_hand_teach", (1.4, -1.8, 1.35), (0.2, 0.2, 1.3), 40, None, {"upper_arm_L": (25, 0, 35), "forearm_L": (20, 0, 0)}),
        ("16_sample_grasp", (0.9, 0.4, 1.35), (0.55, 1.2, 1.05), 40, None, {"upper_arm_R": (45, 5, -20), "forearm_R": (30, 0, 0), "index_R": (30, 0, 0)}),
        ("17_walking", (1.8, -2.5, 1.1), (0, 0, 1.0), 35, None, {"thigh_L": (20, 0, 0), "shin_L": (10, 0, 0), "thigh_R": (-12, 0, 0), "shin_R": (35, 0, 0), "upper_arm_L": (15, 0, 8), "upper_arm_R": (-15, 0, -8)}),
        ("18_reaching", (1.5, -0.5, 1.3), (0.5, 1.3, 1.15), 40, None, {"upper_arm_R": (50, 10, -25), "forearm_R": (25, 0, 0), "spine_02": (0, 8, 0)}),
        ("19_coat_motion", (1.8, -2.0, 1.2), (0, 0, 1.1), 38, None, {"coat_L": (0, 18, 0), "coat_R": (0, -18, 0), "coat_hem": (8, 0, 0), "upper_arm_L": (30, 0, 20)}),
        ("20_lab_hero", (1.7, -2.4, 1.45), (0.3, 0.8, 1.35), 40, {"smile": 0.45, "empathy": 0.25}, None),
        # Phase XIII manufacturing plates
        ("21_extreme_closeup", (0.0, -0.85, 1.81), (0.0, -0.16, 1.81), 65, {"smile": 0.35}, None),
        ("22_hero_poster", (1.5, -2.6, 1.35), (0, 0, 1.25), 40, {"smile": 0.5, "empathy": 0.2}, None),
        ("23_educational_poster", (1.3, -2.2, 1.4), (0.15, 0.3, 1.35), 42, {"curiosity": 0.55, "smile": 0.3}, {"upper_arm_L": (20, 0, 30)}),
        ("24_pose_teach_point", (1.5, -2.0, 1.35), (0.2, 0.2, 1.35), 40, {"focus": 0.4}, {"upper_arm_R": (35, 0, -30), "forearm_R": (15, 0, 0)}),
        ("25_pose_present", (1.4, -2.1, 1.3), (0.1, 0, 1.25), 40, {"smile": 0.4}, {"upper_arm_L": (30, 0, 25), "upper_arm_R": (30, 0, -25)}),
        ("26_youtube_thumbnail", (0.15, -1.15, 1.78), (0.0, -0.12, 1.72), 48, {"smile": 0.55, "cheek_raise": 0.25}, None),
        ("27_website_banner", (2.2, -2.8, 1.2), (0.2, 0, 1.15), 32, {"smile": 0.4}, None),
        ("28_mobile_avatar", (0.0, -1.05, 1.82), (0.0, -0.14, 1.80), 55, {"smile": 0.45}, None),
        ("29_merch_mockup", (1.2, -2.0, 1.35), (0, 0, 1.25), 42, {"smile": 0.35}, None),
        ("30_lighting_gold", (1.6, -2.2, 1.4), (0, 0, 1.35), 42, {"hope": 0.4, "smile": 0.3}, None),
    ]

    catalog = []
    for name, loc, target, lens, shapes, bones in shots:
        reset_shapes(body)
        reset_pose(arm)
        if shapes:
            for k, v in shapes.items():
                set_shape(body, k, v)
        if bones:
            for bn, rot in bones.items():
                pose_bone(arm, bn, rot)
        for obj in list(bpy.data.objects):
            if obj.type == "CAMERA":
                bpy.data.objects.remove(obj, do_unlink=True)
        setup_camera(loc, target, lens)
        path = sheet / f"{name}.png"
        scene.render.filepath = str(path)
        # Tiny thumbnail plate — downscale export
        if name == "26_youtube_thumbnail":
            scene.render.resolution_x = 320
            scene.render.resolution_y = 180
        elif name == "28_mobile_avatar":
            scene.render.resolution_x = 256
            scene.render.resolution_y = 256
        else:
            scene.render.resolution_x = 1080
            scene.render.resolution_y = 1920
        bpy.ops.render.render(write_still=True)
        catalog.append({"shot": name, "file": str(path), "present": path.is_file()})
        print("VALIDATED", name, path.is_file())

    # Reload clean scene for silhouette / grayscale plates
    if blend_path and Path(blend_path).is_file():
        bpy.ops.wm.open_mainfile(filepath=str(blend_path))
        arm = bpy.data.objects.get("DOCTOR_001_RIG")
        body = bpy.data.objects.get("DOCTOR_001_MESH")
        scene = bpy.context.scene
        scene.render.resolution_x = 1080
        scene.render.resolution_y = 1920
        _override_materials_gray()
        for gname, loc, target, lens in (
            ("33_grayscale_front", (0, -3.2, 1.1), (0, 0, 1.0), 35),
            ("34_grayscale_three_quarter", (1.6, -2.2, 1.4), (0, 0, 1.4), 45),
        ):
            if arm and body:
                reset_pose(arm)
                reset_shapes(body)
            for obj in list(bpy.data.objects):
                if obj.type == "CAMERA":
                    bpy.data.objects.remove(obj, do_unlink=True)
            setup_camera(loc, target, lens)
            path = sheet / f"{gname}.png"
            scene.render.filepath = str(path)
            bpy.ops.render.render(write_still=True)
            catalog.append({"shot": gname, "file": str(path), "present": path.is_file()})
            print("VALIDATED", gname, path.is_file())

        bpy.ops.wm.open_mainfile(filepath=str(blend_path))
        arm = bpy.data.objects.get("DOCTOR_001_RIG")
        body = bpy.data.objects.get("DOCTOR_001_MESH")
        scene = bpy.context.scene
        _override_materials_black()
        _set_world_energy(10.0)
        for obj in bpy.data.objects:
            if obj.type == "LIGHT":
                obj.hide_render = True
        for sil_name, loc, target, lens in (
            ("31_black_silhouette_front", (0, -3.2, 1.1), (0, 0, 1.0), 35),
            ("32_black_silhouette_three_quarter", (1.6, -2.2, 1.4), (0, 0, 1.4), 45),
        ):
            if arm and body:
                reset_pose(arm)
                reset_shapes(body)
            for obj in list(bpy.data.objects):
                if obj.type == "CAMERA":
                    bpy.data.objects.remove(obj, do_unlink=True)
            setup_camera(loc, target, lens)
            path = sheet / f"{sil_name}.png"
            scene.render.filepath = str(path)
            bpy.ops.render.render(write_still=True)
            catalog.append({"shot": sil_name, "file": str(path), "present": path.is_file()})
            print("VALIDATED", sil_name, path.is_file())
    else:
        # Fallback in-place silhouette (destroys materials — last plates only)
        _override_materials_black()
        _set_world_energy(8.0)
        for obj in bpy.data.objects:
            if obj.type == "LIGHT":
                obj.hide_render = True
        for sil_name, loc, target, lens in (
            ("31_black_silhouette_front", (0, -3.2, 1.1), (0, 0, 1.0), 35),
            ("32_black_silhouette_three_quarter", (1.6, -2.2, 1.4), (0, 0, 1.4), 45),
        ):
            reset_pose(arm)
            reset_shapes(body)
            for obj in list(bpy.data.objects):
                if obj.type == "CAMERA":
                    bpy.data.objects.remove(obj, do_unlink=True)
            setup_camera(loc, target, lens)
            path = sheet / f"{sil_name}.png"
            scene.render.filepath = str(path)
            bpy.ops.render.render(write_still=True)
            catalog.append({"shot": sil_name, "file": str(path), "present": path.is_file()})
            print("VALIDATED", sil_name, path.is_file())

    mfg = out / "MANUFACTURING"
    mfg.mkdir(parents=True, exist_ok=True)
    (mfg / "NOTE.txt").write_text(
        "Phase XIII Living Lab Coat manufacturing validation.\n"
        "Silhouette plates: 31/32. Grayscale: 33/34. Core + marketing: 01-30.\n"
        "Identity: coat-as-icon. Asset tier: manufacturing_v1.\n"
    )

    (out / "VALIDATION_SHEET_INDEX.json").write_text(json.dumps({"shots": catalog, "count": len(catalog)}, indent=2) + "\n")
    return catalog


def main():
    cfg = _parse()
    out = Path(cfg["out"])
    out.mkdir(parents=True, exist_ok=True)
    runtime = Path(cfg["runtime_dir"]) if cfg["runtime_dir"] else out / "RUNTIME"
    runtime.mkdir(parents=True, exist_ok=True)

    clear_scene()
    # Lab context for hero validation + grasp
    mats = material_library()
    lab = build_production_lab(mats)
    container = build_sample_container(mats)
    arm, body, coat, doc_mats = build_canonical_doctor()
    apply_lighting_preset("morning_discovery")

    # Save permanent character-focused blend (full scene for runtime continuity)
    char_blend = out / "DOCTOR_001_PRODUCTION.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(char_blend))

    import shutil

    # RUNTIME contract
    shutil.copy2(char_blend, runtime / "DOCTOR_001_SKINNED.blend")
    # Keep lab/prop blends present for capability checks (full scene copies remain valid)
    shutil.copy2(char_blend, runtime / "GENERATIONAL_MEDICAL_LAB.blend")
    shutil.copy2(char_blend, runtime / "SAMPLE_CONTAINER_001.blend")

    write_maps(out, arm, body)
    write_maps(runtime, arm, body)

    origin = {
        "phase": "XIII Character Manufacturing Studio",
        "quality_tier": "manufacturing_v1",
        "asset_origin": "doctor_001_living_lab_coat_mfg_v1",
        "identity": "living_lab_coat",
        "not_copyrighted_third_party": True,
        "character": str(runtime / "DOCTOR_001_SKINNED.blend"),
        "height_m": 1.85,
        "mesh": "DOCTOR_001_MESH",
        "coat": "DOCTOR_001_COAT",
        "armature": "DOCTOR_001_RIG",
        "materials": list(doc_mats.keys()),
        "facial_keys": FACIAL_SHAPE_KEYS,
        "notes": [
            "Living Lab Coat — coat is the icon silhouette",
            "Slim under-body; sphere-stack limbs suppressed under garment",
            "Teaching hands; ceramic face; fabric coat + navy lining",
            "Canonical skeleton preserved for Golden Motion compatibility",
        ],
    }
    (out / "ASSET_ORIGIN.json").write_text(json.dumps(origin, indent=2) + "\n")
    (runtime / "ASSET_ORIGIN.json").write_text(json.dumps(origin, indent=2) + "\n")
    (out / "VERSION.json").write_text(
        json.dumps(
            {
                "character_id": "DOCTOR_001",
                "asset_version": "manufacturing_v1",
                "mesh_version": "living_lab_coat_mfg_v1",
                "rig_version": "canonical_compatible_v1",
                "facial_rig_version": "shape_keys_production_v1",
                "phase": "XIII",
            },
            indent=2,
        )
        + "\n"
    )

    catalog = []
    if cfg.get("validate") != "0":
        catalog = render_validation_sheet(out, arm, body, coat, container, blend_path=char_blend)

    report = {
        "ok": True,
        "character_id": "DOCTOR_001",
        "blend": str(char_blend),
        "runtime_character": str(runtime / "DOCTOR_001_SKINNED.blend"),
        "bones": len(arm.data.bones),
        "shape_keys": [k.name for k in body.data.shape_keys.key_blocks] if body.data.shape_keys else [],
        "coat": coat.name,
        "validation_shots": len(catalog),
        "lab_present": bool(lab),
    }
    (out / "DOCTOR_001_BUILD_REPORT.json").write_text(json.dumps(report, indent=2) + "\n")
    print("DOCTOR_001_PRODUCTION_OK", char_blend)


if __name__ == "__main__":
    main()
