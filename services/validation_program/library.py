"""Validation Library — searchable store of every validation production."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.env import project_root

LIB_ROOT = project_root() / "data" / "productions" / "_validation" / "validation_program"
DB_PATH = LIB_ROOT / "VALIDATION_LIBRARY.db"
INDEX_JSON = LIB_ROOT / "VALIDATION_LIBRARY.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_library() -> Path:
    LIB_ROOT.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS validations (
                validation_id TEXT PRIMARY KEY,
                production_id TEXT,
                topic TEXT,
                category TEXT,
                created_at TEXT,
                success INTEGER,
                overall_score REAL,
                creative_score REAL,
                opportunity_score REAL,
                hook_score REAL,
                viewer_prediction REAL,
                elapsed_ms INTEGER,
                render_ms INTEGER,
                measurements_json TEXT,
                failures_json TEXT,
                weaknesses_json TEXT,
                creative_review TEXT,
                audience_review TEXT,
                optimization_json TEXT,
                metrics_json TEXT,
                artifact_dir TEXT
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_val_category ON validations(category)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_val_score ON validations(overall_score)"
        )
        conn.commit()
    return DB_PATH


def store_validation(
    card: dict[str, Any],
    *,
    validation_id: str,
    creative_director_review: str = "",
    audience_review: str = "",
    optimization: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Persist one production into the Validation Library + per-run folder."""
    ensure_library()
    artifact_dir = LIB_ROOT / "runs" / validation_id
    artifact_dir.mkdir(parents=True, exist_ok=True)

    production_report = {
        "validation_id": validation_id,
        "production_id": card.get("production_id"),
        "topic": card.get("topic"),
        "category": card.get("category"),
        "scores": card.get("measurements"),
        "overall_program_score": card.get("overall_program_score"),
        "timing": card.get("timing"),
        "success": card.get("success"),
        "generated_at": _now(),
    }
    (artifact_dir / "Production_Report.json").write_text(json.dumps(production_report, indent=2) + "\n", encoding="utf-8")
    (artifact_dir / "Creative_Director_Review.md").write_text(
        "# Creative Director Review\n\n"
        + (creative_director_review or str(card.get("creative_recommendation") or "_No recommendation._") + "\n"),
        encoding="utf-8",
    )
    (artifact_dir / "Audience_Intelligence_Review.md").write_text(
        "# Audience Intelligence Review\n\n"
        + (audience_review or str(card.get("audience_lesson") or "_No lesson recorded._") + "\n"),
        encoding="utf-8",
    )
    (artifact_dir / "Failure_Log.json").write_text(
        json.dumps({"failures": card.get("failures") or [], "success": card.get("success")}, indent=2) + "\n",
        encoding="utf-8",
    )
    (artifact_dir / "Optimization_Suggestions.json").write_text(
        json.dumps(optimization or [], indent=2) + "\n", encoding="utf-8"
    )
    (artifact_dir / "Production_Metrics.json").write_text(
        json.dumps(
            {
                "timing": card.get("timing"),
                "overall_program_score": card.get("overall_program_score"),
                "creative_excellence_score": card.get("creative_excellence_score"),
                "opportunity_score": card.get("opportunity_score"),
                "viewer_prediction": card.get("viewer_prediction"),
                "hook_score": card.get("hook_score"),
                "validation_score": card.get("validation_score"),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    timing = card.get("timing") or {}
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO validations (
                validation_id, production_id, topic, category, created_at, success,
                overall_score, creative_score, opportunity_score, hook_score, viewer_prediction,
                elapsed_ms, render_ms, measurements_json, failures_json, weaknesses_json,
                creative_review, audience_review, optimization_json, metrics_json, artifact_dir
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(validation_id) DO UPDATE SET
                production_id=excluded.production_id,
                overall_score=excluded.overall_score,
                creative_score=excluded.creative_score,
                measurements_json=excluded.measurements_json,
                failures_json=excluded.failures_json,
                creative_review=excluded.creative_review,
                audience_review=excluded.audience_review,
                optimization_json=excluded.optimization_json,
                metrics_json=excluded.metrics_json,
                artifact_dir=excluded.artifact_dir,
                success=excluded.success
            """,
            (
                validation_id,
                card.get("production_id"),
                card.get("topic"),
                card.get("category"),
                _now(),
                1 if card.get("success") else 0,
                float(card.get("overall_program_score") or 0),
                card.get("creative_excellence_score"),
                card.get("opportunity_score"),
                card.get("hook_score"),
                card.get("viewer_prediction"),
                int(timing.get("elapsed_ms") or 0),
                int(timing.get("render_ms") or 0),
                json.dumps(card.get("measurements") or {}),
                json.dumps(card.get("failures") or []),
                json.dumps(card.get("weaknesses") or []),
                creative_director_review or str(card.get("creative_recommendation") or ""),
                audience_review or str(card.get("audience_lesson") or ""),
                json.dumps(optimization or []),
                json.dumps(timing),
                str(artifact_dir),
            ),
        )
        conn.commit()

    _refresh_index()
    return {"validation_id": validation_id, "artifact_dir": str(artifact_dir), "db": str(DB_PATH)}


def _refresh_index() -> None:
    rows = list_validations(limit=500)
    INDEX_JSON.write_text(
        json.dumps({"updated_at": _now(), "count": len(rows), "validations": rows}, indent=2, default=str) + "\n",
        encoding="utf-8",
    )


def list_validations(
    *,
    category: str = "",
    min_score: float | None = None,
    success: bool | None = None,
    query: str = "",
    limit: int = 100,
) -> list[dict[str, Any]]:
    ensure_library()
    sql = "SELECT * FROM validations WHERE 1=1"
    params: list[Any] = []
    if category:
        sql += " AND category=?"
        params.append(category)
    if min_score is not None:
        sql += " AND overall_score>=?"
        params.append(min_score)
    if success is not None:
        sql += " AND success=?"
        params.append(1 if success else 0)
    if query:
        sql += " AND (topic LIKE ? OR production_id LIKE ? OR validation_id LIKE ?)"
        q = f"%{query}%"
        params.extend([q, q, q])
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute(sql, params)
        out = []
        for r in cur.fetchall():
            d = dict(r)
            for key, raw in (
                ("measurements", "measurements_json"),
                ("failures", "failures_json"),
                ("weaknesses", "weaknesses_json"),
                ("optimization", "optimization_json"),
                ("metrics", "metrics_json"),
            ):
                try:
                    d[key] = json.loads(d.pop(raw) or ("{}" if key != "failures" and key != "weaknesses" and key != "optimization" else "[]"))
                except json.JSONDecodeError:
                    d[key] = {} if key in ("measurements", "metrics") else []
            d["success"] = bool(d.get("success"))
            out.append(d)
        return out


def completed_validation_ids() -> set[str]:
    return {str(r["validation_id"]) for r in list_validations(limit=500)}
