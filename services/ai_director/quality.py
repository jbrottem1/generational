"""Quality validation for the AI Director — conflict detection and graceful degradation.

Validates DirectorPackages and upstream alignment without raising. Findings
land in `validation` and `upstream_alignment` for downstream agents and
human review.
"""

from __future__ import annotations

from services.ai_director.models import DirectorStatus

# Supported provider families the Director knows about (informational only).
KNOWN_PROVIDER_FAMILIES = (
    "creative", "asset_generation", "voice", "render", "post_production",
)

# Format → required upstream packages for full (non-degraded) direction.
_FORMAT_UPSTREAM_EXPECTATIONS = {
    "short_form": ("script_package",),
    "long_form": ("script_package", "visual_package"),
    "documentary": ("script_package",),
    "cinematic": ("script_package", "visual_package", "audio_package"),
    "cartoon": ("script_package",),
    "podcast": ("script_package", "audio_package"),
}


def _upstream_packages(item: dict) -> list:
    """Which canonical slots are populated on this item."""
    slots = (
        "script_package", "visual_package", "audio_package",
        "creative_package", "behavioral_intelligence", "attention_graph",
        "asset_package", "render_package", "post_production_package",
        "seo_package", "analytics_package",
    )
    return [slot for slot in slots if item.get(slot)]


def detect_conflicts(item: dict, director: dict) -> list:
    """Find conflicting creative choices across upstream packages."""
    conflicts = []
    strategy = director.get("production_strategy", {})
    fmt = strategy.get("format", "")

    # Creative Studio blueprint vs Director format.
    creative = item.get("creative_package") or {}
    blueprint = creative.get("creative_blueprint") or {}
    if blueprint:
        bp_type = blueprint.get("production_type", "")
        type_format_map = {
            "cinematic_video": "cinematic",
            "science_visualization": "educational",
            "documentary_film": "documentary",
            "animated_explainer": "cartoon",
            "podcast_visual": "podcast",
        }
        expected = type_format_map.get(bp_type, "")
        if expected and expected != fmt:
            conflicts.append({
                "type": "format_mismatch",
                "director": fmt,
                "creative_studio": bp_type,
                "message": f"Director chose '{fmt}' but Creative Studio blueprint is '{bp_type}'.",
            })

        bp_aspect = blueprint.get("aspect_ratio", "")
        orient = strategy.get("orientation", "")
        if bp_aspect and orient:
            bp_orient = "vertical" if bp_aspect in ("9:16", "4:5") else "horizontal"
            if bp_orient != orient:
                conflicts.append({
                    "type": "orientation_mismatch",
                    "director": orient,
                    "creative_studio": bp_aspect,
                    "message": f"Director orientation '{orient}' conflicts with blueprint aspect '{bp_aspect}'.",
                })

    # Visual package vs Director camera plan.
    visual = item.get("visual_package") or {}
    if visual.get("scenes") and director.get("camera_plan"):
        vis_style = str(visual.get("visual_style", "")).lower()
        cam_grammar = director["camera_plan"].get("camera_grammar", "").lower()
        if vis_style and "documentary" in vis_style and "documentary" not in cam_grammar:
            conflicts.append({
                "type": "camera_style_mismatch",
                "message": "Visual package suggests documentary style but camera plan differs.",
            })

    # Audio vs narration plan.
    audio = item.get("audio_package") or {}
    narration = director.get("narration_plan") or {}
    if audio.get("voice_style") and narration.get("voice_selection"):
        audio_voice = str(audio.get("voice_style", {}).get("name", "")).lower()
        dir_voice = str(narration.get("voice_selection", "")).lower()
        if audio_voice and dir_voice and audio_voice != dir_voice and audio_voice != "narrator":
            conflicts.append({
                "type": "voice_mismatch",
                "director": dir_voice,
                "audio": audio_voice,
                "message": f"Narration plan voice '{dir_voice}' differs from audio package '{audio_voice}'.",
            })

    # Impossible requests.
    runtime = director.get("expected_runtime") or {}
    platforms = director.get("target_platforms") or []
    target = runtime.get("target_sec", 0)
    for platform in platforms:
        max_dur = platform.get("max_duration_sec", 0)
        if max_dur and target > max_dur * 1.1:
            conflicts.append({
                "type": "impossible_duration",
                "platform": platform.get("platform"),
                "target_sec": target,
                "max_sec": max_dur,
                "message": f"Target runtime {target}s exceeds {platform.get('platform')} max {max_dur}s.",
            })

    return conflicts


