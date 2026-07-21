"""Prediction vs reality evaluation for published experiments."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from services.creative_performance_lab.models import RESULT_STATUSES
from services.creative_performance_lab.store import load_experiment, save_experiment


def attach_published_video(
    experiment_id: str,
    *,
    variant_label: str,
    platform_video_id: str,
    platform: str = "youtube_shorts",
    publish_timestamp: str = "",
) -> dict[str, Any]:
    exp = load_experiment(experiment_id)
    if not exp:
        raise FileNotFoundError(experiment_id)
    pubs = list(exp.get("publishing_ids") or [])
    pubs.append(
        {
            "variant_label": variant_label,
            "platform_video_id": platform_video_id,
            "platform": platform,
            "publish_timestamp": publish_timestamp or datetime.now(timezone.utc).isoformat(),
        }
    )
    exp["publishing_ids"] = pubs
    exp["status"] = "awaiting_analytics"
    # Link into analytics layer when available
    try:
        from services.analytics import attach_experiment

        attach_experiment(
            content_id=platform_video_id,
            experiment_id=experiment_id,
            variant_id=f"{experiment_id}_{variant_label}",
        )
    except Exception:  # noqa: BLE001
        pass
    save_experiment(exp)
    return exp


def refresh_analytics(experiment_id: str) -> dict[str, Any]:
    from services.creative_performance_lab.analytics_providers import get_analytics_provider

    exp = load_experiment(experiment_id)
    if not exp:
        raise FileNotFoundError(experiment_id)
    provider = get_analytics_provider(str(exp.get("platform") or "youtube_shorts"))
    results = []
    for pub in exp.get("publishing_ids") or []:
        vid = str(pub.get("platform_video_id") or "")
        if not vid:
            continue
        fetched = provider.fetch_video_metrics(vid)
        results.append({**pub, "analytics": fetched, "retrieved_at": datetime.now(timezone.utc).isoformat()})
    exp["meta"] = {**(exp.get("meta") or {}), "analytics_snapshots": results}
    if results and provider.is_available():
        exp["status"] = "evaluating"
    save_experiment(exp)
    return {"experiment_id": experiment_id, "snapshots": results, "provider_available": provider.is_available()}


def evaluate_experiment(experiment_id: str) -> dict[str, Any]:
    """Compare predictions to actuals; never declare winners with thin data."""
    exp = load_experiment(experiment_id)
    if not exp:
        raise FileNotFoundError(experiment_id)
    snapshots = (exp.get("meta") or {}).get("analytics_snapshots") or []
    variants = exp.get("variants") or []
    if not snapshots:
        result = {
            "status": "INSUFFICIENT_DATA",
            "reason": "No analytics snapshots. Attach platform video IDs and refresh analytics.",
            "sample_size": 0,
        }
        exp["final_result"] = result
        exp["status"] = "insufficient_data"
        save_experiment(exp)
        return result

    # Extract comparable metrics when present (YouTube shapes vary)
    actual_rows = []
    for snap in snapshots:
        metrics = ((snap.get("analytics") or {}).get("metrics") or {})
        actual_rows.append(
            {
                "variant_label": snap.get("variant_label"),
                "views": _num(metrics, "views"),
                "ctr": _num(metrics, "ctr", "clickThroughRate"),
                "avg_view_duration": _num(metrics, "averageViewDuration", "average_view_duration"),
                "completion_rate": _num(metrics, "completion_rate", "averageViewPercentage"),
                "shares": _num(metrics, "shares"),
            }
        )

    usable = [r for r in actual_rows if (r.get("views") or 0) > 0 or (r.get("completion_rate") or 0) > 0]
    total_views = sum(float(r.get("views") or 0) for r in usable)
    if not usable or total_views < 200:
        status = "INSUFFICIENT_DATA" if total_views < 50 else "EARLY_SIGNAL"
        result = {
            "status": status,
            "sample_size": int(total_views),
            "actual_rows": actual_rows,
            "reason": "Need more views / retention samples before confirming a winner.",
            "evidence_sufficient": False,
        }
        exp["final_result"] = result
        exp["status"] = status.lower()
        exp["confidence_level"] = 0.2 if status == "EARLY_SIGNAL" else 0.05
        save_experiment(exp)
        return result

    # Ranking accuracy vs predictions
    pred_rank = sorted(
        variants,
        key=lambda v: -float((v.get("prediction") or {}).get("completion_rate_pct") or v.get("overall_score") or 0),
    )
    actual_rank = sorted(usable, key=lambda r: (-float(r.get("completion_rate") or 0), -float(r.get("views") or 0)))
    pred_winner = (pred_rank[0].get("label") if pred_rank else "")
    actual_winner = actual_rank[0].get("variant_label") if actual_rank else ""
    human_winner = ((exp.get("meta") or {}).get("human_preferred_winner") or "")

    errors = []
    for row in usable:
        v = next((x for x in variants if x.get("label") == row.get("variant_label")), {})
        pred_c = float((v.get("prediction") or {}).get("completion_rate_pct") or 0)
        act_c = float(row.get("completion_rate") or 0)
        if pred_c and act_c:
            abs_err = abs(pred_c - act_c)
            pct_err = abs_err / max(act_c, 1e-6) * 100
            errors.append({"variant": row.get("variant_label"), "absolute_error": round(abs_err, 2), "percent_error": round(pct_err, 1)})

    if total_views >= 2000 and pred_winner == actual_winner:
        status = "CONFIRMED_WINNER"
        conf = 0.8
    elif total_views >= 500:
        status = "PROVISIONAL_WINNER"
        conf = 0.55
    else:
        status = "EARLY_SIGNAL"
        conf = 0.35
    if pred_winner and actual_winner and pred_winner != actual_winner and total_views >= 500:
        # still can name actual winner provisionally
        pass

    result = {
        "status": status if status in RESULT_STATUSES else "INCONCLUSIVE",
        "predicted_winner": pred_winner,
        "actual_winner": actual_winner,
        "human_selected_winner": human_winner,
        "ranking_accuracy": pred_winner == actual_winner,
        "human_vs_actual": (human_winner == actual_winner) if human_winner else None,
        "prediction_errors": errors,
        "sample_size": int(total_views),
        "evidence_sufficient": status in ("PROVISIONAL_WINNER", "CONFIRMED_WINNER"),
        "disclaimer": "Real platform metrics only — never invented.",
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }
    exp["final_result"] = result
    exp["confidence_level"] = conf
    exp["status"] = status.lower()
    save_experiment(exp)
    return result


def _num(d: dict, *keys: str) -> float:
    for k in keys:
        if k in d and d[k] is not None:
            try:
                return float(d[k])
            except (TypeError, ValueError):
                continue
    return 0.0
