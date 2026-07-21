"""Persist PQA reports and learning comparisons."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.log import get_logger, log_event

logger = get_logger(__name__)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STORE = ROOT / "data" / "generational_os" / "pqa_reports"
VALIDATION_DIR = ROOT / "data" / "productions" / "_validation" / "production_qa"


def _now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def store_report(report: dict[str, Any], *, idea_id: str = "", store_dir: Path | None = None) -> Path:
    """Append-friendly storage: one JSON file per report + rolling index."""
    store_dir = Path(store_dir or DEFAULT_STORE)
    store_dir.mkdir(parents=True, exist_ok=True)
    safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in (idea_id or report.get("idea_id") or "item"))[:48]
    path = store_dir / f"pqa_{safe_id}_{_now_stamp()}.json"
    path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    index_path = store_dir / "index.json"
    index: list[dict] = []
    if index_path.is_file():
        try:
            index = json.loads(index_path.read_text(encoding="utf-8"))
            if not isinstance(index, list):
                index = []
        except Exception:
            index = []
    index.append(
        {
            "path": str(path.relative_to(ROOT)) if str(path).startswith(str(ROOT)) else str(path),
            "idea_id": report.get("idea_id"),
            "title": report.get("title"),
            "overall_score": report.get("overall_score"),
            "decision": report.get("decision"),
            "created_at": report.get("created_at"),
        }
    )
    index_path.write_text(json.dumps(index[-500:], indent=2), encoding="utf-8")
    log_event(logger, "production_qa.report_stored", path=str(path), decision=report.get("decision"))
    return path


def write_validation_bundle(report: dict[str, Any], *, name: str = "PQA_E2E") -> dict[str, Path]:
    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
    json_path = VALIDATION_DIR / f"{name}.json"
    md_path = VALIDATION_DIR / f"{name}_REPORT.md"
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    md_path.write_text(str(report.get("report_markdown") or "# PQA\n"), encoding="utf-8")
    return {"json": json_path, "markdown": md_path}


def load_recent_reports(limit: int = 50, store_dir: Path | None = None) -> list[dict]:
    store_dir = Path(store_dir or DEFAULT_STORE)
    index_path = store_dir / "index.json"
    if not index_path.is_file():
        return []
    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    out: list[dict] = []
    for entry in reversed(index[-limit:]):
        rel = entry.get("path") or ""
        path = ROOT / rel if not Path(rel).is_absolute() else Path(rel)
        if path.is_file():
            try:
                out.append(json.loads(path.read_text(encoding="utf-8")))
            except Exception:
                continue
    return out
