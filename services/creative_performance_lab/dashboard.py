"""Creative Performance Lab dashboard board for Studio executive UI."""

from __future__ import annotations

from typing import Any

from services.creative_performance_lab.knowledge import search_learnings
from services.creative_performance_lab.store import list_experiments, load_knowledge


def build_creative_performance_board() -> dict[str, Any]:
    experiments = list_experiments(limit=100)
    by_status: dict[str, list] = {}
    for e in experiments:
        by_status.setdefault(str(e.get("status") or "unknown"), []).append(e)

    learnings = load_knowledge().get("learnings") or []
    active_learnings = [L for L in learnings if L.get("active", True)]

    # Prediction accuracy among evaluated experiments
    evaluated = [e for e in experiments if e.get("status") in ("confirmed_winner", "provisional_winner", "inconclusive", "early_signal")]
    ranking_hits = 0
    ranking_n = 0
    for e in evaluated:
        # load full? index may lack final_result — skip if missing
        pass

    opt = {}
    try:
        from services.optimization_lab.dashboard import build_optimization_dashboard

        opt = build_optimization_dashboard()
    except Exception:  # noqa: BLE001
        opt = {}

    pi = {}
    try:
        from services.publishing_intelligence.dashboard import build_studio_intelligence_dashboard

        pi = build_studio_intelligence_dashboard()
    except Exception:  # noqa: BLE001
        pi = {}

    return {
        "active_experiments": by_status.get("variants_ready", []) + by_status.get("draft", []),
        "awaiting_human_review": by_status.get("awaiting_human_review", []),
        "awaiting_publishing": by_status.get("awaiting_publishing", []),
        "awaiting_analytics": by_status.get("awaiting_analytics", []),
        "confirmed_winners": by_status.get("confirmed_winner", []),
        "inconclusive": by_status.get("inconclusive", []) + by_status.get("insufficient_data", []),
        "experiment_count": len(experiments),
        "recent_experiments": experiments[:10],
        "validated_learnings_count": len(active_learnings),
        "recent_learnings": active_learnings[:8],
        "best_hook_patterns": [L.get("winning_pattern") for L in search_learnings(creative_variable="hook_structure", limit=5)],
        "best_narrator_profiles": (opt.get("best_narration_styles") or [])[:5],
        "prediction_note": "Internal predictions are never shown as real audience results",
        "optimization_lab": {
            "videos_optimized": opt.get("videos_optimized"),
            "avg_predicted_ctr": opt.get("average_predicted_ctr"),
        },
        "publishing_intelligence": {
            "confidence_score": pi.get("confidence_score"),
            "calibration": (pi.get("calibration") or {}).get("status") if isinstance(pi.get("calibration"), dict) else pi.get("calibration"),
        },
        "ranking_accuracy_n": ranking_n,
        "ranking_accuracy_hits": ranking_hits,
    }
