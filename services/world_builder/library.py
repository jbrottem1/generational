"""Reusable world library — store, search, extend, reuse (not a disconnected app)."""

from __future__ import annotations

import copy
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.world_builder.catalog import get_catalog, get_world, select_world_type
from services.world_builder.models import WORLD_SCHEMA_VERSION, world_id_for_type

ROOT = Path(__file__).resolve().parents[2]
LIB_ROOT = ROOT / "data" / "world_builder" / "library"
INDEX_PATH = LIB_ROOT / "LIBRARY_INDEX.json"
USAGE_PATH = LIB_ROOT / "USAGE_HISTORY.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", (text or "").lower()) if len(t) > 1}


def ensure_library() -> None:
    LIB_ROOT.mkdir(parents=True, exist_ok=True)
    if not INDEX_PATH.exists():
        INDEX_PATH.write_text(json.dumps({"version": "1.0", "worlds": {}, "updated_at": ""}, indent=2) + "\n", encoding="utf-8")


def load_index() -> dict[str, Any]:
    ensure_library()
    try:
        return json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": "1.0", "worlds": {}, "updated_at": ""}


def save_index(data: dict[str, Any]) -> Path:
    ensure_library()
    data["updated_at"] = _now()
    INDEX_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return INDEX_PATH


def seed_library_from_catalog() -> dict[str, Any]:
    """Register catalog templates into the reusable library."""
    idx = load_index()
    worlds = dict(idx.get("worlds") or {})
    added = 0
    for wid, world in get_catalog().items():
        if wid not in worlds:
            worlds[wid] = _index_entry(world)
            _write_world_file(world)
            added += 1
        else:
            # Keep approved custom worlds; refresh templates lightly
            if worlds[wid].get("source") == "catalog_template":
                worlds[wid] = _index_entry(world)
                _write_world_file(world)
    idx["worlds"] = worlds
    save_index(idx)
    return {"ok": True, "added": added, "total": len(worlds)}


def _index_entry(world: dict[str, Any]) -> dict[str, Any]:
    return {
        "world_id": world.get("world_id"),
        "name": world.get("name"),
        "world_type": world.get("world_type"),
        "category": world.get("category") or world.get("world_type"),
        "topics": world.get("applicable_topics") or world.get("keywords") or [],
        "time_periods": world.get("time_periods") or [],
        "audiences": world.get("audiences") or ["general_public"],
        "visual_styles": world.get("visual_styles") or [],
        "scientific_accuracy": world.get("scientific_accuracy") or world.get("historical_accuracy") or 70,
        "historical_accuracy": world.get("historical_accuracy") or 70,
        "reuse_count": int(world.get("reuse_count") or 0),
        "last_usage": world.get("last_usage") or "",
        "source": world.get("source") or "catalog_template",
        "path": str(LIB_ROOT / f"{world.get('world_id')}.json"),
        "zones": [z.get("id") for z in (world.get("zones") or []) if isinstance(z, dict)],
        "channel_identity": world.get("channel_identity") or "",
    }


def _write_world_file(world: dict[str, Any]) -> Path:
    ensure_library()
    path = LIB_ROOT / f"{world.get('world_id')}.json"
    payload = dict(world)
    payload["schema_version"] = WORLD_SCHEMA_VERSION
    payload["saved_at"] = _now()
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def get_library_world(world_id: str) -> dict[str, Any] | None:
    path = LIB_ROOT / f"{world_id}.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    return get_world(world_id=world_id)


def save_world(world: dict[str, Any], *, source: str = "custom") -> dict[str, Any]:
    world = dict(world)
    world["source"] = source
    world.setdefault("world_id", world_id_for_type(str(world.get("world_type") or world.get("name") or "Custom")))
    _write_world_file(world)
    idx = load_index()
    worlds = dict(idx.get("worlds") or {})
    worlds[str(world["world_id"])] = _index_entry(world)
    idx["worlds"] = worlds
    save_index(idx)
    return world


def create_world_variation(base_world_id: str, *, name: str = "", extra_zones: list[dict] | None = None, overrides: dict | None = None) -> dict[str, Any]:
    base = get_library_world(base_world_id) or get_world(world_id=base_world_id)
    if not base:
        raise ValueError(f"unknown_world:{base_world_id}")
    world = copy.deepcopy(base)
    suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    world["world_id"] = f"{base_world_id}_VAR_{suffix}"
    world["name"] = name or f"{base.get('name')} Variant"
    world["parent_world_id"] = base_world_id
    if extra_zones:
        world.setdefault("zones", []).extend(extra_zones)
    if overrides:
        world.update(overrides)
    return save_world(world, source="variation")


