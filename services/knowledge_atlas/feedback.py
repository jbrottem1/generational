"""Knowledge Atlas post-lesson feedback — self-improvement loop."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.knowledge_atlas.catalog import load_atlas, save_catalog
from services.knowledge_atlas.models import AtlasAsset

FEEDBACK_PATH = Path(__file__).resolve().parents[2] / "data" / "knowledge_atlas" / "feedback.json"


def _load_feedback() -> dict[str, Any]:
    if not FEEDBACK_PATH.is_file():
        return {"schema_version": 1, "entries": []}
    return json.loads(FEEDBACK_PATH.read_text(encoding="utf-8"))


def _save_feedback(data: dict[str, Any]) -> None:
    FEEDBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
    FEEDBACK_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def record_lesson_visuals(
    *,
    lesson_id: str,
    asset_ids: list[str],
    effective: bool = True,
    notes: str = "",
) -> dict[str, Any]:
    """Record visual usage after a lesson; bump reuse counts."""
    catalog = load_atlas()
    ts = datetime.now(timezone.utc).isoformat()
    used: list[str] = []

    for aid in asset_ids:
        asset = catalog.get(aid)
        if asset is None:
            continue
        used.append(aid)
        history = list(asset.reuse_history) + [f"{lesson_id}@{ts}"]
        payload = asset.to_dict()
        payload["reuse_count"] = asset.reuse_count + 1
        payload["reuse_history"] = history[-20:]
        catalog[aid] = AtlasAsset.from_dict(payload)

    if used:
        save_catalog(catalog)

    entry = {
        "lesson_id": lesson_id,
        "asset_ids": used,
        "effective": effective,
        "notes": notes,
        "recorded_at": ts,
    }
    fb = _load_feedback()
    fb.setdefault("entries", []).append(entry)
    _save_feedback(fb)
    return entry
