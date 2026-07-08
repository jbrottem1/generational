"""Media Production service — orchestrates the production pipeline for approved content.

Runs AFTER the intelligence pipeline completes. Only publishable (approved)
scripts enter the media production workflow. The intelligence workflow itself
is never modified.
"""

from __future__ import annotations

from core.jobs import get_queue
from core.log import get_logger, log_event
from core.production_models import stage_statuses_from_steps
from core.workflows import WORKFLOW_JOB_TYPE, ensure_workflow_handler

logger = get_logger(__name__)

INTELLIGENCE_STAGE_DEFS = [
    ("research", "Research"),
    ("ideation", "Ideas"),
    ("psychology", "Psychology"),
    ("ranking", "Ranking"),
    ("script", "Scripts"),
    ("critic", "Critic"),
    ("revision", "Revision"),
    ("citation", "Citation"),
    ("seo", "SEO"),
    ("quality", "Quality Gate"),
]

PRODUCTION_STAGE_DEFS = [
    ("scene_planning", "Scene Planning"),
    ("narration", "Narration"),
    ("visual_planning", "Visuals"),
    ("asset_manager", "Assets"),
    ("subtitle", "Subtitles"),
    ("timeline", "Timeline"),
    ("render_package", "Render Package"),
    ("publishing_queue", "Publishing Queue"),
]


def _prepare_approved(ideas: list) -> list:
    """Only scripts that passed the quality gate enter production."""
    approved = []
    for idea in ideas:
        if not idea.get("publishable"):
            continue
        entry = dict(idea)
        entry.setdefault("thumbnail_concept", idea.get("thumbnail_concept", ""))
        approved.append(entry)
    return approved


def run_media_production(context: dict) -> dict:
    """Execute the media_production workflow for approved scripts in context."""
    approved = _prepare_approved(context.get("ideas", []))
    if not approved:
        log_event(logger, "production.skipped", reason="no_approved_content")
        return {
            "production_packages": [],
            "production_steps": [],
            "production_dashboard": _build_dashboard(context.get("pipeline_steps", []), []),
            "production_skipped": True,
        }

    prod_context = {
        "command": context.get("command", ""),
        "niche": context.get("niche", ""),
        "subject": context.get("subject", ""),
        "model": context.get("model", ""),
        "approved_content": approved,
        "voice_mode": context.get("voice_mode", "ai"),
        "voice_profile_id": context.get("voice_profile_id", ""),
        "target_platform": context.get("target_platform", "youtube_shorts"),
    }

    queue = get_queue()
    ensure_workflow_handler(queue)
    job = queue.submit(WORKFLOW_JOB_TYPE, {"workflow": "media_production", "context": prod_context})
    job = queue.run(job.id)

    if job.status != "succeeded":
        log_event(logger, "production.failed", error=job.error)
        return {
            "production_packages": [],
            "production_steps": job.result.get("run", {}).get("steps", []) if job.result else [],
            "production_dashboard": _build_dashboard(context.get("pipeline_steps", []), []),
            "production_error": job.error,
        }

    result_ctx = job.result["context"]
    prod_steps = job.result["run"]["steps"]
    packages = result_ctx.get("production_packages", [])

    _attach_packages_to_ideas(context.get("ideas", []), packages)

    log_event(logger, "production.completed", packages=len(packages), queued=result_ctx.get("queued_count", 0))
    return {
        "production_packages": packages,
        "production_steps": prod_steps,
        "production_dashboard": _build_dashboard(context.get("pipeline_steps", []), prod_steps),
        "queued_count": result_ctx.get("queued_count", 0),
    }


def _attach_packages_to_ideas(ideas: list, packages: list) -> None:
    by_title = {p.get("title"): p for p in packages}
    for idea in ideas:
        if not idea.get("publishable"):
            continue
        pkg = by_title.get(idea.get("title"))
        if pkg:
            idea["production"] = {
                "content_id": pkg.get("content_id"),
                "scenes": len(pkg.get("scenes", [])),
                "duration_sec": pkg.get("timeline", {}).get("duration_sec", 0),
                "render_package_id": pkg.get("render_package", {}).get("package_id", ""),
                "queue_status": pkg.get("queue_status", ""),
                "assets": len(pkg.get("assets", [])),
            }


def _build_dashboard(intelligence_steps: list, production_steps: list) -> list:
    intel = stage_statuses_from_steps(intelligence_steps or [], INTELLIGENCE_STAGE_DEFS)
    prod = stage_statuses_from_steps(production_steps or [], PRODUCTION_STAGE_DEFS)
    if not production_steps:
        for item in prod:
            item["state"] = "waiting"
    return intel + prod


def full_pipeline_stage_defs() -> list:
    return INTELLIGENCE_STAGE_DEFS + PRODUCTION_STAGE_DEFS
