"""Ideation service — runs the intelligence pipeline for the UI.

Submits the command as a job to the central JobQueue, which executes the
"intelligence" workflow (trend discovery → opportunity ranking → research →
candidates → psychology → ranking → scripts → critic → revision → citation →
SEO → quality gate) through the WorkflowEngine.
Final assets are recorded into the Knowledge Base.
"""

from __future__ import annotations

from core.constants import DEFAULT_PUBLISH_THRESHOLD
from core.jobs import get_queue
from core.log import get_logger, log_event
from core.models import build_result
from core.workflows import WORKFLOW_JOB_TYPE, ensure_workflow_handler

logger = get_logger(__name__)


def run_command(
    command: str,
    count: int,
    model: str,
    threshold: int = DEFAULT_PUBLISH_THRESHOLD,
    voice_mode: str = "ai",
    voice_profile_id: str = "",
    research_settings: "dict | None" = None,
    project_name: str | None = None,
) -> dict:
    """Run the intelligence pipeline for a command.

    Returns a result dict (see core.models.build_result) enriched with
    "research", "quality_summary", "pipeline_steps", and transient
    "tokens_used"/"error" keys.
    """
    queue = get_queue()
    ensure_workflow_handler(queue)

    job = queue.submit(
        WORKFLOW_JOB_TYPE,
        {
            "workflow": "intelligence",
            "context": {
                "command": command,
                "count": count,
                "model": model,
                "threshold": threshold,
                "research_settings": research_settings,
                "project_name": project_name,
            },
        },
    )
    job = queue.run(job.id)
    log_event(logger, "ideation.job_finished", job_id=job.id, status=job.status)

    if job.status != "succeeded":
        return _fallback_result(command, count, model, job.error)

    context = job.result["context"]
    context["voice_mode"] = voice_mode
    context["voice_profile_id"] = voice_profile_id
    result = build_result(
        command=command,
        niche=context["niche"],
        video_count=context["video_count"],
        goal=context["goal"],
        ideas=context.get("ideas", []),
        demo_mode=context.get("demo_mode", True),
        model=model,
    )
    result["research"] = context.get("research", {})
    if context.get("research_bundle"):
        result["research_bundle"] = context["research_bundle"]
    result["trend_opportunities"] = context.get("trend_opportunities", [])
    result["trend_dashboard"] = context.get("trend_dashboard", {})
    result["top_opportunity"] = context.get("top_opportunity", {})
    result["quality_summary"] = context.get("quality_summary", {})
    result["pipeline_steps"] = job.result["run"]["steps"]
    result["tokens_used"] = context.get("tokens_used", 0)
    if context.get("error"):
        result["error"] = context["error"]

    _record_knowledge(result, context)

    from services.production import run_media_production

    production = run_media_production(context)
    result["production_packages"] = production.get("production_packages", [])
    result["production_steps"] = production.get("production_steps", [])
    result["production_dashboard"] = production.get("production_dashboard", [])
    result["queued_count"] = production.get("queued_count", 0)
    if production.get("production_error"):
        result["production_error"] = production["production_error"]
    if production.get("production_skipped"):
        result["production_skipped"] = True

    return result


def _record_knowledge(result: dict, context: dict) -> None:
    """Feed final assets and research into the Knowledge Base."""
    from services.knowledge import CATEGORY, get_knowledge_base

    kb = get_knowledge_base()
    source = "demo" if result["demo_mode"] else "openai"
    try:
        research = result.get("research", {})
        if research:
            kb.add_entry(
                CATEGORY.RESEARCH,
                {
                    "command": result["command"],
                    "subject": context.get("subject", ""),
                    "summary": research.get("executive_summary") or research.get("summary", ""),
                    "source_count": research.get("source_count", 0),
                    "providers_used": research.get("providers_used", []),
                    "important_facts": research.get("important_facts", []),
                },
                {"niche": result["niche"], "source": source},
            )
        for idea in result["ideas"]:
            metadata = {
                "niche": result["niche"],
                "source": source,
                "publish_score": idea.get("scores", {}).get("publish"),
            }
            if idea.get("hook"):
                kb.add_entry(CATEGORY.HOOKS, idea["hook"], metadata)
            if idea.get("title"):
                kb.add_entry(CATEGORY.TITLES, idea["title"], metadata)
            if idea.get("script"):
                kb.add_entry(CATEGORY.SCRIPTS, idea["script"], metadata)
            if idea.get("thumbnail_concept"):
                kb.add_entry(CATEGORY.THUMBNAILS, idea["thumbnail_concept"], metadata)
        for keyword in context.get("seo_keywords", []):
            kb.add_entry(CATEGORY.SEO_KEYWORDS, keyword, {"niche": result["niche"], "source": source})
    except OSError as exc:
        log_event(logger, "ideation.knowledge_record_failed", level=30, error=str(exc))


def _fallback_result(command: str, count: int, model: str, error: str) -> dict:
    """Guards against infrastructure bugs so the UI still gets a usable result."""
    from core import parsing
    from core.ai import GenerationRequest
    from core.ai.demo_provider import DemoProvider

    niche = parsing.detect_niche(command)
    subject = parsing.detect_subject(command, fallback=niche.lower())
    generation = DemoProvider().generate_ideas(
        GenerationRequest(command=command, niche=niche, subject=subject, count=count, model=model)
    )
    result = build_result(
        command=command,
        niche=niche,
        video_count=parsing.detect_video_count(command),
        goal=parsing.build_goal(subject),
        ideas=generation.ideas,
        demo_mode=True,
        model=model,
    )
    result["tokens_used"] = 0
    result["error"] = error or "Job execution failed."
    return result