def extend_world(world_id: str, *, zone: dict[str, Any] | None = None, objects: list[dict] | None = None) -> dict[str, Any]:
    world = get_library_world(world_id)
    if not world:
        raise ValueError(f"unknown_world:{world_id}")
    if zone:
        world.setdefault("zones", []).append(zone)
    if objects:
        world.setdefault("objects", []).extend(objects)
    return save_world(world, source=world.get("source") or "extended")


def record_world_usage(world_id: str, *, topic: str = "", production_id: str = "", channel: str = "") -> None:
    ensure_library()
    history = []
    if USAGE_PATH.exists():
        try:
            history = json.loads(USAGE_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            history = []
    history.append({"world_id": world_id, "topic": topic, "production_id": production_id, "channel": channel, "at": _now()})
    USAGE_PATH.write_text(json.dumps(history[-1000:], indent=2) + "\n", encoding="utf-8")
    idx = load_index()
    entry = (idx.get("worlds") or {}).get(world_id)
    if entry:
        entry["reuse_count"] = int(entry.get("reuse_count") or 0) + 1
        entry["last_usage"] = _now()
        idx["worlds"][world_id] = entry
        save_index(idx)


def search_worlds(
    query: str = "",
    *,
    time_period: str = "",
    location_type: str = "",
    audience: str = "",
    channel: str = "",
    limit: int = 8,
) -> list[dict[str, Any]]:
    seed_library_from_catalog()
    q = _tokens(query)
    rows = []
    for entry in (load_index().get("worlds") or {}).values():
        hay = _tokens(
            " ".join(
                [
                    str(entry.get("name") or ""),
                    str(entry.get("world_type") or ""),
                    str(entry.get("category") or ""),
                    " ".join(map(str, entry.get("topics") or [])),
                    " ".join(map(str, entry.get("zones") or [])),
                ]
            )
        )
        overlap = len(q & hay) / max(1, len(q)) if q else 0.3
        if location_type and location_type.lower() not in str(entry.get("world_type") or "").lower() and location_type.lower() not in str(entry.get("category") or "").lower():
            # soft penalty not hard filter
            overlap *= 0.7
        if time_period and entry.get("time_periods") and time_period not in entry.get("time_periods"):
            overlap *= 0.85
        if audience and entry.get("audiences") and audience not in entry.get("audiences"):
            overlap *= 0.9
        reuse = int(entry.get("reuse_count") or 0)
        # Prefer suitable, lightly penalize overuse
        score = overlap * 70 + float(entry.get("scientific_accuracy") or 70) * 0.2 - min(15, reuse * 1.5)
        if channel and entry.get("channel_identity") == channel:
            score += 8
        rows.append({**entry, "selection_score": round(score, 2), "query_overlap": round(overlap, 3)})
    rows.sort(key=lambda r: (-float(r.get("selection_score") or 0), int(r.get("reuse_count") or 0)))
    return rows[:limit]


def select_best_world(
    *,
    topic: str = "",
    niche: str = "",
    location_type: str = "",
    time_period: str = "",
    audience: str = "",
    channel: str = "",
    existing_world_id: str = "",
) -> dict[str, Any]:
    """Return best + alternatives + reasoning (reuse existing when compatible)."""
    if existing_world_id:
        w = get_library_world(existing_world_id)
        if w:
            return {
                "best": _index_entry(w),
                "alternatives": [],
                "selection_reasoning": f"Continuity: reuse existing_world_id={existing_world_id}",
                "reuse_score": 100.0,
                "continuity_compatibility": 1.0,
                "required_adaptations": [],
            }

    hits = search_worlds(topic or location_type or niche, time_period=time_period, location_type=location_type, audience=audience, channel=channel, limit=6)
    # Also bias by catalog select
    preferred_type = select_world_type(topic=topic, niche=niche, preferred=location_type)
    for h in hits:
        if h.get("world_type") == preferred_type:
            h["selection_score"] = float(h.get("selection_score") or 0) + 15
    hits.sort(key=lambda r: -float(r.get("selection_score") or 0))
    if not hits:
        w = get_world(world_type=preferred_type) or get_world(world_type="Research Center")
        return {
            "best": _index_entry(w or {}),
            "alternatives": [],
            "selection_reasoning": f"Fallback template for type={preferred_type}",
            "reuse_score": 0.0,
            "continuity_compatibility": 0.5,
            "required_adaptations": ["seed_from_template"],
        }
    best = hits[0]
    return {
        "best": best,
        "alternatives": hits[1:4],
        "selection_reasoning": (
            f"Selected {best.get('world_id')} ({best.get('world_type')}) for topic='{topic}' "
            f"via semantic overlap={best.get('query_overlap')} and accuracy={best.get('scientific_accuracy')}"
        ),
        "reuse_score": float(100 - min(40, int(best.get("reuse_count") or 0) * 3)),
        "continuity_compatibility": 1.0 if not existing_world_id else 0.8,
        "required_adaptations": [],
    }
