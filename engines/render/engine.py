"""RenderEngine — Agent 6's entry point: ProductionPackage in, render package out.

Consumes the planning layers (script_package / structured_script,
scene_breakdown, visual_package, audio_package, captions, thumbnail_plan,
quality_score) and produces the complete render-ready package for one
9:16 vertical short: timeline, scene render plans, caption render plan,
audio mix plan, asset requirements, warnings, and a simulated (mock)
render result.

Failure policy: rendering NEVER crashes the pipeline. Ideas that cannot be
planned get a safe mock render package with diagnostics; an empty context
returns a SKIPPED summary. The orchestrator's render stage stays green.
"""

from __future__ import annotations

from engines.contracts import ContractEngine
from engines.render.assets import AssetResolver
from engines.render.audio_mix import AudioMixer
from engines.render.captions import CaptionRenderer
from engines.render.models import (
    OUTPUT_FORMAT,
    RENDER_ENGINE_VERSION,
    RENDER_PACKAGE_VERSION,
    SUPPORTED_PLATFORMS,
    RenderStatus,
)
from engines.render.motion import MotionPlanner
from engines.render.packaging import OutputPackager
from engines.render.renderer import MockRenderer
from engines.render.scene_plans import SceneRenderer
from engines.render.timeline import TimelineBuilder
from engines.render.transitions import TransitionPlanner
from engines.render.validator import RenderValidator


# --------------------------------------------------------- scene normalization

def _scene_from_breakdown(raw: dict, index: int) -> dict:
    """Map a structured-script breakdown entry onto the Director scene shape."""
    start = float(raw.get("start_sec", 0.0))
    end = float(raw.get("end_sec", 0.0))
    duration = float(raw.get("duration_sec", 0.0)) or max(end - start, 0.0)
    broll = str(raw.get("broll_type", "")).lower()
    asset_type = "stock_footage" if "stock" in broll else "ai_image"
    return {
        "scene_number": int(raw.get("scene", raw.get("scene_number", index + 1))),
        "purpose": raw.get("section", raw.get("purpose", "story_beat")),
        "emotion": raw.get("emotion", ""),
        "length_sec": duration,
        "narration": raw.get("narration", ""),
        "visual_description": raw.get("visual_description", ""),
        "camera_motion": raw.get("camera_style", "") or raw.get("motion", ""),
        "zoom": "",
        "motion_intensity": 50,
        "transition_in": "none",
        "transition_out": raw.get("transition", "hard cut"),
        "asset_type": asset_type,
        "ai_image_prompt": raw.get("visual_description", ""),
        "ai_video_prompt": "",
        "stock_footage_query": raw.get("visual_description", "") if asset_type == "stock_footage" else "",
        "text_overlay": "",
        "overlay": "",
        "caption_placement": "bottom third, safe zone",
        "caption_timing": {"start_sec": start, "end_sec": end or start + duration},
        "caption_emphasis": raw.get("caption_emphasis", []),
        "sound_effect": raw.get("sound_cue", ""),
        "sfx_timing": {},
    }


def normalize_scenes(idea: dict) -> "tuple[list, list]":
    """Best available scene list for an idea, plus warnings about fallbacks.

    Prefers the Director's fully-annotated visual_package scenes; degrades
    to the structured script's scene_breakdown, then the package-level
    scene_breakdown — the renderer plans with whatever exists.
    """
    warnings = []
    scenes = (idea.get("visual_package") or {}).get("scenes") or []
    if scenes:
        return list(scenes), warnings

    breakdown = (
        (idea.get("structured_script") or {}).get("scene_breakdown")
        or (idea.get("script_package") or {}).get("structured_script", {}).get("scene_breakdown")
        or idea.get("scene_breakdown")
        or []
    )
    if breakdown:
        warnings.append(
            "No visual_package scenes — timeline built from the script scene "
            "breakdown (reduced camera/motion detail)."
        )
        return [_scene_from_breakdown(raw, index) for index, raw in enumerate(breakdown)], warnings

    warnings.append("No scenes available from any planning layer.")
    return [], warnings


def _audio_package_of(idea: dict) -> dict:
    return idea.get("audio_package") or idea.get("voice_assets") or idea.get("voice_package") or {}


