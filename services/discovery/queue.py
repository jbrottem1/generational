"""Real-time discovery production queue — persisted, continuously reordered."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.env import project_root
from services.discovery.models import QueueItem, _now_iso

QUEUE_DIR = project_root() / "data" / "discovery"
QUEUE_PATH = QUEUE_DIR / "PRODUCTION_QUEUE.json"


def _default_payload() -> dict[str, Any]:
    return {
        "updated_at": _now_iso(),
        "items": [],
        "series": [],
        "deferred": [],
        "stats": {"queued": 0, "ready": 0, "deferred": 0},
    }


def load_queue(path: Path | None = None) -> dict[str, Any]:
    target = path or QUEUE_PATH
    if not target.is_file():
        return _default_payload()
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "items" in data:
            return data
    except Exception:  # noqa: BLE001
        pass
    return _default_payload()


def save_queue(payload: dict[str, Any], path: Path | None = None) -> Path:
    target = path or QUEUE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    payload["updated_at"] = _now_iso()
    items = payload.get("items") or []
    deferred = payload.get("deferred") or []
    payload["stats"] = {
        "queued": sum(1 for i in items if i.get("status") == "queued"),
        "ready": sum(1 for i in items if i.get("status") == "ready"),
        "deferred": len(deferred),
        "total": len(items),
    }
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return target


def upsert_items(items: list[QueueItem], *, path: Path | None = None) -> dict[str, Any]:
    """Merge new ranked items into the queue; reorder by publishing_priority."""
    payload = load_queue(path)
    by_topic = {str(i.get("topic") or "").lower(): i for i in payload.get("items") or []}
    for item in items:
        key = item.topic.lower()
        existing = by_topic.get(key)
        data = item.to_dict()
        if existing:
            data["queue_id"] = existing.get("queue_id") or data["queue_id"]
            data["created_at"] = existing.get("created_at") or data["created_at"]
            # Preserve in_production / published
            if existing.get("status") in ("in_production", "published"):
                data["status"] = existing["status"]
        by_topic[key] = data

    merged = list(by_topic.values())
    merged.sort(
        key=lambda i: (
            int(i.get("publishing_priority") or 0),
            int(i.get("discovery_score") or 0),
            float(i.get("confidence_score") or 0),
        ),
        reverse=True,
    )
    # Re-number priorities after sort
    for idx, row in enumerate(merged):
        if row.get("status") not in ("in_production", "published", "deferred"):
            row["publishing_priority"] = max(1, 100 - idx)
            row["updated_at"] = _now_iso()
    payload["items"] = merged
    save_queue(payload, path)
    return payload


def defer_item(topic: str, reason: str, verification: dict[str, Any], *, path: Path | None = None) -> dict[str, Any]:
    payload = load_queue(path)
    deferred = list(payload.get("deferred") or [])
    deferred.append(
        {
            "topic": topic,
            "reason": reason,
            "verification": verification,
            "updated_at": _now_iso(),
        }
    )
    # Keep last 100 deferrals
    payload["deferred"] = deferred[-100:]
    # Mark matching queue item deferred if present
    for item in payload.get("items") or []:
        if str(item.get("topic") or "").lower() == topic.lower():
            item["status"] = "deferred"
            item["verification"] = verification
            item["updated_at"] = _now_iso()
    save_queue(payload, path)
    return payload


def top_queue(n: int = 10, *, path: Path | None = None) -> list[dict[str, Any]]:
    payload = load_queue(path)
    items = [
        i
        for i in payload.get("items") or []
        if i.get("status") in ("queued", "ready")
    ]
    return items[:n]
