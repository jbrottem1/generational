"""Generational Cinematic Direction Studio.

Not an animation engine. Not a renderer.
Directs every shot before rendering begins.
"""

from services.cinematic_direction_studio.attach import (
    attach_cinematic_direction,
    attach_cinematic_direction_to_candidate,
)
from services.cinematic_direction_studio.package import (
    build_director_package,
    build_episode_director_package,
)
from services.cinematic_direction_studio.validation import (
    validate_director_package,
    validate_episode_direction,
)

__all__ = [
    "attach_cinematic_direction",
    "attach_cinematic_direction_to_candidate",
    "build_director_package",
    "build_episode_director_package",
    "validate_director_package",
    "validate_episode_direction",
]
