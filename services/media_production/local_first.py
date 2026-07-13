"""Local-first production gate — Generational OS V2.5 handoff."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from services.generational_os.orchestrator import prepare_production
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
    domain: str = "Biology",
    subject: str = "",
    series: str = "",
    episode: str = "",
) -> dict[str, Any]:
    """Cloud → PRODUCTION_BRIEF + RENDER_PACKAGE. Local → proceed to render."""
    write_execution_snapshot()
    ctx = get_execution_context()

    package_path = job_output or Path("RENDER_PACKAGE.json")
    prep = prepare_production(
        project_id=job_id,
        title=title,
        subject=subject or title,
        hook=hook,
        takeaway=takeaway,
        main_concept=main_concept,
        educational_objective=main_concept,
        demo_id=demo_id,
        filename=filename,
        beats=beats,
        domain=domain,
        series=series,
        episode=episode,
        sources=sources,
        package_path=package_path if str(package_path).endswith("RENDER_PACKAGE.json") else Path("RENDER_PACKAGE.json"),
    )

    if should_render_media(allow_cloud_smoke=allow_cloud_smoke) or prep.get("proceed"):
        return {
            "proceed": True,
            "mode": ctx.mode.value,
            "message": "Local render authorized.",
            "brief_path": prep.get("brief_path"),
            "render_package_path": prep.get("render_package_path"),
        }

    # Backward compatibility — also write LOCAL_RENDER_JOB.json
    legacy_job = build_render_job(
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
        output_path=Path("LOCAL_RENDER_JOB.json"),
    )
    legacy_path = write_render_job(legacy_job, Path("LOCAL_RENDER_JOB.json"))

    return {
        "proceed": False,
        "ok": True,
        "status": "awaiting_local_render",
        "message": cloud_status_message(),
        "mode": ctx.mode.value,
        "brief_path": prep.get("brief_path"),
        "render_package_path": prep.get("render_package_path"),
        "job_path": str(legacy_path.resolve()),
        "local_command": prep.get("local_command") or legacy_job.get("local_command"),
        "export": prep.get("export") or legacy_job.get("export"),
    }
