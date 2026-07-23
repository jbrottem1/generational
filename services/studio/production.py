"""Studio production execution — routes through Workflow Executor → Orchestrator."""

from __future__ import annotations

import re

from core.constants import DEFAULT_PUBLISH_THRESHOLD
from services.studio.models import platform_label

_LONGFORM_PATTERNS = (
    r"\b\d+\s*(hour|hr|minute|min)\b",
    r"\bdocumentary\b",
    r"\bpodcast\b",
    r"\baudiobook\b",
    r"\bcourse\b",
    r"\bseries\b",
    r"\bchannel\b",
    r"\bcampaign\b",
    r"\bfeature\b",
    r"\blong[\s-]?form\b",
)

_PLATFORM_PRODUCTION_TYPE = {
    "youtube_shorts": "youtube_short",
    "youtube_long": "longform",
    "tiktok": "youtube_short",
    "instagram_reels": "youtube_short",
    "facebook": "youtube_short",
    "x": "youtube_short",
    "linkedin": "youtube_short",
    "podcast": "podcast",
    "audiobook": "podcast",
    "course": "course",
    "presentation": "course",
    "documentary": "documentary",
    "animated_series": "animated_episode",
    "marketing_campaign": "campaign",
    "multi_platform": "campaign",
}

_STEP_STATUS_TO_ORCH = {
    "completed": "SUCCESS",
    "failed": "FAILED",
    "skipped": "SKIPPED",
    "cancelled": "SKIPPED",
    "running": "RUNNING",
    "retrying": "RUNNING",
    "pending": "PENDING",
    "waiting": "PENDING",
}


def is_longform_command(command: str) -> bool:
    lowered = command.lower()
    return any(re.search(pattern, lowered) for pattern in _LONGFORM_PATTERNS)


def build_settings_preview(command: str, settings: dict) -> dict:
    """Summarize production settings before execution."""
    platform = settings.get("platform", "youtube_shorts")
    return {
        "command": command,
        "platform": platform_label(platform),
        "platform_id": platform,
        "video_length_sec": settings.get("video_length_sec", 60),
        "video_length_label": _format_duration(settings.get("video_length_sec", 60)),
        "voice": settings.get("voice", "ai"),
        "narrator": settings.get("narrator", "documentary"),
        "visual_style": settings.get("visual_style", "cinematic"),
        "camera_style": settings.get("camera_style", "dynamic"),
        "music_style": settings.get("music_style", "uplifting"),
        "pacing": settings.get("pacing", "dynamic"),
        "target_audience": settings.get("target_audience", "general"),
        "language": settings.get("language", "en"),
        "brand": settings.get("brand", ""),
        "character_set": settings.get("character_set", ""),
        "creative_style": settings.get("creative_style", "narrative_arc"),
        "quality_level": settings.get("quality_level", "standard"),
        "budget_usd": settings.get("budget_usd", 0.0),
        "preferred_providers": settings.get("preferred_providers", []),
        "longform": is_longform_command(command),
        "video_count": _detect_count(command),
    }


def _format_duration(seconds: int) -> str:
    if seconds >= 3600:
        hours = seconds // 3600
        mins = (seconds % 3600) // 60
        return f"{hours}h {mins}m" if mins else f"{hours}h"
    if seconds >= 60:
        return f"{seconds // 60}m"
    return f"{seconds}s"


def _detect_count(command: str) -> int:
    from core import parsing
    return parsing.detect_video_count(command)


def _production_type_for_platform(platform: str, settings: dict | None = None) -> str:
    settings = settings or {}
    explicit = str(settings.get("production_type") or "").strip()
    if explicit:
        return explicit
    return _PLATFORM_PRODUCTION_TYPE.get(platform, "full_production")


def _build_workflow_config(command: str, settings: dict, *, model: str, longform: bool = False):
    from services.workflow_executor import WorkflowConfig

    platform = settings.get("platform", "youtube_shorts")
    count = _detect_count(command)
    if count < 1:
        count = 1
    prefs = {}
    preferred = settings.get("preferred_providers") or []
    if preferred:
        prefs["preferred_providers"] = list(preferred)
    ptype = _production_type_for_platform(platform, settings)
    return WorkflowConfig(
        production_type=ptype,
        target_platform=platform,
        platform_targets=[platform],
        count=count,
        model=model,
        quality_level=settings.get("quality_level", "standard"),
        budget_usd=float(settings.get("budget_usd") or 0.0),
        provider_preferences=prefs,
        longform_mode=longform or is_longform_command(command) or ptype in {
            "longform", "documentary", "podcast", "course", "animated_episode",
        },
    )


