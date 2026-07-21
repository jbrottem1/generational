"""V1 Validation Program runner — real end-to-end productions via existing ops."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from core.log import get_logger, log_event
from services.validation_program.bottlenecks import build_recommendations, detect_bottlenecks
from services.validation_program.catalog import filter_catalog
from services.validation_program.dashboard import write_executive_dashboard
from services.validation_program.library import (
    LIB_ROOT,
    completed_validation_ids,
    ensure_library,
    store_validation,
)
from services.validation_program.scoring import score_validation_run

logger = get_logger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_validation_program(
    *,
    limit: int | None = None,
    offset: int = 0,
    categories: list[str] | None = None,
    skip_completed: bool = True,
    resume: bool = True,
    dry_ingest_ops_id: str | None = None,
) -> dict[str, Any]:
    """
    Produce / score validation videos using existing run_studio_ops.

    Architecture frozen — no new engines. Publishing stays off.
    """
    from services.production_operations import run_studio_ops

    ensure_library()
    catalog = filter_catalog(categories=categories, limit=limit, offset=offset)
    done = completed_validation_ids() if skip_completed else set()

    results: list[dict[str, Any]] = []
    log_event(logger, "validation_program.started", planned=len(catalog), already_done=len(done))

    # Optional: ingest an existing ops production without re-running
    if dry_ingest_ops_id:
        ingest = ingest_existing_production(dry_ingest_ops_id, validation_id=f"ingest_{dry_ingest_ops_id}")
        results.append(ingest)

    for brief in catalog:
        vid = brief["validation_id"]
        if resume and vid in done:
            log_event(logger, "validation_program.skip_completed", validation_id=vid)
            continue

        log_event(logger, "validation_program.production_started", validation_id=vid, topic=brief["topic"])
        ops = run_studio_ops(
            topic=brief["topic"],
            platform=brief["platform"],
            length_sec=int(brief["length_sec"]),
            style=brief.get("style") or "educational",
            narrator=brief.get("narrator") or brief.get("voice") or "professor",
            voice=brief.get("voice") or "default",
            quality_target=98,
            constraints={
                "audience": brief.get("audience") or "",
                "publishing_enabled": False,
                "validation_program": True,
                "category": brief["category"],
            },
            context={
                "candidate_count": 1,
                "video_count": 1,
                "validation_program": True,
                "domain": brief["category"],
                "category": brief["category"],
                "audience": brief.get("audience") or "",
                "publishing_enabled": False,
            },
        )
        if isinstance(ops.get("brief"), dict):
            ops["brief"]["domain"] = brief["category"]

        card = score_validation_run(ops, category=brief["category"])
        # Attach stage_ms into timing (already in card)
        status = ops.get("status") or {}
        if isinstance(status.get("stages"), list) and card.get("timing"):
            card["timing"]["stage_ms"] = {
                str(s.get("key")): int(s.get("duration_ms") or 0)
                for s in status["stages"]
                if isinstance(s, dict) and s.get("key")
            }

        opts = build_recommendations(
            {
                "sample_size": 1,
                "weakest_creative_modules": [
                    {"module": k, "average": v, "samples": 1}
                    for k, v in sorted((card.get("measurements") or {}).items(), key=lambda kv: kv[1])[:5]
                ],
                "slowest_modules": [
                    {"module": k, "average": v, "samples": 1}
                    for k, v in sorted(
                        ((card.get("timing") or {}).get("stage_ms") or {}).items(),
                        key=lambda kv: -kv[1],
                    )[:3]
                ],
                "common_rendering_problems": [
                    {"issue": f.get("error") or f.get("warning") or "", "count": 1}
                    for f in (card.get("failures") or [])
                    if (f.get("stage") in ("rendering", "export"))
                ],
            }
        )

        stored = store_validation(
            card,
            validation_id=vid,
            creative_director_review=str(card.get("creative_recommendation") or ""),
            audience_review=str(card.get("audience_lesson") or ""),
            optimization=opts,
        )
        results.append({"validation_id": vid, "card": card, "stored": stored})
        log_event(
            logger,
            "validation_program.production_finished",
            validation_id=vid,
            overall=card.get("overall_program_score"),
            success=card.get("success"),
        )

    bottlenecks = detect_bottlenecks()
    recommendations = build_recommendations(bottlenecks)
    dash_paths = write_executive_dashboard()

    summary = {
        "generated_at": _now(),
        "program": "V1 Validation Program",
        "planned_this_batch": len(catalog),
        "executed_this_batch": len(results),
        "library_total": len(completed_validation_ids()),
        "target": 100,
        "results": [
            {
                "validation_id": r.get("validation_id"),
                "topic": (r.get("card") or {}).get("topic"),
                "overall": (r.get("card") or {}).get("overall_program_score"),
                "success": (r.get("card") or {}).get("success"),
                "production_id": (r.get("card") or {}).get("production_id"),
            }
            for r in results
        ],
        "bottlenecks": bottlenecks,
        "recommendations": recommendations,
        "dashboard": {k: str(v) for k, v in dash_paths.items()},
        "library_root": str(LIB_ROOT),
        "architecture_frozen": True,
        "publishing_enabled": False,
    }
    summary_path = LIB_ROOT / "VALIDATION_PROGRAM_SUMMARY.json"
    summary_path.write_text(json.dumps(summary, indent=2, default=str) + "\n", encoding="utf-8")
    (LIB_ROOT / "VALIDATION_PROGRAM_REPORT.md").write_text(_format_summary_md(summary), encoding="utf-8")
    log_event(logger, "validation_program.batch_complete", executed=len(results), library=summary["library_total"])
    return summary


def ingest_existing_production(production_id: str, *, validation_id: str = "", category: str = "biology") -> dict[str, Any]:
    """Score an existing ops production into the library without re-running."""
    from pathlib import Path

    from services.production_operations.status import ops_dir

    root = ops_dir(production_id)
    report_path = root / "PRODUCTION_REPORT.json"
    status_path = root / "PRODUCTION_OPS_STATUS.json"
    report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {}
    status = json.loads(status_path.read_text(encoding="utf-8")) if status_path.exists() else {}
    brief = status.get("brief") or {"topic": report.get("topic"), "domain": category}
    ops = {
        "production_id": production_id,
        "success": status.get("success"),
        "report": report,
        "status": status,
        "brief": brief,
        "context": {
            "creative_excellence": {
                "creative_excellence_score": report.get("creative_excellence_score"),
                "single_recommendation": {"recommendation": report.get("creative_recommendation")},
            },
            "audience_intelligence_review": {
                "highest_impact_improvement": report.get("audience_intelligence_lesson"),
                "path": report.get("audience_intelligence_review_path"),
            },
        },
        "elapsed_ms": status.get("elapsed_ms"),
    }
    vid = validation_id or f"ingest_{production_id}"
    card = score_validation_run(ops, category=category or brief.get("domain") or "general")
    if isinstance(status.get("stages"), list):
        card.setdefault("timing", {})["stage_ms"] = {
            str(s.get("key")): int(s.get("duration_ms") or 0)
            for s in status["stages"]
            if isinstance(s, dict)
        }
    opts = build_recommendations(detect_bottlenecks([{"measurements": card.get("measurements"), "metrics": card.get("timing"), "failures": card.get("failures"), "success": card.get("success")}]))
    stored = store_validation(
        card,
        validation_id=vid,
        creative_director_review=str(card.get("creative_recommendation") or ""),
        audience_review=str(card.get("audience_lesson") or ""),
        optimization=opts,
    )
    return {"validation_id": vid, "card": card, "stored": stored}


def _format_summary_md(summary: dict[str, Any]) -> str:
    lines = [
        "# V1 Validation Program Report",
        "",
        f"**Generated:** {summary.get('generated_at')}",
        f"**Library total:** {summary.get('library_total')} / {summary.get('target')}",
        f"**This batch:** {summary.get('executed_this_batch')}",
        "",
        "## Batch results",
        "",
    ]
    for r in summary.get("results") or []:
        lines.append(
            f"- `{r.get('validation_id')}` · {r.get('topic')} · score={r.get('overall')} · success={r.get('success')}"
        )
    lines += ["", "## Top recommendations", ""]
    for rec in (summary.get("recommendations") or [])[:5]:
        lines.append(f"### {rec.get('priority')}: {rec.get('problem')}")
        lines.append(f"- Evidence: {rec.get('evidence')}")
        lines.append(f"- Expected: {rec.get('expected_improvement')}")
        lines.append(f"- Impact: {rec.get('estimated_impact')}")
        lines.append("")
    lines += ["_Architecture frozen. No automatic redesign._", ""]
    return "\n".join(lines)
