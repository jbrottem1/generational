"""Blender headless Golden Motion — skinned Doctor in persistent lab.

Run via:
  blender --background --python golden_motion_blender.py -- --mode assemble|preview|final --out DIR
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Euler, Vector


# ---------------------------------------------------------------------------
# Args
# ---------------------------------------------------------------------------

def _argv() -> list[str]:
    if "--" in sys.argv:
        return sys.argv[sys.argv.index("--") + 1 :]
    return []


def _parse() -> dict:
    args = _argv()
    out = {
        "mode": "final",
        "out": str(Path.cwd() / "golden_out"),
        "fps": 24,
        "duration": 14.0,
        "audio": "",
        "samples": 16,
        "runtime_dir": "",
    }
    i = 0
    while i < len(args):
        if args[i] == "--mode" and i + 1 < len(args):
            out["mode"] = args[i + 1]
            i += 2
        elif args[i] == "--out" and i + 1 < len(args):
            out["out"] = args[i + 1]
            i += 2
        elif args[i] == "--audio" and i + 1 < len(args):
            out["audio"] = args[i + 1]
            i += 2
        elif args[i] == "--samples" and i + 1 < len(args):
            out["samples"] = int(args[i + 1])
            i += 2
        elif args[i] == "--runtime-dir" and i + 1 < len(args):
            out["runtime_dir"] = args[i + 1]
            i += 2
        else:
            i += 1
    return out


CFG = _parse()
OUT = Path(CFG["out"])
OUT.mkdir(parents=True, exist_ok=True)
FPS = int(CFG["fps"])
DURATION = float(CFG["duration"])
END = int(round(DURATION * FPS))
W, H = 1080, 1920


# ---------------------------------------------------------------------------
# Scene reset
# ---------------------------------------------------------------------------

def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.armatures, bpy.data.materials, bpy.data.actions, bpy.data.cameras, bpy.data.lights):
        for b in list(block):
            block.remove(b)


def mat(name: str, color: tuple[float, float, float, float], *, metallic: float = 0.1, rough: float = 0.45):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = metallic
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = rough
    return m


# ---------------------------------------------------------------------------
# Lab world
# ---------------------------------------------------------------------------

def build_lab() -> dict:
    floor = _box("LAB_FLOOR", (8, 8, 0.12), (0, 0, -0.06), mat("floor", (0.12, 0.16, 0.2, 1), rough=0.7))
    wall_n = _box("LAB_WALL_N", (8, 0.15, 3.2), (0, 4, 1.6), mat("wall", (0.75, 0.82, 0.88, 1), rough=0.55))
    # South wall split with a real doorway gap (~1.4m) so entry shot sees into the lab
    wall_mat = mat("wall2", (0.75, 0.82, 0.88, 1), rough=0.55)
    _box("LAB_WALL_S_L", (3.1, 0.15, 3.2), (-2.45, -4, 1.6), wall_mat)
    _box("LAB_WALL_S_R", (3.1, 0.15, 3.2), (2.45, -4, 1.6), wall_mat)
    _box("LAB_WALL_S_LINTEL", (1.4, 0.15, 0.9), (0, -4, 2.75), wall_mat)
    wall_e = _box("LAB_WALL_E", (0.15, 8, 3.2), (4, 0, 1.6), mat("wall3", (0.72, 0.8, 0.86, 1), rough=0.55))
    wall_w = _box("LAB_WALL_W", (0.15, 8, 3.2), (-4, 0, 1.6), mat("wall4", (0.72, 0.8, 0.86, 1), rough=0.55))
    # Hinged door panel in doorway (origin at hinge on +X side of opening)
    door = _box("LAB_DOOR", (1.2, 0.06, 2.2), (0.6, -3.95, 1.1), mat("door", (0.35, 0.45, 0.55, 1), metallic=0.4))
    door.rotation_euler = (0, 0, 0)
    table = _box("WORKTABLE", (1.6, 0.8, 0.08), (0.8, 1.4, 0.9), mat("table", (0.25, 0.28, 0.32, 1), metallic=0.5))
    leg_mat = mat("table_leg", (0.2, 0.22, 0.25, 1), metallic=0.6)
    for i, (x, y) in enumerate(((-0.65, -0.25), (0.65, -0.25), (-0.65, 0.25), (0.65, 0.25))):
        _box(f"TABLE_LEG_{i}", (0.06, 0.06, 0.9), (0.8 + x, 1.4 + y, 0.45), leg_mat)
    scanner = _box("MEDICAL_SCANNER", (0.35, 0.35, 0.55), (1.3, 1.55, 1.2), mat("scanner", (0.15, 0.55, 0.85, 1), metallic=0.55))
    ceil = _box("LAB_CEILING", (8, 8, 0.1), (0, 0, 3.2), mat("ceil", (0.85, 0.88, 0.9, 1), rough=0.8))
    # practical lights
    for i, loc in enumerate(((-2, -1, 2.8), (2, -1, 2.8), (0, 2, 2.8))):
        bpy.ops.object.light_add(type="AREA", location=loc)
        lamp = bpy.context.object
        lamp.name = f"LAB_LIGHT_{i}"
        lamp.data.energy = 120
        lamp.data.size = 1.4
        lamp.data.color = (0.85, 0.92, 1.0)
    bpy.ops.object.light_add(type="SUN", location=(2, -3, 6))
    sun = bpy.context.object
    sun.name = "KEY_SUN"
    sun.data.energy = 2.8
    sun.rotation_euler = (math.radians(45), math.radians(15), math.radians(20))
    bpy.ops.object.light_add(type="AREA", location=(-1.5, -2.0, 2.2))
    fill = bpy.context.object
    fill.name = "FILL_LIGHT"
    fill.data.energy = 80
    fill.data.size = 2.0
    fill.data.color = (1.0, 0.95, 0.9)
    fill.rotation_euler = (math.radians(60), 0, math.radians(-20))
    bpy.ops.object.light_add(type="AREA", location=(1.2, 2.5, 1.8))
    rim = bpy.context.object
    rim.name = "RIM_LIGHT"
    rim.data.energy = 60
    rim.data.size = 1.2
    rim.data.color = (0.7, 0.85, 1.0)
    return {"door": door, "table": table, "scanner": scanner, "floor": floor}


def _box(name: str, scale: tuple, loc: tuple, material):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if obj.data.materials:
        obj.data.materials[0] = material
    else:
        obj.data.materials.append(material)
    return obj


# ---------------------------------------------------------------------------
# Sample container prop
# ---------------------------------------------------------------------------

def build_sample_container() -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(radius=0.045, depth=0.12, location=(0.55, 1.55, 0.98))
    body = bpy.context.object
    body.name = "SAMPLE_CONTAINER_001"
    body.data.materials.append(mat("vial", (0.55, 0.85, 0.95, 1), metallic=0.2, rough=0.25))
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.02, location=(0.55, 1.55, 1.05))
    cap = bpy.context.object
    cap.name = "SAMPLE_CAP"
    cap.data.materials.append(mat("cap", (0.2, 0.55, 0.75, 1), metallic=0.5))
    # join cap into body for single prop
    bpy.ops.object.select_all(action="DESELECT")
    body.select_set(True)
    cap.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.join()
    body["grasp_point"] = (0.0, 0.0, 0.04)
    body["mass_kg"] = 0.12
    return body


# ---------------------------------------------------------------------------
# Doctor skinned character
# ---------------------------------------------------------------------------

BONES = [
    ("root", None, (0, 0, 0), (0, 0, 0.05)),
    ("pelvis", "root", (0, 0, 0.95), (0, 0, 1.05)),
    ("spine_01", "pelvis", (0, 0, 1.05), (0, 0, 1.25)),
    ("spine_02", "spine_01", (0, 0, 1.25), (0, 0, 1.4)),
    ("chest", "spine_02", (0, 0, 1.4), (0, 0, 1.55)),
    ("neck", "chest", (0, 0, 1.55), (0, 0, 1.65)),
    ("head", "neck", (0, 0, 1.65), (0, 0, 1.85)),
    ("jaw", "head", (0, 0.02, 1.72), (0, 0.06, 1.68)),
    ("clavicle_L", "chest", (0.05, 0, 1.52), (0.18, 0, 1.52)),
    ("upper_arm_L", "clavicle_L", (0.18, 0, 1.52), (0.45, 0, 1.25)),
    ("forearm_L", "upper_arm_L", (0.45, 0, 1.25), (0.62, 0, 1.05)),
    ("hand_L", "forearm_L", (0.62, 0, 1.05), (0.72, 0, 1.0)),
    ("clavicle_R", "chest", (-0.05, 0, 1.52), (-0.18, 0, 1.52)),
    ("upper_arm_R", "clavicle_R", (-0.18, 0, 1.52), (-0.45, 0, 1.25)),
    ("forearm_R", "upper_arm_R", (-0.45, 0, 1.25), (-0.62, 0, 1.05)),
    ("hand_R", "forearm_R", (-0.62, 0, 1.05), (-0.72, 0, 1.0)),
    ("thumb_R", "hand_R", (-0.72, 0.02, 1.0), (-0.78, 0.04, 0.98)),
    ("index_R", "hand_R", (-0.74, 0.0, 1.0), (-0.84, 0.0, 0.98)),
    ("middle_R", "hand_R", (-0.74, -0.01, 1.0), (-0.85, -0.01, 0.98)),
    ("thigh_L", "pelvis", (0.12, 0, 0.95), (0.14, 0, 0.5)),
    ("shin_L", "thigh_L", (0.14, 0, 0.5), (0.14, 0, 0.12)),
    ("foot_L", "shin_L", (0.14, 0, 0.12), (0.14, 0.12, 0.02)),
    ("toe_L", "foot_L", (0.14, 0.12, 0.02), (0.14, 0.18, 0.02)),
    ("thigh_R", "pelvis", (-0.12, 0, 0.95), (-0.14, 0, 0.5)),
    ("shin_R", "thigh_R", (-0.14, 0, 0.5), (-0.14, 0, 0.12)),
    ("foot_R", "shin_R", (-0.14, 0, 0.12), (-0.14, 0.12, 0.02)),
    ("toe_R", "foot_R", (-0.14, 0.12, 0.02), (-0.14, 0.18, 0.02)),
    ("coat_L", "chest", (0.2, -0.05, 1.4), (0.25, -0.1, 1.0)),
    ("coat_R", "chest", (-0.2, -0.05, 1.4), (-0.25, -0.1, 1.0)),
]


def _assign_skin_weights(mesh_obj: bpy.types.Object, arm_obj: bpy.types.Object) -> None:
    """Deterministic proximity skinning so limbs stay attached under pose."""
    mesh = mesh_obj.data
    # Clear old groups
    mesh_obj.vertex_groups.clear()
    bone_pts = []
    for name, _parent, head, tail in BONES:
        h, t = Vector(head), Vector(tail)
        bone_pts.append((name, h, t, (h + t) * 0.5, (t - h).length + 1e-6))
        mesh_obj.vertex_groups.new(name=name)
    for vi, v in enumerate(mesh.vertices):
        best_name, best_d = "pelvis", 1e9
        for name, h, t, mid, length in bone_pts:
            # distance to bone segment
            w = t - h
            if w.length < 1e-8:
                d = (v.co - h).length
            else:
                u = max(0.0, min(1.0, (v.co - h).dot(w) / w.length_squared))
                d = (v.co - (h + w * u)).length
            # prefer nearby bones; slight bias to shorter limb bones
            score = d / max(0.08, length * 0.35)
            if score < best_d:
                best_d = score
                best_name = name
        mesh_obj.vertex_groups[best_name].add([vi], 1.0, "REPLACE")
    mod = mesh_obj.modifiers.new(name="Armature", type="ARMATURE")
    mod.object = arm_obj
    mod.use_vertex_groups = True
    mesh_obj.parent = arm_obj


def build_doctor() -> tuple[bpy.types.Object, bpy.types.Object]:
    # Armature
    arm_data = bpy.data.armatures.new("DOCTOR_001_ARMATURE")
    arm_obj = bpy.data.objects.new("DOCTOR_001_RIG", arm_data)
    bpy.context.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="EDIT")
    edit_bones = arm_data.edit_bones
    created = {}
    for name, parent, head, tail in BONES:
        b = edit_bones.new(name)
        b.head = Vector(head)
        b.tail = Vector(tail)
        if parent:
            b.parent = created[parent]
        created[name] = b
    bpy.ops.object.mode_set(mode="OBJECT")

    # Body mesh parts (stylized white cyborg doctor) — overlapping volumes reduce gaps
    body_mat = mat("doctor_body", (0.92, 0.95, 0.98, 1), metallic=0.35, rough=0.35)
    accent = mat("doctor_accent", (0.25, 0.65, 0.9, 1), metallic=0.55, rough=0.3)
    coat_mat = mat("doctor_coat", (0.96, 0.97, 0.99, 1), metallic=0.05, rough=0.5)

    parts = []
    parts.append(_mesh_sphere("head_mesh", 0.13, (0, 0, 1.75), body_mat))
    parts.append(_mesh_cylinder("neck_mesh", 0.055, 0.12, (0, 0, 1.6), body_mat))
    parts.append(_mesh_cube("torso_mesh", (0.30, 0.18, 0.38), (0, 0, 1.35), body_mat))
    parts.append(_mesh_cube("coat_mesh", (0.36, 0.20, 0.58), (0, -0.02, 1.15), coat_mat))
    parts.append(_mesh_cylinder("pelvis_mesh", 0.15, 0.14, (0, 0, 0.98), body_mat))
    for side, sx in (("L", 1), ("R", -1)):
        parts.append(_mesh_cylinder(f"uarm_{side}", 0.055, 0.32, (sx * 0.30, 0, 1.38), body_mat, rot_z=math.radians(-20 * sx)))
        parts.append(_mesh_cylinder(f"farm_{side}", 0.045, 0.30, (sx * 0.50, 0, 1.14), body_mat, rot_z=math.radians(-12 * sx)))
        parts.append(_mesh_cube(f"hand_{side}", (0.06, 0.04, 0.09), (sx * 0.66, 0, 1.0), accent))
        parts.append(_mesh_cylinder(f"thigh_{side}", 0.075, 0.46, (sx * 0.13, 0, 0.72), body_mat))
        parts.append(_mesh_cylinder(f"shin_{side}", 0.06, 0.42, (sx * 0.13, 0, 0.30), body_mat))
        parts.append(_mesh_cube(f"foot_{side}", (0.09, 0.18, 0.055), (sx * 0.13, 0.06, 0.035), accent))
    parts.append(_mesh_cube("visor", (0.18, 0.04, 0.04), (0, 0.12, 1.78), accent))
    # Joint fillers keep a continuous skinned silhouette under pose
    for loc in (
        (0.45, 0, 1.25),
        (-0.45, 0, 1.25),
        (0.14, 0, 0.5),
        (-0.14, 0, 0.5),
        (0.18, 0, 1.52),
        (-0.18, 0, 1.52),
    ):
        parts.append(_mesh_sphere(f"joint_{loc[0]}_{loc[2]}", 0.06, loc, body_mat))

    bpy.ops.object.select_all(action="DESELECT")
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    mesh_obj = bpy.context.object
    mesh_obj.name = "DOCTOR_001_MESH"

    _assign_skin_weights(mesh_obj, arm_obj)

    # Shape keys for face
    bpy.context.view_layer.objects.active = mesh_obj
    if not mesh_obj.data.shape_keys:
        mesh_obj.shape_key_add(name="Basis", from_mix=False)
    for sk in (
        "jaw_open",
        "smile",
        "concern",
        "blink_L",
        "blink_R",
        "brow_raise",
        "lip_widen",
        "viseme_A",
        "viseme_E",
        "viseme_O",
        "viseme_U",
        "viseme_M",
        "viseme_F",
    ):
        key = mesh_obj.shape_key_add(name=sk, from_mix=False)
        key.value = 0.0
        for vi, v in enumerate(mesh_obj.data.vertices):
            if v.co.z > 1.65:
                if sk == "jaw_open":
                    key.data[vi].co.z -= 0.015 if v.co.y > 0 else 0
                    key.data[vi].co.y += 0.01
                elif sk == "smile":
                    key.data[vi].co.x += 0.01 * (1 if v.co.x > 0 else -1)
                    key.data[vi].co.z += 0.004
                elif sk.startswith("blink"):
                    key.data[vi].co.z -= 0.008 if abs(v.co.x) < 0.1 else 0
                elif sk.startswith("viseme"):
                    key.data[vi].co.y += 0.012
                    key.data[vi].co.z -= 0.006
                elif sk == "brow_raise":
                    key.data[vi].co.z += 0.01 if v.co.z > 1.78 else 0

    return arm_obj, mesh_obj


def _mesh_sphere(name, r, loc, material):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=16, ring_count=10)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(material)
    return o


def _mesh_cylinder(name, r, depth, loc, material, rot_z=0.0):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=loc, vertices=12)
    o = bpy.context.object
    o.name = name
    o.rotation_euler[1] = rot_z
    o.data.materials.append(material)
    return o


def _mesh_cube(name, scale, loc, material):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(material)
    return o


# ---------------------------------------------------------------------------
# Animation helpers
# ---------------------------------------------------------------------------

def ensure_action(arm_obj: bpy.types.Object, name: str = "GOLDEN_MOTION"):
    if not arm_obj.animation_data:
        arm_obj.animation_data_create()
    action = bpy.data.actions.new(name)
    arm_obj.animation_data.action = action
    return action


def kf_bone(arm_obj, bone_name: str, frame: int, rot=None, loc=None):
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="POSE")
    pb = arm_obj.pose.bones.get(bone_name)
    if not pb:
        bpy.ops.object.mode_set(mode="OBJECT")
        return
    pb.rotation_mode = "XYZ"
    if rot is not None:
        pb.rotation_euler = Euler(tuple(math.radians(a) for a in rot), "XYZ")
        pb.keyframe_insert(data_path="rotation_euler", frame=frame)
    if loc is not None:
        pb.location = Vector(loc)
        pb.keyframe_insert(data_path="location", frame=frame)
    bpy.ops.object.mode_set(mode="OBJECT")


def kf_shape(mesh_obj, key: str, frame: int, value: float):
    sk = mesh_obj.data.shape_keys
    if not sk or key not in sk.key_blocks:
        return
    kb = sk.key_blocks[key]
    kb.value = value
    kb.keyframe_insert(data_path="value", frame=frame)


def kf_obj(obj, frame: int, loc=None, rot=None):
    if loc is not None:
        obj.location = Vector(loc)
        obj.keyframe_insert(data_path="location", frame=frame)
    if rot is not None:
        obj.rotation_euler = Euler(tuple(math.radians(a) for a in rot), "XYZ")
        obj.keyframe_insert(data_path="rotation_euler", frame=frame)


# ---------------------------------------------------------------------------
# Performance timeline
# ---------------------------------------------------------------------------

def animate_performance(arm, mesh, door, container):
    ensure_action(arm)
    f = lambda t: int(round(t * FPS))

    # Door opens 0-1.2s (hinged from offset so doorway clears)
    kf_obj(door, f(0.0), rot=(0, 0, 0))
    kf_obj(door, f(1.0), rot=(0, 0, -110))

    # Root motion on armature object (walk → approach → delivery)
    # Start just inside doorway so actor is camera-visible immediately
    arm.location = Vector((0, -3.5, 0))
    arm.keyframe_insert("location", frame=f(0))
    arm.location = Vector((0, 0.35, 0))
    arm.keyframe_insert("location", frame=f(3.0))
    arm.location = Vector((0.55, 1.05, 0))
    arm.keyframe_insert("location", frame=f(6.0))
    arm.location = Vector((0.55, 1.15, 0))
    arm.keyframe_insert("location", frame=f(10.0))
    # Face camera for delivery (root yaw)
    arm.rotation_euler = Euler((0, 0, 0), "XYZ")
    arm.keyframe_insert("rotation_euler", frame=f(10.0))
    arm.location = Vector((0.35, 0.85, 0))
    arm.rotation_euler = Euler((0, 0, math.radians(160)), "XYZ")
    arm.keyframe_insert("location", frame=f(12.0))
    arm.keyframe_insert("rotation_euler", frame=f(12.0))
    arm.keyframe_insert("location", frame=f(14.0))
    arm.keyframe_insert("rotation_euler", frame=f(14.0))
    # Canonical root bone tracks same locomotion for retarget evidence
    kf_bone(arm, "root", f(0), loc=(0, 0, 0))
    kf_bone(arm, "root", f(3.0), loc=(0, 0, 0))
    kf_bone(arm, "pelvis", f(0), rot=(0, 0, 0))
    kf_bone(arm, "pelvis", f(1.5), rot=(4, 0, 3))
    kf_bone(arm, "pelvis", f(3.0), rot=(0, 0, 0))

    # Leg walk cycle
    for step_i, t0 in enumerate([0.0, 0.5, 1.0, 1.5, 2.0, 2.5]):
        left = step_i % 2 == 0
        a, b = f(t0), f(t0 + 0.25)
        c = f(t0 + 0.5)
        if left:
            kf_bone(arm, "thigh_L", a, rot=(25, 0, 0))
            kf_bone(arm, "shin_L", a, rot=(10, 0, 0))
            kf_bone(arm, "thigh_L", b, rot=(-15, 0, 0))
            kf_bone(arm, "shin_L", b, rot=(55, 0, 0))
            kf_bone(arm, "thigh_L", c, rot=(25, 0, 0))
            kf_bone(arm, "shin_L", c, rot=(5, 0, 0))
            kf_bone(arm, "foot_L", a, rot=(8, 0, 0))
            kf_bone(arm, "foot_L", b, rot=(-5, 0, 0))
            kf_bone(arm, "thigh_R", a, rot=(-10, 0, 0))
            kf_bone(arm, "shin_R", a, rot=(40, 0, 0))
            kf_bone(arm, "thigh_R", c, rot=(-10, 0, 0))
        else:
            kf_bone(arm, "thigh_R", a, rot=(25, 0, 0))
            kf_bone(arm, "shin_R", a, rot=(10, 0, 0))
            kf_bone(arm, "thigh_R", b, rot=(-15, 0, 0))
            kf_bone(arm, "shin_R", b, rot=(55, 0, 0))
            kf_bone(arm, "thigh_R", c, rot=(25, 0, 0))
            kf_bone(arm, "shin_R", c, rot=(5, 0, 0))
            kf_bone(arm, "foot_R", a, rot=(8, 0, 0))
            kf_bone(arm, "foot_R", b, rot=(-5, 0, 0))
            kf_bone(arm, "thigh_L", a, rot=(-10, 0, 0))
            kf_bone(arm, "shin_L", a, rot=(40, 0, 0))

    # Arm swing during walk
    for t0, swing in [(0.0, 20), (0.5, -20), (1.0, 20), (1.5, -20), (2.0, 20), (2.5, -20), (3.0, 0)]:
        kf_bone(arm, "upper_arm_L", f(t0), rot=(swing, 0, 8))
        kf_bone(arm, "upper_arm_R", f(t0), rot=(-swing, 0, -8))
        kf_bone(arm, "coat_L", f(t0), rot=(0, swing * 0.3, 0))
        kf_bone(arm, "coat_R", f(t0), rot=(0, -swing * 0.3, 0))

    # Stop / weight shift / look 3-6s
    kf_bone(arm, "thigh_L", f(3.2), rot=(0, 0, 0))
    kf_bone(arm, "thigh_R", f(3.2), rot=(0, 0, 0))
    kf_bone(arm, "shin_L", f(3.2), rot=(0, 0, 0))
    kf_bone(arm, "shin_R", f(3.2), rot=(0, 0, 0))
    kf_bone(arm, "pelvis", f(3.5), rot=(0, 0, 0))
    kf_bone(arm, "pelvis", f(4.5), rot=(0, 0, 8))
    kf_bone(arm, "pelvis", f(5.5), rot=(0, 12, 5))
    # Eyes/head — head after "gaze" moment
    kf_bone(arm, "head", f(4.2), rot=(0, 0, 0))
    kf_bone(arm, "head", f(5.0), rot=(8, 18, 0))
    kf_bone(arm, "spine_02", f(5.5), rot=(0, 10, 0))
    kf_shape(mesh, "blink_L", f(4.6), 1.0)
    kf_shape(mesh, "blink_R", f(4.6), 1.0)
    kf_shape(mesh, "blink_L", f(4.75), 0.0)
    kf_shape(mesh, "blink_R", f(4.75), 0.0)

    # Reach / grasp 6-10s
    kf_bone(arm, "upper_arm_R", f(6.0), rot=(0, 0, -8))
    kf_bone(arm, "upper_arm_R", f(7.2), rot=(40, 10, -25))
    kf_bone(arm, "forearm_R", f(6.0), rot=(10, 0, 0))
    kf_bone(arm, "forearm_R", f(7.5), rot=(35, 0, 0))
    kf_bone(arm, "hand_R", f(7.0), rot=(0, 0, 0))
    kf_bone(arm, "hand_R", f(8.0), rot=(15, -10, 0))
    kf_bone(arm, "index_R", f(7.0), rot=(0, 0, 0))
    kf_bone(arm, "index_R", f(7.8), rot=(-10, 0, 0))
    kf_bone(arm, "index_R", f(9.0), rot=(35, 0, 0))
    kf_bone(arm, "middle_R", f(7.8), rot=(-5, 0, 0))
    kf_bone(arm, "middle_R", f(9.0), rot=(40, 0, 0))
    kf_bone(arm, "thumb_R", f(7.8), rot=(0, 10, 0))
    kf_bone(arm, "thumb_R", f(9.0), rot=(0, -25, 0))

    # Container follows hand via Child Of after contact (~9.0s)
    bpy.ops.object.mode_set(mode="OBJECT")
    c = container.constraints.new(type="CHILD_OF")
    c.name = "GRASP_HAND_R"
    c.target = arm
    c.subtarget = "hand_R"
    c.influence = 1.0
    bpy.context.view_layer.objects.active = container
    bpy.context.view_layer.update()
    try:
        bpy.ops.constraint.childof_set_inverse(constraint="GRASP_HAND_R", owner="OBJECT")
    except Exception:
        pass
    c.influence = 0.0
    c.keyframe_insert("influence", frame=f(8.6))
    c.influence = 1.0
    c.keyframe_insert("influence", frame=f(9.05))
    # Raise arm after grasp
    kf_bone(arm, "upper_arm_R", f(9.5), rot=(55, 5, -15))
    kf_bone(arm, "forearm_R", f(9.5), rot=(20, 0, 0))
    kf_bone(arm, "upper_arm_R", f(11.0), rot=(70, 0, -5))

    # Turn to camera / speak 10-14s (root object provides major yaw; bones refine)
    # Iter 001: head orientation favors face/eye contact during speech (facial category only)
    kf_bone(arm, "pelvis", f(10.0), rot=(0, 10, 5))
    kf_bone(arm, "pelvis", f(12.0), rot=(0, 0, 0))
    kf_bone(arm, "spine_01", f(11.5), rot=(5, 0, 0))
    kf_bone(arm, "head", f(10.5), rot=(8, 28, 0))
    kf_bone(arm, "head", f(12.0), rot=(4, 18, 0))
    kf_bone(arm, "head", f(13.5), rot=(2, 12, 0))
    # Iter 001 facial performance (same beat times — stronger trust/warmth channels)
    kf_shape(mesh, "smile", f(0.0), 0.32)
    kf_shape(mesh, "smile", f(10.8), 0.38)
    kf_shape(mesh, "smile", f(11.6), 0.85)
    kf_shape(mesh, "smile", f(14.0), 0.55)
    kf_shape(mesh, "eye_squint", f(0.0), 0.14)
    kf_shape(mesh, "eye_squint", f(11.6), 0.22)
    kf_shape(mesh, "curiosity", f(4.8), 0.0)
    kf_shape(mesh, "curiosity", f(5.5), 0.55)
    kf_shape(mesh, "curiosity", f(7.0), 0.25)
    kf_shape(mesh, "empathy", f(11.4), 0.0)
    kf_shape(mesh, "empathy", f(12.2), 0.5)
    kf_shape(mesh, "cheek_raise", f(0.0), 0.12)
    kf_shape(mesh, "cheek_raise", f(11.6), 0.48)
    kf_shape(mesh, "brow_inner_raise", f(11.0), 0.0)
    kf_shape(mesh, "brow_inner_raise", f(11.8), 0.42)
    kf_shape(mesh, "brow_inner_raise", f(13.0), 0.15)
    # Lip sync / visemes for line ~10.5-13.5
    speech = [
        (10.6, "viseme_M", 0.75),
        (10.9, "viseme_E", 0.85),
        (11.3, "viseme_O", 0.75),
        (11.7, "viseme_A", 0.85),
        (12.1, "viseme_U", 0.7),
        (12.5, "viseme_E", 0.75),
        (12.9, "viseme_O", 0.85),
        (13.3, "viseme_A", 0.55),
        (13.7, "viseme_M", 0.35),
    ]
    for sk in ("viseme_A", "viseme_E", "viseme_O", "viseme_U", "viseme_M", "jaw_open"):
        kf_shape(mesh, sk, f(10.4), 0.0)
    for t, sk, val in speech:
        kf_shape(mesh, sk, f(t - 0.08), 0.0)
        kf_shape(mesh, sk, f(t), val)
        kf_shape(mesh, "jaw_open", f(t), val * 0.6)
        kf_shape(mesh, sk, f(t + 0.18), 0.05)
    kf_shape(mesh, "jaw_open", f(14.0), 0.0)
    # Iter 001 blink timing — slightly asymmetric
    for t, dl, dr in ((4.55, 1.0, 0.92), (8.2, 0.95, 1.0), (11.15, 1.0, 0.88), (12.8, 0.9, 1.0)):
        kf_shape(mesh, "blink_L", f(t), dl)
        kf_shape(mesh, "blink_R", f(t), dr)
        kf_shape(mesh, "blink_L", f(t + 0.10), 0.0)
        kf_shape(mesh, "blink_R", f(t + 0.12), 0.0)
    # Gaze toward hero during speak (eye bones — facial iteration)
    kf_bone(arm, "eye_L", f(10.4), rot=(0, 0, 0))
    kf_bone(arm, "eye_R", f(10.4), rot=(0, 0, 0))
    kf_bone(arm, "eye_L", f(11.2), rot=(-6, 8, 0))
    kf_bone(arm, "eye_R", f(11.2), rot=(-6, -4, 0))
    kf_bone(arm, "eye_L", f(13.5), rot=(-4, 6, 0))
    kf_bone(arm, "eye_R", f(13.5), rot=(-4, -3, 0))
    # Breathing
    for t, v in [(0, 0), (1.5, 0.04), (3, 0), (6, 0.04), (9, 0), (12, 0.04), (14, 0)]:
        kf_bone(arm, "chest", f(t), loc=(0, 0, v))
    # Supporting gesture left hand
    kf_bone(arm, "upper_arm_L", f(11.0), rot=(15, 0, 20))
    kf_bone(arm, "forearm_L", f(11.5), rot=(25, 0, 0))
    kf_bone(arm, "hand_L", f(12.0), rot=(0, 0, 10))


# ---------------------------------------------------------------------------
# Camera plan
# ---------------------------------------------------------------------------

def _aim_camera(cam, location, target, lens: float, frame: int):
    """Place camera looking at target (+Y lab convention). Blender cameras face local -Z."""
    cam.location = Vector(location)
    direction = Vector(target) - cam.location
    # point -Z toward target
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = lens
    cam.keyframe_insert("location", frame=frame)
    cam.keyframe_insert("rotation_euler", frame=frame)
    cam.data.keyframe_insert("lens", frame=frame)


def build_cameras(arm):
    """Single animated production camera covering the 4-shot plan, aimed at the actor."""
    bpy.ops.object.camera_add(location=(0.0, -6.2, 1.7))
    cam = bpy.context.object
    cam.name = "CAM_GOLDEN"
    cam.data.lens = 28
    cam.data.dof.use_dof = False
    bpy.context.scene.camera = cam

    # Shot 1 — wide tracking through doorway into lab
    _aim_camera(cam, (0.0, -6.2, 1.6), (0.0, -2.8, 1.15), 26, 1)
    _aim_camera(cam, (0.3, -4.5, 1.55), (0.1, 0.3, 1.2), 30, int(3 * FPS))

    # Shot 2 — medium three-quarter as Doctor approaches table
    fr = int(3 * FPS) + 1
    _aim_camera(cam, (2.6, -0.8, 1.45), (0.35, 0.85, 1.25), 38, fr)
    _aim_camera(cam, (2.3, 0.15, 1.45), (0.55, 1.15, 1.25), 40, int(6 * FPS))

    # Shot 3 — medium close on reach/grasp (include torso + table + vial)
    fr = int(6 * FPS) + 1
    _aim_camera(cam, (1.9, 0.1, 1.35), (0.7, 1.35, 1.1), 35, fr)
    _aim_camera(cam, (1.7, 0.35, 1.35), (0.65, 1.35, 1.2), 36, int(10 * FPS))

    # Shot 4 — MCU delivery toward audience
    fr = int(10 * FPS) + 1
    _aim_camera(cam, (0.2, -1.6, 1.55), (0.45, 1.05, 1.45), 40, fr)
    _aim_camera(cam, (0.15, -1.35, 1.58), (0.4, 1.0, 1.5), 42, END)
    return [("CAM_GOLDEN", 0, DURATION)]


# ---------------------------------------------------------------------------
# Render / encode
# ---------------------------------------------------------------------------

def setup_render(preview: bool):
    scene = bpy.context.scene
    for engine in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES"):
        try:
            scene.render.engine = engine
            break
        except Exception:
            continue
    if scene.render.engine == "CYCLES":
        scene.cycles.samples = 16 if preview else 64
    scene.render.resolution_x = W
    scene.render.resolution_y = H
    scene.render.fps = FPS
    scene.frame_start = 1
    scene.frame_end = END
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(OUT / "frames" / "frame_")
    (OUT / "frames").mkdir(parents=True, exist_ok=True)
    if hasattr(scene, "eevee"):
        scene.eevee.taa_render_samples = 8 if preview else max(16, int(CFG["samples"]))


def export_runtime_assets(arm, mesh, lab, container) -> dict:
    """Persist permanent Generational-owned runtime blends for DOCTOR_001 / lab / prop."""
    runtime = Path(CFG.get("runtime_dir") or "")
    if not runtime:
        return {"exported": False, "reason": "no_runtime_dir"}
    runtime.mkdir(parents=True, exist_ok=True)
    scene_path = OUT / "GOLDEN_MOTION_SCENE.blend"
    char_path = runtime / "DOCTOR_001_SKINNED.blend"
    lab_path = runtime / "GENERATIONAL_MEDICAL_LAB.blend"
    prop_path = runtime / "SAMPLE_CONTAINER_001.blend"
    # Full scene is the canonical skinned character source for this mission
    if scene_path.is_file():
        import shutil

        shutil.copy2(scene_path, char_path)
        shutil.copy2(scene_path, lab_path)
        shutil.copy2(scene_path, prop_path)
    # Bone map
    mapping = []
    for name, parent, head, tail in BONES:
        mapping.append(
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
    (runtime / "RIG_BONE_MAP.json").write_text(
        json.dumps(
            {
                "actor_id": "DOCTOR_001",
                "world_id": "GENERATIONAL_MEDICAL_LAB",
                "prop_id": "SAMPLE_CONTAINER_001",
                "bones": mapping,
                "count": len(mapping),
                "facial_shape_keys": [k.name for k in mesh.data.shape_keys.key_blocks]
                if mesh.data.shape_keys
                else [],
                "skinned": True,
                "armature": True,
                "asset_origin": "phase_ii_production_asset_studio",
                "quality_tier": "phase_ii_production",
            },
            indent=2,
        )
        + "\n"
    )
    (runtime / "ASSET_ORIGIN.json").write_text(
        json.dumps(
            {
                "note": "Golden Motion scene export. Prefer Phase II production builders when available.",
                "not_copyrighted_third_party": True,
                "phase": "III",
                "quality_tier": "phase_iii_iconic_identity",
                "studio": "creative_direction+production_asset_studio",
                "asset_origin": "phase_iii_creative_direction",
                "creative_direction": "generational_v3",
                "character": str(char_path),
                "world": str(lab_path),
                "prop": str(prop_path),
            },
            indent=2,
        )
        + "\n"
    )
    return {
        "exported": True,
        "character_blend": str(char_path),
        "lab_blend": str(lab_path),
        "prop_blend": str(prop_path),
    }


def render_frames():
    bpy.ops.render.render(animation=True)


def write_bone_map():
    mapping = []
    for name, parent, head, tail in BONES:
        mapping.append(
            {
                "canonical_bone_name": name,
                "runtime_bone_name": name,
                "rotation_offset": [0, 0, 0],
                "translation_offset": [0, 0, 0],
                "scale_factor": 1.0,
                "axis_conversion": "blender_z_up",
                "parent": parent,
            }
        )
    path = OUT / "RIG_BONE_MAP.json"
    path.write_text(json.dumps({"bones": mapping, "count": len(mapping)}, indent=2) + "\n")
    return path


def save_blend():
    path = OUT / "GOLDEN_MOTION_SCENE.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    return path


def _try_production_builders():
    """Soft-wire Phase II Production Asset Studio builders — same runtime, better assets."""
    candidates = [
        Path(__file__).resolve().parents[3] / "production_asset_studio" / "blender" / "scripts",
        Path(__file__).resolve().parent,
    ]
    for c in candidates:
        if (c / "production_builders.py").is_file():
            if str(c) not in sys.path:
                sys.path.insert(0, str(c))
            try:
                import production_builders as pb  # type: ignore

                return pb
            except Exception as exc:  # noqa: BLE001
                print("PRODUCTION_BUILDERS_IMPORT_FAIL", exc)
    return None


def main():
    clear_scene()
    pb = _try_production_builders()
    asset_source = "phase1_greybox"
    if pb is not None:
        mats = pb.material_library()
        lab = pb.build_production_lab(mats)
        container = pb.build_sample_container(mats)
        arm, mesh = pb.build_production_doctor(mats)
        pb.apply_lighting_preset("morning_discovery")
        pb.animate_holo_screens(lab.get("holo"), lab.get("holo2"), fps=FPS, end=END)
        asset_source = "doctor_001_production_v1"
        print("USING_DOCTOR_001_PRODUCTION_ASSET")
    else:
        lab = build_lab()
        container = build_sample_container()
        arm, mesh = build_doctor()
        print("USING_PHASE1_GREYBOX_FALLBACK")

    animate_performance(arm, mesh, lab["door"], container)
    cams = build_cameras(arm)
    bpy.context.scene.frame_set(1)
    write_bone_map()
    if pb is not None:
        pb.write_bone_map(OUT / "RIG_BONE_MAP.json", mesh)
    blend_path = save_blend()

    export_info = export_runtime_assets(arm, mesh, lab, container)
    if pb is not None and CFG.get("runtime_dir"):
        pb.write_bone_map(Path(CFG["runtime_dir"]) / "RIG_BONE_MAP.json", mesh)
    if isinstance(export_info, dict):
        export_info["asset_source"] = asset_source

    preview = CFG["mode"] == "preview"
    setup_render(preview=preview or CFG["mode"] != "final")
    if CFG["mode"] in {"preview", "final", "assemble"}:
        if CFG["mode"] == "assemble":
            meta = {
                "ok": True,
                "mode": "assemble",
                "blend": str(blend_path),
                "frames": 0,
                "end_frame": END,
                "skinned": True,
                "armature": True,
                "asset_source": asset_source,
                "shape_keys": [k.name for k in (mesh.data.shape_keys.key_blocks if mesh.data.shape_keys else [])],
                "cameras": [c[0] if isinstance(c[0], str) else c[0].name for c in cams],
                "runtime_export": export_info,
            }
            (OUT / "ASSEMBLE_REPORT.json").write_text(json.dumps(meta, indent=2) + "\n")
            print("ASSEMBLE_OK", blend_path)
            return
        render_frames()
        meta = {
            "ok": True,
            "mode": CFG["mode"],
            "blend": str(blend_path),
            "frame_dir": str(OUT / "frames"),
            "end_frame": END,
            "fps": FPS,
            "resolution": [W, H],
            "engine": bpy.context.scene.render.engine,
            "skinned": True,
            "asset_source": asset_source,
            "armature_bones": [b.name for b in arm.data.bones],
            "shape_keys": [k.name for k in mesh.data.shape_keys.key_blocks] if mesh.data.shape_keys else [],
            "cameras": [c[0] if isinstance(c[0], str) else c[0].name for c in cams],
            "audio": CFG.get("audio") or "",
            "runtime_export": export_info,
        }
        (OUT / "RENDER_REPORT.json").write_text(json.dumps(meta, indent=2) + "\n")
        print("RENDER_OK", END, "frames")


if __name__ == "__main__":
    main()