def _studio_context_extra(settings: dict, *, research_settings=None, project_name=None, threshold=DEFAULT_PUBLISH_THRESHOLD) -> dict:
    platform = settings.get("platform", "youtube_shorts")
    extra = {
        "voice_mode": settings.get("voice", "ai"),
        "voice_profile_id": settings.get("narrator", ""),
        "studio_settings": settings,
        "platform": platform,
        "video_length_sec": settings.get("video_length_sec", 60),
        "visual_style": settings.get("visual_style", ""),
        "music_style": settings.get("music_style", ""),
        "pacing": settings.get("pacing", ""),
        "target_audience": settings.get("target_audience", ""),
        "language": settings.get("language", "en"),
        "brand": settings.get("brand", ""),
        "quality_level": settings.get("quality_level", "standard"),
        "preferred_providers": settings.get("preferred_providers", []),
        "threshold": threshold,
        "publish_threshold": threshold,
    }
    if research_settings:
        extra["research_settings"] = research_settings
    if project_name:
        extra["project_name"] = project_name
    # Always inject historical learning so the next video starts smarter
    try:
        from services.analytics.integration import learning_context_extra
        from services.learning.consult import consult_context

        topic = str(settings.get("topic") or project_name or "")
        extra.update(learning_context_extra())
        if topic:
            extra.update(
                consult_context(
                    topic,
                    niche=str(settings.get("target_audience") or ""),
                    platform=str(platform),
                    runtime_sec=int(settings.get("video_length_sec") or 60),
                )
            )
    except Exception:
        pass
    return extra


def _stage_reports_from_run(run) -> list:
    reports = []
    for step in run.workflow.steps:
        reports.append({
            "stage": step.stage,
            "status": _STEP_STATUS_TO_ORCH.get(step.status, "PENDING"),
            "duration_ms": step.duration_ms,
            "errors": list(step.errors),
            "warnings": list(step.warnings),
            "confidence": step.confidence,
            "diagnostics": dict(step.diagnostics or {}),
        })
    return reports


def _record_knowledge(result: dict, context: dict) -> None:
    from services.knowledge import CATEGORY, get_knowledge_base
    kb = get_knowledge_base()
    source = "demo" if result.get("demo_mode", True) else "openai"
    try:
        research = result.get("research", {})
        if research:
            kb.add_entry(CATEGORY.RESEARCH, {
                "command": result.get("command", ""),
                "subject": context.get("subject", ""),
                "summary": research.get("executive_summary") or research.get("summary", ""),
                "source_count": research.get("source_count", 0),
                "providers_used": research.get("providers_used", []),
                "important_facts": research.get("important_facts", []),
            }, {"niche": result.get("niche", ""), "source": source})
        for idea in result.get("ideas", []):
            metadata = {"niche": result.get("niche", ""), "source": source, "publish_score": idea.get("scores", {}).get("publish")}
            if idea.get("hook"):
                kb.add_entry(CATEGORY.HOOKS, idea["hook"], metadata)
            if idea.get("title"):
                kb.add_entry(CATEGORY.TITLES, idea["title"], metadata)
            if idea.get("script"):
                kb.add_entry(CATEGORY.SCRIPTS, idea["script"], metadata)
            if idea.get("thumbnail_concept"):
                kb.add_entry(CATEGORY.THUMBNAILS, idea["thumbnail_concept"], metadata)
    except Exception:
        pass


def result_from_project_run(run, settings: dict) -> dict:
    from core.models import build_result
    from services.workflow_executor import WorkflowStatus, studio_status

    context = dict(run.context or {})
    command = run.command or context.get("command", "")
    model = run.config.model if run.config else context.get("model", "demo")
    ideas = list(context.get("ideas") or [])
    count = int(context.get("count") or (run.config.count if run.config else 1))

    if ideas or run.status == WorkflowStatus.COMPLETED:
        result = build_result(
            command=command, niche=context.get("niche", ""),
            video_count=context.get("video_count", count), goal=context.get("goal", ""),
            ideas=ideas, demo_mode=context.get("demo_mode", True), model=model,
        )
    else:
        result = {
            "command": command, "niche": context.get("niche", ""), "video_count": count,
            "goal": context.get("goal", ""), "ideas": ideas,
            "demo_mode": context.get("demo_mode", True), "model": model,
        }

    result["research"] = context.get("research", {})
    if context.get("research_bundle"):
        result["research_bundle"] = context["research_bundle"]
    result["trend_opportunities"] = context.get("trend_opportunities", [])
    result["trend_dashboard"] = context.get("trend_dashboard", {})
    result["top_opportunity"] = context.get("top_opportunity", {})
    result["quality_summary"] = context.get("quality_summary", {})
    result["pipeline_steps"] = context.get("pipeline_steps", [])
    result["tokens_used"] = context.get("tokens_used", 0)
    result["production_packages"] = context.get("production_packages", [])
    result["production_steps"] = context.get("production_steps", [])
    result["production_dashboard"] = context.get("production_dashboard", [])
    result["queued_count"] = context.get("queued_count", 0)
    result["unified_packages"] = context.get("unified_packages") or list(run.result.packages or [])
    result["stage_reports"] = _stage_reports_from_run(run)
    result["production_report"] = dict(run.result.production_report or context.get("production_report") or {})
    result["render_summary"] = context.get("render_summary", {})
    result["seo_optimization_report"] = context.get("seo_optimization_report", {})
    result["publishing_result"] = context.get("publishing_result", {})
    result["publish_schedule"] = context.get("publish_schedule", [])
    result["analytics_summary"] = context.get("analytics_summary", {})
    result["learning_report"] = context.get("learning_report", {})
    result["learning_recommendations"] = context.get("learning_recommendations", {})
    result["learning_metadata"] = context.get("learning_metadata", {})
    if context.get("production_error"):
        result["production_error"] = context["production_error"]
    if context.get("production_skipped"):
        result["production_skipped"] = True

    platform = settings.get("platform", "youtube_shorts")
    result["studio_settings"] = settings
    result["platform"] = platform
    result["settings_preview"] = build_settings_preview(command, settings)
    result["workflow_run_id"] = run.run_id
    result["workflow_status"] = run.status
    result["workflow_studio_status"] = studio_status(run)
    result["provider_usage"] = dict(run.provider_usage or run.result.provider_usage or {})
    result["estimated_cost_usd"] = run.estimated_cost_usd or run.result.estimated_cost_usd

    if run.status == WorkflowStatus.FAILED:
        result["error"] = run.result.error or "Workflow failed"
    elif run.result.partial:
        result["error"] = run.result.error or "Workflow completed with partial outputs"
    elif context.get("error"):
        result["error"] = context["error"]

    _record_knowledge(result, context)
    return result


