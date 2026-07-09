"""Packager — folds the final pipeline context into ProductionPackage objects.

One package per idea. This is the ONLY place that knows how engine outputs
(idea fields, visual/audio packages, media production output) map onto the
standardized model — engines never build packages themselves.
"""

from __future__ import annotations

from services.orchestrator.models import ProductionPackage


def _captions_for(idea: dict, context: dict) -> dict:
    """Prefer rendered subtitle tracks from media production; fall back to the
    Visual Intelligence caption plan (planning-stage data)."""
    for pkg in context.get("production_packages", []):
        if pkg.get("title") == idea.get("title") and pkg.get("subtitles"):
            return pkg["subtitles"]
    caption_plan = idea.get("visual_package", {}).get("caption_plan")
    if caption_plan:
        return {"status": "planned", "caption_plan": caption_plan}
    return {"status": "pending"}


def _thumbnail_plan(idea: dict) -> list:
    plan = list(idea.get("thumbnail_concepts", []))
    concept_text = idea.get("thumbnail_concept", "")
    if concept_text:
        plan.append({"source": "seo", "concept": concept_text})
    return plan


def build_package(idea: dict, context: dict) -> ProductionPackage:
    """Build one ProductionPackage from a finished idea + shared context."""
    top = context.get("top_opportunity", {})
    trend = top.get("trend", {})
    visual = idea.get("visual_package", {})
    audio = idea.get("audio_package", {})
    production = idea.get("production", {})

    package = ProductionPackage(
        brand=context.get("project_name") or context.get("niche", ""),
        language=trend.get("language", "en"),
        target_country=trend.get("country", "US"),
        platforms=[context.get("target_platform", "youtube_shorts")],
        trend_score=int(top.get("opportunity_score", 0)),
        # Higher = more open field (competition inverted for consistency
        # with every other 0-100 "bigger is better" score).
        competition_score=int(round((1 - float(trend.get("competition", 0.5))) * 100)),
        psychology_score=int(idea.get("psychology_score", 0)),
        attention_score=int(idea.get("attention_graph", {}).get("attention_score", 0)),
        hook=idea.get("hook", ""),
        script=idea.get("script", ""),
        scene_breakdown=visual.get("scenes", []) or idea.get("structured_script", {}).get("scenes", []),
        visual_assets={
            "storyboard": visual.get("storyboard", []),
            "image_prompts": visual.get("image_prompts", []),
            "video_prompts": visual.get("video_prompts", []),
            "hook_sequence": visual.get("hook_sequence", []),
            "aspect_ratio": visual.get("aspect_ratio", ""),
            "color_palette": visual.get("color_palette", {}),
            "visual_score": idea.get("visual_score", 0),
        },
        voice_assets={
            "voice_style": audio.get("voice_style", {}),
            "narration_plan": audio.get("narration_plan", {}),
            "pacing": audio.get("pacing", {}),
            "sfx_plan": audio.get("sfx_plan", {}),
            "scene_cues": audio.get("scene_cues", []),
            "audio_score": idea.get("audio_score", 0),
        },
        music_assets=audio.get("music_direction", {}),
        captions=_captions_for(idea, context),
        thumbnail_plan=_thumbnail_plan(idea),
        seo_package={
            "title": idea.get("title", ""),
            "description": idea.get("description", ""),
            "hashtags": idea.get("hashtags", []),
            "keywords": idea.get("keywords", []),
            "seo_score": idea.get("seo_score", 0),
        },
        quality_score=int(idea.get("scores", {}).get("publish", 0)),
        publish_ready=bool(idea.get("publishable")),
        analytics_placeholder={"status": "awaiting_publish", "metrics": {}},
        # v8.1 canonical ContentPackage fields (Agents 6-10 read/write zones).
        target_platforms=[context.get("target_platform", "youtube_shorts")],
        target_language=trend.get("language", "en"),
        topic=context.get("subject", ""),
        keywords=list(idea.get("keywords", [])),
        opportunity_score=int(top.get("opportunity_score", 0)),
        virality_score=int(idea.get("scores", {}).get("virality", 0)),
        script_package={
            "script": idea.get("script", ""),
            "structured_script": idea.get("structured_script", {}),
            "variants": idea.get("script_variants", []),
            "script_score": idea.get("script_score", 0),
        },
        visual_package=visual,
        audio_package=audio,
        render_package=dict(production),          # Agent 6 replaces with real render output
        publishing_package={},                    # Agent 7 fills (schedule, accounts, metadata)
        analytics_package={},                     # Agent 9 fills (post-publish performance)
        learning_metadata={},                     # Agent 9 fills (learning signals)
        status="approved" if idea.get("publishable") else "held",
        diagnostics={"gate_failures": idea.get("gate_failures", [])},
    )

    # Additive traceability fields (extras are first-class in to_dict()).
    package.extras["title"] = idea.get("title", "")
    package.extras["scores"] = idea.get("scores", {})
    package.extras["citations"] = {
        "citation_count": idea.get("citations", {}).get("citation_count", 0),
        "claim_confidence": idea.get("citations", {}).get("claim_confidence", 0),
    }
    package.extras["threat_report"] = idea.get("threat_report", {})
    package.extras["render_package_id"] = production.get("render_package_id", "")
    package.extras["queue_status"] = production.get("queue_status", "")
    return package


def build_packages(context: dict) -> "list[ProductionPackage]":
    """One ProductionPackage per finished idea in the context."""
    return [build_package(idea, context) for idea in context.get("ideas", [])]
