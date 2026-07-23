"""GenOS permanent learning store — lessons after every production."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.env import project_root

LEARN_DB = project_root() / "data" / "generational_os" / "GENOS_LEARNING.db"
LESSONS_JSON = project_root() / "data" / "generational_os" / "LESSONS_LEARNED.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_learning_db() -> Path:
    LEARN_DB.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(LEARN_DB) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS lessons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                production_id TEXT,
                topic TEXT,
                platform TEXT,
                creative_score REAL,
                audience_score REAL,
                trend_score REAL,
                publishing_time TEXT,
                performance_json TEXT,
                highest_impact_lesson TEXT,
                recommended_improvement TEXT,
                recorded_at TEXT
            )
            """
        )
        conn.commit()
    return LEARN_DB


def record_production_lesson(
    *,
    production_id: str = "",
    topic: str = "",
    platform: str = "youtube_shorts",
    creative_score: float | None = None,
    audience_score: float | None = None,
    trend_score: float | None = None,
    publishing_time: str = "",
    performance: dict[str, Any] | None = None,
    highest_impact_lesson: str = "",
    recommended_improvement: str = "",
) -> dict[str, Any]:
    """Store one production lesson permanently for future GenOS decisions."""
    ensure_learning_db()
    row = {
        "production_id": production_id,
        "topic": topic,
        "platform": platform,
        "creative_score": creative_score,
        "audience_score": audience_score,
        "trend_score": trend_score,
        "publishing_time": publishing_time or _now(),
        "performance": performance or {},
        "highest_impact_lesson": highest_impact_lesson,
        "recommended_improvement": recommended_improvement,
        "recorded_at": _now(),
    }
    with sqlite3.connect(LEARN_DB) as conn:
        conn.execute(
            """
            INSERT INTO lessons (
                production_id, topic, platform, creative_score, audience_score, trend_score,
                publishing_time, performance_json, highest_impact_lesson, recommended_improvement, recorded_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                row["production_id"],
                row["topic"],
                row["platform"],
                row["creative_score"],
                row["audience_score"],
                row["trend_score"],
                row["publishing_time"],
                json.dumps(row["performance"]),
                row["highest_impact_lesson"],
                row["recommended_improvement"],
                row["recorded_at"],
            ),
        )
        conn.commit()

    # Mirror JSON (last 200)
    lessons = []
    if LESSONS_JSON.exists():
        try:
            lessons = list((json.loads(LESSONS_JSON.read_text(encoding="utf-8")).get("lessons") or []))
        except (OSError, json.JSONDecodeError):
            lessons = []
    lessons.insert(0, row)
    LESSONS_JSON.parent.mkdir(parents=True, exist_ok=True)
    LESSONS_JSON.write_text(
        json.dumps({"updated_at": _now(), "count": len(lessons[:200]), "lessons": lessons[:200]}, indent=2) + "\n",
        encoding="utf-8",
    )

    # Soft feed Trend Opportunity library when possible
    try:
        from services.trend_opportunity.learning import record_actual_performance

        if performance:
            record_actual_performance(
                topic=topic,
                category="science",
                production_id=production_id,
                actual=performance,
            )
    except Exception:  # noqa: BLE001
        pass

    # Soft feed Audience Intelligence lesson statement
    try:
        if highest_impact_lesson:
            from services.audience_intelligence import add_lesson

            add_lesson(
                statement=highest_impact_lesson,
                category="subject_best_practices",
                confidence=0.6,
                platform=platform,
                topic=topic,
                production_id=production_id,
                source="genos_learning",
                evidence=[{"type": "genos", "production_id": production_id, "creative_score": creative_score}],
            )
    except Exception:  # noqa: BLE001
        pass

    return row


def extract_lesson_from_ops_result(ops: dict[str, Any], *, topic: str = "", trend_score: float | None = None) -> dict[str, Any]:
    """Pull creative / audience signals from a run_studio_ops result."""
    report = ops.get("report") or ops.get("production_report") or {}
    ctx = ops.get("context") or {}
    ce = ctx.get("creative_excellence") or {}
    ai = ctx.get("audience_intelligence_review") or {}
    creative = float(
        ce.get("creative_excellence_score")
        or report.get("creative_excellence_score")
        or 0
    ) or None
    lesson = (
        (ce.get("single_recommendation") or {}).get("recommendation")
        if isinstance(ce.get("single_recommendation"), dict)
        else ce.get("single_recommendation")
    )
    if isinstance(lesson, dict):
        lesson = lesson.get("recommendation")
    lesson = str(lesson or report.get("creative_recommendation") or ai.get("highest_impact_improvement") or "")
    audience = None
    if ai.get("lesson_id"):
        audience = 70.0  # presence signal
    return record_production_lesson(
        production_id=str(ops.get("production_id") or (ops.get("status") or {}).get("production_id") or ""),
        topic=topic or str(report.get("topic") or ""),
        platform=str(report.get("platform") or "youtube_shorts"),
        creative_score=creative,
        audience_score=audience,
        trend_score=trend_score,
        highest_impact_lesson=lesson or "Review creative excellence recommendation for next production.",
        recommended_improvement=lesson or "Ship the single highest-impact creative fix before publishing.",
        performance={},
    )


def list_lessons(limit: int = 25) -> list[dict[str, Any]]:
    ensure_learning_db()
    with sqlite3.connect(LEARN_DB) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute("SELECT * FROM lessons ORDER BY id DESC LIMIT ?", (limit,))
        rows = []
        for r in cur.fetchall():
            d = dict(r)
            try:
                d["performance"] = json.loads(d.pop("performance_json") or "{}")
            except json.JSONDecodeError:
                d["performance"] = {}
            rows.append(d)
        return rows
