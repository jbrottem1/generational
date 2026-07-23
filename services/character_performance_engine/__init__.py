"""Generational Character Performance Engine.

Pre-render performance system: blocking → locomotion → body → interactions →
environment life → camera-follow → simulation → true_motion bridge.

Not a renderer. Not an image generator. Not an animation filter.
"""

from services.character_performance_engine.package import (
    attach_character_performances,
    build_character_performance,
    build_episode_performance_package,
)
from services.character_performance_engine.true_motion_bridge import (
    package_true_motion_fields,
    path_to_ffmpeg_exprs,
    simulation_to_true_motion_path,
)
from services.character_performance_engine.validation import (
    rendered_performance_inspection_template,
    validate_character_performance,
)

__all__ = [
    "attach_character_performances",
    "build_character_performance",
    "build_episode_performance_package",
    "package_true_motion_fields",
    "path_to_ffmpeg_exprs",
    "rendered_performance_inspection_template",
    "simulation_to_true_motion_path",
    "validate_character_performance",
]