def _output_format_for(idea: dict, context: "dict | None") -> dict:
    """Resolve aspect/resolution from idea or studio settings; default 9:16."""
    ctx = context or {}
    settings = ctx.get("studio_settings") or ctx.get("settings") or {}
    aspect = (
        idea.get("aspect_ratio")
        or settings.get("aspect_ratio")
        or settings.get("orientation")
        or ""
    )
    width = int(settings.get("width") or idea.get("width") or 0)
    height = int(settings.get("height") or idea.get("height") or 0)
    try:
        from services.media_production.formats import resolve_output_format

        return resolve_output_format(aspect=str(aspect), width=width, height=height)
    except Exception:  # noqa: BLE001
        return dict(OUTPUT_FORMAT)


# ------------------------------------------------------------ asset resolution

def build_asset_requests(idea: dict, scenes: list) -> list:
    """The Director's asset requests, or requests derived from the scenes."""
    requests = (idea.get("visual_package") or {}).get("asset_requests") or []
    if requests:
        return list(requests)
    derived = []
    for scene in scenes:
        source = scene.get("asset_type", "ai_image")
        derived.append(
            {
                "source": source,
                "asset_kind": "video" if source in ("ai_video", "stock_footage") else "image",
                "scene_number": scene.get("scene_number", 0),
                "duration_sec": scene.get("length_sec", 0),
                "aspect_ratio": OUTPUT_FORMAT["aspect_ratio"],
                "prompt": scene.get("ai_image_prompt") or scene.get("visual_description", ""),
                "query": scene.get("stock_footage_query", ""),
            }
        )
    return derived


def resolve_idea_assets(idea: dict) -> dict:
    """Resolve (mock-fulfil) every visual asset an idea needs."""
    scenes, _ = normalize_scenes(idea)
    requests = build_asset_requests(idea, scenes)
    resolution = AssetResolver().resolve(requests)
    resolution["requests"] = requests
    return resolution


# --------------------------------------------------------------- safe fallback

def safe_mock_render_package(title: str, reason: str) -> dict:
    """The package returned when planning is impossible — never a crash."""
    resolution = OUTPUT_FORMAT["resolution"]
    return {
        "render_package_version": RENDER_PACKAGE_VERSION,
        "render_engine_version": RENDER_ENGINE_VERSION,
        "title": title,
        "output_format": dict(OUTPUT_FORMAT),
        "platforms": list(SUPPORTED_PLATFORMS),
        "resolution": f"{resolution['width']}x{resolution['height']}",
        "aspect_ratio": OUTPUT_FORMAT["aspect_ratio"],
        "duration_sec": 0.0,
        "timeline": {"segments": [], "segment_count": 0, "total_duration_sec": 0.0},
        "scene_render_plan": [],
        "caption_render_plan": {"segments": []},
        "audio_mix_plan": {"tracks": {}},
        "transition_plan": {"transitions": []},
        "motion_plan": [],
        "asset_requirements": [],
        "missing_assets": [],
        "render_warnings": [reason],
        "estimated_render_duration_sec": 0.0,
        "production_readiness_score": 0,
        "validation": {
            "status": RenderStatus.SKIPPED,
            "checks": [],
            "problems": [reason],
            "production_readiness_score": 0,
        },
        "render_status": RenderStatus.SKIPPED,
        "mock_output_path": "",
        "file_uri": "",
        "render_log": [],
        "render_job": {},
        "mock": True,
        "render_manifest": {"ready_for_publishing": False, "warnings": 1},
    }


# ------------------------------------------------------------- render assembly

