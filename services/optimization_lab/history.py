"""Module 7 — Experiment History database."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.env import project_root

_HISTORY_FILE = "data/analytics/optimization_experiments.json"


def _path() -> Path:
    return project_root() / _HISTORY_FILE


def _load() -> list[dict]:
    path = _path()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _save(rows: list[dict]) -> None:
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, indent=2), encoding="utf-8")


def record_experiment(
    *,
    topic: str,
    platform: str,
    production_score: int,
    winner: dict,
    rejected: list[dict],
    critique: dict,
    improvements: list[str],
    lessons: list[str],
    predictions: dict | None = None,
) -> dict[str, Any]:
    """Persist a searchable experiment run."""
    rows = _load()
    entry = {
        "experiment_id": f"opt_{uuid.uuid4().hex[:12]}",
        "topic": topic,
        "date": datetime.now(timezone.utc).isoformat(),
        "platform": platform,
        "production_score": production_score,
        "winning_version": {
            "label": winner.get("label"),
            "variant_id": winner.get("variant_id"),
            "overall": winner.get("overall_score") or (winner.get("scores") or {}).get("overall"),
            "title": (winner.get("axes") or {}).get("title"),
            "hook": (winner.get("axes") or {}).get("hook"),
        },
        "rejected_versions": [
            {
                "label": r.get("label"),
                "overall": r.get("overall_score"),
                "reason": "Lower composite score than winner",
            }
            for r in rejected
        ],
        "reasons": [i.get("message") for i in (critique.get("issues") or [])][:8],
        "improvements": improvements[:12],
        "lessons_learned": lessons[:12],
        "predictions": predictions or {},
    }
    rows.append(entry)
    _save(rows[-500:])  # keep last 500
    return entry


def search_experiments(
    *,
    topic: str = "",
    platform: str = "",
    min_score: int = 0,
    limit: int = 20,
) -> list[dict]:
    topic_l = topic.lower().strip()
    platform_l = platform.lower().strip()
    out = []
    for row in reversed(_load()):
        if topic_l and topic_l not in str(row.get("topic") or "").lower():
            continue
        if platform_l and platform_l not in str(row.get("platform") or "").lower():
            continue
        if int(row.get("production_score") or 0) < min_score:
            continue
        out.append(row)
        if len(out) >= limit:
            break
    return out
