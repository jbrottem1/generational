"""AnimationPackage assembly — the engine's single deliverable.

`build_animation_package()` turns one ContentPackage-style item into one
complete cinematic production plan (ANIMATION_PACKAGE_FIELDS). Consumes
Creative Studio, Asset Generation, Visual Intelligence, Voice, Script,
Psychology, and Optimization Lab outputs when present — never mutates
those slots.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from providers.animation import build_provider_instructions, provider_plan
from services.animation.camera import plan_camera
from services.animation.character import (
    plan_body_animation,
    plan_character_motion,
    plan_choreography,
    plan_facial_animation,
)
from services.animation.config import AnimationConfig, get_animation_config
from services.animation.effects import (
    plan_audio_sync,
    plan_lighting_cues,
    plan_motion_graphics,
    plan_subtitle_timing,
    plan_transitions,
    plan_visual_effects,
)
from services.animation.lip_sync import plan_lip_sync
from services.animation.models import (
    ANIMATION_ENGINE_VERSION,
    ANIMATION_PACKAGE_VERSION,
    ReadinessStatus,
)
from services.animation.quality import production_readiness, validate_package
from services.animation.timeline import build_scene_timing, build_timeline


def collect_animation_items(context: dict) -> "tuple[list, str]":
    """Items this run should plan, preferring canonical ContentPackage dicts."""
    packages = context.get("unified_packages") or []
    if packages:
        return list(packages), "unified_packages"
    for key in ("ideas", "selected_ideas"):
        items = context.get(key) or []
        if items:
            return list(items), key
    return [], ""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _scenes_from_item(item: dict) -> "list[dict]":
    creative = item.get("creative_package") or {}
    storyboard = creative.get("storyboard") or []
    if storyboard:
        return list(storyboard)

    visual = item.get("visual_package") or {}
    scenes = visual.get("scenes") or visual.get("scene_plans") or []
    if scenes:
        return [
            {
                "scene_id": str(scene.get("scene_id") or scene.get("scene_number") or f"scene_{idx}"),
                "purpose": str(scene.get("purpose") or scene.get("role") or ""),
                "emotion": str(scene.get("emotion") or ""),
                "narration": str(scene.get("narration") or scene.get("voiceover") or ""),
                "visual_description": str(
                    scene.get("visual_description") or scene.get("description") or ""
                ),
                "camera_angle": str(scene.get("camera_angle") or scene.get("shot_type") or ""),
                "camera_movement": str(
                    scene.get("camera_movement") or scene.get("camera_motion") or ""
                ),
                "lighting": str(scene.get("lighting") or ""),
                "color_palette": str(scene.get("color_palette") or ""),
                "animation_style": str(scene.get("animation_style") or ""),
                "motion_instructions": str(
                    scene.get("motion_instructions") or scene.get("motion_recommendation") or ""
                ),
                "transitions": scene.get("transitions") or {},
                "background": str(scene.get("background") or scene.get("environment") or ""),
                "props": list(scene.get("props") or []),
                "characters": list(scene.get("characters") or []),
                "overlay_graphics": list(scene.get("overlay_graphics") or []),
                "estimated_duration_sec": float(
                    scene.get("estimated_duration_sec")
                    or scene.get("length_sec")
                    or scene.get("duration_sec")
                    or 3.0
                ),
                "asset_requirements": list(scene.get("asset_requirements") or []),
                "production_notes": str(scene.get("production_notes") or ""),
            }
            for idx, scene in enumerate(scenes, start=1)
        ]

    breakdown = item.get("scene_breakdown") or []
    if breakdown and all(isinstance(entry, dict) for entry in breakdown):
        return [
            {
                "scene_id": str(entry.get("scene_id") or f"scene_{idx}"),
                "purpose": str(entry.get("purpose") or entry.get("beat") or f"beat_{idx}"),
                "emotion": str(entry.get("emotion") or ""),
                "narration": str(entry.get("narration") or entry.get("line") or ""),
                "visual_description": str(entry.get("visual") or entry.get("description") or ""),
                "camera_angle": str(entry.get("camera") or "medium"),
                "camera_movement": str(entry.get("movement") or "push"),
                "lighting": str(entry.get("lighting") or "soft key"),
                "color_palette": "",
                "animation_style": "",
                "motion_instructions": str(entry.get("motion") or ""),
                "transitions": {"in": "cut", "out": entry.get("transition", "cut")},
                "background": str(entry.get("background") or ""),
                "props": [],
                "characters": list(entry.get("characters") or []),
                "overlay_graphics": [],
                "estimated_duration_sec": float(entry.get("duration_sec") or 3.0),
                "asset_requirements": [],
                "production_notes": "",
            }
            for idx, entry in enumerate(breakdown, start=1)
        ]

    # Script-only fallback: split into narrative beats.
    script = str(
        (item.get("script_package") or {}).get("script")
        or item.get("script")
        or item.get("hook")
        or ""
    ).strip()
    if not script:
        return []
    sentences = [part.strip() for part in script.replace("!", ".").replace("?", ".").split(".") if part.strip()]
    if not sentences:
        sentences = [script]
    return [
        {
            "scene_id": f"scene_{idx}",
            "purpose": "hook" if idx == 1 else ("payoff" if idx == len(sentences) else "develop"),
            "emotion": "curiosity" if idx == 1 else "neutral",
            "narration": sentence,
            "visual_description": sentence,
            "camera_angle": "wide" if idx == 1 else ("close-up" if idx == len(sentences) else "medium"),
            "camera_movement": "push",
            "lighting": "cinematic soft key",
            "color_palette": "",
            "animation_style": "",
            "motion_instructions": "subtle character performance",
            "transitions": {"in": "cut", "out": "cut"},
            "background": "",
            "props": [],
            "characters": [],
            "overlay_graphics": [],
            "estimated_duration_sec": 3.0,
            "asset_requirements": [],
            "production_notes": "derived from script",
        }
        for idx, sentence in enumerate(sentences[:40], start=1)
    ]


def _shot_list_from_item(item: dict, scenes: "list[dict]") -> "list[dict]":
    creative = item.get("creative_package") or {}
    shot_list = creative.get("shot_list") or []
    if shot_list:
        return list(shot_list)
    visual = item.get("visual_package") or {}
    shots = visual.get("shot_list") or []
    if shots:
        return list(shots)
    return []


def _resolve_config(item: dict, context: "dict | None", config: "AnimationConfig | None") -> AnimationConfig:
    base = config or get_animation_config()
    overrides = {}
    # Optimization Lab / psychology / platform hints (additive consumption).
    opt = item.get("optimization_package") or (context or {}).get("optimization_summary") or {}
    if isinstance(opt, dict):
        if opt.get("target_platform"):
            overrides["target_platform"] = opt["target_platform"]
        if opt.get("aspect_ratio"):
            overrides["target_aspect_ratio"] = opt["aspect_ratio"]
        if opt.get("motion_intensity"):
            overrides["motion_intensity"] = opt["motion_intensity"]

    platforms = item.get("target_platforms") or item.get("platforms") or []
    if platforms and not overrides.get("target_platform"):
        overrides["target_platform"] = platforms[0]
    if item.get("target_platform"):
        overrides["target_platform"] = item["target_platform"]

    creative = item.get("creative_package") or {}
    blueprint = creative.get("creative_blueprint") or {}
    if blueprint.get("aspect_ratio"):
        overrides["target_aspect_ratio"] = blueprint["aspect_ratio"]
    if blueprint.get("target_duration_sec"):
        overrides["target_duration_sec"] = float(blueprint["target_duration_sec"])
    if blueprint.get("visual_style"):
        style = str(blueprint["visual_style"])
        if "anime" in style:
            overrides["animation_style"] = "anime"
            overrides["camera_style"] = "anime"
        elif "cartoon" in style or "2d" in style:
            overrides["animation_style"] = "2d"

    # Soft psychology hint — only when intensity was left at the default.
    psych = item.get("psychology_package") or {}
    if (
        psych.get("energy") in ("high", "intense")
        and base.motion_intensity == "moderate"
        and "motion_intensity" not in overrides
    ):
        overrides["motion_intensity"] = "high"

    if not overrides:
        return base
    merged = base.to_dict()
    merged.update(overrides)
    return AnimationConfig(**{k: v for k, v in merged.items() if k in AnimationConfig.__dataclass_fields__})


def build_animation_package(
    item: dict,
    context: "dict | None" = None,
    config: "AnimationConfig | None" = None,
) -> dict:
    """One AnimationPackage for one content item. Never raises."""
    resolved = _resolve_config(item, context, config)
    scenes = _scenes_from_item(item)[: resolved.max_scenes_per_package]
    shot_list = _shot_list_from_item(item, scenes)
    creative = item.get("creative_package") or {}
    asset_package = item.get("asset_package") or {}

    scene_timing = build_scene_timing(scenes, shot_list, resolved)
    camera_plan = plan_camera(
        scenes, shot_list, resolved, creative.get("camera_plan") or {},
    )
    # Re-align shot absolute times to scene timing when shot list lacked times.
    if scene_timing and camera_plan.get("shots"):
        by_scene = {t["scene_id"]: t for t in scene_timing}
        cursor_offsets: "dict[str, float]" = {}
        for shot in camera_plan["shots"]:
            timing = by_scene.get(shot["scene_id"])
            if not timing:
                continue
            used = cursor_offsets.get(shot["scene_id"], 0.0)
            duration = float(shot.get("duration_sec", 0) or 0) or float(timing["duration_sec"])
            # Keep relative lengths but clamp into the scene window.
            remaining = max(0.5, float(timing["end_sec"]) - float(timing["start_sec"]) - used)
            duration = min(duration, remaining)
            start = float(timing["start_sec"]) + used
            shot["start_sec"] = round(start, 3)
            shot["end_sec"] = round(start + duration, 3)
            shot["duration_sec"] = round(duration, 3)
            cursor_offsets[shot["scene_id"]] = used + duration

    character_motion = plan_character_motion(scenes, scene_timing, item, resolved)
    facial_animation = plan_facial_animation(scenes, scene_timing, item, resolved)
    body_animation = plan_body_animation(character_motion)
    lip_sync_plan = plan_lip_sync(scenes, scene_timing, item, resolved)
    choreography = plan_choreography(scenes, character_motion)
    transitions = plan_transitions(scenes, scene_timing, camera_plan, resolved)
    visual_effects, particle_effects = plan_visual_effects(scenes, scene_timing, resolved)
    lighting_cues = plan_lighting_cues(scenes, scene_timing, camera_plan)
    motion_graphics = plan_motion_graphics(scenes, scene_timing, item, resolved)
    audio_synchronization = plan_audio_sync(scenes, scene_timing, item)
    subtitle_timing = plan_subtitle_timing(scenes, scene_timing, lip_sync_plan)
    timeline = build_timeline(
        scene_timing, camera_plan, character_motion, facial_animation,
        lip_sync_plan, transitions, visual_effects, audio_synchronization,
        subtitle_timing, resolved, item,
    )

    export_metadata = {
        "fps": resolved.fps,
        "aspect_ratio": resolved.target_aspect_ratio,
        "target_duration_sec": timeline.get("total_duration_sec", 0),
        "target_platforms": list(
            item.get("target_platforms")
            or item.get("platforms")
            or [resolved.target_platform]
        ),
        "resolution": "1080x1920" if resolved.target_aspect_ratio == "9:16" else "1920x1080",
        "animation_style": resolved.animation_style,
        "camera_style": resolved.camera_style,
        "motion_intensity": resolved.motion_intensity,
        "motion_smoothing": resolved.motion_smoothing,
        "quality_tier": resolved.animation_quality,
        "series_id": str(item.get("series_id", "")),
        "episode_index": item.get("episode_index", 0),
    }

    provider_instructions = build_provider_instructions(
        camera_plan, character_motion, lip_sync_plan, visual_effects, resolved,
    )

    package = {
        "animation_package_version": ANIMATION_PACKAGE_VERSION,
        "engine_version": ANIMATION_ENGINE_VERSION,
        "project_id": str(item.get("project_id", "")),
        "config": resolved.to_dict(),
        "timeline": timeline,
        "scene_timing": scene_timing,
        "camera_plan": camera_plan,
        "character_motion": character_motion,
        "facial_animation": facial_animation,
        "lip_sync_plan": lip_sync_plan,
        "body_animation": body_animation,
        "lighting_cues": lighting_cues,
        "transitions": transitions,
        "visual_effects": visual_effects,
        "particle_effects": particle_effects,
        "motion_graphics": motion_graphics,
        "audio_synchronization": audio_synchronization,
        "subtitle_timing": subtitle_timing,
        "export_metadata": export_metadata,
        "provider_instructions": provider_instructions,
        "choreography": choreography,
        "generated_at": _now_iso(),
        # Internal QC aids (stripped from public diagnostics if needed).
        "_asset_refs": list(asset_package.get("assets") or []),
        "_asset_requirements": list(creative.get("asset_requirements") or []),
    }

    validation = validate_package(package)
    readiness = production_readiness(package, validation)
    package["validation"] = validation
    package["production_readiness"] = readiness
    package["quality_report"] = {
        "status": validation["status"],
        "warnings": list(validation["warnings"]),
        "blockers": list(validation["blockers"]),
        "checks": dict(validation["checks"]),
        "readiness": readiness,
        "provider_plan": provider_plan(resolved),
    }
    package["animation_diagnostics"] = {
        "scenes": len(scenes),
        "shots": len(camera_plan.get("shots", [])),
        "motions": len(character_motion),
        "facial_cues": len(facial_animation),
        "lip_sync_tracks": len(lip_sync_plan),
        "transitions": len(transitions),
        "effects": len(visual_effects),
        "particles": len(particle_effects),
        "motion_graphics": len(motion_graphics),
        "subtitle_cues": len(subtitle_timing),
        "total_duration_sec": timeline.get("total_duration_sec", 0),
        "fps": resolved.fps,
        "providers": sorted({ins.get("provider_id", "") for ins in provider_instructions}),
    }
    # Drop internal-only keys from the published package surface.
    package.pop("_asset_refs", None)
    package.pop("_asset_requirements", None)
    return package


def plan_items(
    items: "list[dict]",
    context: "dict | None" = None,
    config: "AnimationConfig | None" = None,
) -> "list[dict]":
    """Plan every item: writes each item's `animation_package` slot."""
    resolved = config or get_animation_config()
    packages: "list[dict]" = []

    def _one(item: dict) -> dict:
        try:
            return build_animation_package(item, context, resolved)
        except Exception as exc:  # noqa: BLE001 - one bad item never stops the engine
            return {
                "animation_package_version": ANIMATION_PACKAGE_VERSION,
                "engine_version": ANIMATION_ENGINE_VERSION,
                "project_id": str(item.get("project_id", "")),
                "production_readiness": {
                    "score": 0,
                    "status": ReadinessStatus.INCOMPLETE,
                    "blockers": [f"animation planning failed: {exc}"],
                },
                "quality_report": {
                    "status": "FAILED",
                    "warnings": [],
                    "blockers": [f"animation planning failed: {exc}"],
                    "checks": {},
                },
                "validation": {
                    "status": "FAILED",
                    "warnings": [],
                    "blockers": [f"animation planning failed: {exc}"],
                    "checks": {},
                },
                "timeline": {},
                "scene_timing": [],
                "camera_plan": {"shots": []},
                "character_motion": [],
                "facial_animation": [],
                "lip_sync_plan": [],
                "body_animation": [],
                "lighting_cues": [],
                "transitions": [],
                "visual_effects": [],
                "particle_effects": [],
                "motion_graphics": [],
                "audio_synchronization": [],
                "subtitle_timing": [],
                "export_metadata": {},
                "provider_instructions": [],
                "choreography": [],
                "animation_diagnostics": {},
                "config": resolved.to_dict(),
                "generated_at": _now_iso(),
            }

    if resolved.parallel_planning and len(items) > 1:
        with ThreadPoolExecutor(max_workers=min(8, len(items))) as pool:
            packages = list(pool.map(_one, items))
    else:
        packages = [_one(item) for item in items]

    for item, package in zip(items, packages):
        item["animation_package"] = package
    return packages
