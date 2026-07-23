"""Opportunity Library — long-term SQLite memory (OPPORTUNITY_LIBRARY.db)."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
LIB_DIR = ROOT / "data" / "trend_opportunity"
DB_PATH = LIB_DIR / "OPPORTUNITY_LIBRARY.db"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_db(path: Path | None = None) -> Path:
    db = path or DB_PATH
    db.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS opportunities (
                opportunity_id TEXT PRIMARY KEY,
                topic TEXT NOT NULL,
                category TEXT,
                first_seen TEXT,
                last_updated TEXT,
                trend_history TEXT,
                opportunity_score REAL,
                previous_productions TEXT,
                previous_performance TEXT,
                lessons_learned TEXT,
                current_status TEXT,
                production_priority INTEGER,
                scores_json TEXT,
                strategy_json TEXT,
                brief_json TEXT,
                confidence REAL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS performance_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                opportunity_id TEXT,
                production_id TEXT,
                predicted_json TEXT,
                actual_json TEXT,
                recorded_at TEXT
            )
            """
        )
        conn.commit()
    return db


def _oid(topic: str, category: str) -> str:
    import hashlib

    return "opp_" + hashlib.sha256(f"{category}::{topic.strip().lower()}".encode()).hexdigest()[:12]


def upsert_opportunity(card: dict[str, Any], *, db_path: Path | None = None) -> str:
    db = ensure_db(db_path)
    topic = str(card.get("topic") or "")
    category = str(card.get("category") or "general")
    oid = str(card.get("opportunity_id") or _oid(topic, category))
    now = _now()
    with sqlite3.connect(db) as conn:
        cur = conn.execute("SELECT first_seen, trend_history, previous_productions, lessons_learned FROM opportunities WHERE opportunity_id=?", (oid,))
        row = cur.fetchone()
        if row:
            first_seen, hist_raw, prev_prod, lessons = row
            hist = json.loads(hist_raw or "[]")
        else:
            first_seen = now
            hist = []
            prev_prod = "[]"
            lessons = "[]"
        hist.append({"at": now, "score": card.get("overall_opportunity_score"), "status": card.get("status")})
        hist = hist[-50:]
        conn.execute(
            """
            INSERT INTO opportunities (
                opportunity_id, topic, category, first_seen, last_updated, trend_history,
                opportunity_score, previous_productions, previous_performance, lessons_learned,
                current_status, production_priority, scores_json, strategy_json, brief_json, confidence
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(opportunity_id) DO UPDATE SET
                last_updated=excluded.last_updated,
                trend_history=excluded.trend_history,
                opportunity_score=excluded.opportunity_score,
                previous_productions=COALESCE(opportunities.previous_productions, excluded.previous_productions),
                previous_performance=COALESCE(opportunities.previous_performance, excluded.previous_performance),
                lessons_learned=COALESCE(opportunities.lessons_learned, excluded.lessons_learned),
                current_status=excluded.current_status,
                production_priority=excluded.production_priority,
                scores_json=excluded.scores_json,
                strategy_json=excluded.strategy_json,
                brief_json=excluded.brief_json,
                confidence=excluded.confidence
            """,
            (
                oid,
                topic,
                category,
                first_seen,
                now,
                json.dumps(hist),
                float(card.get("overall_opportunity_score") or 0),
                prev_prod if row else json.dumps(card.get("previous_productions") or []),
                json.dumps(card.get("previous_performance") or {}),
                lessons if row else json.dumps(card.get("lessons_learned") or []),
                str(card.get("status") or "ranked"),
                int(card.get("production_priority") or 0),
                json.dumps(card.get("scores") or {}),
                json.dumps(card.get("strategy") or {}),
                json.dumps(card.get("production_brief") or {}),
                float(card.get("confidence") or 0),
            ),
        )
        conn.commit()
    return oid


def get_opportunity(topic: str, category: str = "science", *, db_path: Path | None = None) -> dict[str, Any] | None:
    db = ensure_db(db_path)
    oid = _oid(topic, category)
    with sqlite3.connect(db) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute("SELECT * FROM opportunities WHERE opportunity_id=?", (oid,))
        row = cur.fetchone()
        if not row:
            # try topic match
            cur = conn.execute("SELECT * FROM opportunities WHERE lower(topic)=lower(?) ORDER BY last_updated DESC LIMIT 1", (topic,))
            row = cur.fetchone()
        if not row:
            return None
        return dict(row)


def production_count(topic: str, category: str = "science", *, db_path: Path | None = None) -> int:
    row = get_opportunity(topic, category, db_path=db_path)
    if not row:
        return 0
    try:
        return len(json.loads(row.get("previous_productions") or "[]"))
    except json.JSONDecodeError:
        return 0


def historical_performance(topic: str, category: str = "science", *, db_path: Path | None = None) -> float:
    row = get_opportunity(topic, category, db_path=db_path)
    if not row:
        return 0.5
    try:
        perf = json.loads(row.get("previous_performance") or "{}")
        if not perf:
            return 0.5
        # Blend retention + CTR if present
        ret = float(perf.get("retention") or perf.get("avg_retention") or 0)
        ctr = float(perf.get("ctr") or 0)
        if ret or ctr:
            return max(0.0, min(1.0, 0.6 * (ret / 100.0 if ret > 1 else ret) + 0.4 * (ctr / 100.0 if ctr > 1 else ctr)))
    except (json.JSONDecodeError, TypeError, ValueError):
        pass
    return 0.5


def list_opportunities(*, status: str = "", limit: int = 50, db_path: Path | None = None) -> list[dict[str, Any]]:
    db = ensure_db(db_path)
    with sqlite3.connect(db) as conn:
        conn.row_factory = sqlite3.Row
        if status:
            cur = conn.execute(
                "SELECT * FROM opportunities WHERE current_status=? ORDER BY production_priority DESC, opportunity_score DESC LIMIT ?",
                (status, limit),
            )
        else:
            cur = conn.execute(
                "SELECT * FROM opportunities ORDER BY production_priority DESC, opportunity_score DESC LIMIT ?",
                (limit,),
            )
        return [dict(r) for r in cur.fetchall()]


def record_production(opportunity_id: str, production_id: str, *, db_path: Path | None = None) -> None:
    db = ensure_db(db_path)
    with sqlite3.connect(db) as conn:
        cur = conn.execute("SELECT previous_productions FROM opportunities WHERE opportunity_id=?", (opportunity_id,))
        row = cur.fetchone()
        if not row:
            return
        prev = json.loads(row[0] or "[]")
        prev.append({"production_id": production_id, "at": _now()})
        conn.execute(
            "UPDATE opportunities SET previous_productions=?, current_status=?, last_updated=? WHERE opportunity_id=?",
            (json.dumps(prev[-40:]), "in_production", _now(), opportunity_id),
        )
        conn.commit()
