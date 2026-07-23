"""Frozen vocabulary — Physics & Interaction Engine.

Not a renderer. Not an image generator. Not a world builder.
Governs how digital actors physically exist and interact inside the world.
"""

from __future__ import annotations

PACKAGE_TYPE = "INTERACTION_PACKAGE"
PHYSICS_PROFILE_TYPE = "PHYSICS_PROFILE"
PACKAGE_VERSION = "1.0.0"
ENGINE_ID = "physics_interaction"
LIBRARY_VERSION = "1.0.0"

SUPPORTED_INTERACTIONS = (
    "walking",
    "running",
    "stopping",
    "turning",
    "jumping",
    "sitting",
    "standing",
    "leaning",
    "opening_doors",
    "closing_doors",
    "picking_up_objects",
    "putting_objects_down",
    "holding_objects",
    "writing",
    "typing",
    "pointing",
    "pressing_buttons",
    "touching_screens",
    "handshakes",
    "hugging",
    "medical_examinations",
    "using_microscopes",
    "using_tools",
    "reading_books",
    "turning_pages",
    "looking_through_windows",
)

HAND_CAPABILITIES = (
    "finger_articulation",
    "grasp_detection",
    "object_grip",
    "pressure",
    "release",
    "hand_object_alignment",
    "dual_hand_interactions",
)

FOOT_CAPABILITIES = (
    "foot_planting",
    "heel_strike",
    "toe_roll",
    "stairs",
    "uneven_terrain",
    "balance",
    "friction",
)

BODY_CAPABILITIES = (
    "center_of_gravity",
    "weight_transfer",
    "momentum",
    "acceleration",
    "deceleration",
    "balance_correction",
    "body_rotation",
    "secondary_motion",
)

OBJECT_PROPERTIES = (
    "mass",
    "center_of_gravity",
    "collision_volume",
    "material",
    "friction",
    "interaction_zones",
)

COLLISION_FORBID = (
    "walking_through_walls",
    "hands_through_objects",
    "feet_below_floors",
    "floating_objects",
    "body_clipping",
)

CLOTHING_FORCES = (
    "coat_movement",
    "shirt_folds",
    "fabric_response",
    "gravity",
    "wind",
    "body_collision",
)

HAIR_FORCES = (
    "gravity",
    "wind",
    "head_motion",
    "secondary_movement",
)

ENV_WIND_TARGETS = (
    "hair",
    "clothing",
    "trees",
    "grass",
    "flags",
    "paper",
)

ENV_RAIN_TARGETS = (
    "surfaces",
    "clothing",
    "puddles",
    "footprints",
)

REJECT_REASONS = (
    "floating_actors",
    "sliding_feet",
    "object_clipping",
    "broken_collisions",
    "weightless_movement",
    "hands_missing_targets",
    "unrealistic_balance",
)

PHYSICS_STATES = (
    "idle",
    "approaching",
    "contacting",
    "grasping",
    "manipulating",
    "releasing",
    "complete",
    "failed",
)
