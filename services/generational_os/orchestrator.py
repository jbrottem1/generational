"""Generational OS orchestrator — brief → package → local handoff."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from services.generational_os.brief import build_production_brief, write_production_brief
from services.generational_os.dashboard import write_dashboard
from services.generational_os.render_package import build_render_package, write_render_package
from services.media_production.execution_mode import get_execution_context, should_render_media


def prepare_production(
    *,
    project_id: str,
    title: str,
    subject: str,
    hook: str,
    takeaway: str,
    main_concept: str,
    educational_objective: str,
    demo_id: str,
    filename: str,
    beats: list[dict[str, Any]],
    domain: str = "",
    series: str = "",
    episode: str = "",
    sources: list[str] | None = None,
    brief_path: Path | None = None,
    package_path: Path | None = None,
) -> dict[str, Any]:
    """Cloud path: Intelligence + Pre-Production artifacts. Local: signals proceed."""
    brief = build_production_brief(
        project_id=project_id,
        title=title,
        subject=subject,
        hook=hook,
        takeaway=takeaway,
        main_concept=main_concept,
        educational_objective=educational_objective,
        domain=domain,
        series=series,
        episode=episode,
        sources=sources,
    )
    brief_out = write_production_brief(brief, brief_path)

    package = build_render_package(
        project_id=project_id,
        title=title,
        demo_id=demo_id,
        filename=filename,
        hook=hook,
        takeaway=takeaway,
        main_concept=main_concept,
        beats=beats,
        domain=domain,
        subject=subject,
        series=series,
        sources=sources,
    )
    package_out = write_render_package(package, package_path)
    write_dashboard()

    ctx = get_execution_context()
    if should_render_media():
        return {
            "proceed": True,
            "mode": ctx.mode.value,
            "brief_path": str(brief_out),
            "render_package_path": str(package_out),
            "message": "Local render authorized.",
        }

    return {
        "proceed": False,
        "ok": True,
        "status": "awaiting_local_render",
        "message": "Production package prepared. Awaiting local render.",
        "mode": ctx.mode.value,
        "brief_path": str(brief_out),
        "render_package_path": str(package_out),
        "local_command": package.get("local_command"),
        "export": package.get("export"),
    }
