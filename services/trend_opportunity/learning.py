"""Learning loop — predicted vs actual performance → future opportunity scores."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.trend_opportunity.library import DB_PATH, ensure_db, get_opportunity, upsert_opportunity


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def predict_performance(card: dict[str, Any]) -> dict[str, Any]:
    """Internal prediction from opportunity scores (not live analytics)."""
    scores = dict(card.get("scores") or {})
    analysis = dict(card.get("analysis") or {})
    overall = float(card.get("overall_opportunity_score") or 0)
    return {
        "ctr": round(float(scores.get("thumbnail_score") or 50) * 0.08, 2),  # %
        "retention": round(float(scores.get("retention_potential") or 50), 1),
        "average_view_duration_sec": round(20 + float(scores.get("retention_potential") or 50) * 0.35, 1),
        "shares": round(float(analysis.get("shareability") or 50) * 0.4, 1),
        "comments": round(float(scores.get("curiosity_score") or 50) * 0.25, 1),
        "likes": round(overall * 0.5, 1),
        "subscriber_gain": round(max(0, overall - 50) * 0.15, 1),
        "watch_time_hours": round(overall * 0.02, 2),
        "source": "trend_opportunity_prediction",
    }


def record_actual_performance(
    *,
    topic: str,
    category: str = "science",
    production_id: str = "",
    actual: dict[str, Any] | None = None,
    predicted: dict[str, Any] | None = None,
    opportunity_id: str = "",
    db_path: Path | None = None,
) -> dict[str, Any]:
    """Compare predicted vs actual; store lesson; update library previous_performance."""
    db = ensure_db(db_path)
    row = get_opportunity(topic, category, db_path=db_path)
    oid = opportunity_id or (row or {}).get("opportunity_id") or ""
    pred = predicted or predict_performance(
        {
            "scores": json.loads((row or {}).get("scores_json") or "{}") if row else {},
            "analysis": {},
            "overall_opportunity_score": (row or {}).get("opportunity_score") or 0,
        }
    )
    act = dict(actual or {})
    # Stub interface: if no actuals, leave empty (future YouTube/TikTok analytics)
    comparison = {}
    for key in ("ctr", "retention", "average_view_duration_sec", "shares", "comments", "likes", "subscriber_gain", "watch_time_hours"):
        comparison[key] = {
            "predicted": pred.get(key),
            "actual": act.get(key),
            "delta": (
                round(float(act[key]) - float(pred[key]), 3)
                if act.get(key) is not None and pred.get(key) is not None
                else None
            ),
        }

    lesson = None
    if act:
        # Simple lesson when retention undershoots
        ret_d = comparison.get("retention", {}).get("delta")
        if ret_d is not None and ret_d < -5:
            lesson = "Retention underperformed prediction — strengthen curiosity gap in first 3s."
        elif comparison.get("ctr", {}).get("delta") is not None and float(comparison["ctr"]["delta"]) < -0.5:
            lesson = "CTR underperformed — revisit thumbnail concept and working title."
        else:
            lesson = "Performance within band — reinforce winning hook/platform patterns."

    with sqlite3.connect(db) as conn:
        conn.execute(
            """
            INSERT INTO performance_events (opportunity_id, production_id, predicted_json, actual_json, recorded_at)
            VALUES (?,?,?,?,?)
            """,
            (oid, production_id, json.dumps(pred), json.dumps(act), _now()),
        )
        if oid:
            cur = conn.execute("SELECT lessons_learned, scores_json, topic, category FROM opportunities WHERE opportunity_id=?", (oid,))
            r = cur.fetchone()
            if r:
                lessons = json.loads(r[0] or "[]")
                if lesson:
                    lessons.append({"at": _now(), "lesson": lesson, "production_id": production_id})
                conn.execute(
                    "UPDATE opportunities SET previous_performance=?, lessons_learned=?, last_updated=? WHERE opportunity_id=?",
                    (json.dumps(act or pred), json.dumps(lessons[-30:]), _now(), oid),
                )
        conn.commit()

    return {
        "opportunity_id": oid,
        "topic": topic,
        "predicted": pred,
        "actual": act,
        "comparison": comparison,
        "lesson": lesson,
        "feeds_future_scores": True,
        "note": "Actual metrics accepted when analytics connected; predictions always recorded",
    }


def performance_adjustment(topic: str, category: str = "science", *, db_path: Path | None = None) -> float:
    """0–1 historical factor for scoring blend."""
    from services.trend_opportunity.library import historical_performance

    return historical_performance(topic, category, db_path=db_path)
