"""Executive operating dashboard — centralized production visibility."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.env import project_root
from services.generational_os.database import list_productions
from services.generational_os.improvement import analyze_improvements
from services.media_production.execution_mode import get_execution_context


def _cache_health_inline() -> dict[str, Any]:
    index = project_root() / "data" / "local_cache" / "index.json"
    reg = project_root() / "data" / "generational_os" / "asset_registry.json"
    entry_count = 0
    if index.is_file():
        entry_count = len(json.loads(index.read_text()).get("entries") or {})
    lib_counts = {}
    if reg.is_file():
        libs = json.loads(reg.read_text()).get("libraries") or {}
        lib_counts = {k: len(v) for k, v in libs.items()}
    return {"cached_assets": entry_count, "registry_libraries": lib_counts}


DASHBOARD_JSON = project_root() / "data" / "generational_os" / "dashboard.json"
DASHBOARD_MD = project_root() / "EXECUTIVE_OPERATING_DASHBOARD.md"


def _bucket(productions: list[dict[str, Any]], key: str, value: str) -> list[dict[str, Any]]:
    return [p for p in productions if p.get(key) == value]


def build_operating_dashboard() -> dict[str, Any]:
    ctx = get_execution_context()
    productions = list_productions()
    qc_scores = [float(p["qc_score"]) for p in productions if p.get("qc_score") is not None]
    render_times = [
        float(p["render_duration_sec"])
        for p in productions
        if p.get("render_duration_sec") is not None
    ]

    verified = _bucket(productions, "local_render_status", "verified")
    failed = [p for p in productions if p.get("local_render_status") == "failed"]
    awaiting = _bucket(productions, "local_render_status", "awaiting_local_render")

    dashboard = {
        "schema_version": 1,
        "os_version": "2.5",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "execution_context": ctx.to_dict(),
        "queues": {
            "active_productions": len(productions),
            "research_queue": _bucket(productions, "pipeline_stage", "research"),
            "script_queue": _bucket(productions, "pipeline_stage", "script"),
            "render_queue": awaiting,
            "local_render_status": {
                "awaiting": len(awaiting),
                "verified": len(verified),
                "failed": len(failed),
            },
            "qc_status": _bucket(productions, "publishing_status", "qc_failed"),
            "ready_for_review": _bucket(productions, "publishing_status", "ready_for_review"),
            "ready_to_publish": _bucket(productions, "publishing_status", "ready_to_publish"),
            "published": _bucket(productions, "publishing_status", "published"),
            "failed_productions": failed,
            "experimental": _bucket(productions, "publishing_status", "experimental"),
        },
        "metrics": {
            "average_qc_score": round(sum(qc_scores) / len(qc_scores), 1) if qc_scores else None,
            "average_render_sec": round(sum(render_times) / len(render_times), 1) if render_times else None,
            "production_success_rate": round(len(verified) / max(1, len(productions)), 3),
            "total_productions": len(productions),
        },
        "system_health": {
            "asset_cache": _cache_health_inline(),
            "execution_mode": ctx.mode.value,
            "can_render_locally": ctx.can_render_media,
        },
        "improvements": analyze_improvements(productions),
        "productions": productions[:50],
    }
    return dashboard


def write_dashboard(path: Path | None = None) -> Path:
    dash = build_operating_dashboard()
    out = path or DASHBOARD_JSON
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dash, indent=2), encoding="utf-8")

    lines = [
        "# Executive Operating Dashboard — Generational OS V2.5",
        "",
        f"**Generated:** {dash['generated_at']}",
        f"**Execution mode:** {dash['execution_context']['mode']}",
        "",
        "## Queues",
        "",
        f"- Active productions: **{dash['queues']['active_productions']}**",
        f"- Awaiting local render: **{dash['queues']['local_render_status']['awaiting']}**",
        f"- Verified exports: **{dash['queues']['local_render_status']['verified']}**",
        f"- Ready for review: **{len(dash['queues']['ready_for_review'])}**",
        f"- Failed: **{len(dash['queues']['failed_productions'])}**",
        "",
        "## Metrics",
        "",
        f"- Average QC score: {dash['metrics']['average_qc_score']}",
        f"- Success rate: {dash['metrics']['production_success_rate']}",
        "",
        "## Top improvements",
        "",
    ]
    for i, rec in enumerate(dash.get("improvements") or [], 1):
        lines.append(f"{i}. {rec}")
    DASHBOARD_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out
