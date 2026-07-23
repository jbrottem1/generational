"""Searchable production history for the Operations Layer.

Reuses learning ProductionMemory and keeps a lightweight ops index.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.production_operations.status import OPS_ROOT

HISTORY_PATH = OPS_ROOT / "PRODUCTION_HISTORY.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load() -> list[dict]:
    if not HISTORY_PATH.exists():
        return []
    try:
        data = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
        return list(data.get("productions") or [])
    except Exception:  # noqa: BLE001
        return []


def _save(rows: list[dict]) -> None:
    OPS_ROOT.mkdir(parents=True, exist_ok=True)
    HISTORY_PATH.write_text(
        json.dumps({"updated_at": _now(), "productions": rows[-500:]}, indent=2),
        encoding="utf-8",
    )


def store_production(
    *,
    production_id: str,
    brief: dict,
    report: dict,
    status: dict,
    context: dict,
) -> dict[str, Any]:
    """Persist one completed/degraded production into searchable history."""
    record = {
        "production_id": production_id,
        "topic": brief.get("topic"),
        "runtime_sec": brief.get("length_sec"),
        "platform": brief.get("platform"),
        "style": brief.get("style"),
        "narrator": brief.get("narrator"),
        "scores": {
            "overall": report.get("overall_quality_score"),
            "hook": report.get("hook_score"),
            "narration": report.get("narration_score"),
            "visual": report.get("visual_score"),
            "audio": report.get("audio_score"),
            "caption": report.get("caption_score"),
            "educational": report.get("educational_accuracy"),
            "retention": report.get("retention_prediction"),
        },
        "assets_used": list(context.get("ops_export_files") or status.get("current_files") or [])[:40],
        "prompt_used": brief.get("command") or brief.get("topic"),
        "thumbnail": ((context.get("candidates") or [{}])[0] or {}).get("thumbnail"),
        "upload_package": context.get("executive_export") or {},
        "performance_predictions": {
            "ctr": report.get("ctr_prediction"),
            "completion": report.get("completion_prediction"),
            "shareability": report.get("shareability"),
        },
        "recommendation": report.get("final_recommendation"),
        "pipeline_health": status.get("pipeline_health"),
        "stored_at": _now(),
    }
    rows = _load()
    rows = [r for r in rows if r.get("production_id") != production_id]
    rows.append(record)
    _save(rows)

    # Also append to permanent learning memory when available
    try:
        from services.learning.productions import get_production_memory, extract_production_record

        item = (context.get("candidates") or [{}])[0] if context.get("candidates") else {}
        if isinstance(item, dict):
            mem = extract_production_record(
                item,
                {**context, "generation_time_ms": status.get("elapsed_ms")},
                run_id=production_id,
                pipeline_used="production_operations",
            )
            mem["production_id"] = production_id
            get_production_memory().add(mem)
    except Exception:  # noqa: BLE001
        pass

    return record


def search_history(
    *,
    query: str = "",
    platform: str = "",
    limit: int = 25,
) -> list[dict]:
    q = (query or "").lower().strip()
    plat = (platform or "").lower().strip()
    rows = list(reversed(_load()))
    out = []
    for row in rows:
        if plat and plat not in str(row.get("platform") or "").lower():
            continue
        hay = f"{row.get('topic')} {row.get('prompt_used')} {row.get('platform')}".lower()
        if q and q not in hay:
            continue
        out.append(row)
        if len(out) >= limit:
            break
    return out
