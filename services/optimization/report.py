"""Optimization Report — one machine- and human-readable summary per run.

Aggregates everything the laboratory did: experiments run, variants
generated, winning and losing variants, confidence, expected performance
lift, per-type experiment summaries, historical trends from the learning
bridge, and every recommendation issued (OPTIMIZATION_REPORT_FIELDS).
"""

from __future__ import annotations

from datetime import datetime, timezone

from services.optimization.learning_bridge import historical_trend_summary
from services.optimization.models import (
    OPTIMIZATION_ENGINE_VERSION,
    OPTIMIZATION_REPORT_VERSION,
    ExperimentStatus,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _variant_summary(variant: dict, experiment: dict) -> dict:
    return {
        "variant_id": variant.get("variant_id", ""),
        "label": variant.get("label", ""),
        "experiment_type": experiment.get("experiment_type", ""),
        "experiment_id": experiment.get("experiment_id", ""),
        "score": variant.get("score", 0),
        "confidence": experiment.get("result", {}).get("confidence", 0),
    }


def build_optimization_report(
    experiments: list,
    recommendations: list,
    items: int,
    warnings: "list | None" = None,
    historical_trends: "list | None" = None,
) -> dict:
    """The OPTIMIZATION_REPORT_FIELDS dict for one laboratory run."""
    winners, losers = [], []
    variants_generated = 0
    summary: dict = {}
    lifts = []

    for experiment in experiments:
        experiment_type = experiment.get("experiment_type", "unknown")
        entry = summary.setdefault(
            experiment_type,
            {"experiments": 0, "completed": 0, "low_confidence": 0, "failed": 0},
        )
        entry["experiments"] += 1
        variants_generated += len(experiment.get("variant_group", {}).get("variants", []))

        status = experiment.get("status", "")
        if status == ExperimentStatus.COMPLETED:
            entry["completed"] += 1
        elif status == ExperimentStatus.LOW_CONFIDENCE:
            entry["low_confidence"] += 1
        elif status == ExperimentStatus.FAILED:
            entry["failed"] += 1

        result = experiment.get("result", {})
        if result.get("winner"):
            winners.append(_variant_summary(result["winner"], experiment))
            lifts.append(float(result.get("expected_lift", 0)))
        for loser in result.get("losers", [])[-2:]:
            losers.append(_variant_summary(loser, experiment))

    confidences = [r["confidence"] for r in recommendations]
    status = "no_items" if not items else ("optimized" if recommendations else "partial")

    return {
        "report_version": OPTIMIZATION_REPORT_VERSION,
        "engine_version": OPTIMIZATION_ENGINE_VERSION,
        "status": status,
        "items": items,
        "experiments_run": len(experiments),
        "variants_generated": variants_generated,
        "winning_variants": winners,
        "losing_variants": losers,
        "average_confidence": int(round(sum(confidences) / len(confidences))) if confidences else 0,
        "expected_lift": round(sum(lifts) / len(lifts), 2) if lifts else 0.0,
        "experiment_summary": summary,
        "historical_trends": (
            historical_trends if historical_trends is not None else historical_trend_summary()
        ),
        "recommendations": recommendations,
        "warnings": list(warnings or []),
        "generated_at": _now_iso(),
    }


def render_report_text(report: dict) -> str:
    """A human-readable rendering of one Optimization Report."""
    lines = [
        f"Optimization Report v{report.get('report_version', '')} — {report.get('status', '')}",
        f"Items: {report.get('items', 0)} · Experiments: {report.get('experiments_run', 0)} · "
        f"Variants: {report.get('variants_generated', 0)}",
        f"Average confidence: {report.get('average_confidence', 0)} · "
        f"Expected lift: {report.get('expected_lift', 0):+.2f}",
        "",
        "Winning variants:",
    ]
    for winner in report.get("winning_variants", [])[:10]:
        lines.append(
            f"  • [{winner['experiment_type']}] {winner['label']} "
            f"(score {winner['score']}, confidence {winner['confidence']})"
        )
    if report.get("historical_trends"):
        lines.append("")
        lines.append("Historical trends:")
        for trend in report["historical_trends"][:5]:
            lines.append(
                f"  • {trend['dimension']}={trend['value']} "
                f"(lift {trend['lift']:+.1f}, confidence {trend['confidence']})"
            )
    if report.get("warnings"):
        lines.append("")
        lines.append("Warnings:")
        lines.extend(f"  • {warning}" for warning in report["warnings"][:10])
    return "\n".join(lines)
