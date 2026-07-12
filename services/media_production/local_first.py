"""Local-first production gate — shared by all flagship render scripts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from services.media_production.execution_mode import (
    cloud_status_message,
    get_execution_context,
    should_render_media,
    write_execution_snapshot,
)
from services.media_production.local_render_job import build_render_job, write_render_job


def gate_production(
    *,
    job_id: str,
    title: str,
    demo_id: str,
    filename: str,
    hook: str,
    takeaway: str,
    main_concept: str,
    beats: list[dict[str, Any]],
    sources: list[str] | None = None,
    render: dict[str, Any] | None = None,
    image_ids: list[str] | None = None,
    job_output: Path | None = None,
    allow_cloud_smoke: bool = False,
) -> dict[str, Any]:
    """Cloud → write LOCAL_RENDER_JOB.json and stop. Local → allow render."""
    write_execution_snapshot()
    ctx = get_execution_context()

    if should_render_media(allow_cloud_smoke=allow_cloud_smoke):
        return {
            "proceed": True,
            "mode": ctx.mode.value,
            "message": "Local render authorized.",
        }

    job = build_render_job(
        job_id=job_id,
        title=title,
        demo_id=demo_id,
        filename=filename,
        hook=hook,
        takeaway=takeaway,
        main_concept=main_concept,
        beats=beats,
        sources=sources,
        render=render,
        image_ids=image_ids,
        output_path=job_output,
    )
    job_path = write_render_job(job, job_output)
    return {
        "proceed": False,
        "ok": True,
        "status": "awaiting_local_render",
        "message": cloud_status_message(),
        "mode": ctx.mode.value,
        "job_path": str(job_path.resolve()),
        "local_command": job.get("local_command"),
        "export": job.get("export"),
    }
