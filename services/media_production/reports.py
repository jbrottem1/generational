"""Production run reports — stored under data/reports/ for analytics."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
REPORTS_ROOT = ROOT / "data" / "reports"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def reports_root() -> Path:
    REPORTS_ROOT.mkdir(parents=True, exist_ok=True)
    return REPORTS_ROOT


def _write(kind: str, payload: dict[str, Any], run_id: str = "") -> str:
    rid = run_id or uuid4().hex[:12]
    folder = reports_root() / rid
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{kind}.json"
    doc = {"kind": kind, "run_id": rid, "created_at": _now(), **payload}
    path.write_text(json.dumps(doc, indent=2, default=str), encoding="utf-8")
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def write_production_report(result: dict, *, run_id: str = "") -> str:
    return _write(
        "production",
        {
            "workflow_run_id": result.get("workflow_run_id") or "",
            "workflow_status": result.get("workflow_status") or result.get("status") or "",
            "ideas": len(result.get("ideas") or []),
            "packages": len(result.get("unified_packages") or result.get("packages") or []),
            "stage_reports": result.get("stage_reports") or [],
            "error": result.get("error") or result.get("production_error") or "",
            "qc": result.get("qc") or {},
        },
        run_id=run_id or str(result.get("workflow_run_id") or "")[:24],
    )


def write_render_report(render_package: dict, *, run_id: str = "") -> str:
    return _write(
        "render",
        {
            "title": render_package.get("title") or "",
            "mock": bool(render_package.get("mock", True)),
            "mp4_path": render_package.get("mp4_path") or render_package.get("file_uri") or "",
            "duration_sec": render_package.get("duration_sec"),
            "resolution": render_package.get("resolution"),
            "render_status": render_package.get("render_status"),
            "warnings": render_package.get("render_warnings") or [],
            "log": render_package.get("render_log") or [],
            "assembly": render_package.get("assembly") or {},
        },
        run_id=run_id,
    )


def write_asset_report(assets: list, *, run_id: str = "") -> str:
    return _write(
        "assets",
        {
            "count": len(assets or []),
            "placeholders": sum(1 for a in (assets or []) if isinstance(a, dict) and a.get("placeholder")),
            "assets": assets or [],
        },
        run_id=run_id,
    )


def write_publishing_report(job: dict, *, run_id: str = "") -> str:
    return _write(
        "publishing",
        {
            "job_id": job.get("job_id") or "",
            "platform": job.get("platform") or "",
            "status": job.get("status") or "",
            "mode": job.get("publish_mode") or job.get("mode") or "",
            "last_error": job.get("last_error") or "",
            "attempts": job.get("attempts") or [],
        },
        run_id=run_id,
    )


def write_performance_report(metrics: dict, *, run_id: str = "") -> str:
    return _write(
        "performance",
        {
            "template": "performance_v1",
            "elapsed_sec": metrics.get("elapsed_sec"),
            "provider_calls": metrics.get("provider_calls"),
            "tokens_used": metrics.get("tokens_used"),
            "estimated_cost_usd": metrics.get("estimated_cost_usd"),
            "stage_timings": metrics.get("stage_timings") or {},
            "notes": metrics.get("notes") or [],
        },
        run_id=run_id,
    )


def write_full_report_bundle(
    result: dict,
    *,
    render_packages: list | None = None,
    assets: list | None = None,
    publish_jobs: list | None = None,
    metrics: dict | None = None,
) -> dict[str, str]:
    run_id = str(result.get("workflow_run_id") or uuid4().hex[:12])
    paths = {
        "production": write_production_report(result, run_id=run_id),
        "performance": write_performance_report(metrics or {}, run_id=run_id),
    }
    for index, render in enumerate(render_packages or []):
        paths[f"render_{index}"] = write_render_report(render, run_id=run_id)
    if assets is not None:
        paths["assets"] = write_asset_report(assets, run_id=run_id)
    for index, job in enumerate(publish_jobs or []):
        paths[f"publishing_{index}"] = write_publishing_report(job, run_id=run_id)
    return paths
