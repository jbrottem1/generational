"""Universe continuity — characters and worlds stay consistent across productions."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = ROOT / "data" / "character_world_studio" / "CONTINUITY_STATE.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_continuity() -> dict[str, Any]:
    if STATE_PATH.is_file():
        try:
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            pass
    return {
        "version": 1,
        "characters_seen": {},
        "locations_seen": {},
        "productions": [],
    }


def save_continuity(state: dict[str, Any]) -> Path:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2, default=str) + "\n", encoding="utf-8")
    return STATE_PATH


def remember_production(
    *,
    topic: str,
    production_id: str,
    hosts: list[dict[str, Any]],
    location: dict[str, Any],
) -> dict[str, Any]:
    state = load_continuity()
    for h in hosts:
        cid = str(h.get("id") or "")
        row = dict(state["characters_seen"].get(cid) or {"id": cid, "name": h.get("name"), "appearances": 0})
        row["appearances"] = int(row.get("appearances") or 0) + 1
        row["last_seen"] = _now()
        row["last_topic"] = topic
        row["signature_clothing"] = h.get("signature_clothing")
        row["silhouette"] = h.get("silhouette")
        state["characters_seen"][cid] = row
    lid = str(location.get("id") or "")
    loc_row = dict(state["locations_seen"].get(lid) or {"id": lid, "name": location.get("name"), "uses": 0})
    loc_row["uses"] = int(loc_row.get("uses") or 0) + 1
    loc_row["last_seen"] = _now()
    loc_row["architecture"] = location.get("architecture")
    loc_row["detail_dressing"] = location.get("detail_dressing")
    state["locations_seen"][lid] = loc_row
    state["productions"] = ([{"topic": topic, "production_id": production_id, "at": _now()}] + list(state.get("productions") or []))[:50]
    save_continuity(state)
    return state


def continuity_notes(hosts: list[dict[str, Any]], location: dict[str, Any]) -> dict[str, Any]:
    state = load_continuity()
    return {
        "characters_prior_appearances": {
            h["id"]: (state.get("characters_seen") or {}).get(h["id"], {}).get("appearances", 0) for h in hosts
        },
        "location_prior_uses": (state.get("locations_seen") or {}).get(str(location.get("id") or ""), {}).get("uses", 0),
        "rules": [
            "Character silhouette and clothing remain locked per host bible",
            "Location architecture and prop dressing remain consistent across visits",
            "Do not invent alternate wardrobe without continuity update",
        ],
    }