def build_render_output(idea: dict, context: "dict | None" = None) -> dict:
    """The complete Agent 6 render package for one idea (JSON-safe dict)."""
    title = idea.get("title") or idea.get("hook") or "Untitled"
    try:
        scenes, warnings = normalize_scenes(idea)
        if not scenes:
            return safe_mock_render_package(
                title, "No scenes available — run the script/visual stages first."
            )

        assets = idea.get("render_assets") or resolve_idea_assets(idea)
        requests = assets.get("requests") or build_asset_requests(idea, scenes)
        warnings.extend(assets.get("warnings", []))

        timeline = TimelineBuilder().build(scenes)
        warnings.extend(timeline.pop("warnings", []))
        transition_plan = TransitionPlanner().plan(scenes)
        motion_plan = MotionPlanner().plan(scenes)
        audio_package = _audio_package_of(idea)
        caption_render_plan = CaptionRenderer().build(scenes, timeline)
        audio_mix_plan = AudioMixer().build(
            scenes, audio_package, timeline, transition_plan["transitions"]
        )
        scene_render_plan = SceneRenderer().build(
            scenes, assets.get("assets", []), audio_package.get("scene_cues", [])
        )

        validation = RenderValidator().validate(
            scenes=scenes,
            timeline=timeline,
            scene_render_plan=scene_render_plan,
            caption_render_plan=caption_render_plan,
            audio_mix_plan=audio_mix_plan,
            missing_assets=assets.get("missing_assets", []),
        )
        warnings.extend(validation.get("problems", []))

        render_result = MockRenderer().render(
            title=title,
            timeline=timeline,
            scene_render_plan=scene_render_plan,
            caption_render_plan=caption_render_plan,
            audio_mix_plan=audio_mix_plan,
            missing_assets=assets.get("missing_assets", []),
            warnings=warnings,
            output_format=_output_format_for(idea, context),
        )

        return OutputPackager().package(
            title=title,
            timeline=timeline,
            scene_render_plan=scene_render_plan,
            caption_render_plan=caption_render_plan,
            audio_mix_plan=audio_mix_plan,
            transition_plan=transition_plan,
            motion_plan=motion_plan,
            asset_requirements=requests,
            missing_assets=assets.get("missing_assets", []),
            render_warnings=render_result.get("warnings", warnings),
            validation=validation,
            render_result=render_result,
            seed=idea.get("production", {}),
        )
    except Exception as exc:  # noqa: BLE001 - render must degrade, never crash
        return safe_mock_render_package(title, f"Render planning failed safely: {exc}")


def _sync_unified_packages(context: dict, ideas: list) -> "list | None":
    """Mirror each idea's render package into context['unified_packages']."""
    unified = context.get("unified_packages")
    if not unified:
        return None
    by_title = {idea.get("title", ""): idea for idea in ideas}
    for package in unified:
        idea = by_title.get(package.get("title", ""))
        if not idea or "render_package" not in idea:
            continue
        merged = dict(package.get("render_package") or {})
        merged.update(idea["render_package"])
        package["render_package"] = merged
        if merged.get("render_manifest", {}).get("ready_for_publishing"):
            package["status"] = "rendered"
    return unified


def render_ideas(context: dict) -> dict:
    """Render every idea in the context; always returns safe updates."""
    ideas = context.get("ideas") or context.get("selected_ideas") or context.get("candidates") or []
    if not ideas:
        return {
            "render_summary": {
                "status": RenderStatus.SKIPPED,
                "reason": "No ideas in context — nothing to render.",
                "rendered": 0,
                "results": [],
            }
        }

    results = []
    for idea in ideas:
        package = build_render_output(idea, context)
        idea["render_package"] = package
        results.append(
            {
                "title": package.get("title", ""),
                "render_status": package.get("render_status", ""),
                "production_readiness_score": package.get("production_readiness_score", 0),
                "duration_sec": package.get("duration_sec", 0.0),
                "mock_output_path": package.get("mock_output_path", ""),
                "warnings": len(package.get("render_warnings", [])),
            }
        )

    statuses = {result["render_status"] for result in results}
    if statuses <= {RenderStatus.SUCCESS}:
        status = RenderStatus.SUCCESS
    elif RenderStatus.FAILED in statuses and statuses <= {RenderStatus.FAILED}:
        status = RenderStatus.FAILED
    else:
        status = RenderStatus.WARNING

    updates = {
        "ideas": ideas,
        "render_summary": {
            "status": status,
            "rendered": len(results),
            "average_readiness": int(
                round(
                    sum(r["production_readiness_score"] for r in results) / len(results)
                )
            ),
            "results": results,
        },
    }
    unified = _sync_unified_packages(context, ideas)
    if unified is not None:
        updates["unified_packages"] = unified
    return updates


# ------------------------------------------------------------------ the engine

class RenderEngine(ContractEngine):
    """Agent 6 — Render & Video Production (plan + mock render, real-ready)."""

    key = "render"
    label = "Render & Video Production"
    icon = "🎞️"
    description = (
        "Convert approved ProductionPackages into render-ready 9:16 vertical "
        "video packages: timeline, scene render plans, captions, audio mix, "
        "and a simulated render — real providers swap in behind interfaces."
    )
    version = RENDER_ENGINE_VERSION
    input_contract = ["ideas"]
    output_contract = ["render_summary"]
    dependencies = ["visual_intelligence", "voice_audio", "quality"]
    capabilities = [
        "render",
        "timeline",
        "captions",
        "audio-mix",
        "motion",
        "transitions",
        "mock-render",
        "vertical-video",
    ]

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        return render_ideas(context)
