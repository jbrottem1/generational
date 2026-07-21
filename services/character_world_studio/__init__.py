"""Character & World Studio — living universe layer for Generational productions."""

from __future__ import annotations

from services.character_world_studio.cast import get_host, list_hosts
from services.character_world_studio.locations import get_location, list_locations
from services.character_world_studio.package import (
    attach_character_world_studio,
    build_character_world_studio_package,
    studio_place_candidate,
)

__all__ = [
    "attach_character_world_studio",
    "build_character_world_studio_package",
    "get_host",
    "get_location",
    "list_hosts",
    "list_locations",
    "studio_place_candidate",
]