def resolve_conflicts(conflicts: list, director: dict) -> tuple[list, list]:
    """Resolve conflicts via graceful degradation. Returns (resolved, remaining)."""
    resolved = []
    remaining = []
    strategy = director.get("production_strategy", {})
    runtime = director.get("expected_runtime") or {}

    for conflict in conflicts:
        ctype = conflict.get("type", "")
        if ctype == "impossible_duration":
            max_sec = conflict.get("max_sec", runtime.get("target_sec", 60))
            runtime["target_sec"] = min(runtime.get("target_sec", max_sec), max_sec)
            runtime["max_sec"] = max_sec
            resolved.append({
                "conflict": conflict,
                "action": f"Capped runtime to {max_sec}s for platform constraint.",
            })
        elif ctype == "format_mismatch":
            # Director wins — Creative Studio should follow director_package.
            resolved.append({
                "conflict": conflict,
                "action": "Director format takes precedence; Creative Studio should reconcile.",
            })
        elif ctype == "orientation_mismatch":
            orient = strategy.get("orientation", "vertical")
            aspect = "9:16" if orient == "vertical" else "16:9"
            resolved.append({
                "conflict": conflict,
                "action": f"Director orientation '{orient}' ({aspect}) takes precedence.",
            })
        else:
            remaining.append(conflict)

    director["expected_runtime"] = runtime
    return resolved, remaining


def apply_degradations(item: dict, director: dict, policies: dict) -> list:
    """Gracefully degrade when upstream packages are missing."""
    degradations = []
    fmt = director.get("production_strategy", {}).get("format", "short_form")
    expected = _FORMAT_UPSTREAM_EXPECTATIONS.get(fmt, ("script_package",))
    present = set(_upstream_packages(item))

    for slot in expected:
        if slot not in present:
            degradations.append({
                "missing": slot,
                "action": f"Proceeded with policy fallbacks; {slot} absent.",
            })

    if not item.get("script") and not item.get("script_package"):
        degradations.append({
            "missing": "script",
            "action": "No script available — direction based on topic/keywords only.",
        })
        director.setdefault("production_strategy", {})["visual_complexity"] = "minimal"

    if degradations:
        fallbacks = policies.get("fallbacks", {})
        if not director.get("visual_style", {}).get("style_id"):
            director.setdefault("visual_style", {})["style_id"] = fallbacks.get("visual_style", "minimal")

    return degradations


def validate_director_package(item: dict, director: dict, policies: dict) -> dict:
    """Full validation pass — returns validation dict (never raises)."""
    warnings = []
    blockers = []
    packages_consumed = _upstream_packages(item)

    conflicts = detect_conflicts(item, director)
    resolved, remaining = resolve_conflicts(conflicts, director)
    degradations = apply_degradations(item, director, policies)

    for conflict in remaining:
        warnings.append(conflict.get("message", str(conflict)))

    for deg in degradations:
        warnings.append(deg["action"])

    # Missing critical direction fields.
    for field in ("production_strategy", "target_platforms", "pacing"):
        if not director.get(field):
            blockers.append(f"Missing required direction field: {field}")

    confidence = 100
    confidence -= len(remaining) * 15
    confidence -= len(degradations) * 5
    confidence = max(0, min(100, confidence))

    degraded = bool(degradations) or bool(remaining)
    if blockers:
        status = DirectorStatus.INCOMPLETE
    elif degraded:
        status = DirectorStatus.DEGRADED
    elif confidence >= 80:
        status = DirectorStatus.READY
    else:
        status = DirectorStatus.NEEDS_REVIEW

    director["upstream_alignment"] = {
        "packages_consumed": packages_consumed,
        "conflicts_detected": conflicts,
        "conflicts_resolved": resolved,
        "degradation_applied": degradations,
    }

    return {
        "status": status,
        "confidence": confidence,
        "warnings": warnings,
        "blockers": blockers,
        "conflicts": len(conflicts),
        "conflicts_resolved": len(resolved),
        "degraded": degraded,
    }
