"""Persistent World & Environment System — contracts and boundaries.

Ownership (frozen architecture):
  Scene Builder → what happens / subjects / actions / duration
  World Builder → where / persistent environment / objects / continuity / spatial links
  AI Cinematic Director → camera / framing / lighting treatment / motion / pacing
  Asset Intelligence → media selection / cache
  Renderer → technical render of approved plans

World Builder must NOT prescribe final camera, framing, lighting treatment, or edit transitions.
"""

from __future__ import annotations

from typing import Any

PACKAGE_VERSION = "2.0.0"
WORLD_SCHEMA_VERSION = "2.0.0"

WORLD_TYPES = (
    "Science Lab",
    "Museum",
    "Ancient Rome",
    "Outer Space",
    "Mars Colony",
    "Rainforest",
    "Ocean Floor",
    "Human Cell",
    "Hospital",
    "Operating Room",
    "Factory",
    "DNA Interior",
    "Solar System",
    "Medieval Village",
    "Courtroom",
    "Stock Exchange",
    "Ancient Egypt",
    "Future City",
    "Nature Preserve",
    "University",
    "Library",
    "Research Center",
    "AI Laboratory",
    "Ocean Research Observatory",
    "Microscopic Biological Environment",
)

# Scene Builder → World Builder request fields
REQUEST_FIELDS = (
    "topic",
    "scene_purpose",
    "time_period",
    "location_type",
    "required_subjects",
    "required_objects",
    "required_actions",
    "scientific_constraints",
    "historical_constraints",
    "continuity_requirements",
    "existing_world_id",
    "platform",
    "audience",
    "channel",
    "scene_id",
)

# Per-scene Environment Package (World Builder output; no cinematic prescriptions)
ENVIRONMENT_PACKAGE_FIELDS = (
    "world_id",
    "world_version",
    "environment_name",
    "selected_zone",
    "spatial_layout",
    "required_persistent_objects",
    "required_temporary_objects",
    "background_activity",
    "environmental_ambience",
    "scale",
    "continuity_state",
    "scientific_constraints",
    "historical_constraints",
    "allowed_subject_positions",
    "restricted_areas",
    "recommended_transition_destination",
    "asset_requirements",
    "world_validation",
)

STATE_EVENT_TYPES = (
    "door_toggled",
    "object_moved",
    "display_activated",
    "equipment_introduced",
    "weather_changed",
    "time_advanced",
    "environmental_damage",
    "character_entered",
    "character_exited",
    "experiment_progressed",
    "location_state_changed",
    "reset",
)


def world_id_for_type(world_type: str) -> str:
    slug = "".join(c if c.isalnum() else "_" for c in world_type.upper()).strip("_")
    while "__" in slug:
        slug = slug.replace("__", "_")
    return f"WORLD-{slug}"


def empty_object(
    *,
    name: str,
    object_id: str = "",
    surface: str = "floor",
    x: float = 0.5,
    y: float = 0.0,
    z: float = 0.5,
    zone: str = "",
    relationships: list[str] | None = None,
    temporary: bool = False,
) -> dict[str, Any]:
    oid = object_id or f"obj_{name.lower().replace(' ', '_')}"
    return {
        "object_id": oid,
        "name": name,
        "surface": surface,
        "anchored": True,
        "temporary": temporary,
        "zone": zone,
        "position": {"x": x, "y": y, "z": z},
        "scale": 1.0,
        "relationships": relationships or [],
    }


def empty_world_request(**overrides: Any) -> dict[str, Any]:
    base = {k: ([] if k.endswith("s") or "constraints" in k or "requirements" in k else "") for k in REQUEST_FIELDS}
    base["required_subjects"] = []
    base["required_objects"] = []
    base["required_actions"] = []
    base["scientific_constraints"] = []
    base["historical_constraints"] = []
    base["continuity_requirements"] = []
    base.update(overrides)
    return base


def empty_world_state(*, world_id: str, production_id: str = "") -> dict[str, Any]:
    return {
        "world_id": world_id,
        "production_id": production_id,
        "object_positions": {},
        "environment_state": {},
        "time_of_day": "day",
        "weather": "",
        "damage": {},
        "introduced_objects": [],
        "visited_zones": [],
        "doors": {},
        "displays": {},
        "characters_present": [],
        "events": [],
        "version": 1,
    }
