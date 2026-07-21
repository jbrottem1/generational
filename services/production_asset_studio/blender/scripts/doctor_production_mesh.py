"""Permanent DOCTOR_001 production mesh builders.

Preserves canonical bone names + facial shape-key contract for BlenderRuntime.
Upgrades greybox primitives into a polished, reusable medical-android hero asset.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector

# Import shared palette/bones/helpers from production_builders when available
PALETTE = {
    "dawn_white": (0.968, 0.957, 0.937, 1.0),
    "warm_sand": (0.910, 0.875, 0.824, 1.0),
    "teal": (0.184, 0.620, 0.737, 1.0),
    "navy": (0.106, 0.165, 0.290, 1.0),
    "skin_shell": (0.94, 0.93, 0.91, 1.0),  # white ceramic-composite
    "skin_warm": (0.88, 0.78, 0.70, 1.0),   # face warmth under ceramic glaze
    "iris": (0.25, 0.55, 0.72, 1.0),
    "iris_glow": (0.45, 0.75, 0.95, 1.0),
    "metal": (0.55, 0.58, 0.62, 1.0),
}

# Canonical body bones — MUST stay compatible with Golden Motion
BONES = [
    ("root", None, (0, 0, 0), (0, 0, 0.05)),
    ("pelvis", "root", (0, 0, 0.95), (0, 0, 1.05)),
    ("spine_01", "pelvis", (0, 0, 1.05), (0, 0, 1.25)),
    ("spine_02", "spine_01", (0, 0, 1.25), (0, 0, 1.4)),
    ("chest", "spine_02", (0, 0, 1.4), (0, 0, 1.55)),
    ("neck", "chest", (0, 0, 1.55), (0, 0, 1.66)),
    ("head", "neck", (0, 0, 1.66), (0, 0, 1.90)),
    ("jaw", "head", (0, -0.03, 1.74), (0, -0.08, 1.70)),
    ("eye_L", "head", (0.052, -0.155, 1.810), (0.052, -0.195, 1.810)),
    ("eye_R", "head", (-0.052, -0.155, 1.810), (-0.052, -0.195, 1.810)),
    ("lid_upper_L", "head", (0.052, -0.160, 1.840), (0.052, -0.180, 1.840)),
    ("lid_upper_R", "head", (-0.052, -0.160, 1.840), (-0.052, -0.180, 1.840)),
    ("lid_lower_L", "head", (0.052, -0.160, 1.782), (0.052, -0.180, 1.782)),
    ("lid_lower_R", "head", (-0.052, -0.160, 1.782), (-0.052, -0.180, 1.782)),
    ("clavicle_L", "chest", (0.06, 0, 1.52), (0.20, 0, 1.52)),
    ("upper_arm_L", "clavicle_L", (0.20, 0, 1.52), (0.46, 0, 1.24)),
    ("forearm_L", "upper_arm_L", (0.46, 0, 1.24), (0.64, 0, 1.04)),
    ("hand_L", "forearm_L", (0.64, 0, 1.04), (0.74, 0, 1.00)),
    ("thumb_L", "hand_L", (0.72, 0.03, 1.00), (0.78, 0.05, 0.98)),
    ("index_L", "hand_L", (0.76, 0.01, 1.00), (0.86, 0.01, 0.98)),
    ("middle_L", "hand_L", (0.76, -0.01, 1.00), (0.87, -0.01, 0.98)),
    ("ring_L", "hand_L", (0.75, -0.025, 1.00), (0.84, -0.03, 0.98)),
    ("clavicle_R", "chest", (-0.06, 0, 1.52), (-0.20, 0, 1.52)),
    ("upper_arm_R", "clavicle_R", (-0.20, 0, 1.52), (-0.46, 0, 1.24)),
    ("forearm_R", "upper_arm_R", (-0.46, 0, 1.24), (-0.64, 0, 1.04)),
    ("hand_R", "forearm_R", (-0.64, 0, 1.04), (-0.74, 0, 1.00)),
    ("thumb_R", "hand_R", (-0.72, 0.03, 1.00), (-0.78, 0.05, 0.98)),
    ("index_R", "hand_R", (-0.76, 0.01, 1.00), (-0.86, 0.01, 0.98)),
    ("middle_R", "hand_R", (-0.76, -0.01, 1.00), (-0.87, -0.01, 0.98)),
    ("ring_R", "hand_R", (-0.75, -0.025, 1.00), (-0.84, -0.03, 0.98)),
    ("thigh_L", "pelvis", (0.12, 0, 0.95), (0.13, 0, 0.50)),
    ("shin_L", "thigh_L", (0.13, 0, 0.50), (0.13, 0, 0.12)),
    ("foot_L", "shin_L", (0.13, 0, 0.12), (0.13, 0.14, 0.02)),
    ("toe_L", "foot_L", (0.13, 0.14, 0.02), (0.13, 0.20, 0.02)),
    ("thigh_R", "pelvis", (-0.12, 0, 0.95), (-0.13, 0, 0.50)),
    ("shin_R", "thigh_R", (-0.13, 0, 0.50), (-0.13, 0, 0.12)),
    ("foot_R", "shin_R", (-0.13, 0, 0.12), (-0.13, 0.14, 0.02)),
    ("toe_R", "foot_R", (-0.13, 0.14, 0.02), (-0.13, 0.20, 0.02)),
    ("coat_L", "chest", (0.24, -0.05, 1.38), (0.30, -0.10, 0.92)),
    ("coat_R", "chest", (-0.24, -0.05, 1.38), (-0.30, -0.10, 0.92)),
    ("coat_hem", "chest", (0, -0.08, 1.10), (0, -0.12, 0.85)),
]

FACIAL_SHAPE_KEYS = [
    "jaw_open",
    "smile",
    "concern",
    "blink_L",
    "blink_R",
    "upper_lid_raise_L",
    "upper_lid_raise_R",
    "eye_squint",
    "brow_raise",
    "brow_inner_raise",
    "brow_outer_raise",
    "brow_lower",
    "cheek_raise",
    "nose_tension",
    "lip_widen",
    "lip_funnel",
    "lip_pucker",
    "lip_press",
    "lip_roll",
    "mouth_corners_up",
    "mouth_corners_down",
    "surprise",
    "focus",
    "empathy",
    "joy",
    "curiosity",
    "determination",
    "hope",
    "amusement",
    "sadness",
    "viseme_REST",
    "viseme_M",
    "viseme_A",
    "viseme_E",
    "viseme_O",
    "viseme_U",
    "viseme_F",
    "viseme_L",
    "viseme_WQ",
    "viseme_smile_speak",
    "viseme_concern_speak",
]


def pbr(
    name: str,
    *,
    base=(0.8, 0.8, 0.8, 1),
    metallic=0.0,
    rough=0.5,
    specular=0.5,
    emission=None,
    emission_strength=0.0,
    alpha=1.0,
    subsurface=0.0,
):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if not bsdf:
        return m
    bsdf.inputs["Base Color"].default_value = base
    if "Metallic" in bsdf.inputs:
        bsdf.inputs["Metallic"].default_value = metallic
    if "Roughness" in bsdf.inputs:
        bsdf.inputs["Roughness"].default_value = rough
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = specular
    elif "Specular" in bsdf.inputs:
        bsdf.inputs["Specular"].default_value = specular
    if emission and "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = emission
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = emission_strength
    # Microscopic roughness variation via noise (subtle — avoid dirty smudging on hero face)
    nt = m.node_tree
    tex = nt.nodes.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = 120.0 if "FACE" in name or "SCLERA" in name else 85.0
    tex.inputs["Detail"].default_value = 4.0
    tex.location = (-400, 0)
    ramp = nt.nodes.new("ShaderNodeMapRange")
    spread = 0.04 if "FACE" in name else 0.12
    ramp.inputs["From Min"].default_value = 0.35
    ramp.inputs["From Max"].default_value = 0.65
    ramp.inputs["To Min"].default_value = max(0.05, rough - spread)
    ramp.inputs["To Max"].default_value = min(0.95, rough + spread)
    ramp.location = (-200, 0)
    nt.links.new(tex.outputs["Fac"], ramp.inputs["Value"])
    nt.links.new(ramp.outputs["Result"], bsdf.inputs["Roughness"])
    if alpha < 1.0:
        m.blend_method = "BLEND"
        if "Alpha" in bsdf.inputs:
            bsdf.inputs["Alpha"].default_value = alpha
    if subsurface > 0 and "Subsurface Weight" in bsdf.inputs:
        bsdf.inputs["Subsurface Weight"].default_value = subsurface
    return m


def doctor_materials() -> dict:
    return {
        "shell": pbr("DOC_SHELL", base=PALETTE["skin_shell"], rough=0.38, metallic=0.05, specular=0.55),
        "face_shell": pbr("DOC_FACE", base=PALETTE["skin_warm"], rough=0.36, metallic=0.02, specular=0.5, subsurface=0.08),
        "navy": pbr("DOC_NAVY", base=PALETTE["navy"], rough=0.42, metallic=0.15),
        "metal": pbr("DOC_METAL", base=PALETTE["metal"], rough=0.28, metallic=0.9),
        "coat": pbr("DOC_COAT", base=PALETTE["dawn_white"], rough=0.92, metallic=0.0, specular=0.18),
        "coat_lining": pbr("DOC_LINING", base=PALETTE["navy"], rough=0.78, metallic=0.05, specular=0.2),
        "coat_trim": pbr(
            "DOC_TRIM",
            base=PALETTE["teal"],
            rough=0.55,
            metallic=0.08,
            emission=PALETTE["teal"],
            emission_strength=0.08,
        ),
        "sclera": pbr("DOC_SCLERA", base=(0.97, 0.965, 0.955, 1), rough=0.18),
        "iris": pbr(
            "DOC_IRIS",
            base=(0.18, 0.42, 0.55, 1),
            rough=0.32,
            metallic=0.0,
            emission=(0.25, 0.45, 0.55, 1),
            emission_strength=0.06,
        ),
        "pupil": pbr("DOC_PUPIL", base=(0.008, 0.01, 0.012, 1), rough=0.4),
        "cornea": pbr("DOC_CORNEA", base=(0.92, 0.96, 1.0, 1), rough=0.03, alpha=0.22),
        "lid": pbr("DOC_LID", base=(0.84, 0.74, 0.66, 1), rough=0.52),
        "hand": pbr("DOC_HAND", base=PALETTE["skin_shell"], rough=0.42, metallic=0.03, specular=0.45),
        "rubber": pbr("DOC_RUBBER", base=(0.08, 0.09, 0.12, 1), rough=0.75),
        "insignia": pbr(
            "DOC_INSIGNIA",
            base=PALETTE["teal"],
            rough=0.38,
            emission=PALETTE["teal"],
            emission_strength=0.45,
        ),
        "joint_fairing": pbr(
            "DOC_JOINT",
            base=PALETTE["navy"],
            rough=0.55,
            metallic=0.08,
        ),
    }


def _apply_smooth(obj, levels=1):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    mod = obj.modifiers.new("SUBSURF", "SUBSURF")
    mod.levels = levels
    mod.render_levels = max(levels, 2)
    bpy.ops.object.modifier_apply(modifier="SUBSURF")
    bpy.ops.object.shade_smooth()
    obj.select_set(False)


def _sphere(name, r, loc, mat, *, segments=32, rings=20, smooth=1):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=segments, ring_count=rings)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(mat)
    if smooth:
        _apply_smooth(o, smooth)
    return o


def _cyl(name, r, depth, loc, mat, *, verts=24, rot=(0, 0, 0), smooth=1):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=loc, vertices=verts, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(mat)
    if smooth:
        _apply_smooth(o, smooth)
    return o


def _box(name, scale, loc, mat, *, smooth=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mat)
    if smooth:
        _apply_smooth(o, smooth)
    return o


def _capsule(name, r, length, loc, mat, *, axis="z", smooth=1):
    """Limb capsule: cylinder + hemispherical ends."""
    parts = []
    if axis == "z":
        parts.append(_cyl(f"{name}_shaft", r, length, loc, mat, verts=20, smooth=0))
        parts.append(_sphere(f"{name}_a", r, (loc[0], loc[1], loc[2] + length * 0.5), mat, segments=16, rings=10, smooth=0))
        parts.append(_sphere(f"{name}_b", r, (loc[0], loc[1], loc[2] - length * 0.5), mat, segments=16, rings=10, smooth=0))
    bpy.ops.object.select_all(action="DESELECT")
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    o = bpy.context.object
    o.name = name
    if smooth:
        _apply_smooth(o, smooth)
    return o


def _apply_world_transform(obj):
    """Bake object transform into mesh data so vertex coords match world bone heads."""
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    obj.select_set(False)


def _assign_skin_weights(mesh_obj, arm_obj):
    mesh_obj.vertex_groups.clear()
    bone_pts = []
    for name, _p, head, tail in BONES:
        h, t = Vector(head), Vector(tail)
        bone_pts.append((name, h, t, (t - h).length + 1e-6))
        mesh_obj.vertex_groups.new(name=name)
    eye_L = Vector((0.052, -0.168, 1.810))
    eye_R = Vector((-0.052, -0.168, 1.810))
    jaw_pt = Vector((0.0, -0.048, 1.702))
    for vi, v in enumerate(mesh_obj.data.vertices):
        # Prefer dedicated eye / jaw bindings for face performance
        if (v.co - eye_L).length < 0.068:
            mesh_obj.vertex_groups["eye_L"].add([vi], 1.0, "REPLACE")
            continue
        if (v.co - eye_R).length < 0.068:
            mesh_obj.vertex_groups["eye_R"].add([vi], 1.0, "REPLACE")
            continue
        if v.co.z < 1.76 and v.co.y < -0.04 and abs(v.co.x) < 0.10 and (v.co - jaw_pt).length < 0.13:
            mesh_obj.vertex_groups["jaw"].add([vi], 1.0, "REPLACE")
            continue
        best_name, best_d = "pelvis", 1e9
        for name, h, t, length in bone_pts:
            if name.startswith(("eye_", "lid_", "jaw", "coat_")):
                continue
            w = t - h
            if w.length < 1e-8:
                d = (v.co - h).length
            else:
                u = max(0.0, min(1.0, (v.co - h).dot(w) / w.length_squared))
                d = (v.co - (h + w * u)).length
            score = d / max(0.07, length * 0.32)
            if score < best_d:
                best_d = score
                best_name = name
        mesh_obj.vertex_groups[best_name].add([vi], 1.0, "REPLACE")
    mod = mesh_obj.modifiers.new(name="Armature", type="ARMATURE")
    mod.object = arm_obj
    mod.use_vertex_groups = True
    mesh_obj.parent = arm_obj


def _build_armature():
    arm_data = bpy.data.armatures.new("DOCTOR_001_ARMATURE")
    arm_obj = bpy.data.objects.new("DOCTOR_001_RIG", arm_data)
    bpy.context.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="EDIT")
    created = {}
    for name, parent, head, tail in BONES:
        b = arm_data.edit_bones.new(name)
        b.head = Vector(head)
        b.tail = Vector(tail)
        if parent:
            b.parent = created[parent]
        created[name] = b
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm_obj


def _add_facial_keys(mesh_obj):
    """Iter 001: stronger readable deltas for smile, lids, brows, mouth (same key names)."""
    bpy.context.view_layer.objects.active = mesh_obj
    if not mesh_obj.data.shape_keys:
        mesh_obj.shape_key_add(name="Basis", from_mix=False)
    for sk in FACIAL_SHAPE_KEYS:
        key = mesh_obj.shape_key_add(name=sk, from_mix=False)
        key.value = 0.0
        for vi, v in enumerate(mesh_obj.data.vertices):
            if v.co.z < 1.60:
                continue
            x, y, z = v.co.x, v.co.y, v.co.z
            face = y < 0.02  # face plane toward -Y cameras
            if sk == "jaw_open":
                if y < -0.02 and z < 1.78:
                    key.data[vi].co.z -= 0.034
                    key.data[vi].co.y -= 0.022
            elif sk in {"smile", "joy", "amusement", "mouth_corners_up", "viseme_smile_speak"}:
                # Wide, readable smile — corners up + out, upper cheeks lift
                if face and z < 1.80:
                    key.data[vi].co.x += 0.028 * (1 if x > 0 else -1) * (0.35 + abs(x) * 4)
                    key.data[vi].co.z += 0.012 + abs(x) * 0.08
                    if abs(x) < 0.03 and z < 1.74:
                        key.data[vi].co.z += 0.006  # soft lip curve
                if face and 1.72 < z < 1.82 and abs(x) > 0.04:
                    key.data[vi].co.z += 0.01  # cheek raise companion
            elif sk in {"concern", "sadness", "mouth_corners_down", "viseme_concern_speak"}:
                if face:
                    key.data[vi].co.z += 0.01 if z > 1.84 else -0.01
                    key.data[vi].co.x += 0.006 * (1 if x > 0 else -1)
            elif sk == "blink_L":
                if x > 0 and 1.76 < z < 1.86 and y < 0.05:
                    key.data[vi].co.z -= 0.028
                    key.data[vi].co.y += 0.006
            elif sk == "blink_R":
                if x < 0 and 1.76 < z < 1.86 and y < 0.05:
                    key.data[vi].co.z -= 0.028
                    key.data[vi].co.y += 0.006
            elif sk in {"upper_lid_raise_L", "upper_lid_raise_R"}:
                side_ok = (x > 0) if sk.endswith("_L") else (x < 0)
                if side_ok and z > 1.80 and y < 0.05:
                    key.data[vi].co.z += 0.014
            elif sk == "eye_squint":
                if 1.76 < z < 1.86 and y < 0.05:
                    key.data[vi].co.z -= 0.014
            elif sk in {"brow_raise", "brow_inner_raise", "brow_outer_raise"}:
                if z > 1.845 and y < 0.05:
                    key.data[vi].co.z += 0.018
                    if sk == "brow_inner_raise" and abs(x) < 0.05:
                        key.data[vi].co.z += 0.006
                    if sk == "brow_outer_raise" and abs(x) > 0.04:
                        key.data[vi].co.z += 0.006
            elif sk == "brow_lower":
                if z > 1.845 and y < 0.05:
                    key.data[vi].co.z -= 0.014
            elif sk in {"cheek_raise", "empathy"}:
                if face and 1.70 < z < 1.82:
                    key.data[vi].co.x += 0.016 * (1 if x > 0 else -1)
                    key.data[vi].co.z += 0.008
            elif sk == "nose_tension":
                if abs(x) < 0.04 and 1.76 < z < 1.84 and y < 0:
                    key.data[vi].co.y -= 0.005
            elif sk == "lip_widen":
                if z < 1.78 and y < 0:
                    key.data[vi].co.x += 0.022 * (1 if x > 0 else -1)
            elif sk in {"lip_funnel", "lip_pucker", "viseme_U", "viseme_WQ", "viseme_O"}:
                if z < 1.80 and y < 0:
                    key.data[vi].co.y -= 0.016
                    key.data[vi].co.x += -0.012 * (1 if x > 0 else -1)
            elif sk in {"lip_press", "lip_roll", "viseme_M"}:
                if z < 1.78 and y < 0:
                    key.data[vi].co.y += 0.01
                    key.data[vi].co.z += 0.004
            elif sk in {"surprise", "hope"}:
                if z > 1.82:
                    key.data[vi].co.z += 0.014
                if y < 0 and z < 1.78:
                    key.data[vi].co.z -= 0.016
            elif sk in {"focus", "determination", "curiosity"}:
                if z > 1.84 and y < 0.05:
                    key.data[vi].co.z += 0.01
                if sk == "curiosity" and abs(x) > 0.03 and z > 1.84:
                    key.data[vi].co.z += 0.004 * (1 if x > 0 else -1)  # micro asymmetry
            elif sk in {"viseme_A", "viseme_E"}:
                if y < 0 and z < 1.80:
                    key.data[vi].co.y -= 0.02
                    key.data[vi].co.z -= 0.016
            elif sk == "viseme_F":
                if y < -0.05 and z < 1.79:
                    key.data[vi].co.y -= 0.012
            elif sk == "viseme_L":
                if y < 0 and z < 1.79:
                    key.data[vi].co.y -= 0.014
    # Phase VIII resting expression: warmth + soft squint (trust)
    sks = mesh_obj.data.shape_keys.key_blocks
    if "smile" in sks:
        sks["smile"].value = 0.38
    if "eye_squint" in sks:
        sks["eye_squint"].value = 0.16
    if "cheek_raise" in sks:
        sks["cheek_raise"].value = 0.14
    if "empathy" in sks:
        sks["empathy"].value = 0.10
    if "mouth_corners_up" in sks:
        sks["mouth_corners_up"].value = 0.12


def _egg_sphere(name, r, loc, mat, *, scale=(1.0, 1.14, 1.10), segments=48, rings=28, smooth=2):
    """Soft egg head — kills perfect UV-sphere robot read (Phase VIII)."""
    o = _sphere(name, r, loc, mat, segments=segments, rings=rings, smooth=0)
    o.scale = scale
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if smooth:
        _apply_smooth(o, smooth)
    return o


def build_canonical_doctor() -> tuple:
    """Manufacture DOCTOR_001 — Living Lab Coat (Phase XIII).

    Identity: coat is the icon. Same bones / shape-key names (architecture frozen).
    """
    mats = doctor_materials()
    arm = _build_armature()
    parts = []
    origin = _box("DOC_ORIGIN", (0.001, 0.001, 0.001), (0, 0, 0), mats["shell"], smooth=0)
    parts.append(origin)

    # --- HEAD: soft egg nested for collar cradle ---
    parts.append(
        _egg_sphere(
            "head_shell",
            0.128,
            (0, 0.012, 1.795),
            mats["face_shell"],
            scale=(1.04, 1.12, 1.08),
            segments=56,
            rings=32,
            smooth=2,
        )
    )
    cranial = _sphere("cranial_panel", 0.078, (0, 0.048, 1.868), mats["navy"], segments=24, rings=14, smooth=0)
    cranial.scale = (1.10, 0.92, 0.48)
    bpy.ops.object.select_all(action="DESELECT")
    cranial.select_set(True)
    bpy.context.view_layer.objects.active = cranial
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    _apply_smooth(cranial, 1)
    parts.append(cranial)

    parts.append(_box("brow_L", (0.046, 0.014, 0.010), (0.048, -0.132, 1.868), mats["navy"], smooth=1))
    parts.append(_box("brow_R", (0.046, 0.014, 0.010), (-0.048, -0.132, 1.868), mats["navy"], smooth=1))
    parts.append(_box("nose_bridge", (0.014, 0.038, 0.044), (0, -0.148, 1.800), mats["face_shell"], smooth=1))
    parts.append(_sphere("nose_tip", 0.014, (0, -0.176, 1.774), mats["face_shell"], segments=14, rings=10, smooth=1))
    for side, sx in (("L", 1), ("R", -1)):
        cheek = _sphere(f"cheek_{side}", 0.026, (sx * 0.070, -0.082, 1.755), mats["face_shell"], segments=16, rings=12, smooth=0)
        cheek.scale = (0.78, 0.62, 0.88)
        bpy.ops.object.select_all(action="DESELECT")
        cheek.select_set(True)
        bpy.context.view_layer.objects.active = cheek
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        _apply_smooth(cheek, 1)
        parts.append(cheek)
    jaw = _sphere("jaw_mesh", 0.058, (0, -0.042, 1.708), mats["face_shell"], segments=24, rings=16, smooth=0)
    jaw.scale = (1.18, 0.82, 0.68)
    bpy.ops.object.select_all(action="DESELECT")
    jaw.select_set(True)
    bpy.context.view_layer.objects.active = jaw
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    _apply_smooth(jaw, 1)
    parts.append(jaw)
    parts.append(_box("lip_upper", (0.058, 0.015, 0.011), (0, -0.162, 1.750), mats["face_shell"], smooth=1))
    parts.append(_box("lip_lower", (0.052, 0.014, 0.012), (0, -0.160, 1.728), mats["face_shell"], smooth=1))
    parts.append(_box("mouth_gap", (0.040, 0.008, 0.007), (0, -0.168, 1.738), mats["navy"], smooth=0))
    parts.append(_sphere("mouth_corner_L", 0.012, (0.058, -0.152, 1.740), mats["face_shell"], segments=10, rings=8, smooth=0))
    parts.append(_sphere("mouth_corner_R", 0.012, (-0.058, -0.152, 1.740), mats["face_shell"], segments=10, rings=8, smooth=0))
    parts.append(_sphere("ear_L", 0.020, (0.132, 0.0, 1.790), mats["face_shell"], segments=12, rings=8, smooth=1))
    parts.append(_sphere("ear_R", 0.020, (-0.132, 0.0, 1.790), mats["face_shell"], segments=12, rings=8, smooth=1))

    for side, sx in (("L", 1), ("R", -1)):
        ex, ey, ez = sx * 0.050, -0.162, 1.812
        parts.append(_sphere(f"socket_{side}", 0.034, (ex, ey + 0.016, ez), mats["navy"], segments=20, rings=12, smooth=1))
        parts.append(_sphere(f"sclera_{side}", 0.031, (ex, ey, ez), mats["sclera"], segments=32, rings=20, smooth=1))
        parts.append(_sphere(f"iris_{side}", 0.0165, (ex, ey - 0.018, ez), mats["iris"], segments=24, rings=14, smooth=1))
        parts.append(_sphere(f"pupil_{side}", 0.010, (ex, ey - 0.028, ez), mats["pupil"], segments=14, rings=10, smooth=0))
        parts.append(_sphere(f"cornea_{side}", 0.032, (ex, ey - 0.005, ez), mats["cornea"], segments=24, rings=14, smooth=1))
        parts.append(
            _sphere(
                f"highlight_{side}",
                0.0030,
                (ex + sx * 0.007, ey - 0.030, ez + 0.007),
                mats["sclera"],
                segments=8,
                rings=6,
                smooth=0,
            )
        )
        parts.append(_box(f"lid_upper_{side}", (0.034, 0.016, 0.013), (ex, ey - 0.006, ez + 0.028), mats["lid"], smooth=1))
        parts.append(_box(f"lid_lower_{side}", (0.030, 0.014, 0.010), (ex, ey - 0.004, ez - 0.026), mats["lid"], smooth=1))

    # Slim under-body — coat owns silhouette
    parts.append(_cyl("neck_shell", 0.048, 0.09, (0, 0.02, 1.640), mats["shell"], verts=24, smooth=1))
    parts.append(_cyl("torso_slim", 0.12, 0.36, (0, 0.02, 1.32), mats["navy"], verts=24, smooth=1))
    parts.append(_cyl("pelvis_slim", 0.10, 0.10, (0, 0.02, 1.00), mats["navy"], verts=20, smooth=1))

    for side, sx in (("L", 1), ("R", -1)):
        parts.append(_capsule(f"farm_{side}", 0.038, 0.22, (sx * 0.52, -0.02, 1.08), mats["shell"], smooth=1))
        parts.append(_box(f"palm_{side}", (0.062, 0.036, 0.085), (sx * 0.68, -0.02, 0.98), mats["hand"], smooth=1))
        for fi, fz in enumerate((0.028, 0.010, -0.008, -0.024)):
            parts.append(
                _cyl(f"finger_{side}_{fi}", 0.012, 0.072, (sx * 0.80, fz - 0.02, 0.98), mats["hand"], verts=12, smooth=0)
            )
        parts.append(
            _cyl(
                f"thumb_{side}",
                0.014,
                0.055,
                (sx * 0.70, 0.040, 0.97),
                mats["hand"],
                verts=12,
                rot=(0, math.radians(40 * sx), 0),
                smooth=0,
            )
        )
        parts.append(_box(f"foot_{side}", (0.078, 0.16, 0.042), (sx * 0.12, 0.05, 0.032), mats["rubber"], smooth=1))
        parts.append(_cyl(f"ankle_{side}", 0.036, 0.08, (sx * 0.12, 0.02, 0.10), mats["shell"], verts=14, smooth=1))

    bpy.ops.object.select_all(action="DESELECT")
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = origin
    bpy.ops.object.join()
    body = bpy.context.object
    body.name = "DOCTOR_001_MESH"
    _apply_world_transform(body)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.ops.object.mode_set(mode="OBJECT")
    face_idx = next(
        (i for i, slot in enumerate(body.material_slots) if slot.material and slot.material.name == "DOC_FACE"),
        None,
    )
    eye_centers = [Vector((0.050, -0.162, 1.812)), Vector((-0.050, -0.162, 1.812))]
    for v in body.data.vertices:
        if v.co.length < 0.01:
            v.select = True
    if face_idx is not None:
        for poly in body.data.polygons:
            if poly.material_index != face_idx:
                continue
            for vi in poly.vertices:
                co = body.data.vertices[vi].co
                for ec in eye_centers:
                    if (co - ec).length < 0.046:
                        body.data.vertices[vi].select = True
                        break
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.delete(type="VERT")
    bpy.ops.object.mode_set(mode="OBJECT")
    _assign_skin_weights(body, arm)
    _add_facial_keys(body)

    # --- COAT: THE ICON (continuous A-line — not disc stack) ---
    coat_origin = _box("COAT_ORIGIN", (0.001, 0.001, 0.001), (0, 0, 0), mats["coat"], smooth=0)
    coat_parts = [coat_origin]
    # Single continuous body volume (tall cylinder) + flare base — avoid stacked saucers
    coat_parts.append(_cyl("coat_body", 0.28, 1.05, (0, -0.05, 0.95), mats["coat"], verts=48, smooth=2))
    coat_parts.append(_cyl("coat_hem_flare", 0.36, 0.22, (0, -0.06, 0.38), mats["coat"], verts=48, smooth=2))
    coat_parts.append(_cyl("coat_hem_edge", 0.40, 0.10, (0, -0.06, 0.24), mats["coat"], verts=40, smooth=1))
    # Soft A-line widen via scaled sphere under hem (skirt mass)
    skirt = _sphere("coat_skirt_mass", 0.34, (0, -0.05, 0.55), mats["coat"], segments=32, rings=16, smooth=0)
    skirt.scale = (1.15, 1.05, 0.55)
    bpy.ops.object.select_all(action="DESELECT")
    skirt.select_set(True)
    bpy.context.view_layer.objects.active = skirt
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    _apply_smooth(skirt, 1)
    coat_parts.append(skirt)
    # High collar cradle
    coat_parts.append(_cyl("coat_collar", 0.14, 0.12, (0, -0.05, 1.56), mats["coat"], verts=32, smooth=1))
    coat_parts.append(_box("coat_collar_stand", (0.11, 0.085, 0.08), (0, -0.13, 1.60), mats["coat"], smooth=1))
    coat_parts.append(_box("coat_collar_wing_L", (0.055, 0.07, 0.10), (0.105, -0.12, 1.58), mats["coat"], smooth=1))
    coat_parts.append(_box("coat_collar_wing_R", (0.055, 0.07, 0.10), (-0.105, -0.12, 1.58), mats["coat"], smooth=1))
    coat_parts.append(_cyl("coat_lining_collar", 0.12, 0.05, (0, -0.01, 1.54), mats["coat_lining"], verts=28, smooth=1))
    # Lapels
    coat_parts.append(_box("coat_lapel_L", (0.055, 0.17, 0.52), (0.105, -0.22, 1.26), mats["coat"], smooth=1))
    coat_parts.append(_box("coat_lapel_R", (0.055, 0.17, 0.52), (-0.105, -0.22, 1.26), mats["coat"], smooth=1))
    coat_parts.append(_box("coat_lapel_line_L", (0.007, 0.10, 0.48), (0.075, -0.24, 1.26), mats["coat_lining"], smooth=0))
    coat_parts.append(_box("coat_lapel_line_R", (0.007, 0.10, 0.48), (-0.075, -0.24, 1.26), mats["coat_lining"], smooth=0))
    # Shoulders + full sleeves (covers arm stubs)
    coat_parts.append(_sphere("coat_shoulder_L", 0.14, (0.30, -0.03, 1.48), mats["coat"], segments=20, rings=12, smooth=1))
    coat_parts.append(_sphere("coat_shoulder_R", 0.14, (-0.30, -0.03, 1.48), mats["coat"], segments=20, rings=12, smooth=1))
    coat_parts.append(
        _cyl("coat_sleeve_L", 0.078, 0.52, (0.44, -0.03, 1.16), mats["coat"], verts=20, rot=(0, 0, math.radians(14)), smooth=1)
    )
    coat_parts.append(
        _cyl("coat_sleeve_R", 0.078, 0.52, (-0.44, -0.03, 1.16), mats["coat"], verts=20, rot=(0, 0, math.radians(-14)), smooth=1)
    )
    coat_parts.append(_cyl("coat_cuff_L", 0.070, 0.05, (0.58, -0.03, 0.96), mats["coat"], verts=16, smooth=0))
    coat_parts.append(_cyl("coat_cuff_R", 0.070, 0.05, (-0.58, -0.03, 0.96), mats["coat"], verts=16, smooth=0))
    coat_parts.append(_cyl("coat_cuff_lining_L", 0.060, 0.028, (0.58, -0.03, 0.94), mats["coat_lining"], verts=14, smooth=0))
    coat_parts.append(_cyl("coat_cuff_lining_R", 0.060, 0.028, (-0.58, -0.03, 0.94), mats["coat_lining"], verts=14, smooth=0))
    # Thin teal piping + pin
    coat_parts.append(_box("coat_piping_L", (0.005, 0.08, 0.70), (0.14, -0.18, 1.10), mats["coat_trim"], smooth=0))
    coat_parts.append(_box("coat_piping_R", (0.005, 0.08, 0.70), (-0.14, -0.18, 1.10), mats["coat_trim"], smooth=0))
    coat_parts.append(_box("insignia", (0.065, 0.016, 0.065), (0.145, -0.28, 1.38), mats["insignia"], smooth=0))

    bpy.ops.object.select_all(action="DESELECT")
    for p in coat_parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = coat_origin
    bpy.ops.object.join()
    coat = bpy.context.object
    coat.name = "DOCTOR_001_COAT"
    _apply_world_transform(coat)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.ops.object.mode_set(mode="OBJECT")
    for v in coat.data.vertices:
        if v.co.length < 0.01:
            v.select = True
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.delete(type="VERT")
    bpy.ops.object.mode_set(mode="OBJECT")
    coat.vertex_groups.clear()
    for name in ("chest", "coat_L", "coat_R", "coat_hem", "spine_02", "clavicle_L", "clavicle_R"):
        coat.vertex_groups.new(name=name)
    for vi, v in enumerate(coat.data.vertices):
        if v.co.z < 0.55:
            coat.vertex_groups["coat_hem"].add([vi], 1.0, "REPLACE")
        elif v.co.x > 0.16:
            coat.vertex_groups["coat_L"].add([vi], 0.7, "REPLACE")
            coat.vertex_groups["clavicle_L"].add([vi], 0.15, "ADD")
            coat.vertex_groups["chest"].add([vi], 0.15, "ADD")
        elif v.co.x < -0.16:
            coat.vertex_groups["coat_R"].add([vi], 0.7, "REPLACE")
            coat.vertex_groups["clavicle_R"].add([vi], 0.15, "ADD")
            coat.vertex_groups["chest"].add([vi], 0.15, "ADD")
        else:
            coat.vertex_groups["chest"].add([vi], 0.85, "REPLACE")
            coat.vertex_groups["spine_02"].add([vi], 0.15, "ADD")
    mod = coat.modifiers.new(name="Armature", type="ARMATURE")
    mod.object = arm
    mod.use_vertex_groups = True
    coat.parent = arm

    arm["canonical_height_m"] = 1.85
    arm["character_id"] = "DOCTOR_001"
    arm["asset_tier"] = "manufacturing_v1"
    arm["sculpt_phase"] = "XIII"
    arm["identity"] = "living_lab_coat"
    arm["hand_grasp_R"] = (-0.70, -0.02, 0.98)
    arm["hand_grasp_L"] = (0.70, -0.02, 0.98)
    arm["foot_contact_L"] = (0.12, 0.05, 0.02)
    arm["foot_contact_R"] = (-0.12, 0.05, 0.02)

    return arm, body, coat, mats
