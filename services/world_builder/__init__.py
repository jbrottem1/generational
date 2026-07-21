"""services.world_builder — Persistent World & Environment System."""

from __future__ import annotations

from services.world_builder.catalog import get_catalog, get_world, list_world_types, select_world_type
from services.world_builder.environment import build_environment_package
from services.world_builder.library import (
    create_world_variation,
    extend_world,
    get_library_world,
    record_world_usage,
    save_world,
    search_worlds,
    seed_library_from_catalog,
    select_best_world,
)
from services.world_builder.models import PACKAGE_VERSION, WORLD_TYPES, empty_world_request
from services.world_builder.package import (
    apply_world_to_candidate,
    build_world_package,
    fulfill_world_request,
    place_candidate_in_world,
)
from services.world_builder.state import (
    apply_state_event,
    load_state,
    reset_world_state,
    save_state,
)
from services.world_builder.validate import (
    validate_environment_package,
    validate_production_continuity,
    validate_world_package,
)

__all__ = [
    "PACKAGE_VERSION",
    "WORLD_TYPES",
    "apply_state_event",
    "apply_world_to_candidate",
    "build_environment_package",
    "build_world_package",
    "create_world_variation",
    "empty_world_request",
    "extend_world",
    "fulfill_world_request",
    "get_catalog",
    "get_library_world",
    "get_world",
    "list_world_types",
    "load_state",
    "place_candidate_in_world",
    "record_world_usage",
    "reset_world_state",
    "save_state",
    "save_world",
    "search_worlds",
    "seed_library_from_catalog",
    "select_best_world",
    "select_world_type",
    "validate_environment_package",
    "validate_production_continuity",
    "validate_world_package",
]
