"""Long-form chapter / scene-group helpers (Agent 23)."""

from __future__ import annotations

from services.autonomous_production.modes import build_chapters, build_scene_groups, mode_defaults
from services.autonomous_production.models import ProductionJob


def prepare_longform_plan(job: ProductionJob) -> ProductionJob:
    """Attach chapters + scene groups when the mode is long-form."""
    defaults = mode_defaults(job.production_mode)
    if not (job.context.longform or defaults.get("longform")):
        if not job.context.chapters:
            job.context.chapters = build_chapters(
                job.command, job.production_mode, unit_count=1
            )
        return job

    unit_count = int(job.context.options.get("unit_count") or defaults.get("unit_count", 1))
    chapters = job.context.chapters or build_chapters(
        job.command, job.production_mode, unit_count=unit_count
    )
    job.context.chapters = chapters
    job.context.scene_groups = job.context.scene_groups or build_scene_groups(chapters)
    job.manifest.chapters = list(chapters)
    job.manifest.scene_groups = list(job.context.scene_groups)
    job.manifest.unit_count = len(chapters)
    job.context.longform = True
    return job


def mark_chapter_status(job: ProductionJob, index: int, status: str) -> None:
    for ch in job.context.chapters:
        if ch.get("index") == index:
            ch["status"] = status
            break
    for sg in job.context.scene_groups:
        if sg.get("chapter_index") == index:
            sg["status"] = status
            break


def chapter_summaries(job: ProductionJob) -> list[dict]:
    return [
        {
            "index": ch.get("index"),
            "title": ch.get("title"),
            "status": ch.get("status", "pending"),
            "estimated_duration_sec": ch.get("estimated_duration_sec", 0),
            "workflow_run_id": ch.get("workflow_run_id", ""),
            "job_id": ch.get("job_id", ""),
        }
        for ch in job.context.chapters
    ]


def should_split_units(job: ProductionJob) -> bool:
    """Whether this job should fan out into parallel/serial child units."""
    defaults = mode_defaults(job.production_mode)
    if job.context.options.get("force_single_unit"):
        return False
    if len(job.context.chapters) <= 1:
        return False
    # Multi-unit modes (course, series, campaign) split; single documentary
    # with segment chapters stays one workflow run with incremental checkpoints.
    if job.production_mode in (
        "course",
        "educational_program",
        "video_series",
        "marketing_campaign",
    ):
        return True
    return bool(defaults.get("parallel_units")) and len(job.context.chapters) > 1
