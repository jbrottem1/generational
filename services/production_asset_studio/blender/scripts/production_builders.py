"""Phase III creative-identity production builders.

Shared by asset export and Golden Motion. Preserves canonical bone names
and facial shape-key contracts required by BlenderRuntime.

Visual identity follows CREATIVE_DIRECTION_GUIDE.md / STYLE_CONSTITUTION.json.
Goal: iconic warm educational cinema — not photorealism.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import bpy
from mathutils import Euler, Vector

# Generational constitution palette (linear-ish sRGB approximations for Principled)
PALETTE = {
    "dawn_white": (0.968, 0.957, 0.937, 1.0),       # #F7F4EF
    "warm_sand": (0.910, 0.875, 0.824, 1.0),        # #E8DFD2
    "teal": (0.184, 0.620, 0.737, 1.0),             # #2F9EBC
    "navy": (0.106, 0.165, 0.290, 1.0),             # #1B2A4A
    "leaf": (0.310, 0.561, 0.357, 1.0),             # #4F8F5B
    "window_gold": (0.949, 0.831, 0.647, 1.0),      # #F2D4A5
    "soft_sky": (0.663, 0.831, 0.910, 1.0),         # #A9D4E8
    "ember": (0.878, 0.478, 0.373, 1.0),            # #E07A5F
    "skin": (0.90, 0.76, 0.66, 1.0),
    "iris": (0.22, 0.48, 0.58, 1.0),
}

# Canonical bones — MUST stay compatible with Golden Motion / RIG_BONE_MAP
BONES = [
    ("root", None, (0, 0, 0), (0, 0, 0.05)),
    ("pelvis", "root", (0, 0, 0.95), (0, 0, 1.05)),
    ("spine_01", "pelvis", (0, 0, 1.05), (0, 0, 1.25)),
    ("spine_02", "spine_01", (0, 0, 1.25), (0, 0, 1.4)),
    ("chest", "spine_02", (0, 0, 1.4), (0, 0, 1.55)),
    ("neck", "chest", (0, 0, 1.55), (0, 0, 1.65)),
    ("head", "neck", (0, 0, 1.65), (0, 0, 1.88)),
    ("jaw", "head", (0, 0.02, 1.74), (0, 0.07, 1.70)),
    ("eye_L", "head", (0.05, 0.12, 1.80), (0.05, 0.18, 1.80)),
    ("eye_R", "head", (-0.05, 0.12, 1.80), (-0.05, 0.18, 1.80)),
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
    ("coat_L", "chest", (0.22, -0.06, 1.4), (0.28, -0.12, 0.95)),
    ("coat_R", "chest", (-0.22, -0.06, 1.4), (-0.28, -0.12, 0.95)),
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
):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
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
    if alpha < 1.0:
        m.blend_method = "BLEND"
        if "Alpha" in bsdf.inputs:
            bsdf.inputs["Alpha"].default_value = alpha
    return m


def material_library() -> dict[str, bpy.types.Material]:
    """Phase III constitution materials — warm, recognizable, non-clinical."""
    return {
        "ceramic": pbr("MAT_CERAMIC", base=PALETTE["dawn_white"], rough=0.28),
        "glass": pbr("MAT_GLASS", base=PALETTE["soft_sky"], rough=0.04, alpha=0.32),
        "steel": pbr("MAT_STEEL", base=(0.62, 0.66, 0.70, 1), rough=0.28, metallic=0.85),
        "carbon_fiber": pbr("MAT_CARBON", base=PALETTE["navy"], rough=0.4, metallic=0.25),
        "plastic": pbr("MAT_PLASTIC", base=PALETTE["teal"], rough=0.38, metallic=0.05),
        "fabric": pbr("MAT_FABRIC", base=PALETTE["dawn_white"], rough=0.82),
        "coat_trim": pbr("MAT_COAT_TRIM", base=PALETTE["teal"], rough=0.45, metallic=0.15),
        "leather": pbr("MAT_LEATHER", base=(0.42, 0.28, 0.18, 1), rough=0.55),
        "wood": pbr("MAT_WOOD", base=PALETTE["warm_sand"], rough=0.55),
        "paint": pbr("MAT_PAINT", base=PALETTE["dawn_white"], rough=0.42),
        "concrete": pbr("MAT_CONCRETE", base=(0.55, 0.52, 0.48, 1), rough=0.85),
        "rubber": pbr("MAT_RUBBER", base=PALETTE["navy"], rough=0.7),
        "skin_composite": pbr("MAT_SKIN", base=PALETTE["skin"], rough=0.42, specular=0.45),
        "floor_polish": pbr("MAT_FLOOR", base=(0.72, 0.68, 0.62, 1), rough=0.18, metallic=0.08),
        "holo": pbr(
            "MAT_HOLO",
            base=PALETTE["soft_sky"],
            rough=0.22,
            emission=PALETTE["soft_sky"],
            emission_strength=3.5,
            alpha=0.5,
        ),
        "plant": pbr("MAT_PLANT", base=PALETTE["leaf"], rough=0.7),
        "iris": pbr("MAT_IRIS", base=PALETTE["iris"], rough=0.22, metallic=0.08),
        "sclera": pbr("MAT_SCLERA", base=(0.97, 0.96, 0.95, 1), rough=0.18),
        "pupil": pbr("MAT_PUPIL", base=(0.05, 0.06, 0.08, 1), rough=0.15),
        "accent": pbr("MAT_ACCENT", base=PALETTE["teal"], rough=0.32, metallic=0.35),
        "brand_mark": pbr(
            "MAT_BRAND",
            base=PALETTE["teal"],
            rough=0.3,
            emission=PALETTE["teal"],
            emission_strength=1.2,
        ),
    }


def _box(name, scale, loc, material, *, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    if obj.data.materials:
        obj.data.materials[0] = material
    else:
        obj.data.materials.append(material)
    return obj


def _cyl(name, r, depth, loc, material, *, verts=24, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=loc, vertices=verts, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj


def _sphere(name, r, loc, material, *, segments=24, rings=16):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=segments, ring_count=rings)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj


def apply_lighting_preset(preset: str = "morning_discovery") -> list[str]:
    """Signature Generational light — warm key, soft fill, teal-cool rim."""
    names = []
    for obj in list(bpy.data.objects):
        if obj.type == "LIGHT":
            bpy.data.objects.remove(obj, do_unlink=True)

    def add(kind, name, loc, energy, *, color=(1, 1, 1), size=1.0, rot=(0, 0, 0)):
        bpy.ops.object.light_add(type=kind, location=loc, rotation=rot)
        lamp = bpy.context.object
        lamp.name = name
        lamp.data.energy = energy
        lamp.data.color = color
        if hasattr(lamp.data, "size"):
            lamp.data.size = size
        names.append(name)
        return lamp

    # Map legacy names
    if preset in {"morning_lab", "morning_discovery", ""}:
        preset = "morning_discovery"

    if preset == "night_laboratory":
        add("AREA", "KEY", (2, -2, 2.6), 45, color=(0.75, 0.88, 1.0), size=1.6)
        add("AREA", "FILL", (-2, -1, 2.2), 22, color=(0.55, 0.65, 0.9), size=2.0)
        add("AREA", "RIM", (0, 3, 2.4), 40, color=(0.35, 0.75, 0.9), size=1.2)
    elif preset == "golden_hour":
        add(
            "SUN",
            "KEY_SUN",
            (4, -3, 5),
            3.2,
            color=(1.0, 0.78, 0.5),
            rot=(math.radians(50), math.radians(20), math.radians(30)),
        )
        add("AREA", "FILL", (-2, -1, 2.0), 45, color=(1.0, 0.9, 0.8), size=2.5)
        add("AREA", "RIM", (1, 3, 2.2), 50, color=(1.0, 0.65, 0.35), size=1.4)
    else:  # morning_discovery — signature Generational
        add(
            "SUN",
            "KEY_SUN",
            (3.0, -4.0, 5.5),
            2.4,
            color=(1.0, 0.94, 0.82),
            rot=(math.radians(48), math.radians(10), math.radians(22)),
        )
        add(
            "AREA",
            "FILL_LIGHT",
            (-2.0, -2.0, 2.2),
            85,
            color=(1.0, 0.96, 0.90),
            size=2.6,
            rot=(math.radians(55), 0, math.radians(-28)),
        )
        add(
            "AREA",
            "RIM_LIGHT",
            (1.6, 2.6, 1.85),
            65,
            color=(0.55, 0.82, 0.92),
            size=1.5,
        )
        add(
            "AREA",
            "WINDOW_PRACTICAL",
            (-3.6, 1.2, 1.9),
            55,
            color=(1.0, 0.92, 0.78),
            size=1.8,
            rot=(math.radians(90), 0, math.radians(90)),
        )
    return names


def build_production_lab(mats: dict) -> dict:
    """Iconic Generational Medical Lab — inspirational teaching sanctuary."""
    floor = _box("LAB_FLOOR", (9, 9, 0.08), (0, 0, -0.04), mats["floor_polish"])
    paint = mats["paint"]
    wood = mats["wood"]
    _box("LAB_WALL_N", (9, 0.12, 3.4), (0, 4.2, 1.7), paint)
    _box("LAB_WALL_S_L", (3.4, 0.12, 3.4), (-2.7, -4.2, 1.7), paint)
    _box("LAB_WALL_S_R", (3.4, 0.12, 3.4), (2.7, -4.2, 1.7), paint)
    _box("LAB_WALL_S_LINTEL", (1.6, 0.12, 1.0), (0, -4.2, 2.9), paint)
    _box("LAB_WALL_E", (0.12, 9, 3.4), (4.2, 0, 1.7), paint)
    _box("LAB_WALL_W", (0.12, 9, 3.4), (-4.2, 0, 1.7), paint)
    _box("LAB_CEILING", (9, 9, 0.1), (0, 0, 3.35), mats["concrete"])

    # Soft wood wainscot / brand identity rail
    _box("WOOD_RAIL_N", (8.5, 0.08, 0.18), (0, 4.05, 0.85), wood)
    _box("BRAND_MARK_PANEL", (0.6, 0.04, 0.18), (0, 4.05, 2.55), mats["brand_mark"])

    door = _box("LAB_DOOR", (1.3, 0.05, 2.3), (0.65, -4.15, 1.15), mats["steel"])
    win = _box("LAB_WINDOW", (2.4, 0.04, 1.5), (-4.15, 1.2, 1.85), mats["glass"])
    _box(
        "OUTDOOR_SCENERY",
        (0.08, 3.8, 2.4),
        (-4.55, 1.2, 1.65),
        pbr(
            "sky_gold",
            base=PALETTE["window_gold"],
            rough=1.0,
            emission=PALETTE["window_gold"],
            emission_strength=1.6,
        ),
    )

    # Teaching worktable — wood top, steel legs
    table = _box("WORKTABLE", (1.9, 0.95, 0.06), (0.9, 1.55, 0.92), wood)
    for i, (x, y) in enumerate(((-0.8, -0.35), (0.8, -0.35), (-0.8, 0.35), (0.8, 0.35))):
        _cyl(f"TABLE_LEG_{i}", 0.035, 0.92, (0.9 + x, 1.55 + y, 0.46), mats["steel"], verts=12)

    scanner = _box("MEDICAL_SCANNER_001", (0.4, 0.4, 0.55), (1.5, 1.75, 1.22), mats["plastic"])
    _cyl("SCANNER_RING", 0.22, 0.05, (1.5, 1.75, 1.5), mats["steel"], rot=(math.radians(90), 0, 0))

    # Research shelf + books (lived-in storytelling)
    _box("SHELF_UNIT", (1.5, 0.38, 2.1), (-3.15, 2.5, 1.15), wood)
    for i in range(10):
        _box(
            f"BOOK_{i}",
            (0.11, 0.2, 0.26),
            (-3.5 + (i % 5) * 0.26, 2.48, 0.45 + (i // 5) * 0.75),
            mats["leather"] if i % 2 else mats["fabric"],
        )

    # Comfort zone — plants + soft seating
    _cyl("PLANT_POT", 0.13, 0.18, (-3.0, -2.4, 0.12), mats["ceramic"], verts=16)
    _sphere("PLANT_FOLIAGE", 0.32, (-3.0, -2.4, 0.48), mats["plant"], segments=16, rings=10)
    _cyl("PLANT_POT_2", 0.1, 0.14, (3.2, 2.8, 0.1), mats["ceramic"], verts=14)
    _sphere("PLANT_FOLIAGE_2", 0.24, (3.2, 2.8, 0.38), mats["plant"], segments=14, rings=8)

    # Soft teaching holograms (curiosity / discovery color script)
    holo = _box("HOLO_DISPLAY_001", (1.0, 0.02, 0.58), (-1.8, 3.95, 1.75), mats["holo"])
    holo2 = _box("HOLO_DISPLAY_002", (0.7, 0.02, 0.42), (2.3, 3.95, 1.65), mats["holo"])

    # Desk / chair / computer — comfortable teaching corner
    _box("DESK_001", (1.25, 0.72, 0.05), (-1.8, -1.5, 0.75), wood)
    for i, (x, y) in enumerate(((-0.5, -0.25), (0.5, -0.25), (-0.5, 0.25), (0.5, 0.25))):
        _cyl(f"DESK_LEG_{i}", 0.03, 0.75, (-1.8 + x, -1.5 + y, 0.375), mats["steel"], verts=8)
    _cyl("CHAIR_001", 0.24, 0.07, (-1.8, -2.35, 0.46), mats["fabric"], verts=18)
    _cyl("CHAIR_STEM", 0.03, 0.4, (-1.8, -2.35, 0.22), mats["steel"], verts=8)
    _box("COMPUTER_001", (0.45, 0.05, 0.3), (-1.8, -1.35, 1.05), mats["carbon_fiber"])
    _box("COMPUTER_SCREEN", (0.42, 0.01, 0.26), (-1.8, -1.32, 1.05), mats["holo"])
    _cyl("COFFEE_MUG_001", 0.04, 0.09, (-1.35, -1.35, 0.82), mats["ceramic"], verts=16)
    _box("WHITEBOARD_001", (1.8, 0.04, 1.1), (3.95, -1.4, 1.7), mats["ceramic"])
    _box("WHITEBOARD_TRIM", (1.85, 0.02, 0.06), (3.95, -1.38, 2.22), mats["coat_trim"])

    _cyl("MICROSCOPE_001", 0.06, 0.28, (0.35, 1.45, 1.1), mats["steel"], verts=16)
    _sphere("MICROSCOPE_EYE", 0.04, (0.35, 1.55, 1.22), mats["glass"], segments=12, rings=8)
    _cyl("DNA_MODEL_001", 0.05, 0.35, (1.1, 1.35, 1.15), mats["plastic"], verts=12)
    _cyl("MEDICINE_BOTTLE_001", 0.035, 0.1, (0.2, 1.7, 0.98), mats["glass"], verts=12)

    # Soft atmospheric depth (not fog soup)
    fog = _box(
        "ATMO_SOFT_HAZE",
        (8, 8, 0.45),
        (0, 0, 2.7),
        pbr("haze", base=PALETTE["dawn_white"], rough=1.0, alpha=0.06),
    )

    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("LAB_WORLD")
        bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.12, 0.11, 0.10, 1)
        bg.inputs[1].default_value = 0.45

    return {
        "door": door,
        "table": table,
        "scanner": scanner,
        "floor": floor,
        "window": win,
        "holo": holo,
        "holo2": holo2,
        "fog": fog,
    }


def build_sample_container(mats: dict) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(radius=0.042, depth=0.13, location=(0.55, 1.55, 0.995), vertices=32)
    body = bpy.context.object
    body.name = "SAMPLE_CONTAINER_001"
    body.data.materials.append(mats["glass"])
    bpy.ops.mesh.primitive_cylinder_add(radius=0.048, depth=0.022, location=(0.55, 1.55, 1.065), vertices=24)
    cap = bpy.context.object
    cap.name = "SAMPLE_CAP"
    cap.data.materials.append(mats["plastic"])
    # Fluid level
    bpy.ops.mesh.primitive_cylinder_add(radius=0.038, depth=0.06, location=(0.55, 1.55, 0.97), vertices=24)
    fluid = bpy.context.object
    fluid.name = "SAMPLE_FLUID"
    fluid.data.materials.append(pbr("fluid", base=(0.3, 0.85, 0.7, 1), rough=0.15, emission=(0.2, 0.7, 0.55, 1), emission_strength=0.4))
    bpy.ops.object.select_all(action="DESELECT")
    body.select_set(True)
    cap.select_set(True)
    fluid.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.join()
    body["grasp_point"] = (0.0, 0.0, 0.04)
    body["mass_kg"] = 0.12
    body["collision"] = "cylinder"
    body["lod"] = "lod0"
    return body


def _assign_skin_weights(mesh_obj: bpy.types.Object, arm_obj: bpy.types.Object) -> None:
    mesh_obj.vertex_groups.clear()
    bone_pts = []
    for name, _parent, head, tail in BONES:
        h, t = Vector(head), Vector(tail)
        bone_pts.append((name, h, t, (t - h).length + 1e-6))
        mesh_obj.vertex_groups.new(name=name)
    for vi, v in enumerate(mesh_obj.data.vertices):
        best_name, best_d = "pelvis", 1e9
        for name, h, t, length in bone_pts:
            w = t - h
            if w.length < 1e-8:
                d = (v.co - h).length
            else:
                u = max(0.0, min(1.0, (v.co - h).dot(w) / w.length_squared))
                d = (v.co - (h + w * u)).length
            score = d / max(0.08, length * 0.35)
            if score < best_d:
                best_d = score
                best_name = name
        mesh_obj.vertex_groups[best_name].add([vi], 1.0, "REPLACE")
    mod = mesh_obj.modifiers.new(name="Armature", type="ARMATURE")
    mod.object = arm_obj
    mod.use_vertex_groups = True
    mesh_obj.parent = arm_obj


def build_production_doctor(mats: dict) -> tuple[bpy.types.Object, bpy.types.Object]:
    """Permanent production DOCTOR_001 — delegates to doctor_production_mesh."""
    from doctor_production_mesh import build_canonical_doctor

    arm, body, coat, _mats = build_canonical_doctor()
    # mats arg retained for API compatibility with callers that prebuild material_library()
    return arm, body


def animate_holo_screens(holo, holo2, fps: int = 24, end: int = 336) -> None:
    """Ambient screen pulse — visual storytelling life."""
    for obj, phase in ((holo, 0.0), (holo2, 1.2)):
        if obj is None or not obj.data.materials:
            continue
        mat = obj.data.materials[0]
        if not mat.use_nodes:
            continue
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if not bsdf or "Emission Strength" not in bsdf.inputs:
            continue
        for fr in range(1, end + 1, max(1, fps // 4)):
            t = fr / fps
            strength = 4.0 + 2.5 * abs(math.sin(t * 2.2 + phase))
            bsdf.inputs["Emission Strength"].default_value = strength
            bsdf.inputs["Emission Strength"].keyframe_insert("default_value", frame=fr)


def write_bone_map(path: Path, mesh) -> None:
    try:
        from doctor_production_mesh import BONES as DOC_BONES
        from doctor_production_mesh import FACIAL_SHAPE_KEYS as DOC_FACE

        bone_src = DOC_BONES
        facial_expected = DOC_FACE
    except Exception:
        bone_src = BONES
        facial_expected = []
    mapping = []
    for name, parent, head, tail in bone_src:
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
    facial = [k.name for k in mesh.data.shape_keys.key_blocks] if mesh.data.shape_keys else []
    path.write_text(
        json.dumps(
            {
                "actor_id": "DOCTOR_001",
                "world_id": "GENERATIONAL_MEDICAL_LAB",
                "prop_id": "SAMPLE_CONTAINER_001",
                "bones": mapping,
                "count": len(mapping),
                "facial_shape_keys": facial,
                "facial_channels_expected": facial_expected,
                "skinned": True,
                "armature": True,
                "asset_origin": "doctor_001_production_v1",
                "quality_tier": "production_v1",
                "creative_direction": "generational_v3",
            },
            indent=2,
        )
        + "\n"
    )
