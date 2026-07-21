"""Animation Engine — closed vocabularies (planning enhancement, no renderer).

V1 = motion minimums. V2 = cinematic storytelling + immersion quality.
"""

from __future__ import annotations

PACKAGE_TYPE = "ANIMATION_PACKAGE"
PACKAGE_VERSION = "2.0.0"

# Every scene must include at least one of these motion classes
MOTION_CLASSES = (
    "character_animation",
    "camera_movement",
    "object_movement",
    "environmental_movement",
    "particle_effects",
    "lighting_movement",
    "physics_animation",
    "ui_animation",
    "motion_graphics",
)

CAMERA_MOVES = (
    "dolly_forward",
    "dolly_backward",
    "crane",
    "orbit",
    "tracking",
    "handheld_documentary",
    "slow_cinematic_push",
    "reveal",
    "parallax",
    "depth_of_field",
    "rack_focus",
    "dynamic_zoom",
    "hero_low_angle_push",
    "vulnerability_high_angle",
)

# Map mission camera moves → MotionPlanner / true_motion tokens
CAMERA_TO_MOTION_EFFECT = {
    "dolly_forward": "cinematic_push_in",
    "dolly_backward": "slow_zoom_out",
    "crane": "slow_zoom_out",
    "orbit": "handheld_drift",
    "tracking": "pan_right",
    "handheld_documentary": "handheld_drift",
    "slow_cinematic_push": "cinematic_push_in",
    "reveal": "cinematic_push_in",
    "parallax": "pan_right",
    "depth_of_field": "documentary_slow_zoom",
    "rack_focus": "documentary_slow_zoom",
    "dynamic_zoom": "quick_punch_in",
    "hero_low_angle_push": "cinematic_push_in",
    "vulnerability_high_angle": "slow_zoom_out",
}

CAMERA_TO_TRUE_MOTION = {
    "dolly_forward": "push_in",
    "dolly_backward": "pull_out",
    "crane": "pull_out",
    "orbit": "orbit",
    "tracking": "tracking",
    "handheld_documentary": "handheld",
    "slow_cinematic_push": "push_in",
    "reveal": "reveal",
    "parallax": "parallax",
    "depth_of_field": "push_in",
    "rack_focus": "rack_focus",
    "dynamic_zoom": "punch_in",
    "hero_low_angle_push": "push_in",
    "vulnerability_high_angle": "pull_out",
}

TRANSITIONS = (
    "match_cut",
    "whip_pan",
    "morph",
    "object_transition",
    "environmental_wipe",
    "light_transition",
    "zoom_transition",
    "seamless_camera_continuation",
    "hard_cut",
    "focus_rack_transition",
    "motion_continue",
)

# Prefer cinematic transitions; avoid defaulting to crossfade
PREFERRED_TRANSITIONS = (
    "match_cut",
    "whip_pan",
    "zoom_transition",
    "object_transition",
    "seamless_camera_continuation",
    "environmental_wipe",
    "light_transition",
    "focus_rack_transition",
    "motion_continue",
    "hard_cut",
)

WORLD_ENV_TYPES = (
    "forest",
    "ocean",
    "city",
    "laboratory",
    "space",
    "countryside",
    "interior",
    "generic",
)

WORLD_ANIMATIONS = {
    "forest": [
        "leaves_moving",
        "wind",
        "birds",
        "sunlight_shifting",
        "fog_drift",
        "branch_sway",
        "dust_motes",
    ],
    "ocean": ["waves", "reflections", "spray", "moving_clouds", "foam", "light_caustics"],
    "city": ["traffic", "pedestrians", "lights", "smoke", "weather", "window_glow"],
    "laboratory": ["monitors", "holograms", "robots", "blinking_lights", "machinery", "dust_motes"],
    "space": ["drifting_particles", "rotating_planets", "moving_stars", "nebula_animation"],
    "countryside": [
        "grass_sway",
        "cloud_drift",
        "bird_flocks",
        "mist_motion",
        "wind",
        "leaves_fall",
        "moving_shadows",
    ],
    "interior": ["practical_light_flicker", "dust_motes", "curtain_sway", "ambient_bounce"],
    "generic": ["ambient_particles", "subtle_parallax", "light_drift", "cloud_drift", "wind"],
}

