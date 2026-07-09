"""Production Report — the single unified diagnostic of a full pipeline run.

`build_production_report()` folds one `PipelineResult` into one JSON-safe
dict that answers, in one place: what ran, in what order, with what status,
what every engine contributed, what content came out, and every warning or
error the run produced. Agent 9's integration contract:

- One report per `run_full_pipeline()` call, attached to
  `PipelineResult.production_report` (and to `to_dict()`).
- The report is diagnostics only — it never mutates the context and never
  raises; a report is produced even for FAILED runs.
- Additive evolution: future sections are appended, existing keys are never
  renamed or removed.
"""

from __future__ import annotations

from datetime import datetime, timezone

from engines import registry
from services.orchestrator.models import StageStatus

PRODUCTION_REPORT_VERSION = "1.0.0"

# The eight production areas of the integrated workflow (mission order),
# mapped onto the orchestrator stage names that implement each of them.
PRODUCTION_WORKFLOW = (
    ("trend_discovery", ("trend",)),
    ("psychology", ("psychology",)),
    ("script_generation", ("script",)),
    ("visual_intelligence", ("visual",)),
    ("voice_audio", ("audio",)),
    ("render", ("render",)),
    ("seo_optimization", ("seo",)),
    ("publishing", ("publish",)),
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _engine_inventory(stage_reports: list) -> list:
    """Availability + readiness for every engine the run touched."""
    keys: "list[str]" = []
    for report in stage_reports:
        for step in report.diagnostics.get("steps", []):
            if step["engine"] not in keys:
                keys.append(step["engine"])

    inventory = []
    for key in keys:
        engine = registry.get_engine(key)
        if engine is None:
            inventory.append({"engine": key, "available": False, "ready": False, "version": ""})
            continue
        entry = {
            "engine": key,
            "label": getattr(engine, "label", "") or key,
            "available": True,
            "ready": bool(engine.is_ready()),
            "version": getattr(engine, "version", ""),
        }
        diagnostics = getattr(engine, "diagnostics", None)
        if callable(diagnostics):
            try:
                contract = diagnostics()
                entry["input_contract"] = contract.get("input_contract", [])
                entry["output_contract"] = contract.get("output_contract", [])
            except Exception:  # noqa: BLE001 - diagnostics must never break reporting
                pass
        inventory.append(entry)
    return inventory


def _workflow_section(stage_reports: list) -> list:
    """The eight production areas, each resolved to its stage outcome."""
    by_stage = {report.stage: report for report in stage_reports}
    section = []
    for area, stage_names in PRODUCTION_WORKFLOW:
        reports = [by_stage[name] for name in stage_names if name in by_stage]
        if not reports:
            section.append({"area": area, "status": StageStatus.SKIPPED, "stages": list(stage_names)})
            continue
        statuses = {report.status for report in reports}
        if StageStatus.FAILED in statuses:
            status = StageStatus.FAILED
        elif StageStatus.WARNING in statuses:
            status = StageStatus.WARNING
        else:
            status = StageStatus.SUCCESS
        section.append(
            {
                "area": area,
                "status": status,
                "stages": [report.stage for report in reports],
                "confidence": max((report.confidence for report in reports), default=0),
                "warnings": [w for report in reports for w in report.warnings],
                "errors": [e for report in reports for e in report.errors],
            }
        )
    return section


def _content_section(result) -> dict:
    context = result.context
    packages = result.packages
    render_summary = context.get("render_summary", {})
    seo_report = context.get("seo_optimization_report", {})
    publishing_result = context.get("publishing_result", {})
    return {
        "ideas": len(context.get("ideas", [])),
        "packages": len(packages),
        "publish_ready": sum(1 for pkg in packages if pkg.publish_ready),
        "package_statuses": _histogram(pkg.status for pkg in packages),
        "render": {
            "status": render_summary.get("status", ""),
            "rendered": render_summary.get("rendered", 0),
            "average_readiness": render_summary.get("average_readiness", 0),
        },
        "optimization": {
            "status": seo_report.get("status", ""),
            "items": seo_report.get("items", 0),
            "overall_optimization_score": seo_report.get("overall_optimization_score", 0),
            "publishing_packages": len(context.get("publishing_packages", [])),
        },
        "publishing": {
            "status": publishing_result.get("status", ""),
            "publish_mode": publishing_result.get("publish_mode", ""),
            "jobs_created": publishing_result.get("jobs_created", 0),
            "published": publishing_result.get("published", 0),
            "scheduled": publishing_result.get("scheduled", 0),
            "failed": publishing_result.get("failed", 0),
            "platforms": publishing_result.get("platforms", []),
            "schedule_entries": len(context.get("publish_schedule", [])),
        },
    }


def _histogram(values) -> dict:
    counts: dict = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return counts


def build_production_report(result) -> dict:
    """One Production Report for one PipelineResult — never raises."""
    try:
        stage_reports = result.stage_reports
        warnings = [f"{r.stage}: {w}" for r in stage_reports for w in r.warnings]
        errors = [f"{r.stage}: {e}" for r in stage_reports for e in r.errors]
        return {
            "report_version": PRODUCTION_REPORT_VERSION,
            "generated_at": _now_iso(),
            "command": result.context.get("command", ""),
            "status": result.status,
            "error": result.error,
            "duration_ms": sum(r.duration_ms for r in stage_reports),
            "workflow": _workflow_section(stage_reports),
            "stages": [r.to_dict() for r in stage_reports],
            "engines": _engine_inventory(stage_reports),
            "content": _content_section(result),
            "warnings": warnings,
            "errors": errors,
        }
    except Exception as exc:  # noqa: BLE001 - reporting must never break the pipeline
        return {
            "report_version": PRODUCTION_REPORT_VERSION,
            "generated_at": _now_iso(),
            "status": getattr(result, "status", StageStatus.FAILED),
            "error": f"Production report generation failed safely: {exc}",
            "workflow": [],
            "stages": [],
            "engines": [],
            "content": {},
            "warnings": [],
            "errors": [f"report: {exc}"],
        }
