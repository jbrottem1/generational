"""Validate worlds, environment packages, and production continuity."""

from __future__ import annotations

from typing import Any


def validate_world_package(package: dict[str, Any]) -> dict[str, Any]:
    fails: list[str] = []
    warnings: list[str] = []
    repairs: list[str] = []
    recommendations: list[str] = []

    world = package.get("world") or {}
    if not package.get("world_id") and not world.get("world_id"):
        fails.append("missing_environment_identity")
    if not (world.get("name") or package.get("name")):
        fails.append("empty_or_meaningless_location")

    env_packages = package.get("environment_packages") or []
    if not env_packages and not package.get("continuity"):
        fails.append("empty_environment_packages")

    # Objects
    objects = list(world.get("objects") or []) + list(world.get("furniture") or [])
    for obj in objects:
        if not isinstance(obj, dict):
            continue
        if not obj.get("surface") or obj.get("anchored") is False:
            fails.append(f"floating_object:{obj.get('object_id') or obj.get('name')}")

    # Era / accuracy
    for wkey in ("scientific_constraints", "historical_constraints"):
        if world.get(wkey) is None and package.get(wkey):
            pass

    # Duplicate empty / meaningless backgrounds (persistent same-zone reuse is allowed)
    bindings = (package.get("continuity") or {}).get("scene_bindings") or []
    bgs = [str(b.get("background_identity") or "") for b in bindings]
    if bgs and all(not bg or bg.endswith("|scale=") for bg in bgs):
        fails.append("excessive_reuse_of_one_background")
    if len(bgs) >= 2 and len(set(bgs)) == 1 and not any(b.get("persistent_object_ids") for b in bindings):
        fails.append("excessive_reuse_of_one_background")

    if not world.get("zones") and len(env_packages) > 2:
        warnings.append("no_zones_defined_for_multi_scene")

    hard = sorted(set(fails))
    return {
        "ok": not hard,
        "passed": not hard,
        "hard_failures": hard,
        "hard_fails": hard,
        "repairable_continuity_issues": sorted(set(repairs)),
        "accuracy_warnings": sorted(set(warnings)),
        "creative_recommendations": recommendations,
        "scene_count": len(env_packages) or len(bindings),
    }


def validate_environment_package(
    env: dict[str, Any],
    *,
    world: dict[str, Any] | None = None,
    previous: dict[str, Any] | None = None,
) -> dict[str, Any]:
    fails: list[str] = []
    warnings: list[str] = []
    repairs: list[str] = []

    if not env.get("world_id"):
        fails.append("missing_environment_identity")
    if not env.get("selected_zone") and not env.get("environment_name"):
        fails.append("empty_or_meaningless_location")
    if not env.get("spatial_layout"):
        fails.append("missing_spatial_layout")

    for obj in list(env.get("required_persistent_objects") or []) + list(env.get("required_temporary_objects") or []):
        if not obj.get("surface") and not obj.get("anchored"):
            fails.append(f"floating_object:{obj.get('name')}")
        if obj.get("anchored") is False:
            fails.append(f"floating_object:{obj.get('name')}")

    # Continuity: unexplained object position changes
    if previous and env.get("continuity_state") and previous.get("continuity_state"):
        prev_pos = (previous.get("continuity_state") or {}).get("object_positions") or {}
        cur_pos = (env.get("continuity_state") or {}).get("object_positions") or {}
        for oid, cur in cur_pos.items():
            if oid in prev_pos:
                p = prev_pos[oid].get("position") or {}
                c = cur.get("position") or {}
                if p and c and p != c:
                    # moved without event reason in state is repairable warning if no moved_at
                    if not cur.get("moved_at") and not cur.get("move_reason"):
                        repairs.append(f"object_moved_without_explanation:{oid}")
                        fails.append(f"objects_changing_position_without_explanation:{oid}")

    # Impossible room connection
    if world and env.get("selected_zone"):
        zone_ids = {z.get("id") for z in (world.get("zones") or []) if isinstance(z, dict)}
        if zone_ids and env.get("selected_zone") not in zone_ids:
            fails.append(f"impossible_room_connection:{env.get('selected_zone')}")

    # Scale consistency
    if env.get("scale") and world and world.get("scale") and env.get("scale") != world.get("scale"):
        fails.append("inconsistent_world_scale")

    # Cinematic prescriptions must be absent
    if env.get("cinematic_prescriptions"):
        fails.append("world_instructions_conflict_with_boundaries")

    hard = sorted(set(fails))
    return {
        "ok": not hard,
        "passed": not hard,
        "hard_failures": hard,
        "hard_fails": hard,
        "repairable_continuity_issues": sorted(set(repairs)),
        "accuracy_warnings": sorted(set(warnings)),
        "creative_recommendations": [],
    }


def validate_production_continuity(
    bindings: list[dict[str, Any]],
    env_packages: list[dict[str, Any]],
    state: dict[str, Any],
) -> dict[str, Any]:
    fails: list[str] = []
    warnings: list[str] = []

    world_ids = {b.get("world_id") for b in bindings if b.get("world_id")}
    if len(world_ids) > 1:
        fails.append("lost_continuity_state_multiple_worlds")

    # Spatial layout contradictions: same object id with different positions across env packages without move events
    move_events = [e for e in (state.get("events") or []) if e.get("type") == "object_moved"]
    if env_packages:
        first_objs = {
            (o.get("object_id") or o.get("name")): o.get("position")
            for o in env_packages[0].get("required_persistent_objects") or []
        }
        for env in env_packages[1:]:
            for o in env.get("required_persistent_objects") or []:
                oid = o.get("object_id") or o.get("name")
                if oid in first_objs and first_objs[oid] and o.get("position") and first_objs[oid] != o.get("position"):
                    if not move_events:
                        fails.append(f"objects_changing_position_without_explanation:{oid}")

    # Unexplained environment change (world id flips)
    if len(world_ids) == 0:
        fails.append("lost_continuity_state")

    # Invalid transitions between zones without connection
    # soft-checked in validate_environment_package

    hard = sorted(set(fails))
    return {
        "ok": not hard,
        "passed": not hard,
        "hard_failures": hard,
        "hard_fails": hard,
        "accuracy_warnings": sorted(set(warnings)),
        "binding_count": len(bindings),
        "state_version": state.get("version"),
    }
