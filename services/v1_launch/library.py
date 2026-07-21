"""Persist V1 Launch pilot production records."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.env import project_root

ROOT = project_root() / "data" / "productions" / "_validation" / "v1_launch"
DB_PATH = ROOT / "LAUNCH_PILOT_LIBRARY.db"
INDEX_JSON = ROOT / "LAUNCH_PILOT_LIBRARY.json"
RUNS = ROOT / "runs"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_library() -> Path:
    ROOT.mkdir(parents=True, exist_ok=True)
    RUNS.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pilots (
                launch_id TEXT PRIMARY KEY,
                production_id TEXT,
                topic TEXT,
                category TEXT,
                created_at TEXT,
                success INTEGER,
                deliverable_ok INTEGER,
                video_exists INTEGER,
                overall_score REAL,
                creative_score REAL,
                elapsed_ms INTEGER,
                failures_json TEXT,
                measurements_json TEXT,
                metrics_json TEXT,
                artifact_dir TEXT
            )
            """
        )
        conn.commit()
    return ROOT


def completed_launch_ids() -> set[str]:
    ensure_library()
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("SELECT launch_id FROM pilots").fetchall()
    return {r[0] for r in rows}


def store_pilot(
    card: dict[str, Any],
    *,
    launch_id: str,
    creative_review: str = "",
    qa_notes: str = "",
) -> dict[str, Any]:
    ensure_library()
    artifact = RUNS / launch_id
    artifact.mkdir(parents=True, exist_ok=True)
    timing = card.get("timing") or {}
    (artifact / "Production_Report.json").write_text(
        json.dumps(
            {
                "launch_id": launch_id,
                "production_id": card.get("production_id"),
                "topic": card.get("topic"),
                "category": card.get("category"),
                "success": card.get("success"),
                "deliverable_ok": card.get("deliverable_ok"),
                "video_exists": card.get("video_exists"),
                "overall_program_score": card.get("overall_program_score"),
                "measurements": card.get("measurements"),
                "timing": timing,
                "generated_at": _now(),
            },
            indent=2,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )
    (artifact / "Creative_Director_Review.md").write_text(
        "# Creative Director Review\n\n" + (creative_review or str(card.get("creative_recommendation") or "_n/a_") + "\n"),
        encoding="utf-8",
    )
    (artifact / "QA_Notes.md").write_text(
        "# QA Notes\n\n"
        + (qa_notes or "")
        + f"\n\n- success={card.get('success')}\n- video_exists={card.get('video_exists')}\n"
        f"- deliverable_ok={card.get('deliverable_ok')}\n- pipeline_health={card.get('pipeline_health')}\n",
        encoding="utf-8",
    )
    (artifact / "Failure_Log.json").write_text(
        json.dumps({"failures": card.get("failures") or []}, indent=2) + "\n", encoding="utf-8"
    )
    (artifact / "Production_Metrics.json").write_text(
        json.dumps(
            {
                "timing": timing,
                "overall_program_score": card.get("overall_program_score"),
                "creative_excellence_score": card.get("creative_excellence_score"),
                "hook_score": card.get("hook_score"),
                "viewer_prediction": card.get("viewer_prediction"),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO pilots (
                launch_id, production_id, topic, category, created_at, success, deliverable_ok,
                video_exists, overall_score, creative_score, elapsed_ms, failures_json,
                measurements_json, metrics_json, artifact_dir
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(launch_id) DO UPDATE SET
                production_id=excluded.production_id,
                success=excluded.success,
                deliverable_ok=excluded.deliverable_ok,
                video_exists=excluded.video_exists,
                overall_score=excluded.overall_score,
                creative_score=excluded.creative_score,
                measurements_json=excluded.measurements_json,
                failures_json=excluded.failures_json,
                metrics_json=excluded.metrics_json,
                artifact_dir=excluded.artifact_dir
            """,
            (
                launch_id,
                card.get("production_id"),
                card.get("topic"),
                card.get("category"),
                _now(),
                1 if card.get("success") else 0,
                1 if card.get("deliverable_ok") else 0,
                1 if card.get("video_exists") else 0,
                float(card.get("overall_program_score") or 0),
                card.get("creative_excellence_score"),
                int(timing.get("elapsed_ms") or 0),
                json.dumps(card.get("failures") or []),
                json.dumps(card.get("measurements") or {}),
                json.dumps(timing),
                str(artifact),
            ),
        )
        conn.commit()
    _refresh_index()
    return {"launch_id": launch_id, "artifact_dir": str(artifact)}


def list_pilots(limit: int = 100) -> list[dict[str, Any]]:
    ensure_library()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM pilots ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        for key, raw in (("failures", "failures_json"), ("measurements", "measurements_json"), ("metrics", "metrics_json")):
            try:
                d[key] = json.loads(d.pop(raw) or ("[]" if key == "failures" else "{}"))
            except json.JSONDecodeError:
                d[key] = [] if key == "failures" else {}
        d["success"] = bool(d.get("success"))
        d["deliverable_ok"] = bool(d.get("deliverable_ok"))
        d["video_exists"] = bool(d.get("video_exists"))
        out.append(d)
    return out


def _refresh_index() -> None:
    rows = list_pilots(limit=100)
    INDEX_JSON.write_text(
        json.dumps({"updated_at": _now(), "count": len(rows), "pilots": rows}, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
