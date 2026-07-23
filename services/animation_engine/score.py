"""Animation Excellence score + cinematic immersion quality gate (V2)."""

from __future__ import annotations

from typing import Any

from services.animation_engine.models import (
    EXCELLENCE_DIMENSIONS,
    MAX_STATIC_RUNTIME_PCT,
    MAX_STILL_WITHOUT_MOTION_SEC,
    MIN_EXCELLENCE_V2,
    MIN_IMMERSION_PASS_RATIO,
    TARGET_SCENE_SEC_HIGH,
    TARGET_SCENE_SEC_LOW,
)


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def score_scene(decision: dict[str, Any]) -> dict[str, float]:
    layers = decision.get("layers") or {}
    active = list(layers.get("active_motion_classes") or [])
    camera = layers.get("camera") or {}
    world = layers.get("world") or {}
    character = layers.get("character") or {}
    cinematic = layers.get("cinematic") or {}
    immersion = layers.get("immersion") or {}
    dur = float(decision.get("duration_sec") or 3.0)

    scene_motion = min(100.0, 40.0 + 12.0 * len(active))
    camera_quality = 92.0 if camera.get("camera_move") and camera.get("forbid_static_lock") else 40.0
    if camera.get("narrative_purpose") and camera.get("motivated"):
        camera_quality = min(100.0, camera_quality + 6.0)
    if camera.get("forbid_purposeless_drift"):
        camera_quality = min(100.0, camera_quality + 2.0)

    character_realism = 88.0 if character.get("enabled") else 55.0
    if not character.get("enabled"):
        character_realism = 72.0
    elif character.get("micro_performance") and character.get("forbid_mannequin"):
        character_realism = min(100.0, character_realism + 8.0)

    world_activity = 90.0 if world.get("living_background") else 35.0
    if world.get("depth_layers") and world.get("continues_without_narration"):
        world_activity = min(100.0, world_activity + 6.0)
    if world.get("allow_abstract_geometry") is False:
        world_activity = min(100.0, world_activity + 2.0)

    pacing = 90.0 if TARGET_SCENE_SEC_LOW <= dur <= TARGET_SCENE_SEC_HIGH + 1.5 else (
        75.0 if dur <= TARGET_SCENE_SEC_HIGH + 3 else 55.0
    )
    storytelling = 88.0 if layers.get("muted_comprehension") else 50.0
    if layers.get("visual_moment") and layers.get("audience_understanding"):
        storytelling = min(100.0, storytelling + 8.0)
    if (layers.get("object") or {}).get("enabled") or (layers.get("motion_graphics") or {}).get("enabled"):
        storytelling = min(100.0, storytelling + 4.0)

    transition = 85.0 if (layers.get("transition_in") or {}).get("avoid_crossfade") else 50.0
    if (layers.get("transition_in") or {}).get("motivated"):
        transition = min(100.0, transition + 8.0)

    intentionality = 70.0
    if cinematic.get("emotion") and cinematic.get("visual_moment"):
        intentionality = 92.0
    if camera.get("narrative_purpose"):
        intentionality = min(100.0, intentionality + 4.0)

    environmental_believability = 60.0
    if world.get("depth_layers") and world.get("atmospheric_perspective"):
        environmental_believability = 90.0
    if world.get("lighting_mood"):
        environmental_believability = min(100.0, environmental_believability + 5.0)

    performance_life = 65.0
    if not character.get("enabled"):
        performance_life = 75.0  # N/A credit when narration has no performer
    elif character.get("micro_performance"):
        performance_life = 90.0

    cinematic_feel = _clamp(
        (scene_motion + camera_quality + world_activity + intentionality) / 4.0
    )
    immersion_score = _clamp(
        (world_activity + character_realism + scene_motion + environmental_believability) / 4.0
        + (5 if immersion.get("passed") else 0)
        + (5 if len(active) >= 3 else 0)
    )

    return {
        "scene_motion": round(scene_motion, 1),
        "camera_quality": round(camera_quality, 1),
        "character_realism": round(character_realism, 1),
        "world_activity": round(world_activity, 1),
        "pacing": round(pacing, 1),
        "visual_storytelling": round(storytelling, 1),
        "transition_quality": round(transition, 1),
        "cinematic_feel": round(cinematic_feel, 1),
        "immersion": round(immersion_score, 1),
        "intentionality": round(intentionality, 1),
        "environmental_believability": round(environmental_believability, 1),
        "performance_life": round(performance_life, 1),
    }


