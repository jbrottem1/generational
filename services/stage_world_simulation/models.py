"""Frozen vocabulary — Stage & World Simulation Engine.

Not a renderer. Not an image generator.
Persistent 3D stages where digital actors perform.
"""

from __future__ import annotations

PACKAGE_TYPE = "WORLD_PACKAGE"
PACKAGE_VERSION = "1.0.0"
ENGINE_ID = "stage_world_simulation"
LIBRARY_VERSION = "1.0.0"

NAV_CAPABILITIES = (
    "walking",
    "running",
    "turning",
    "stairs",
    "sitting",
    "opening_doors",
    "approaching_objects",
    "moving_around_furniture",
    "avoiding_collisions",
)

LIVING_CHANNELS = (
    "moving_trees",
    "wind",
    "flowing_water",
    "animated_screens",
    "people_walking",
    "birds",
    "clouds",
    "steam",
    "lighting_changes",
    "ambient_particles",
)

CAMERA_MODES = (
    "tracking",
    "follow",
    "wide_establishing",
    "medium_coverage",
    "close_up_reaction",
    "over_the_shoulder",
    "motivated",
)

CAMERA_TO_TRUE_MOTION = {
    "tracking": "tracking",
    "follow": "tracking",
    "wide_establishing": "pull_out",
    "medium_coverage": "orbit",
    "close_up_reaction": "push_in",
    "over_the_shoulder": "handheld",
    "motivated": "tracking",
}

PROP_INTERACTIONS: dict[str, tuple[str, ...]] = {
    "chair": ("sit", "stand"),
    "desk": ("lean", "write", "place_object"),
    "microscope": ("inspect", "adjust", "point"),
    "whiteboard": ("write", "erase", "present"),
    "door": ("open", "close", "enter", "exit"),
    "hologram": ("point", "gesture", "explain"),
    "console": ("type", "touch", "lean"),
    "bookshelf": ("browse", "take_book", "place_book"),
    "bench": ("sit", "stand"),
    "exhibit": ("inspect", "point", "activate"),
}

GEOMETRY_ELEMENTS = (
    "floor",
    "walls",
    "ceilings",
    "doors",
    "windows",
    "furniture",
    "props",
)

REJECT_REASONS = (
    "flat_image_background",
    "actors_cannot_navigate",
    "objects_not_interactable",
    "environment_static",
    "camera_replaces_character_movement",
)

# Mission recurring locations
RECURRING_WORLD_IDS = (
    "WORLD-GMRI-MEDICAL-LAB",
    "WORLD-LECTURE-HALL",
    "WORLD-SCIENCE-MUSEUM",
    "WORLD-LIBRARY",
    "WORLD-FOREST",
    "WORLD-CITY-PARK",
    "WORLD-SPACE-STATION",
    "WORLD-HOSPITAL",
    "WORLD-CLASSROOM",
    "WORLD-OCEAN-RESEARCH",
)
