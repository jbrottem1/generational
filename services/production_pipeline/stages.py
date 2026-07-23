"""Production Pipeline Integration — stage map and I/O contracts.

Maps the 10 conceptual production stages onto existing engines.
Does not rewrite agents — only documents and orders them.
"""

from __future__ import annotations

from typing import Any

# Ordered production stages (user contract). Engines listed are existing keys.
PRODUCTION_STAGES: tuple[dict[str, Any], ...] = (
    {
        "key": "research",
        "label": "Research",
        "engines": ["research", "ideation"],
        "inputs": ["command"],
        "outputs": ["research", "research_references", "niche", "subject", "candidates"],
        "notes": "Ideation seeds candidates so Psychology has content to score (existing pipeline pattern).",
    },
    {
        "key": "psychology",
        "label": "Psychology",
        "engines": ["psychology"],
        "inputs": ["candidates"],
        "outputs": ["candidates", "psychology_summary"],
        "notes": "Scores ViralScore / psychology report onto each candidate.",
    },
    {
        "key": "studio_director",
        "label": "Studio Director",
        "engines": ["ai_director"],
        "inputs": ["candidates", "unified_packages"],
        "outputs": ["director_package", "production_blueprint", "ai_director_summary"],
        "notes": "Production Blueprint before any creative production engines.",
    },
    {
        "key": "script_generator",
        "label": "Script Generator",
        "engines": ["script_generation"],
        "inputs": ["candidates"],
        "outputs": ["candidates", "script_generation_summary"],
        "notes": "Attaches winning script + script_package per candidate.",
    },
    {
        "key": "scene_builder",
        "label": "Scene Builder",
        "engines": ["visual_intelligence", "scene_planning", "visual_planning"],
        "inputs": ["candidates", "approved_content"],
        "outputs": ["candidates", "production_packages", "visual_intelligence_package"],
        "notes": "Visual storyboard + structured scenes on production packages.",
    },
    {
        "key": "media_generation",
        "label": "Media Generation",
        "engines": ["image", "asset_manager"],
        "inputs": ["ideas", "production_packages"],
        "outputs": ["ideas", "production_packages", "render_assets_summary"],
        "notes": "Image resolution + asset tracking. Asset generation remains available when creative packages exist.",
    },
    {
        "key": "voice_generation",
        "label": "Voice Generation",
        "engines": ["voice_audio", "narration", "voice"],
        "inputs": ["candidates", "production_packages"],
        "outputs": ["candidates", "production_packages", "voice_audio_summary", "voice_packages"],
        "notes": "Audio plan (voice_audio) then narration/voice tracks.",
    },
    {
        "key": "video_assembly",
        "label": "Video Assembly",
        "engines": ["subtitle", "timeline", "render_package", "studio_render", "video"],
        "inputs": ["production_packages", "candidates", "ideas"],
        "outputs": ["production_packages", "candidates", "studio_render_summary", "render_summary"],
        "notes": "Timeline, captions, render package, studio render, video assemble.",
    },
    {
        "key": "quality_control",
        "label": "Quality Control",
        "engines": ["quality", "production_qa"],
        "inputs": ["selected_ideas", "candidates"],
        "outputs": ["ideas", "quality_summary", "pqa_summary", "pqa_reports"],
        "notes": "Publish gate (quality) + Production QA (production_qa).",
    },
    {
        "key": "export",
        "label": "Export",
        "engines": ["optimization_lab"],
        "inputs": ["candidates"],
        "outputs": ["optimization_packages", "optimization_summary"],
        "notes": "Optimization Lab finalizes variants / export prep. Files land under data/productions/{id}/.",
    },
)

STAGE_KEYS: tuple[str, ...] = tuple(s["key"] for s in PRODUCTION_STAGES)

STAGE_BY_KEY: dict[str, dict[str, Any]] = {s["key"]: s for s in PRODUCTION_STAGES}


def flat_engine_order() -> list[str]:
    """Flatten stage engines into a single WorkflowEngine step list."""
    ordered: list[str] = []
    seen: set[str] = set()
    for stage in PRODUCTION_STAGES:
        for key in stage["engines"]:
            if key not in seen:
                ordered.append(key)
                seen.add(key)
    return ordered


def stage_contract_table() -> list[dict[str, Any]]:
    """Machine-readable I/O verification table for docs and tests."""
    return [
        {
            "stage": s["key"],
            "label": s["label"],
            "engines": list(s["engines"]),
            "inputs": list(s["inputs"]),
            "outputs": list(s["outputs"]),
            "notes": s.get("notes") or "",
        }
        for s in PRODUCTION_STAGES
    ]
