"""Frozen vocabulary for the Character Performance Engine.

This is NOT a renderer. Packages describe actor blocking, locomotion,
interactions, living environments, and camera-follow contracts that existing
Animation Engine / true_motion systems execute.
"""

from __future__ import annotations

PACKAGE_TYPE = "CHARACTER_PERFORMANCE_PACKAGE"
PACKAGE_VERSION = "1.0.0"
ENGINE_ID = "character_performance_engine"

# Continuous body verbs — must appear in every non-dramatic scene
BODY_ACTIONS = (
    "walk",
    "turn",
    "stop",
    "weight_shift",
    "breathe",
    "look_around",
    "head_turn",
    "eye_track",
    "blink",
    "arm_gesture",
    "finger_motion",
    "shoulder_motion",
    "hip_rotation",
    "foot_plant",
    "balance",
    "momentum",
    "secondary_motion",
)

INTERACTION_VERBS = (
    "pick_up",
    "point",
    "touch_display",
    "open_door",
    "sit",
    "stand",
    "lean",
    "use_whiteboard",
    "look_through_microscope",
    "approach_patient",
    "walk_toward_camera",
    "walk_away",
)

ENVIRONMENT_LIFE = (
    "doors_open",
    "people_walk",
    "machines_operate",
    "screens_update",
    "clouds_move",
    "trees_sway",
    "grass_wind",
    "steam_rise",
    "lights_flicker",
    "birds_fly",
    "water_flow",
    "cars_pass",
    "particles_drift",
)

CAMERA_FOLLOW_MODES = (
    "walk_and_talk",
    "tracking",
    "follow",
    "over_the_shoulder",
    "conversation_coverage",
    "wide_establishing",
    "close_up_reaction",
    "orbit_demonstrate",
)

# true_motion camera tokens that FOLLOW action (not replace it)
CAMERA_TO_TRUE_MOTION = {
    "walk_and_talk": "tracking",
    "tracking": "tracking",
    "follow": "tracking",
    "over_the_shoulder": "handheld",
    "conversation_coverage": "orbit",
    "wide_establishing": "pull_out",
    "close_up_reaction": "push_in",
    "orbit_demonstrate": "orbit",
}

PERFORMANCE_HINTS = (
    "walk_explain",
    "point_teach",
    "celebrate",
    "swim_float",
)

# Reject signatures — "could be recreated by moving a still photograph"
REJECT_SIGNATURES = (
    "moving_still_image",
    "camera_only_movement",
    "ken_burns",
    "floating_head",
    "talking_photograph",
    "static_background",
    "minimal_body_movement",
    "lifeless_performance",
    "image_pan",
    "image_zoom",
    "photo_scale",
    "photo_rotate",
    "layer_slide_only",
)

MAX_STATIONARY_SEC = 3.0
MIN_LOCOMOTION_WAYPOINTS = 2
MIN_BODY_ACTIONS = 6
MIN_ENVIRONMENT_LIFE = 3
MIN_INTERACTIONS = 1
