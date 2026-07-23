"""Local-first production gate — prepare package then always proceed to render."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from services.generational_os.orchestrator import prepare_production
from services.media_production.execution_mode import (
    get_execution_context,
    local_status_message,
    write_execution_snapshot,
)


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
    """Write PRODUCTION_BRIEF + RENDER_PACKAGE, then authorize local render.

    ``allow_cloud_smoke`` is ignored (local-first — no cloud production path).
    """
    _ = (allow_cloud_smoke, render, image_ids)
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
        package_path=package_path
        if str(package_path).endswith("RENDER_PACKAGE.json")
        else Path("RENDER_PACKAGE.json"),
    )

    return {
        "proceed": True,
        "ok": True,
        "mode": ctx.mode.value,
        "status": "ready_to_render",
        "message": local_status_message(),
        "brief_path": prep.get("brief_path"),
        "render_package_path": prep.get("render_package_path"),
        "local_command": prep.get("local_command"),
        "export": prep.get("export"),
    }
