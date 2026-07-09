"""Animation Quality Engine — detect planning conflicts before render.

Findings are warnings/blockers in a validation dict — QC never raises and
never crashes the pipeline.
"""

from __future__ import annotations

from services.animation.models import TransitionType, readiness_status

# Core planning fields that must exist before QC / readiness are attached.
_REQUIRED_PLAN_FIELDS = (
    "timeline",
    "scene_timing",
    "camera_plan",
    "character_motion",
    "facial_animation",
    "lip_sync_plan",
    "body_animation",
    "lighting_cues",
    "transitions",
    "visual_effects",
    "particle_effects",
    "motion_graphics",
    "audio_synchronization",
    "subtitle_timing",
    "export_metadata",
    "provider_instructions",
    "choreography",
)


def validate_package(package: dict) -> dict:
    """Validate one animation_package draft."""
    warnings: "list[str]" = []
    blockers: "list[str]" = []
    checks: dict = {}

    # Contract completeness (planning surface — QC fields attach after this).
    missing_fields = [field for field in _REQUIRED_PLAN_FIELDS if field not in package]
    checks["contract"] = {"missing_fields": missing_fields}
    if missing_fields:
        warnings.append(f"missing package fields: {missing_fields}")

    timeline = package.get("timeline") or {}
    scene_timing = package.get("scene_timing") or []
    camera = package.get("camera_plan") or {}
    shots = camera.get("shots") or []
    motions = package.get("character_motion") or []
    lip = package.get("lip_sync_plan") or []
    transitions = package.get("transitions") or []
    assets = (package.get("export_metadata") or {})

    # Empty production.
    if not scene_timing and not shots:
        blockers.append("no scene timing or camera shots — nothing to animate")

    # Timeline conflicts — overlapping scene ranges on the scene track.
    overlaps = []
    ordered = sorted(scene_timing, key=lambda t: float(t.get("start_sec", 0)))
    for prev, curr in zip(ordered, ordered[1:]):
        if float(curr.get("start_sec", 0)) < float(prev.get("end_sec", 0)) - 1e-6:
            overlaps.append(f"{prev.get('scene_id')} overlaps {curr.get('scene_id')}")
    checks["timeline_conflicts"] = {"overlaps": len(overlaps)}
    warnings.extend(f"timeline conflict: {issue}" for issue in overlaps)

    # Missing assets — creative/asset refs when present should be usable.
    item_assets = package.get("_asset_refs") or []
    creative_reqs = package.get("_asset_requirements") or []
    if creative_reqs and not item_assets:
        warnings.append("creative asset requirements present but asset_package is empty")
    checks["missing_assets"] = {
        "requirements": len(creative_reqs),
        "generated": len(item_assets),
    }

    # Camera collisions — two shots with identical start and overlapping paths.
    collisions = []
    for a, b in zip(shots, shots[1:]):
        if a.get("scene_id") == b.get("scene_id") and abs(
            float(a.get("start_sec", 0)) - float(b.get("start_sec", 0))
        ) < 1e-6:
            collisions.append(f"{a.get('shot_id')} and {b.get('shot_id')} share start time")
        # Extreme opposing orbits in the same scene at overlapping times.
        if (
            a.get("movement") == "orbit"
            and b.get("movement") == "orbit"
            and a.get("scene_id") == b.get("scene_id")
            and float(a.get("end_sec", 0)) > float(b.get("start_sec", 0))
        ):
            collisions.append(f"orbit collision risk: {a.get('shot_id')} / {b.get('shot_id')}")
    checks["camera_collisions"] = {"count": len(collisions)}
    warnings.extend(f"camera: {issue}" for issue in collisions)

    # Animation conflicts — same character with contradictory locomotion.
    anim_conflicts = []
    by_char_scene: "dict[tuple, list]" = {}
    for motion in motions:
        key = (motion.get("character_id"), motion.get("scene_id"))
        by_char_scene.setdefault(key, []).append(motion)
    for key, group in by_char_scene.items():
        actions = {
            a.get("action")
            for m in group
            for a in m.get("actions", [])
            if a.get("action") in ("walking", "running", "idle")
        }
        if "walking" in actions and "running" in actions:
            anim_conflicts.append(f"{key[0]} in {key[1]} both walking and running")
    checks["animation_conflicts"] = {"count": len(anim_conflicts)}
    warnings.extend(f"animation conflict: {issue}" for issue in anim_conflicts)

    # Continuity — abrupt camera style jumps (establishing → extreme close with no medium).
    continuity = []
    for prev, curr in zip(shots, shots[1:]):
        if prev.get("shot_type") == "establishing" and curr.get("shot_type") == "extreme_close_up":
            continuity.append(
                f"jump cut framing {prev.get('shot_id')}→{curr.get('shot_id')} (establishing to ECU)"
            )
    checks["continuity"] = {"issues": len(continuity)}
    warnings.extend(f"continuity: {issue}" for issue in continuity)

    # Lip sync mismatches — words outside scene window.
    lip_issues = []
    timing_by_scene = {t.get("scene_id"): t for t in scene_timing}
    for plan in lip:
        timing = timing_by_scene.get(plan.get("scene_id"), {})
        scene_start = float(timing.get("start_sec", 0))
        scene_end = float(timing.get("end_sec", 0)) or scene_start + 999
        for word in plan.get("words") or []:
            if float(word.get("start_sec", 0)) < scene_start - 0.05:
                lip_issues.append(f"{plan.get('lip_sync_id')} word starts before scene")
                break
            if float(word.get("end_sec", 0)) > scene_end + 0.25:
                lip_issues.append(f"{plan.get('lip_sync_id')} word ends after scene")
                break
        if not plan.get("phonemes") and plan.get("words"):
            lip_issues.append(f"{plan.get('lip_sync_id')} has words but no phonemes")
    checks["lip_sync"] = {"issues": len(lip_issues)}
    warnings.extend(f"lip sync: {issue}" for issue in lip_issues)

    # Invalid transitions.
    invalid_tr = [
        t.get("transition_id", "?")
        for t in transitions
        if t.get("transition_type") not in TransitionType.ALL
    ]
    checks["transitions"] = {"invalid": len(invalid_tr)}
    warnings.extend(f"invalid transition: {tid}" for tid in invalid_tr)

    # Motion errors — zero-duration shots, missing keyframes.
    motion_errors = []
    for shot in shots:
        if float(shot.get("duration_sec", 0) or 0) <= 0:
            motion_errors.append(f"{shot.get('shot_id')} has non-positive duration")
        if not shot.get("keyframes"):
            motion_errors.append(f"{shot.get('shot_id')} missing keyframes")
    checks["motion_errors"] = {"count": len(motion_errors)}
    warnings.extend(f"motion: {issue}" for issue in motion_errors)

    # Duration sanity vs export metadata.
    total = float(timeline.get("total_duration_sec", 0) or 0)
    target = float(assets.get("target_duration_sec", 0) or 0)
    if target and total > 0 and abs(total - target) / target > 0.5:
        warnings.append(f"timeline {total}s diverges >50% from target {target}s")
    checks["duration"] = {"total_sec": total, "target_sec": target}

    status = "FAILED" if blockers else ("WARNING" if warnings else "SUCCESS")
    return {"status": status, "warnings": warnings, "blockers": blockers, "checks": checks}


def production_readiness(package: dict, validation: dict) -> dict:
    """0-100 readiness score the Render / Post engines can gate on."""
    score = 100
    score -= 12 * len(validation.get("blockers", []))
    score -= 3 * min(len(validation.get("warnings", [])), 12)
    timeline = package.get("timeline") or {}
    if not timeline.get("tracks"):
        score -= 20
    if not (package.get("camera_plan") or {}).get("shots"):
        score -= 15
    score = max(0, min(100, int(score)))
    return {
        "score": score,
        "status": readiness_status(score, validation.get("blockers", [])),
        "blockers": list(validation.get("blockers", [])),
    }
