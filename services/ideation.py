"""Ideation service — runs the v2.0 intelligence pipeline for the UI.

Submits the command as a job to the central JobQueue, which executes the
"intelligence" workflow (research → candidates → psychology → ranking →
scripts → critic → revision → SEO → quality gate) through the WorkflowEngine.
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
            "context": {"command": command, "count": count, "model": model, "threshold": threshold},
        },
    )
    job = queue.run(job.id)
    log_event(logger, "ideation.job_finished", job_id=job.id, status=job.status)

    if job.status != "succeeded":
        return _fallback_result(command, count, model, job.error)

    context = job.result["context"]
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
    result["quality_summary"] = context.get("quality_summary", {})
    result["pipeline_steps"] = job.result["run"]["steps"]
    result["tokens_used"] = context.get("tokens_used", 0)
    if context.get("error"):
        result["error"] = context["error"]

    _record_knowledge(result, context)
    return result


def _record_knowledge(result: dict, context: dict) -> None:
    """Feed final assets into the Knowledge Base for the future learning engine."""
    from services.knowledge import CATEGORY, get_knowledge_base

    kb = get_knowledge_base()
    source = "demo" if result["demo_mode"] else "openai"
    try:
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
