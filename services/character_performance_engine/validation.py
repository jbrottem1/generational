"""Reject shots that are photographs with camera moves — not actor performances."""

from __future__ import annotations

from typing import Any

from services.character_performance_engine.models import (
    MAX_STATIONARY_SEC,
    MIN_BODY_ACTIONS,
    MIN_ENVIRONMENT_LIFE,
    MIN_INTERACTIONS,
    MIN_LOCOMOTION_WAYPOINTS,
    REJECT_SIGNATURES,
)


def validate_character_performance(package: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(package, dict) or not package:
        return {
            "ok": False,
            "score": 0,
            "failures": ["missing_character_performance_package"],
            "rejects": list(REJECT_SIGNATURES),
        }

    failures: list[str] = []
    rejects_hit: list[str] = []

    blocking = package.get("blocking") or {}
    loco = package.get("locomotion") or {}
    body = package.get("body_performance") or {}
    interactions = package.get("interactions") or {}
    env = package.get("environment_life") or {}
    cam = package.get("camera_follow") or {}
    sim = package.get("simulation") or {}

    waypoints = list(loco.get("waypoints") or [])
    if len(waypoints) < MIN_LOCOMOTION_WAYPOINTS:
        failures.append("insufficient_locomotion_waypoints")
        rejects_hit.append("minimal_body_movement")

    travel = float(loco.get("path_distance_norm") or 0)
    if travel < 0.08:
        failures.append("path_travel_too_small")
        rejects_hit.append("camera_only_movement")

    if not loco.get("never_float") or not loco.get("foot_plants"):
        failures.append("missing_foot_contact_contract")
        rejects_hit.append("floating_head")

    actions = list(body.get("body_actions_present") or [])
    if len(actions) < MIN_BODY_ACTIONS:
        failures.append("insufficient_body_actions")
        rejects_hit.append("lifeless_performance")

    if not body.get("continuous"):
        failures.append("body_not_continuous")
        rejects_hit.append("talking_photograph")

    # Stationary holds
    for hold in body.get("holds") or []:
        span = float(hold.get("t_end") or 0) - float(hold.get("t_start") or 0)
        if span > MAX_STATIONARY_SEC and not hold.get("allowed"):
            failures.append("stationary_exceeds_3s")
            rejects_hit.append("lifeless_performance")
        if not hold.get("micro_motion_required"):
            failures.append("hold_without_micro_motion")

    if int(interactions.get("count") or len(interactions.get("events") or [])) < MIN_INTERACTIONS:
        failures.append("no_world_interaction")
        rejects_hit.append("talking_photograph")

    channels = list(env.get("channels") or [])
    if len(channels) < MIN_ENVIRONMENT_LIFE or not env.get("living"):
        failures.append("environment_not_alive")
        rejects_hit.append("static_background")

    if cam.get("camera_replaces_action") is True:
        failures.append("camera_replaces_action")
        rejects_hit.append("camera_only_movement")

    if not cam.get("follows_actor_path"):
        failures.append("camera_does_not_follow_actor")
        rejects_hit.append("ken_burns")

    if not sim.get("actor_driven") or len(sim.get("keyframes") or []) < 3:
        failures.append("simulation_missing_actor_path")
        rejects_hit.append("moving_still_image")

    # Explicit anti-Ken-Burns flags on package
    if package.get("ken_burns") is True or package.get("motion_class") == "ken_burns":
        failures.append("ken_burns_flag")
        rejects_hit.append("ken_burns")

    questions = set(blocking.get("questions_answered") or [])
    required_q = {
        "where_is_everyone",
        "where_walking",
        "where_looking",
        "what_touching",
        "what_reacting_to",
        "where_end_shot",
    }
    if not required_q.issubset(questions):
        failures.append("blocking_incomplete")

    score = max(0, 100 - 12 * len(failures))
    ok = not failures
    return {
        "ok": ok,
        "score": score,
        "failures": failures,
        "rejects_hit": sorted(set(rejects_hit)),
        "reject_catalog": list(REJECT_SIGNATURES),
        "quality_test": (
            "Reject any shot that could be recreated by moving a still photograph."
        ),
        "success_standard": (
            "Viewer believes: I'm watching an animated television show — "
            "not animated pictures."
        ),
        "mp4_required": True,
        "note": (
            "Passing this plan gate is necessary but not sufficient. "
            "Inspect the final MP4 for genuine character animation."
        ),
    }


def rendered_performance_inspection_template() -> dict[str, Any]:
    """Checklist for human / review agents inspecting the MP4."""
    return {
        "inspect_mp4": True,
        "checks": [
            "character_walks_or_gestures_continuously",
            "feet_contact_ground",
            "no_ken_burns_only_feel",
            "environment_elements_move",
            "camera_follows_rather_than_replaces_action",
            "interactions_with_props_or_set",
            "no_floating_or_sliding",
            "feels_like_animated_show_not_photos",
        ],
        "auto_pass_forbidden": True,
    }
