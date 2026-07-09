"""Animation & Cinematic Production — Agent 16's motion planning layer.

Transforms static creative assets into fully planned animated productions:
timeline, camera, character motion, facial, lip sync, VFX, transitions,
audio sync, and provider instructions. Does NOT render final video.

Public surface:
    from services.animation import build_animation_package, plan_items
    from services.animation import batch_plan, plan_series
"""

from services.animation.batch import batch_plan, plan_series, prepare_render_batch
from services.animation.config import (
    ANIMATION_STYLES,
    CAMERA_STYLES,
    MOTION_INTENSITIES,
    QUALITY_TIERS,
    AnimationConfig,
    configure,
    get_animation_config,
    reset_animation_config,
)
from services.animation.models import (
    ANIMATION_ENGINE_VERSION,
    ANIMATION_PACKAGE_FIELDS,
    ANIMATION_PACKAGE_VERSION,
    ANIMATION_SUMMARY_FIELDS,
    BODY_ANIMATION_FIELDS,
    CAMERA_KEYFRAME_FIELDS,
    CAMERA_SHOT_FIELDS,
    CHARACTER_MOTION_FIELDS,
    CHOREOGRAPHY_FIELDS,
    EFFECT_FIELDS,
    EXPORT_METADATA_FIELDS,
    FACIAL_ANIMATION_FIELDS,
    LIGHTING_CUE_FIELDS,
    LIP_SYNC_FIELDS,
    MOTION_GRAPHICS_FIELDS,
    PROVIDER_INSTRUCTION_FIELDS,
    QUALITY_REPORT_FIELDS,
    SCENE_TIMING_FIELDS,
    SUBTITLE_CUE_FIELDS,
    TIMELINE_CLIP_FIELDS,
    TIMELINE_FIELDS,
    TIMELINE_TRACK_FIELDS,
    TRANSITION_FIELDS,
    CameraMovement,
    CameraShotType,
    CharacterAction,
    EffectType,
    FacialExpression,
    ReadinessStatus,
    TransitionType,
)
from services.animation.package import (
    build_animation_package,
    collect_animation_items,
    plan_items,
)
from services.animation.quality import production_readiness, validate_package

__all__ = [
    "ANIMATION_ENGINE_VERSION",
    "ANIMATION_PACKAGE_FIELDS",
    "ANIMATION_PACKAGE_VERSION",
    "ANIMATION_STYLES",
    "ANIMATION_SUMMARY_FIELDS",
    "BODY_ANIMATION_FIELDS",
    "CAMERA_KEYFRAME_FIELDS",
    "CAMERA_SHOT_FIELDS",
    "CAMERA_STYLES",
    "CHARACTER_MOTION_FIELDS",
    "CHOREOGRAPHY_FIELDS",
    "EFFECT_FIELDS",
    "EXPORT_METADATA_FIELDS",
    "FACIAL_ANIMATION_FIELDS",
    "LIGHTING_CUE_FIELDS",
    "LIP_SYNC_FIELDS",
    "MOTION_GRAPHICS_FIELDS",
    "MOTION_INTENSITIES",
    "PROVIDER_INSTRUCTION_FIELDS",
    "QUALITY_REPORT_FIELDS",
    "QUALITY_TIERS",
    "SCENE_TIMING_FIELDS",
    "SUBTITLE_CUE_FIELDS",
    "TIMELINE_CLIP_FIELDS",
    "TIMELINE_FIELDS",
    "TIMELINE_TRACK_FIELDS",
    "TRANSITION_FIELDS",
    "AnimationConfig",
    "CameraMovement",
    "CameraShotType",
    "CharacterAction",
    "EffectType",
    "FacialExpression",
    "ReadinessStatus",
    "TransitionType",
    "batch_plan",
    "build_animation_package",
    "collect_animation_items",
    "configure",
    "get_animation_config",
    "plan_items",
    "plan_series",
    "prepare_render_batch",
    "production_readiness",
    "reset_animation_config",
    "validate_package",
]
