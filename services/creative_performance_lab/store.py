"""Persist Creative Performance Lab experiments (separate from pipeline)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
LAB_ROOT = ROOT / "data" / "creative_performance_lab"
EXPERIMENTS_DIR = LAB_ROOT / "experiments"
INDEX_PATH = LAB_ROOT / "experiments_index.json"
KNOWLEDGE_PATH = LAB_ROOT / "creative_performance_knowledge.json"


def ensure_dirs() -> None:
    EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)
    LAB_ROOT.mkdir(parents=True, exist_ok=True)


def experiment_path(experiment_id: str) -> Path:
    return EXPERIMENTS_DIR / experiment_id / "EXPERIMENT.json"


def save_experiment(data: dict[str, Any]) -> Path:
    ensure_dirs()
    eid = str(data.get("experiment_id") or "unknown")
    path = experiment_path(eid)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    _upsert_index(data)
    return path


def load_experiment(experiment_id: str) -> dict[str, Any] | None:
    path = experiment_path(experiment_id)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def list_experiments(*, status: str = "", limit: int = 50) -> list[dict[str, Any]]:
    ensure_dirs()
    if INDEX_PATH.exists():
        try:
            rows = json.loads(INDEX_PATH.read_text(encoding="utf-8")).get("experiments") or []
        except (OSError, json.JSONDecodeError):
            rows = []
    else:
        rows = []
    if status:
        rows = [r for r in rows if r.get("status") == status]
    return rows[:limit]


def _upsert_index(data: dict[str, Any]) -> None:
    ensure_dirs()
    index = {"experiments": []}
    if INDEX_PATH.exists():
        try:
            index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            index = {"experiments": []}
    rows = [r for r in (index.get("experiments") or []) if r.get("experiment_id") != data.get("experiment_id")]
    rows.insert(
        0,
        {
            "experiment_id": data.get("experiment_id"),
            "topic": data.get("topic"),
            "platform": data.get("platform"),
            "status": data.get("status"),
            "variables_tested": data.get("variables_tested"),
            "updated_at": data.get("updated_at"),
            "confidence_level": data.get("confidence_level"),
        },
    )
    index["experiments"] = rows[:200]
    INDEX_PATH.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")


def load_knowledge() -> dict[str, Any]:
    ensure_dirs()
    if not KNOWLEDGE_PATH.exists():
        return {"version": "1.0", "learnings": []}
    try:
        return json.loads(KNOWLEDGE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": "1.0", "learnings": []}


def save_knowledge(data: dict[str, Any]) -> Path:
    ensure_dirs()
    KNOWLEDGE_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return KNOWLEDGE_PATH
