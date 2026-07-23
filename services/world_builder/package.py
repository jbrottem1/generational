"""Build production World Packages + per-scene Environment Packages.

Enriches scene packages — does not replace Scene Builder or Cinematic Director.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.world_builder.environment import build_environment_package
from services.world_builder.library import (
    get_library_world,
    record_world_usage,
    seed_library_from_catalog,
    select_best_world,
)
from services.world_builder.models import PACKAGE_VERSION, empty_world_request
from services.world_builder.state import apply_state_event, continuity_snapshot, initialize_state_from_world, load_state
from services.world_builder.validate import validate_environment_package, validate_production_continuity, validate_world_package

ROOT = Path(__file__).resolve().parents[2]
OUT_ROOT = ROOT / "data" / "world_builder" / "packages"


def fulfill_world_request(request: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
    """Scene Builder → World Builder contract entrypoint."""
    req = empty_world_request(**{**(request or {}), **kwargs})
    return build_world_package(
        {
            "topic": req.get("topic"),
            "title": req.get("topic"),
            "niche": req.get("location_type") or "",
            "script": " ".join(str(a) for a in (req.get("required_actions") or [])),
            "platform": req.get("platform"),
            "audience": req.get("audience"),
        },
        topic=str(req.get("topic") or ""),
        niche=str(req.get("location_type") or ""),
        world_id=str(req.get("existing_world_id") or ""),
        world_type=str(req.get("location_type") or ""),
        request=req,
        scene_count=int(kwargs.get("scene_count") or 0) or None,
        production_id=str(kwargs.get("production_id") or req.get("topic") or "default"),
    )


def build_world_package(
    candidate: dict[str, Any] | None = None,
    *,
    topic: str = "",
    niche: str = "",
    script: str = "",
    world_type: str = "",
    world_id: str = "",
    scene_count: int | None = 0,
    request: dict[str, Any] | None = None,
    production_id: str = "default",
    platform: str = "",
    audience: str = "",
) -> dict[str, Any]:
    """Production-level package: world + environment packages per scene + state."""
    seed_library_from_catalog()
    candidate = dict(candidate or {})
    request = dict(request or {})
    topic = topic or str(candidate.get("topic") or candidate.get("title") or request.get("topic") or "")
    niche = niche or str(candidate.get("niche") or "")
    script = script or str(candidate.get("script") or "")
    platform = platform or str(candidate.get("platform") or request.get("platform") or "")
    audience = audience or str(candidate.get("audience") or request.get("audience") or "general_public")
    production_id = production_id or topic.replace(" ", "_")[:48] or "default"

    existing = world_id or str(request.get("existing_world_id") or candidate.get("world_id") or "")
    selection = select_best_world(
        topic=topic,
        niche=niche,
        location_type=world_type or str(request.get("location_type") or ""),
        time_period=str(request.get("time_period") or ""),
        audience=audience,
        channel=str(request.get("channel") or candidate.get("channel") or ""),
        existing_world_id=existing,
    )
    best_id = str((selection.get("best") or {}).get("world_id") or "")
    world = get_library_world(best_id) or {}
    if not world:
        from services.world_builder.catalog import get_world

        world = get_world(world_id=best_id) or get_world(world_type=world_type) or {}

    # State
    state = load_state(str(world.get("world_id") or best_id), production_id)
    if not state.get("object_positions"):
        state = initialize_state_from_world(world, production_id=production_id)

    scenes = _source_scenes(candidate, scene_count=scene_count or 0, script=script)
    zones = [z for z in (world.get("zones") or []) if isinstance(z, dict)]
    env_packages: list[dict[str, Any]] = []
    bindings: list[dict[str, Any]] = []

    for i, scene in enumerate(scenes):
        zone = zones[i % len(zones)] if zones else {"id": "main", "name": "Primary"}
        # Inherit state; mark zone visit
        state = apply_state_event(
            state,
            "character_entered",
            {"character": "talent", "zone": zone.get("id")},
        )
        env = build_environment_package(
            world,
            scene=scene,
            zone_id=str(zone.get("id") or ""),
            state=state,
            request={**request, "topic": topic, "scene_id": scene.get("scene_id")},
        )
        env["world_validation"] = validate_environment_package(env, world=world, previous=env_packages[-1] if env_packages else None)
        env_packages.append(env)

        # Continuity binding — spatial identity only (no cinematic lighting/camera prescriptions)
        bindings.append(
            {
                "scene_id": scene.get("scene_id") or f"s{i+1}",
                "world_id": world.get("world_id"),
                "zone_id": zone.get("id"),
                "environment_name": world.get("name"),
                "spatial_fingerprint": f"{world.get('world_id')}:{zone.get('id')}",
                "persistent_object_ids": [o.get("object_id") or o.get("name") for o in env.get("required_persistent_objects") or []],
                "background_identity": f"{world.get('world_id')}|{zone.get('id')}|scale={world.get('scale')}",
                "narration_excerpt": str(scene.get("narration") or "")[:120],
            }
        )

    continuity = validate_production_continuity(bindings, env_packages, state)

    package = {
        "package_version": PACKAGE_VERSION,
        "package_type": "world_production",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "topic": topic,
        "niche": niche,
        "platform": platform,
        "audience": audience,
        "production_id": production_id,
        "world_id": world.get("world_id"),
        "world_version": world.get("schema_version") or world.get("version") or PACKAGE_VERSION,
        "world_type": world.get("world_type"),
        "name": world.get("name"),
        "selection": selection,
        "world": world,
        "continuity": {
            "single_world": True,
            "world_id": world.get("world_id"),
            "state": continuity_snapshot(state),
            "scene_bindings": bindings,
            "note": "Same world across scenes; zone may change; object positions inherited from state",
        },
        "environment_packages": env_packages,
        "ambience_handoff": {
            "labels": world.get("sound_ambience") or [],
            "target": "sound_design",
        },
        "asset_requirements_summary": _merge_assets(env_packages),
        "continuity_validation": continuity,
        "renderer_feed": {
            "note": "Separate from cinematic_direction_package — spatial/environment only",
            "environment_packages": env_packages,
            "world_id": world.get("world_id"),
        },
        "contracts": {
            "environment_package": "services.world_builder",
            "cinematic_direction_package": "services.cinematic_director",
            "separation": "renderer receives both; they must not overwrite each other",
        },
    }
    package["validation"] = validate_world_package(package)
    package["validation"]["continuity"] = continuity

    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    slug = "".join(c if c.isalnum() or c in "-_" else "_" for c in (topic or world.get("name") or "world"))[:48]
    path = OUT_ROOT / f"{slug}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    path.write_text(json.dumps(package, indent=2) + "\n", encoding="utf-8")
    package["path"] = str(path)

    record_world_usage(str(world.get("world_id")), topic=topic, production_id=production_id)
    return package


def apply_world_to_candidate(candidate: dict[str, Any], package: dict[str, Any]) -> dict[str, Any]:
    """Enrich Scene Builder fields without replacing cinematic direction."""
    out = dict(candidate)
    vp = dict(out.get("visual_package") or {})
    scenes = list(vp.get("scenes") or out.get("scenes") or [])
    env_by_scene = {e.get("scene_id"): e for e in package.get("environment_packages") or []}

    if not scenes:
        scenes = [{"scene_id": e.get("scene_id"), "narration": ""} for e in package.get("environment_packages") or []]

    enriched = []
    for i, scene in enumerate(scenes):
        sid = scene.get("scene_id") or f"s{i+1}"
        env = env_by_scene.get(sid)
        if not env and package.get("environment_packages"):
            env = package["environment_packages"][min(i, len(package["environment_packages"]) - 1)]
        row = dict(scene)
        if env:
            # Scene Builder consumeable location fields — NOT cinematic lighting/camera
            zone = env.get("zone") or {}
            activity = list(env.get("background_activity") or zone.get("ambient_activity") or [])[:3]
            activity_bits = ", ".join(str(a) for a in activity) if activity else "subtle environmental motion"
            row["environment"] = zone.get("description") or env.get("environment_name")
            # V2 quality: encode layered depth + ambient motion into background language
            row["background"] = (
                f"{env.get('environment_name')} / zone={env.get('selected_zone')} / "
                f"world_id={env.get('world_id')} (persistent) / "
                f"depth=layered FG-subject BG-architecture / activity={activity_bits}"
            )
            row["world_id"] = env.get("world_id")
            row["zone_id"] = env.get("selected_zone")
            row["environment_package"] = env
            row["world_direction"] = {
                "world_id": env.get("world_id"),
                "zone_id": env.get("selected_zone"),
                "continuity": True,
                "ambient_activity": activity,
                "note": "Cinematic Director chooses camera/lighting; World supplies place + ambient layers",
            }
            # Do not overwrite row["lighting"] / camera_* if cinematic already set
            if not row.get("color_palette") and (env.get("aesthetic_context") or {}).get("base_palette"):
                row["color_palette"] = env["aesthetic_context"]["base_palette"]
        enriched.append(row)

    vp["scenes"] = enriched
    vp["world_summary"] = {
        "world_id": package.get("world_id"),
        "world_type": package.get("world_type"),
        "validation": package.get("validation"),
    }
    out["visual_package"] = vp
    out["world_package"] = package
    out["environment_package"] = package  # production-level alias
    out["environment_packages"] = package.get("environment_packages")
    out["world_id"] = package.get("world_id")
    out["scenes"] = enriched
    # Keep cinematic package untouched if present
    return out


def place_candidate_in_world(candidate: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    pkg = build_world_package(candidate, **kwargs)
    return apply_world_to_candidate(candidate, pkg)


def _source_scenes(candidate: dict[str, Any], *, scene_count: int, script: str) -> list[dict[str, Any]]:
    vp = candidate.get("visual_package") or {}
    scenes = list(vp.get("scenes") or candidate.get("scenes") or [])
    if scenes:
        return scenes
    n = scene_count or 4
    parts = [p.strip() for p in (script or candidate.get("title") or "Scene").replace(".", ".|").split("|") if p.strip()]
    if len(parts) < n:
        parts = (parts + [f"Beat {i+1}" for i in range(n)])[:n]
    else:
        parts = parts[:n]
    return [{"scene_id": f"s{i+1}", "narration": parts[i]} for i in range(len(parts))]


def _merge_assets(env_packages: list[dict[str, Any]]) -> dict[str, Any]:
    missing = []
    resolved = []
    for e in env_packages:
        ar = e.get("asset_requirements") or {}
        missing.extend(ar.get("missing") or [])
        resolved.extend(ar.get("resolved") or [])
    return {"resolved_count": len(resolved), "missing_count": len(missing), "missing": missing[:20], "resolved": resolved[:20]}
