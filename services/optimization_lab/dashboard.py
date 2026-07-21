"""Module 9 — Executive Optimization Dashboard metrics."""

from __future__ import annotations

from typing import Any

from services.optimization_lab.history import search_experiments
from services.optimization_lab.knowledge import load_patterns


def build_optimization_dashboard() -> dict[str, Any]:
    """Aggregate self-improving studio metrics for Studio Dashboard."""
    experiments = search_experiments(limit=100)
    scores = [int(e.get("production_score") or 0) for e in experiments]
    avg_qa = int(round(sum(scores) / len(scores))) if scores else 0

    ctrs = []
    rets = []
    for e in experiments:
        pred = e.get("predictions") or {}
        if pred.get("ctr_pct") is not None:
            ctrs.append(float(pred["ctr_pct"]))
        if pred.get("completion_rate_pct") is not None:
            rets.append(float(pred["completion_rate_pct"]))

    topics: dict[str, list[int]] = {}
    hooks: list[str] = []
    narrations: list[str] = []
    for e in experiments:
        topic = str(e.get("topic") or "unknown")
        topics.setdefault(topic, []).append(int(e.get("production_score") or 0))
        w = e.get("winning_version") or {}
        if w.get("hook"):
            hooks.append(str(w["hook"])[:100])
    patterns = load_patterns()
    narrations = list(patterns.get("strong_narration_patterns") or [])[:5]

    top_topics = sorted(
        (
            {"topic": t, "avg_score": int(round(sum(v) / len(v))), "n": len(v)}
            for t, v in topics.items()
        ),
        key=lambda r: (r["avg_score"], r["n"]),
        reverse=True,
    )[:8]

    return {
        "videos_optimized": len(experiments),
        "videos_published_proxy": sum(1 for e in experiments if int(e.get("production_score") or 0) >= 95),
        "average_qa_score": avg_qa,
        "average_predicted_ctr": round(sum(ctrs) / len(ctrs), 2) if ctrs else 0.0,
        "average_retention_proxy": round(sum(rets) / len(rets), 1) if rets else 0.0,
        "top_performing_topics": top_topics,
        "best_hooks": hooks[:8],
        "best_narration_styles": narrations,
        "system_health": "healthy" if avg_qa >= 90 or not experiments else ("learning" if avg_qa >= 75 else "needs_attention"),
        "learning_progress": {
            "experiments_recorded": len(experiments),
            "patterns_loaded": {k: len(v) if isinstance(v, list) else 1 for k, v in patterns.items()},
            "knowledge_file": "data/analytics/optimization_patterns.json",
        },
        "queue_status": {"pending_reviews": 0, "running_experiments": 0},
        "api_usage": {"note": "Inherited from provider dashboard"},
        "recent_experiments": experiments[:5],
    }
