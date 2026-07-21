"""Generational Character Rig Studio — permanent digital actors.

Not a renderer. Not an image generator. Not a video generator.
Scenes reference actors; scenes never recreate actors.
"""

from services.character_rig_studio.attach import attach_character_rigs
from services.character_rig_studio.library import (
    ensure_library,
    get_actor,
    list_actors,
    load_library,
    resolve_character_rig,
)
from services.character_rig_studio.materialize import materialize_character_rig
from services.character_rig_studio.package import build_character_rig
from services.character_rig_studio.validation import validate_character_rig

__all__ = [
    "attach_character_rigs",
    "build_character_rig",
    "ensure_library",
    "get_actor",
    "list_actors",
    "load_library",
    "materialize_character_rig",
    "resolve_character_rig",
    "validate_character_rig",
]
