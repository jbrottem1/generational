"""Generational Real-Time Animation Execution Layer.

Converts studio packages into EXECUTABLE_ANIMATION_SCENE and drives a
skeletal runtime via AnimationExecutionAdapter.

Does not create another planning framework.
Does not fake skeletal animation with still-image motion.
"""

from services.animation_execution.capability import audit_capabilities
from services.animation_execution.golden_motion import run_golden_motion_validation
from services.animation_execution.scene import build_executable_animation_scene
from services.animation_execution.select_runtime import select_runtime

__all__ = [
    "audit_capabilities",
    "build_executable_animation_scene",
    "run_golden_motion_validation",
    "select_runtime",
]
