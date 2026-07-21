"""Production Validation Suite — real content runs via existing ops pipeline."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.log import get_logger, log_event
from services.production_validation.catalog import DOMAIN_PRODUCTIONS
from services.production_validation.compare import load_baseline_suite, write_comparison_report
from services.production_validation.evaluate import aggregate_weaknesses, evaluate_production
from services.production_validation.roadmap import write_improvement_roadmap

logger = get_logger(__name__)

ROOT = Path(__file__).resolve().parents[2]
OUT_ROOT = ROOT / "data" / "productions" / "_validation" / "content_validation"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_validation_suite(
    *,
    domains: list[str] | None = None,
    limit: int | None = None,
    platform_override: str | None = None,
) -> dict[str, Any]:
    """Produce real videos across domains and evaluate publishing readiness."""
    # Lazy import avoids circular import via engines → workflows at package load.
    from services.production_operations import run_studio_ops

    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    baseline_path = OUT_ROOT / "CONTENT_VALIDATION_BASELINE.json"
    suite_path = OUT_ROOT / "CONTENT_VALIDATION_SUITE.json"
    # Freeze first full suite as baseline for before/after comparisons.
    if suite_path.exists() and not baseline_path.exists():
        baseline_path.write_text(suite_path.read_text(encoding="utf-8"), encoding="utf-8")
    before = load_baseline_suite(OUT_ROOT)
    briefs = list(DOMAIN_PRODUCTIONS)
    if domains:
        wanted = {d.lower() for d in domains}
        briefs = [b for b in briefs if b["domain"] in wanted]
    if limit is not None:
        briefs = briefs[: max(0, int(limit))]

    evaluations: list[dict] = []
    log_event(logger, "content_validation.started", domains=len(briefs))

    for brief in briefs:
        log_event(logger, "content_validation.production_started", domain=brief["domain"], topic=brief["topic"])
        result = run_studio_ops(
            topic=brief["topic"],
            platform=platform_override or brief["platform"],
            length_sec=int(brief["length_sec"]),
            style=brief.get("style") or "educational",
            narrator=brief.get("voice") or "professor",
            voice=brief.get("voice") or "default",
            quality_target=98,
            constraints={"audience": brief.get("audience") or ""},
            # One finished video per domain — validation is content-quality, not ideation breadth.
            context={
                "candidate_count": 1,
                "video_count": 1,
                "content_validation": True,
                "domain": brief["domain"],
                "audience": brief.get("audience") or "",
            },
        )
        # Stamp domain onto brief for evaluation
        if isinstance(result.get("brief"), dict):
            result["brief"]["domain"] = brief["domain"]
            result["brief"].setdefault("constraints", {})["audience"] = brief.get("audience")
        evaluation = evaluate_production(result)
        evaluation["domain"] = brief["domain"]
        evaluation["audience"] = brief.get("audience")
        evaluation["input"] = {
            "topic": brief["topic"],
            "platform": platform_override or brief["platform"],
            "length_sec": brief["length_sec"],
            "style": brief.get("style"),
            "audience": brief.get("audience"),
            "voice": brief.get("voice"),
        }
        evaluations.append(evaluation)
        log_event(
            logger,
            "content_validation.production_finished",
            domain=brief["domain"],
            overall=evaluation["scores"]["overall_production_score"],
            publish_ready=evaluation["publish_ready"],
            weaknesses=len(evaluation["weaknesses"]),
        )

    weakness_rank = aggregate_weaknesses(evaluations)
    averages = _average_scores(evaluations)
    publishable = sum(1 for e in evaluations if e.get("publish_ready"))
    summary = {
        "generated_at": _now(),
        "version": "1.0.0",
        "productions": len(evaluations),
        "publish_ready_count": publishable,
        "publish_ready_pct": round(100.0 * publishable / max(len(evaluations), 1), 1),
        "average_scores": averages,
        "weakness_ranking": weakness_rank,
        "evaluations": evaluations,
    }

    suite_path = OUT_ROOT / "CONTENT_VALIDATION_SUITE.json"
    suite_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    roadmap_path = write_improvement_roadmap(summary, OUT_ROOT)

    compare_path = None
    if before and before.get("average_scores"):
        compare_path = write_comparison_report(before=before, after=summary, out_dir=OUT_ROOT)

    md = OUT_ROOT / "CONTENT_VALIDATION_REPORT.md"
    md.write_text(_markdown_report(summary), encoding="utf-8")

    log_event(
        logger,
        "content_validation.finished",
        productions=len(evaluations),
        publish_ready_pct=summary["publish_ready_pct"],
        top_weakness=(weakness_rank[0]["label"] if weakness_rank else "none"),
        overall=(summary.get("average_scores") or {}).get("overall_production_score"),
    )
    return {
        **summary,
        "suite_path": str(suite_path),
        "report_path": str(md),
        "roadmap_path": str(roadmap_path),
        "comparison_path": str(compare_path) if compare_path else None,
        "baseline_overall": (before.get("average_scores") or {}).get("overall_production_score") if before else None,
    }


def _average_scores(evaluations: list[dict]) -> dict[str, float]:
    if not evaluations:
        return {}
    keys = list((evaluations[0].get("scores") or {}).keys())
    out = {}
    for k in keys:
        vals = [float((e.get("scores") or {}).get(k) or 0) for e in evaluations]
        out[k] = round(sum(vals) / len(vals), 2)
    return out


def _markdown_report(summary: dict) -> str:
    lines = [
        "# Content Validation Report",
        "",
        f"Generated: {summary.get('generated_at')}",
        f"Productions: **{summary.get('productions')}**",
        f"Publish-ready: **{summary.get('publish_ready_count')}** ({summary.get('publish_ready_pct')}%)",
        "",
        "## Average scores",
    ]
    for k, v in (summary.get("average_scores") or {}).items():
        lines.append(f"- {k}: {v}")
    lines.extend(["", "## Productions", ""])
    for e in summary.get("evaluations") or []:
        lines.append(
            f"- **{e.get('domain')}** — {e.get('topic')} → "
            f"overall {e.get('scores', {}).get('overall_production_score')} "
            f"| ready={e.get('publish_ready')} | weaknesses={len(e.get('weaknesses') or [])}"
        )
    lines.extend(["", "## Weaknesses (ranked by impact)", ""])
    for w in summary.get("weakness_ranking") or []:
        lines.append(
            f"{w.get('rank')}. **{w.get('label')}** "
            f"(impact {w.get('impact')}, seen {w.get('count')}×, avg score {w.get('avg_score')})"
        )
    lines.append("")
    return "\n".join(lines)
