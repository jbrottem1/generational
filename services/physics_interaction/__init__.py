"""Generational Physics & Interaction Engine.

Not a renderer. Not an image generator. Not a world builder.
Actors and objects obey physics. Nothing floats, clips, or teleports.
"""

from services.physics_interaction.attach import attach_physics_interactions
from services.physics_interaction.interaction import (
    build_interaction_package,
    plan_interactions_from_scene,
)
from services.physics_interaction.library import (
    ensure_physics_library,
    resolve_physics_profile,
)
from services.physics_interaction.materialize import (
    materialize_interaction,
    materialize_physics_profile,
)
from services.physics_interaction.package import build_physics_profile, build_scene_physics
from services.physics_interaction.validation import (
    validate_interaction_package,
    validate_physics_profile,
)

__all__ = [
    "attach_physics_interactions",
    "build_interaction_package",
    "build_physics_profile",
    "build_scene_physics",
    "ensure_physics_library",
    "materialize_interaction",
    "materialize_physics_profile",
    "plan_interactions_from_scene",
    "resolve_physics_profile",
    "validate_interaction_package",
    "validate_physics_profile",
]
