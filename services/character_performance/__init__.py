"""Facial Performance System — structured character performance for existing animation layers.

Architecture frozen. Not a renderer. Plans are contracts; MP4 inspection is the quality gate.
"""

from __future__ import annotations

from services.character_performance.attention import build_attention, infer_attention_from_scene
from services.character_performance.blinking import blink_probability, build_blink_profile
from services.character_performance.emotion import EmotionVector, blend_emotions, resolve_emotion
from services.character_performance.face_rig import face_rig_profile
from services.character_performance.gaze import GazeMode, compute_eye_pose, plan_gaze_events
from services.character_performance.performance_plan import (
    attach_facial_performance_plans,
    build_facial_performance_plan,
)
from services.character_performance.speech import build_speech_performance
from services.character_performance.validation import (
    rendered_facial_inspection_template,
    validate_facial_performance_plan,
    validate_scene_facial_plans,
)

__all__ = [
    "EmotionVector",
    "GazeMode",
    "attach_facial_performance_plans",
    "blend_emotions",
    "blink_probability",
    "build_attention",
    "build_blink_profile",
    "build_facial_performance_plan",
    "build_speech_performance",
    "compute_eye_pose",
    "face_rig_profile",
    "infer_attention_from_scene",
    "plan_gaze_events",
    "rendered_facial_inspection_template",
    "resolve_emotion",
    "validate_facial_performance_plan",
    "validate_scene_facial_plans",
]
