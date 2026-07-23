"""Eight Production Asset Studio departments — catalogs only, no new engines."""

from __future__ import annotations

from typing import Any

from services.production_asset_studio.models import DEPARTMENT_IDS


def list_departments() -> list[dict[str, Any]]:
    return [department_catalog(d) for d in DEPARTMENT_IDS]


def department_catalog(department_id: str) -> dict[str, Any]:
    builders = {
        "character_studio": _character,
        "environment_studio": _environment,
        "prop_studio": _props,
        "material_studio": _materials,
        "lighting_studio": _lighting,
        "facial_performance_studio": _facial,
        "animation_library": _animation,
        "visual_storytelling": _storytelling,
    }
    fn = builders.get(department_id)
    if not fn:
        return {"department_id": department_id, "ok": False, "reason": "unknown_department"}
    return fn()


def _character() -> dict[str, Any]:
    return {
        "department_id": "character_studio",
        "display_name": "Character Studio",
        "mission": "Production meshes, facial/body topology, clothing, materials — runtime-compatible",
        "priority_actors": ["DOCTOR_001", "FOUNDER_001"],
        "future_actors": ["TEACHER_001", "HISTORIAN_001", "ENGINEER_001", "NURSE_001", "PATIENT_CHILD_001"],
        "deliverables": [
            "production_mesh",
            "facial_topology",
            "body_topology",
            "skeletal_compatibility",
            "facial_rig",
            "clothing",
            "hair",
            "materials",
            "textures",
            "expressions",
            "animation_compatibility",
        ],
        "assets": [
            {
                "asset_id": "DOCTOR_001",
                "quality_tier": "phase_ii_production",
                "runtime_path": "data/studio_assets/DOCTOR_001/RUNTIME/DOCTOR_001_SKINNED.blend",
                "must_preserve": ["armature", "skinning", "shape_keys", "canonical_bones"],
            }
        ],
        "forbidden": ["image_plate_actors", "ken_burns_characters", "runtime_incompatible_rigs"],
    }


def _environment() -> dict[str, Any]:
    return {
        "department_id": "environment_studio",
        "display_name": "Environment Studio",
        "mission": "Replace greybox worlds with cinematic navigable locations",
        "priority_worlds": ["GENERATIONAL_MEDICAL_LAB"],
        "requirements": [
            "modern_architecture",
            "cinematic_lighting",
            "polished_floors",
            "laboratory_equipment",
            "holographic_displays",
            "furniture",
            "shelves",
            "books",
            "plants",
            "windows",
            "outdoor_scenery",
            "atmospheric_depth",
            "reflections",
            "high_quality_materials",
            "fully_navigable",
        ],
        "assets": [
            {
                "asset_id": "GENERATIONAL_MEDICAL_LAB",
                "world_package_id": "WORLD-GMRI-MEDICAL-LAB",
                "quality_tier": "phase_ii_production",
                "runtime_path": "data/studio_assets/DOCTOR_001/RUNTIME/GENERATIONAL_MEDICAL_LAB.blend",
                "flat_image_background": False,
            }
        ],
    }


def _props() -> dict[str, Any]:
    prop_ids = [
        "SAMPLE_CONTAINER_001",
        "MICROSCOPE_001",
        "MEDICAL_SCANNER_001",
        "DNA_MODEL_001",
        "COMPUTER_001",
        "TABLET_001",
        "COFFEE_MUG_001",
        "BOOK_STACK_001",
        "CHAIR_001",
        "DESK_001",
        "MEDICINE_BOTTLE_001",
        "WHITEBOARD_001",
        "LAB_INSTRUMENT_SET_001",
    ]
    return {
        "department_id": "prop_studio",
        "display_name": "Prop Studio",
        "mission": "Reusable production props with collision, grasp, and LOD",
        "required_fields": [
            "geometry",
            "materials",
            "collision",
            "interaction_points",
            "grasp_points",
            "lod_versions",
        ],
        "assets": [
            {
                "asset_id": pid,
                "quality_tier": "phase_ii_production",
                "grasp_points": ["grasp_primary"],
                "lod": ["lod0", "lod1"],
            }
            for pid in prop_ids
        ],
    }


def _materials() -> dict[str, Any]:
    mats = [
        "ceramic",
        "glass",
        "steel",
        "carbon_fiber",
        "plastic",
        "fabric",
        "leather",
        "wood",
        "paint",
        "concrete",
        "rubber",
        "skin_composite",
    ]
    return {
        "department_id": "material_studio",
        "display_name": "Material Studio",
        "mission": "Production PBR materials replacing placeholders",
        "workflow": "blender_principled_bsdf",
        "assets": [{"asset_id": f"MAT_{m.upper()}", "material_id": m, "pbr": True} for m in mats],
    }


def _lighting() -> dict[str, Any]:
    presets = [
        "morning_lab",
        "golden_hour",
        "soft_classroom",
        "night_laboratory",
        "hospital_emergency",
        "museum",
        "forest",
        "rain",
        "snow",
        "sunset",
    ]
    return {
        "department_id": "lighting_studio",
        "display_name": "Lighting Studio",
        "mission": "Reusable cinematic lighting presets",
        "assets": [
            {
                "asset_id": f"LIGHT_{p.upper()}",
                "preset_id": p,
                "includes": ["key", "fill", "rim", "practicals", "exposure"],
            }
            for p in presets
        ],
        "default_for_golden_motion": "morning_lab",
    }


def _facial() -> dict[str, Any]:
    return {
        "department_id": "facial_performance_studio",
        "display_name": "Facial Performance Studio",
        "mission": "Upgrade DOCTOR_001 facial realism while preserving shape-key contract",
        "supports": [
            "eye_moisture",
            "iris_detail",
            "independent_eyeballs",
            "micro_expressions",
            "natural_blinking",
            "brow_movement",
            "cheeks",
            "jaw",
            "lips",
            "visemes",
            "smiles",
            "concern",
            "joy",
            "curiosity",
            "empathy",
        ],
        "required_shape_keys": [
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
        ],
        "assets": [{"asset_id": "DOCTOR_001_FACE", "actor_id": "DOCTOR_001"}],
    }


def _animation() -> dict[str, Any]:
    clips = [
        "walking",
        "running",
        "idle",
        "teaching",
        "listening",
        "thinking",
        "greeting",
        "writing",
        "typing",
        "pointing",
        "picking_up_objects",
        "holding_objects",
        "sitting",
        "standing",
        "laughing",
        "looking_around",
        "medical_examination",
    ]
    return {
        "department_id": "animation_library",
        "display_name": "Animation Library",
        "mission": "Reusable skeletal animation clips — never image animation",
        "clip_format": "blender_action_or_joint_tracks",
        "assets": [{"asset_id": f"CLIP_{c.upper()}", "clip_id": c, "skeletal": True} for c in clips],
    }


def _storytelling() -> dict[str, Any]:
    return {
        "department_id": "visual_storytelling",
        "display_name": "Visual Storytelling",
        "mission": "Depth, life, and atmosphere without changing execution engines",
        "scene_layers": ["foreground", "midground", "background"],
        "requires": [
            "depth",
            "parallax",
            "ambient_movement",
            "weather",
            "dust",
            "fog",
            "volumetric_light",
            "moving_screens",
            "people_or_life_cues",
        ],
        "assets": [
            {
                "asset_id": "STORY_LAB_ATMOSPHERE_001",
                "world_id": "GENERATIONAL_MEDICAL_LAB",
                "effects": ["screen_pulse", "window_parallax", "soft_fog", "dust_motes"],
            }
        ],
    }