def animation_excellence(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    if not decisions:
        empty = {d: 0.0 for d in EXCELLENCE_DIMENSIONS}
        return {
            "animation_excellence_score": 0.0,
            "dimensions": empty,
            "passed": False,
            "reason": "no_scenes",
            "engine_version": "2.0.0",
        }
    dims: dict[str, list[float]] = {d: [] for d in EXCELLENCE_DIMENSIONS}
    for dec in decisions:
        scored = dec.get("excellence") or score_scene(dec)
        for k in EXCELLENCE_DIMENSIONS:
            dims[k].append(float(scored.get(k) or 0))
    averages = {k: round(sum(v) / len(v), 1) for k, v in dims.items()}
    overall = round(sum(averages.values()) / len(averages), 1)
    return {
        "animation_excellence_score": overall,
        "dimensions": averages,
        "passed": overall >= MIN_EXCELLENCE_V2,
        "target": MIN_EXCELLENCE_V2,
        "engine_version": "2.0.0",
    }


def quality_gate(decisions: list[dict[str, Any]], *, total_runtime_sec: float | None = None) -> dict[str, Any]:
    """
    Reject when:
    - >10% runtime static
    - frozen backgrounds
    - no camera motion / purposeless drift
    - lifeless characters when characters planned
    - immersion checklist failures dominate
    - abstract / empty visual flags
    """
    failures: list[str] = []
    warnings: list[str] = []
    n = len(decisions) or 1
    static_sec = 0.0
    runtime = float(total_runtime_sec or 0.0)
    if runtime <= 0:
        runtime = sum(float(d.get("duration_sec") or 0) for d in decisions) or 1.0

    locked_camera = 0
    frozen_bg = 0
    lifeless_chars = 0
    empty_motion = 0
    purposeless = 0
    immersion_fails = 0
    abstract_worlds = 0
    used_cameras: list[str] = []
    re_render_scenes: list[Any] = []

    for d in decisions:
        layers = d.get("layers") or {}
        dur = float(d.get("duration_sec") or 0)
        active = list(layers.get("active_motion_classes") or [])
        if not active or not layers.get("passes_motion_minimum"):
            empty_motion += 1
            static_sec += dur
            re_render_scenes.append(d.get("scene_number"))
        camera = layers.get("camera") or {}
        cam_move = str(camera.get("camera_move") or "")
        if not cam_move or cam_move in {"static", "static_hold", "locked"}:
            locked_camera += 1
            re_render_scenes.append(d.get("scene_number"))
        if cam_move and not camera.get("narrative_purpose") and not camera.get("motivated"):
            purposeless += 1
            warnings.append(f"scene_{d.get('scene_number')}_purposeless_camera")
        if cam_move:
            used_cameras.append(cam_move)
        world = layers.get("world") or {}
        if not world.get("living_background"):
            frozen_bg += 1
            re_render_scenes.append(d.get("scene_number"))
        if world.get("allow_abstract_geometry") is True:
            abstract_worlds += 1
            re_render_scenes.append(d.get("scene_number"))
        ch = layers.get("character") or {}
        if ch.get("enabled") and not (ch.get("actions") or ch.get("micro_performance")):
            lifeless_chars += 1
            re_render_scenes.append(d.get("scene_number"))
        imm = layers.get("immersion") or {}
        if imm and not imm.get("passed"):
            immersion_fails += 1
            re_render_scenes.append(d.get("scene_number"))
        if dur > MAX_STILL_WITHOUT_MOTION_SEC and len(active) < 2:
            warnings.append(f"scene_{d.get('scene_number')}_low_motion_density")

    static_pct = (static_sec / max(runtime, 0.01)) * 100.0
    immersion_pass_ratio = 1.0 - (immersion_fails / max(n, 1))

    if static_pct > MAX_STATIC_RUNTIME_PCT:
        failures.append(f"static_runtime_{static_pct:.1f}pct_exceeds_{MAX_STATIC_RUNTIME_PCT}")
    if locked_camera > max(1, n // 5):
        failures.append("camera_remains_locked")
    if frozen_bg > max(1, n // 4):
        failures.append("backgrounds_frozen")
    if lifeless_chars:
        failures.append("characters_never_move")
    if empty_motion:
        failures.append("scenes_without_motion")
    if purposeless > max(1, n // 3):
        failures.append("purposeless_camera_movement")
    if abstract_worlds:
        failures.append("abstract_geometry_worlds")
    if immersion_pass_ratio < MIN_IMMERSION_PASS_RATIO:
        failures.append(f"immersion_pass_ratio_{immersion_pass_ratio:.2f}_below_{MIN_IMMERSION_PASS_RATIO}")
    if len(set(used_cameras)) < min(3, n) and n >= 3:
        warnings.append("repeated_camera_angles")

    # Unique re-render targets
    unique_rerender = []
    seen = set()
    for s in re_render_scenes:
        if s in seen or s is None:
            continue
        seen.add(s)
        unique_rerender.append(s)

    passed = not failures
    return {
        "passed": passed,
        "decision": "APPROVE" if passed else "REJECT",
        "failures": failures,
        "warnings": warnings,
        "engine_version": "2.0.0",
        "re_render_scenes": unique_rerender,
        "metrics": {
            "static_runtime_pct": round(static_pct, 2),
            "locked_camera_scenes": locked_camera,
            "frozen_background_scenes": frozen_bg,
            "empty_motion_scenes": empty_motion,
            "purposeless_camera_scenes": purposeless,
            "immersion_failures": immersion_fails,
            "immersion_pass_ratio": round(immersion_pass_ratio, 3),
            "abstract_world_scenes": abstract_worlds,
            "unique_camera_moves": len(set(used_cameras)),
            "scene_count": n,
            "runtime_sec": round(runtime, 2),
        },
    }
