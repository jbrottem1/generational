"""Learning loop — compare PQA predicted metrics to post-publish actuals."""

from __future__ import annotations

from typing import Any

from core.log import get_logger, log_event
from services.production_qa.store import load_recent_reports, store_report

logger = get_logger(__name__)


def extract_predicted_metrics(report: dict[str, Any]) -> dict[str, float]:
    predicted = dict(report.get("predicted_metrics") or {})
    psych = (report.get("categories") or {}).get("psychology") or {}
    details = psych.get("details") if isinstance(psych, dict) else {}
    if isinstance(details, dict) and details.get("predicted_metrics"):
        predicted = {**details["predicted_metrics"], **predicted}
    out: dict[str, float] = {}
    for key in (
        "ctr",
        "avg_watch_time_sec",
        "drop_off_risk",
        "shareability",
        "replay_probability",
        "subscriber_conversion",
    ):
        if key in predicted and predicted[key] is not None:
            try:
                out[key] = float(predicted[key])
            except (TypeError, ValueError):
                continue
    return out


def compare_predicted_vs_actual(
    report: dict[str, Any],
    actual: dict[str, Any],
) -> dict[str, Any]:
    """Diff predicted PQA psychology metrics against analytics actuals."""
    predicted = extract_predicted_metrics(report)
    mapping = {
        "ctr": ("ctr", "click_through_rate"),
        "avg_watch_time_sec": ("avg_watch_time", "average_view_duration", "watch_time_sec"),
        "shareability": ("shares", "share_rate"),
        "replay_probability": ("replays", "replay_rate"),
        "subscriber_conversion": ("subscribers_gained", "subscribe_rate"),
        "drop_off_risk": ("drop_off_rate", "audience_retention_drop"),
    }
    comparisons: list[dict] = []
    for pred_key, actual_keys in mapping.items():
        if pred_key not in predicted:
            continue
        actual_val = None
        used = None
        for ak in actual_keys:
            if actual.get(ak) is not None:
                actual_val = actual.get(ak)
                used = ak
                break
        if actual_val is None:
            continue
        try:
            actual_f = float(actual_val)
            pred_f = float(predicted[pred_key])
        except (TypeError, ValueError):
            continue
        # Normalize rates that may be 0–1 vs 0–100
        if actual_f <= 1.0 and pred_f > 1.0 and pred_key in ("ctr", "shareability", "replay_probability", "subscriber_conversion", "drop_off_risk"):
            actual_f *= 100.0
        delta = actual_f - pred_f
        comparisons.append(
            {
                "metric": pred_key,
                "predicted": pred_f,
                "actual": actual_f,
                "actual_field": used,
                "delta": round(delta, 3),
                "abs_error": round(abs(delta), 3),
            }
        )

    mae = (
        round(sum(c["abs_error"] for c in comparisons) / len(comparisons), 3)
        if comparisons
        else None
    )
    result = {
        "idea_id": report.get("idea_id"),
        "title": report.get("title"),
        "pqa_overall": report.get("overall_score"),
        "comparisons": comparisons,
        "mean_abs_error": mae,
        "learning_signal": "calibrate_psychology_weights" if (mae or 0) > 15 else "stable",
    }
    log_event(
        logger,
        "production_qa.learning_compare",
        idea_id=report.get("idea_id"),
        mae=mae,
        n=len(comparisons),
    )
    return result


def record_performance_feedback(
    idea_id: str,
    actual_metrics: dict[str, Any],
    *,
    persist: bool = True,
) -> dict[str, Any]:
    """Find latest PQA report for idea_id and attach performance comparison."""
    reports = load_recent_reports(limit=100)
    match = next((r for r in reports if str(r.get("idea_id") or "") == str(idea_id)), None)
    if not match:
        return {"ok": False, "reason": "no_pqa_report", "idea_id": idea_id}
    comparison = compare_predicted_vs_actual(match, actual_metrics)
    match = dict(match)
    match["performance_feedback"] = comparison
    match["actual_metrics"] = actual_metrics
    if persist:
        store_report(match, idea_id=idea_id)
    return {"ok": True, "comparison": comparison}