# Foreground / midground / background life tokens (V2 depth)
WORLD_DEPTH_LAYERS = {
    "forest": {
        "foreground": ["near_fern_sway", "leaf_litter"],
        "midground": ["tree_trunks", "path_haze"],
        "background": ["canopy_parallax", "sky_clouds"],
    },
    "ocean": {
        "foreground": ["foam_line", "spray"],
        "midground": ["wave_set", "boat_silhouette"],
        "background": ["horizon_haze", "cloud_banks"],
    },
    "city": {
        "foreground": ["street_edge", "signage_glow"],
        "midground": ["traffic_band", "storefronts"],
        "background": ["skyline_parallax", "sky"],
    },
    "laboratory": {
        "foreground": ["bench_edge", "instrument_glow"],
        "midground": ["equipment_bank", "screen_wash"],
        "background": ["room_depth", "ceiling_lights"],
    },
    "space": {
        "foreground": ["dust_near", "station_rail"],
        "midground": ["craft_body"],
        "background": ["star_field", "nebula"],
    },
    "countryside": {
        "foreground": ["grass_blades", "fence_post"],
        "midground": ["hill_roll", "cottage_or_field"],
        "background": ["distant_ridge", "cloud_banks", "birds"],
    },
    "interior": {
        "foreground": ["table_edge", "practical_lamp"],
        "midground": ["room_furniture"],
        "background": ["window_light", "wall_depth"],
    },
    "generic": {
        "foreground": ["near_parallax_band"],
        "midground": ["subject_stage"],
        "background": ["sky_or_wall", "ambient_drift"],
    },
}

CHARACTER_ACTIONS = (
    "blink",
    "head_turn",
    "walk",
    "gesture_while_speaking",
    "point_at_object",
    "emotional_react",
    "lip_sync",
    "breathe",
    "weight_shift",
    "eye_focus",
    "anticipation",
    "follow_through",
    "cloth_sway",
)

CHARACTER_MICRO = (
    "idle_breathe",
    "soft_blink",
    "gaze_shift",
    "posture_settle",
    "hand_settle",
    "weight_transfer",
)

OBJECT_ANIM_HINTS = {
    "hydrant": ["flowing_water", "valves_turning", "cutaway", "pressure_visualization"],
    "heart": ["beating", "blood_flow", "valves_opening"],
    "volcano": ["magma_movement", "smoke", "ash", "lava"],
    "black hole": ["accretion_disk", "gravitational_lensing", "debris_orbiting"],
    "blackhole": ["accretion_disk", "gravitational_lensing", "debris_orbiting"],
    "gold": ["coin_cascade", "chest_open", "glint"],
    "water": ["flow", "ripple", "pour"],
    "fire": ["flame_react", "embers", "smoke_drift"],
    "flag": ["fabric_wave"],
    "door": ["weighted_swing"],
}

MOTION_GRAPHICS_TYPES = (
    "animated_label",
    "arrow",
    "highlight",
    "kinetic_typography",
    "diagram",
    "callout",
    "map",
    "timeline",
)

EMOTIONS = (
    "curiosity",
    "awe",
    "tension",
    "warmth",
    "melancholy",
    "clarity",
    "focus",
)

LIGHTING_MOODS = (
    "golden_hour",
    "soft_daylight",
    "storm",
    "moonlight",
    "firelight",
    "volumetric_sunlight",
    "cinematic_contrast",
    "practical_interior",
)

SHOT_SIZES = (
    "establishing_wide",
    "dynamic_medium",
    "intimate_close_up",
    "hero_low_angle",
    "high_angle_vulnerable",
)

REJECT_VISUALS = (
    "static_background",
    "lifeless_environment",
    "placeholder_asset",
    "floating_icon",
    "abstract_geometry",
    "meaningless_movement",
    "purposeless_camera_drift",
    "poor_composition",
    "empty_frame",
    "low_resolution_asset",
    "repeated_mechanical_loop",
    "powerpoint_motion",
    "slideshow_presentation",
)

EXCELLENCE_DIMENSIONS = (
    "scene_motion",
    "camera_quality",
    "character_realism",
    "world_activity",
    "pacing",
    "visual_storytelling",
    "transition_quality",
    "cinematic_feel",
    "immersion",
    # V2 additions (averaged into excellence)
    "intentionality",
    "environmental_believability",
    "performance_life",
)

# Soft gate thresholds
MAX_STATIC_RUNTIME_PCT = 10.0
TARGET_SCENE_SEC_LOW = 2.0
TARGET_SCENE_SEC_HIGH = 4.0
MAX_STILL_WITHOUT_MOTION_SEC = 2.0
MIN_IMMERSION_PASS_RATIO = 0.85
MIN_EXCELLENCE_V2 = 78.0