def run_studio_production(command: str, settings: dict, *, model: str = "gpt-4o-mini", threshold: int = DEFAULT_PUBLISH_THRESHOLD, research_settings=None, project_name=None) -> dict:
    """Run full production via Workflow Executor → Orchestrator.

    Canonical Studio path (Agents 20→21→Orchestrator). Does not call engines
    or provider APIs directly.
    """
    from services.workflow_executor import get_workflow_executor

    config = _build_workflow_config(command, settings, model=model)
    context_extra = _studio_context_extra(settings, research_settings=research_settings, project_name=project_name, threshold=threshold)
    run = get_workflow_executor().execute(command, config=config, context_extra=context_extra)
    return result_from_project_run(run, settings)


def run_executive_production(
    command: str,
    settings: dict | None = None,
    *,
    plan_only: bool = False,
    skip_publishing: bool = False,
    publish_mode: str = "scheduled",
    category: str = "science",
) -> dict:
    """One-command studio path via Executive Orchestrator."""
    from services.executive_orchestrator import create_video, ensure_executive_handler

    ensure_executive_handler()
    settings = settings or {}
    platform = str(settings.get("platform") or "")
    extra = {}
    if platform:
        extra["target_platform"] = platform
    result = create_video(
        command,
        category=category,
        publish_mode=publish_mode,
        plan_only=plan_only,
        skip_publishing=skip_publishing,
        context_extra=extra or None,
    )
    return {
        "ok": result.get("status") == "completed",
        "executive_run": result,
        "ideas": [],
        "command": command,
        "demo_mode": True,
        "pipeline_steps": [
            {
                "engine": stage.get("key"),
                "status": stage.get("status"),
                "error": stage.get("error") or "",
            }
            for stage in (result.get("stages") or {}).values()
        ],
        "quality_summary": {
            "pqa_score": result.get("qa_score"),
            "pqa_decision": result.get("qa_decision"),
        },
        "executive_export": result.get("export_paths"),
        "error": result.get("error") or "",
    }


def submit_longform_job(command: str, settings: dict, *, model: str = "gpt-4o-mini", project_name: str = "", threshold: int = DEFAULT_PUBLISH_THRESHOLD, research_settings=None) -> dict:
    """Submit a durable long-form job via Workflow Executor (`workflow_run`)."""
    from core.jobs import get_queue
    from services.workflow_executor import WORKFLOW_JOB_TYPE, ensure_workflow_handler, get_workflow_executor

    config = _build_workflow_config(command, settings, model=model, longform=True)
    context_extra = _studio_context_extra(settings, research_settings=research_settings, project_name=project_name or None, threshold=threshold)
    executor = get_workflow_executor()
    run = executor.create_run(command, config, context_extra=context_extra)
    queue = get_queue()
    ensure_workflow_handler(queue)
    job = queue.submit(WORKFLOW_JOB_TYPE, {
        "resume_run_id": run.run_id,
        "command": command,
        "config": config.to_dict(),
        "context_extra": context_extra,
    })
    return {
        "job_id": job.id,
        "run_id": run.run_id,
        "checkpoint_id": run.run_id,
        "status": run.status,
        "command": command,
        "longform": True,
        "workflow_job_type": WORKFLOW_JOB_TYPE,
    }
