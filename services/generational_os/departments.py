"""GenOS department registry — every existing system is a managed department."""

from __future__ import annotations

from typing import Any

# Department → existing service / role (no new engines)
DEPARTMENTS: dict[str, dict[str, Any]] = {
    "trend_opportunity": {
        "label": "Trend & Opportunity Intelligence",
        "service": "services.trend_opportunity",
        "role": "decide_what_to_create",
        "entrypoint": "run_trend_opportunity",
    },
    "research": {
        "label": "Research Engine",
        "service": "services.research",
        "role": "facts_and_sources",
        "engine": "research",
    },
    "psychology": {
        "label": "Psychology Engine",
        "service": "engines.psychology",
        "role": "viewer_psychology",
        "engine": "psychology",
    },
    "studio_director": {
        "label": "Studio Director",
        "service": "services.ai_director",
        "role": "creative_direction",
        "engine": "ai_director",
    },
    "script": {
        "label": "Script Generator",
        "service": "engines.script_generation",
        "role": "script",
        "engine": "script_generation",
    },
    "scene_builder": {
        "label": "Scene Builder",
        "service": "services.visual",
        "role": "scenes",
        "engine": "visual_intelligence",
    },
    "world_builder": {
        "label": "Persistent World Builder",
        "service": "services.world_builder",
        "role": "world_continuity",
    },
    "visual_asset_director": {
        "label": "Visual Asset Director",
        "service": "services.visual_asset_director",
        "role": "visual_qc_gate",
    },
    "cinematic_director": {
        "label": "AI Cinematic Director",
        "service": "services.cinematic_director",
        "role": "camera_lighting_motion",
    },
    "voice_studio": {
        "label": "ElevenLabs Voice Studio",
        "service": "services.voice_studio",
        "role": "narration",
        "engine": "voice_audio",
    },
    "renderer": {
        "label": "Existing Renderer",
        "service": "services.studio_render",
        "role": "render",
        "engine": "studio_render",
    },
    "creative_performance_lab": {
        "label": "Creative Performance Lab",
        "service": "services.creative_performance_lab",
        "role": "creative_experiments",
    },
    "creative_excellence": {
        "label": "Creative Excellence / QA",
        "service": "services.creative_excellence",
        "role": "creative_qa",
    },
    "audience_intelligence": {
        "label": "Audience Intelligence",
        "service": "services.audience_intelligence",
        "role": "audience_review_and_briefs",
    },
    "publishing_intelligence": {
        "label": "Publishing Intelligence",
        "service": "services.publishing_intelligence",
        "role": "publish_strategy",
    },
    "production_operations": {
        "label": "Production Operations (Agent 0 Studio)",
        "service": "services.production_operations",
        "role": "execute_studio_pipeline",
        "entrypoint": "run_studio_ops",
    },
}


# Operating loop stages mapped to departments (compose only)
OPERATING_LOOP: tuple[dict[str, str], ...] = (
    {"step": "check_trend_intelligence", "department": "trend_opportunity"},
    {"step": "select_opportunity", "department": "trend_opportunity"},
    {"step": "generate_production_brief", "department": "trend_opportunity"},
    {"step": "launch_research", "department": "research"},
    {"step": "launch_psychology", "department": "psychology"},
    {"step": "generate_script", "department": "script"},
    {"step": "build_world", "department": "world_builder"},
    {"step": "generate_scenes", "department": "scene_builder"},
    {"step": "validate_visual_assets", "department": "visual_asset_director"},
    {"step": "apply_cinematic_direction", "department": "cinematic_director"},
    {"step": "generate_narration", "department": "voice_studio"},
    {"step": "render_final_video", "department": "renderer"},
    {"step": "run_creative_qa", "department": "creative_excellence"},
    {"step": "package_production", "department": "production_operations"},
    {"step": "publish_when_enabled", "department": "publishing_intelligence"},
    {"step": "collect_analytics", "department": "audience_intelligence"},
    {"step": "audience_review", "department": "audience_intelligence"},
    {"step": "update_opportunity_library", "department": "trend_opportunity"},
    {"step": "store_lessons_learned", "department": "creative_excellence"},
)


def list_departments() -> list[dict[str, Any]]:
    return [{"key": k, **v} for k, v in DEPARTMENTS.items()]


def department_health() -> dict[str, Any]:
    """Soft import-check each department (available vs import-error)."""
    rows = []
    for key, spec in DEPARTMENTS.items():
        mod = spec.get("service") or ""
        ok = False
        err = ""
        try:
            __import__(mod)
            ok = True
        except Exception as exc:  # noqa: BLE001
            err = str(exc)[:120]
        rows.append({"key": key, "label": spec["label"], "available": ok, "error": err})
    return {
        "departments": rows,
        "available_count": sum(1 for r in rows if r["available"]),
        "total": len(rows),
    }
