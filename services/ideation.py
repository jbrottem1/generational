"""Ideation service — turns a natural-language command into a content batch.

Public API for the UI. Internally, the command is submitted as a job to the
central JobQueue, which executes the "ideation" workflow through the
WorkflowEngine and the registered IdeationEngine. The job runs synchronously
today (Streamlit's execution model); moving it to a background worker later
changes nothing for callers.
"""

from __future__ import annotations

from core.jobs import get_queue
from core.log import get_logger, log_event
from core.models import build_result
from core.workflows import WORKFLOW_JOB_TYPE, ensure_workflow_handler

logger = get_logger(__name__)


def run_command(command: str, count: int, model: str) -> dict:
    """Parse a command and generate a content batch.

    Returns a result dict (see core.models.build_result) with extra transient
    "tokens_used" and, on fallback, "error" keys.
    """
    queue = get_queue()
    ensure_workflow_handler(queue)

    job = queue.submit(
        WORKFLOW_JOB_TYPE,
        {"workflow": "ideation", "context": {"command": command, "count": count, "model": model}},
    )
    job = queue.run(job.id)
    log_event(logger, "ideation.job_finished", job_id=job.id, status=job.status)

    if job.status != "succeeded":
        # The workflow layer never raises in normal operation; this guards
        # against infrastructure bugs so the UI still gets a usable result.
        from core.ai import GenerationRequest
        from core.ai.demo_provider import DemoProvider
        from core import parsing

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
        result["error"] = job.error or "Job execution failed."
        return result

    context = job.result["context"]
    result = build_result(
        command=command,
        niche=context["niche"],
        video_count=context["video_count"],
        goal=context["goal"],
        ideas=context["ideas"],
        demo_mode=context["demo_mode"],
        model=model,
    )
    result["tokens_used"] = context.get("tokens_used", 0)
    if context.get("error"):
        result["error"] = context["error"]
    return result
