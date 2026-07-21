"""Generational Stage & World Simulation Engine.

Persistent explorable 3D stages. Not a renderer. Not an image generator.
Characters move through the world — they do not stand in front of photographs.
"""

from services.stage_world_simulation.attach import (
    attach_world_simulation,
    attach_world_to_candidate,
)
from services.stage_world_simulation.library import (
    ensure_world_library,
    get_world,
    list_worlds,
    load_library,
    resolve_world_package,
)
from services.stage_world_simulation.materialize import materialize_world_package
from services.stage_world_simulation.package import build_world_package
from services.stage_world_simulation.validation import validate_world_package

__all__ = [
    "attach_world_simulation",
    "attach_world_to_candidate",
    "build_world_package",
    "ensure_world_library",
    "get_world",
    "list_worlds",
    "load_library",
    "materialize_world_package",
    "resolve_world_package",
    "validate_world_package",
]
