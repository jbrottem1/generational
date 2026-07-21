"""World state management — doors, moves, displays, continuity inheritance."""

from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.world_builder.models import STATE_EVENT_TYPES, empty_world_state

ROOT = Path(__file__).resolve().parents[2]
STATE_ROOT = ROOT / "data" / "world_builder" / "state"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def state_path(world_id: str, production_id: str = "default") -> Path:
    safe_w = "".join(c if c.isalnum() or c in "-_" else "_" for c in world_id)
    safe_p = "".join(c if c.isalnum() or c in "-_" else "_" for c in production_id) or "default"
    return STATE_ROOT / safe_w / f"{safe_p}.json"


def load_state(world_id: str, production_id: str = "default") -> dict[str, Any]:
    path = state_path(world_id, production_id)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    return empty_world_state(world_id=world_id, production_id=production_id)


def save_state(state: dict[str, Any]) -> Path:
    path = state_path(str(state.get("world_id") or "WORLD"), str(state.get("production_id") or "default"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    return path


def initialize_state_from_world(world: dict[str, Any], *, production_id: str = "default") -> dict[str, Any]:
    """Seed object positions and environment from world definition."""
    wid = str(world.get("world_id") or "")
    state = empty_world_state(world_id=wid, production_id=production_id)
    positions = {}
    for obj in list(world.get("objects") or []) + list(world.get("furniture") or []):
        if not isinstance(obj, dict):
            continue
        oid = str(obj.get("object_id") or obj.get("name") or "")
        if oid:
            positions[oid] = {
                "position": dict(obj.get("position") or {}),
                "zone": obj.get("zone") or "",
                "surface": obj.get("surface") or "floor",
                "anchored": bool(obj.get("anchored", True)),
            }
    state["object_positions"] = positions
    state["weather"] = str(world.get("weather") or "")
    state["environment_state"] = {
        "architecture": list(world.get("architecture") or []),
        "scale": world.get("scale") or "",
        "zones": [z.get("id") for z in (world.get("zones") or []) if isinstance(z, dict)],
    }
    for z in world.get("zones") or []:
        if isinstance(z, dict) and z.get("doors"):
            for d in z["doors"]:
                state["doors"][str(d)] = "closed"
    save_state(state)
    return state


def apply_state_event(state: dict[str, Any], event_type: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Mutate and persist world state. Later scenes inherit unless reset."""
    if event_type not in STATE_EVENT_TYPES:
        raise ValueError(f"unknown_state_event:{event_type}")
    out = copy.deepcopy(state)
    payload = dict(payload or {})
    event = {"type": event_type, "at": _now(), "payload": payload}
    out.setdefault("events", []).append(event)
    out["version"] = int(out.get("version") or 1) + 1

    if event_type == "reset":
        wid = str(out.get("world_id") or "")
        pid = str(out.get("production_id") or "default")
        out = empty_world_state(world_id=wid, production_id=pid)
        out["events"] = [event]
        save_state(out)
        return out

    if event_type == "door_toggled":
        door = str(payload.get("door_id") or "")
        if door:
            cur = out.setdefault("doors", {}).get(door, "closed")
            out["doors"][door] = payload.get("state") or ("open" if cur == "closed" else "closed")

    if event_type == "object_moved":
        oid = str(payload.get("object_id") or "")
        if oid:
            entry = out.setdefault("object_positions", {}).setdefault(oid, {})
            if payload.get("position"):
                entry["position"] = dict(payload["position"])
            if payload.get("zone"):
                entry["zone"] = payload["zone"]
            entry["moved_at"] = _now()
            entry["move_reason"] = payload.get("reason") or "script"

    if event_type == "display_activated":
        did = str(payload.get("display_id") or "")
        if did:
            out.setdefault("displays", {})[did] = {"active": True, "content": payload.get("content") or ""}

    if event_type == "equipment_introduced":
        oid = str(payload.get("object_id") or payload.get("name") or "")
        if oid and oid not in out.get("introduced_objects", []):
            out.setdefault("introduced_objects", []).append(oid)
            out.setdefault("object_positions", {})[oid] = {
                "position": dict(payload.get("position") or {}),
                "zone": payload.get("zone") or "",
                "surface": payload.get("surface") or "floor",
                "anchored": True,
                "introduced": True,
            }

    if event_type == "weather_changed":
        out["weather"] = str(payload.get("weather") or out.get("weather") or "")

    if event_type == "time_advanced":
        out["time_of_day"] = str(payload.get("time_of_day") or out.get("time_of_day") or "day")

    if event_type == "environmental_damage":
        area = str(payload.get("area") or "general")
        out.setdefault("damage", {})[area] = payload.get("description") or "damaged"

    if event_type == "character_entered":
        name = str(payload.get("character") or "")
        if name and name not in out.get("characters_present", []):
            out.setdefault("characters_present", []).append(name)
        zone = str(payload.get("zone") or "")
        if zone and zone not in out.get("visited_zones", []):
            out.setdefault("visited_zones", []).append(zone)

    if event_type == "character_exited":
        name = str(payload.get("character") or "")
        out["characters_present"] = [c for c in out.get("characters_present") or [] if c != name]

    if event_type == "experiment_progressed":
        out.setdefault("environment_state", {})["experiment"] = payload

    if event_type == "location_state_changed":
        out.setdefault("environment_state", {}).update(payload)

    # Visit zone tracking
    zone = str(payload.get("zone") or "")
    if zone and zone not in (out.get("visited_zones") or []):
        out.setdefault("visited_zones", []).append(zone)

    save_state(out)
    return out


def reset_world_state(world_id: str, production_id: str = "default") -> dict[str, Any]:
    state = empty_world_state(world_id=world_id, production_id=production_id)
    state["events"] = [{"type": "reset", "at": _now(), "payload": {}}]
    save_state(state)
    return state


def continuity_snapshot(state: dict[str, Any]) -> dict[str, Any]:
    """Compact continuity block for Environment Packages."""
    return {
        "version": state.get("version"),
        "time_of_day": state.get("time_of_day"),
        "weather": state.get("weather"),
        "object_positions": state.get("object_positions") or {},
        "visited_zones": state.get("visited_zones") or [],
        "doors": state.get("doors") or {},
        "displays": state.get("displays") or {},
        "introduced_objects": state.get("introduced_objects") or [],
        "characters_present": state.get("characters_present") or [],
        "event_count": len(state.get("events") or []),
    }
