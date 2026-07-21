"""Virtual Film Director — closed vocabularies (direction only, no renderer)."""

from __future__ import annotations

PACKAGE_TYPE = "VIRTUAL_FILM_DIRECTOR_PACKAGE"
PACKAGE_VERSION = "1.0.0"

SHOT_LANGUAGE = (
    "epic_establishing",
    "wide_landscape",
    "hero_shot",
    "medium_dialogue",
    "close_up",
    "extreme_close_up",
    "over_the_shoulder",
    "pov",
    "tracking_shot",
    "orbit_shot",
    "crane_shot",
    "drone_shot",
    "reveal_shot",
    "push_in",
    "pull_out",
    "parallax",
    "rack_focus",
    "slow_motion",
    "action_follow",
)

# Map VFD shot language → Animation Engine / true_motion tokens
SHOT_TO_TRUE_MOTION = {
    "epic_establishing": "pull_out",
    "wide_landscape": "pull_out",
    "hero_shot": "push_in",
    "medium_dialogue": "push_in",
    "close_up": "push_in",
    "extreme_close_up": "punch_in",
    "over_the_shoulder": "tracking",
    "pov": "handheld",
    "tracking_shot": "tracking",
    "orbit_shot": "orbit",
    "crane_shot": "pull_out",
    "drone_shot": "pull_out",
    "reveal_shot": "reveal",
    "push_in": "push_in",
    "pull_out": "pull_out",
    "parallax": "parallax",
    "rack_focus": "rack_focus",
    "slow_motion": "push_in",
    "action_follow": "tracking",
}

SHOT_TO_AE_CAMERA = {
    "epic_establishing": "crane",
    "wide_landscape": "crane",
    "hero_shot": "hero_low_angle_push",
    "medium_dialogue": "slow_cinematic_push",
    "close_up": "dolly_forward",
    "extreme_close_up": "dynamic_zoom",
    "over_the_shoulder": "tracking",
    "pov": "handheld_documentary",
    "tracking_shot": "tracking",
    "orbit_shot": "orbit",
    "crane_shot": "crane",
    "drone_shot": "crane",
    "reveal_shot": "reveal",
    "push_in": "slow_cinematic_push",
    "pull_out": "dolly_backward",
    "parallax": "parallax",
    "rack_focus": "rack_focus",
    "slow_motion": "slow_cinematic_push",
    "action_follow": "tracking",
}

SHOT_SIZE_FROM_LANGUAGE = {
    "epic_establishing": "establishing_wide",
    "wide_landscape": "establishing_wide",
    "hero_shot": "hero_low_angle",
    "medium_dialogue": "dynamic_medium",
    "close_up": "intimate_close_up",
    "extreme_close_up": "intimate_close_up",
    "over_the_shoulder": "dynamic_medium",
    "pov": "intimate_close_up",
    "tracking_shot": "dynamic_medium",
    "orbit_shot": "dynamic_medium",
    "crane_shot": "establishing_wide",
    "drone_shot": "establishing_wide",
    "reveal_shot": "establishing_wide",
    "push_in": "dynamic_medium",
    "pull_out": "establishing_wide",
    "parallax": "dynamic_medium",
    "rack_focus": "intimate_close_up",
    "slow_motion": "dynamic_medium",
    "action_follow": "dynamic_medium",
}

EMOTIONAL_BEATS = (
    "curiosity",
    "wonder",
    "discovery",
    "explanation",
    "scale",
    "surprise",
    "relief",
    "payoff",
)

LENS_STYLES = (
    "wide_24mm",
    "standard_35mm",
    "portrait_50mm",
    "close_85mm",
    "telephoto_tele",
    "anamorphic_feel",
)

CAMERA_ANGLES = (
    "eye_level",
    "low_angle_hero",
    "high_angle_vulnerable",
    "dutch_subtle",
    "overhead",
    "ground_level",
)

TRANSITIONS = (
    "hard_cut",
    "motion_match_cut",
    "lighting_continuity",
    "object_continuation",
    "environmental_continuation",
    "character_continuation",
    "natural_reveal",
    "perspective_shift",
    "focus_rack_transition",
    "seamless_camera_continuation",
)

DIRECTOR_QUESTIONS = (
    "why_scene_exists",
    "what_viewer_learns",
    "emotion_to_feel",
    "notice_first",
    "what_should_move",
    "what_should_remain_still",
    "camera_begin",
    "camera_end",
    "cinematic_payoff",
)

ANIMATION_PRIORITIES = (
    "character_performance",
    "environment_life",
    "camera_storytelling",
    "object_physics",
    "lighting_mood",
    "motion_graphics_explain",
)
