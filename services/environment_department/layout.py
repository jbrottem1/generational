"""Spatial layout, zones, and layered foreground/midground/background design."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Transform:
    position: tuple[float, float, float]
    rotation: tuple[float, float, float] = (0.0, 0.0, 0.0)
    scale: tuple[float, float, float] = (1.0, 1.0, 1.0)


@dataclass
class SceneNode:
    node_id: str
    node_type: str
    transform: Transform
    material_id: str | None = None
    children: list[SceneNode] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    animated: bool = False
    interaction_points: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "transform": asdict(self.transform),
            "material_id": self.material_id,
            "children": [c.to_dict() for c in self.children],
            "tags": self.tags,
            "animated": self.animated,
            "interaction_points": self.interaction_points,
        }


def default_lab_zones() -> list[dict[str, Any]]:
    return [
        {
            "zone_id": "teaching_zone",
            "bounds": [[-2, 0, -2], [4, 3, 4]],
            "function": "doctor_explanation",
            "camera_access": True,
            "character_access": True,
        },
        {
            "zone_id": "sterile_lab_zone",
            "bounds": [[5, 0, -4], [11, 3, 3]],
            "function": "sample_analysis",
            "camera_access": True,
            "character_access": "authorized_only",
        },
        {
            "zone_id": "circulation_path",
            "bounds": [[-8, 0, -1], [8, 3, 1]],
            "function": "staff_movement",
            "camera_access": True,
            "character_access": True,
        },
    ]


def layered_spatial_design(*, environment_id: str) -> dict[str, Any]:
    return {
        "environment_id": environment_id,
        "require_three_layers": True,
        "foreground": [
            {"id": "scanner_arm_edge", "type": "prop", "purpose": "depth_frame"},
            {"id": "plant_edge", "type": "vegetation", "purpose": "life_and_parallax"},
            {"id": "console_rail", "type": "architecture", "purpose": "camera_frame"},
        ],
        "midground": [
            {"id": "primary_character", "type": "character", "purpose": "action"},
            {"id": "diagnostic_hologram", "type": "prop", "purpose": "education_focus"},
            {"id": "teaching_console", "type": "prop", "purpose": "function"},
        ],
        "background": [
            {"id": "observation_window", "type": "architecture", "purpose": "depth"},
            {"id": "researchers_working", "type": "background_population", "purpose": "inhabited_world"},
            {"id": "secondary_lab_bays", "type": "architecture", "purpose": "function_history"},
            {"id": "sky_or_courtyard", "type": "exterior", "purpose": "world_beyond_frame"},
        ],
        "depth_tools": [
            "focus",
            "scale",
            "contrast",
            "lighting",
            "atmospheric_haze",
            "color_temperature",
            "motion_speed",
            "parallax",
        ],
        "reject": ["flat_backdrop", "empty_void", "single_layer_only"],
    }


def build_scene_graph(environment_id: str) -> dict[str, Any]:
    root = SceneNode(
        node_id=f"{environment_id}_root",
        node_type="architecture",
        transform=Transform((0, 0, 0)),
        tags=["root"],
        children=[
            SceneNode(
                "floor",
                "architecture",
                Transform((0, 0, 0), scale=(18, 1, 25)),
                material_id="medical_floor_polymer",
                tags=["floor", "contact"],
            ),
            SceneNode(
                "teaching_console",
                "prop",
                Transform((0, 1.0, -1.5)),
                material_id="brushed_titanium_medical",
                tags=["midground", "interaction"],
                interaction_points=["screen", "handle"],
                animated=True,
            ),
            SceneNode(
                "plant_edge",
                "vegetation",
                Transform((-2.2, 0.0, 1.0)),
                material_id="leaf_translucent",
                tags=["foreground"],
                animated=True,
            ),
            SceneNode(
                "observation_window",
                "architecture",
                Transform((0, 2.5, -12)),
                material_id="glass_clear",
                tags=["background"],
            ),
            SceneNode(
                "key_sun",
                "light",
                Transform((-3, 5, 2)),
                tags=["key"],
            ),
        ],
    )
    return {
        "environment_id": environment_id,
        "root": root.to_dict(),
        "node_types": [
            "architecture",
            "terrain",
            "prop",
            "vegetation",
            "vehicle",
            "character",
            "light",
            "weather",
            "particle_system",
            "signage",
            "path",
            "water",
            "background_population",
        ],
    }


def build_layout(environment: dict[str, Any]) -> dict[str, Any]:
    eid = environment.get("environment_id") or "environment"
    dims = environment.get("dimensions_meters") or {}
    return {
        "environment_id": eid,
        "dimensions_meters": dims,
        "zones": default_lab_zones() if "lab" in str(eid) or "medical" in str(eid) else default_lab_zones(),
        "paths": ["main_circulation", "sterile_access", "emergency_exit_east"],
        "entrances": ["main_airlock"],
        "exits": ["main_airlock", "emergency_exit_east"],
        "camera_safe_zones": ["teaching_zone"],
        "character_movement_zones": ["teaching_zone", "circulation_path"],
        "interaction_zones": ["teaching_console", "scanner_bay"],
        "equipment_zones": ["sterile_lab_zone"],
        "collision_boundaries": True,
        "visibility_zones": ["teaching_zone_to_window"],
        "lighting_zones": ["clinical_key", "holo_practical", "window_fill"],
        "sound_zones": ["soft_hvac", "holo_hum", "distant_footsteps"],
        "layered_spatial_design": layered_spatial_design(environment_id=str(eid)),
        "scene_graph": build_scene_graph(str(eid)),
    }
