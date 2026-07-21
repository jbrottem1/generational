"""Quality gates — reject floating, sliding, clipping, weightless motion."""

from __future__ import annotations

from typing import Any

from services.physics_interaction.models import (
    BODY_CAPABILITIES,
    FOOT_CAPABILITIES,
    HAND_CAPABILITIES,
    REJECT_REASONS,
    SUPPORTED_INTERACTIONS,
)


def validate_interaction_package(package: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(package, dict) or not package:
        return {
            "ok": False,
            "score": 0,
            "failures": ["missing_interaction_package"],
            "rejects": list(REJECT_REASONS),
        }

    failures: list[str] = []
    rejects: list[str] = []

    for field in (
        "interaction_id",
        "actor",
        "target",
        "interaction_type",
        "contact_points",
        "physics_state",
        "constraints",
        "animation_requirements",
        "completion_state",
    ):
        if package.get(field) in (None, "", [], {}):
            failures.append(f"missing_{field}")

    itype = package.get("interaction_type")
    if itype not in SUPPORTED_INTERACTIONS:
        failures.append("unsupported_interaction_type")

    constraints = package.get("constraints") or {}
    if not constraints.get("no_float"):
        failures.append("allows_float")
        rejects.append("floating_actors")
    if not constraints.get("no_clip"):
        failures.append("allows_clip")
        rejects.append("object_clipping")
    if not constraints.get("no_teleport"):
        failures.append("allows_teleport")
        rejects.append("broken_collisions")

    contacts = package.get("contact_points") or []
    if not contacts:
        failures.append("no_contact_points")
        rejects.append("hands_missing_targets")
    elif constraints.get("hand_must_hit_target") and not any(
        "hand" in str(c.get("id") or "").lower()
        or "finger" in str(c.get("id") or "").lower()
        or "index" in str(c.get("id") or "").lower()
        for c in contacts
    ):
        # locomotion interactions may not need hands
        if itype not in {
            "walking",
            "running",
            "stopping",
            "turning",
            "jumping",
            "standing",
            "sitting",
            "looking_through_windows",
        }:
            failures.append("hand_contact_missing")
            rejects.append("hands_missing_targets")

    score = max(0, 100 - 12 * len(failures))
    return {
        "ok": not failures,
        "score": score,
        "failures": failures,
        "rejects_hit": sorted(set(rejects)),
        "reject_catalog": list(REJECT_REASONS),
    }


def validate_physics_profile(profile: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(profile, dict) or not profile:
        return {
            "ok": False,
            "score": 0,
            "failures": ["missing_physics_profile"],
            "rejects": list(REJECT_REASONS),
        }

    failures: list[str] = []
    rejects: list[str] = []

    hand = profile.get("hand_physics") or {}
    if not set(HAND_CAPABILITIES).issubset(set(hand.get("capabilities") or [])):
        failures.append("hand_physics_incomplete")
        rejects.append("hands_missing_targets")

    foot = profile.get("foot_physics") or {}
    if not set(FOOT_CAPABILITIES).issubset(set(foot.get("capabilities") or [])):
        failures.append("foot_physics_incomplete")
        rejects.append("sliding_feet")
    if not (foot.get("planting") or {}).get("no_slide"):
        failures.append("feet_may_slide")
        rejects.append("sliding_feet")

    body = profile.get("body_physics") or {}
    if not set(BODY_CAPABILITIES).issubset(set(body.get("capabilities") or [])):
        failures.append("body_physics_incomplete")
        rejects.append("weightless_movement")
    if "float" not in set(body.get("forbid") or []):
        failures.append("body_allows_float")
        rejects.append("floating_actors")

    collision = profile.get("collision") or {}
    if not collision.get("enabled"):
        failures.append("collision_disabled")
        rejects.append("broken_collisions")

    clothing = profile.get("clothing_physics") or {}
    if not clothing.get("simulate_as_fabric"):
        failures.append("clothing_not_simulated")

    hair = profile.get("hair_physics") or {}
    if not hair.get("secondary_movement"):
        failures.append("hair_no_secondary_motion")

    objects = profile.get("objects") or []
    if not objects:
        failures.append("no_object_physics")

    interactions = profile.get("interactions") or []
    if interactions:
        for ix in interactions:
            rev = validate_interaction_package(ix)
            if not rev.get("ok"):
                failures.append(f"interaction_invalid:{ix.get('interaction_id')}")
                rejects.extend(rev.get("rejects_hit") or [])

    # Balance sanity
    if not (body.get("balance") or {}).get("correction"):
        failures.append("no_balance_correction")
        rejects.append("unrealistic_balance")

    score = max(0, 100 - 8 * len(failures))
    return {
        "ok": not failures,
        "score": score,
        "failures": failures,
        "rejects_hit": sorted(set(rejects)),
        "reject_catalog": list(REJECT_REASONS),
        "success": (
            "Every actor behaves like a physical being inside a physical world. "
            "Interactions appear believable and consistent across every production."
        ),
        "mp4_required": True,
        "note": (
            "Passing this plan gate is necessary but not sufficient. "
            "Inspect the final MP4 for float, slide, clip, and missed hand targets."
        ),
    }
