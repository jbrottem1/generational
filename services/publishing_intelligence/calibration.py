"""Phase 3 — Prediction calibration: predicted vs actual + prior updates."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.production_qa.learning import compare_predicted_vs_actual
from services.publishing_intelligence.analytics_layer import list_intelligence_records

ROOT = Path(__file__).resolve().parents[2]
CALIBRATION_PATH = ROOT / "data" / "analytics" / "prediction_calibration.json"
PRIORS_PATH = ROOT / "data" / "analytics" / "prediction_priors.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _f(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def compare_intelligence_predictions(record: dict) -> dict[str, Any]:
    """Mission comparisons: hook/CTR/completion/share predicted vs actual."""
    pred = record.get("predicted_metrics") or {}
    act = record.get("actual_metrics") or {}
    pairs = [
        ("hook_vs_retention", pred.get("hook_score"), act.get("audience_retention"), "Predicted hook → actual retention"),
        ("ctr", pred.get("ctr"), act.get("ctr"), "Predicted CTR → actual CTR"),
        ("completion", pred.get("completion"), act.get("audience_retention") or act.get("average_view_duration"), "Predicted completion → actual completion"),
        ("shareability", pred.get("shareability"), act.get("shares"), "Predicted shareability → actual shares"),
    ]
    comparisons = []
    for metric, predicted, actual, label in pairs:
        if predicted is None or actual is None:
            continue
        p = _f(predicted)
        a = _f(actual)
        # Normalize share counts into a rough rate score when needed
        if metric == "shareability" and a > 1 and p <= 100:
            # treat share count relative to views if available
            views = _f((record.get("actual_metrics") or {}).get("views"), 0)
            a = (a / views * 100.0) if views > 0 else min(100.0, a)
        if a <= 1.0 and p > 1.0 and metric in ("ctr", "completion", "shareability", "hook_vs_retention"):
            a *= 100.0
        delta = a - p
        comparisons.append(
            {
                "metric": metric,
                "label": label,
                "predicted": round(p, 3),
                "actual": round(a, 3),
                "delta": round(delta, 3),
                "abs_error": round(abs(delta), 3),
                "accurate": abs(delta) <= 15.0,
            }
        )
    avg_err = (
        sum(c["abs_error"] for c in comparisons) / len(comparisons) if comparisons else None
    )
    accuracy = None
    if comparisons:
        accuracy = round(100.0 * sum(1 for c in comparisons if c["accurate"]) / len(comparisons), 1)
    return {
        "video_id": record.get("video_id"),
        "topic": record.get("topic"),
        "platform": record.get("platform"),
        "comparisons": comparisons,
        "mean_abs_error": round(avg_err, 3) if avg_err is not None else None,
        "prediction_accuracy_pct": accuracy,
    }


def build_calibration_report(limit: int = 200) -> dict[str, Any]:
    """Aggregate prediction accuracy across intelligence records."""
    records = list_intelligence_records(limit=limit)
    per_video = []
    for rec in records:
        # Skip records with no actuals yet
        actuals = rec.get("actual_metrics") or {}
        if not any(v is not None for v in actuals.values()):
            continue
        per_video.append(compare_intelligence_predictions(rec))

    # Also include PQA-style comparisons when reports embed actuals
    metric_errors: dict[str, list[float]] = {}
    for row in per_video:
        for c in row.get("comparisons") or []:
            metric_errors.setdefault(c["metric"], []).append(float(c["abs_error"]))

    by_metric = {
        m: {
            "n": len(errs),
            "mean_abs_error": round(sum(errs) / len(errs), 3),
            "highlight": "overconfident" if sum(errs) / len(errs) > 20 else "calibrated",
        }
        for m, errs in metric_errors.items()
        if errs
    }
    accuracies = [r["prediction_accuracy_pct"] for r in per_video if r.get("prediction_accuracy_pct") is not None]
    report = {
        "generated_at": _now(),
        "version": "2.0.0",
        "videos_calibrated": len(per_video),
        "average_prediction_accuracy_pct": round(sum(accuracies) / len(accuracies), 1) if accuracies else None,
        "by_metric": by_metric,
        "divergence_highlights": [
            {"metric": m, **meta}
            for m, meta in sorted(by_metric.items(), key=lambda kv: -kv[1]["mean_abs_error"])
            if meta["mean_abs_error"] > 12
        ],
        "per_video": per_video[-50:],
    }
    CALIBRATION_PATH.parent.mkdir(parents=True, exist_ok=True)
    CALIBRATION_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def recalibrate_priors(report: dict | None = None) -> dict[str, Any]:
    """Update soft prediction priors from calibration errors (additive, never rewrite engines)."""
    report = report or build_calibration_report()
    priors = {
        "updated_at": _now(),
        "version": "2.0.0",
        "ctr_bias": 0.0,
        "completion_bias": 0.0,
        "share_bias": 0.0,
        "retention_bias": 0.0,
        "notes": [],
    }
    if PRIORS_PATH.exists():
        try:
            priors.update(json.loads(PRIORS_PATH.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            pass

    by_metric = report.get("by_metric") or {}
    # Bias correction: if we over-predicted, push prior down (negative bias)
    mapping = {
        "ctr": "ctr_bias",
        "completion": "completion_bias",
        "shareability": "share_bias",
        "hook_vs_retention": "retention_bias",
    }
    for metric, prior_key in mapping.items():
        meta = by_metric.get(metric)
        if not meta:
            continue
        # Use mean signed? we only have abs — nudge conservatively by half MAE toward humility
        mae = float(meta["mean_abs_error"])
        # Shrink prior toward zero then apply humility discount when MAE high
        old = float(priors.get(prior_key) or 0.0)
        humility = -min(8.0, mae * 0.25)
        priors[prior_key] = round(0.7 * old + 0.3 * humility, 3)
        priors["notes"].append(f"{metric}: MAE={mae} → {prior_key}={priors[prior_key]}")

    PRIORS_PATH.write_text(json.dumps(priors, indent=2), encoding="utf-8")
    return priors


def apply_priors_to_prediction(prediction: dict) -> dict:
    """Additive adjustment of a predict_performance() result using stored priors."""
    if not PRIORS_PATH.exists():
        return prediction
    try:
        priors = json.loads(PRIORS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return prediction
    out = dict(prediction)
    if out.get("expected_ctr") is not None:
        out["expected_ctr"] = round(max(0.5, float(out["expected_ctr"]) + float(priors.get("ctr_bias") or 0)), 3)
    if out.get("expected_audience_retention") is not None:
        out["expected_audience_retention"] = round(
            max(5.0, float(out["expected_audience_retention"]) + float(priors.get("completion_bias") or 0)),
            3,
        )
    out["calibration_priors_applied"] = True
    return out


def calibrate_from_pqa_and_actual(pqa_report: dict, actual: dict) -> dict:
    """Reuse existing PQA learning comparator."""
    return compare_predicted_vs_actual(pqa_report, actual)
