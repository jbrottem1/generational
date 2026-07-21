"""Reusable animation clip library owned by each actor."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.character_rig_studio.models import PERFORMANCE_CLIPS

ROOT = Path(__file__).resolve().parents[2]


def build_performance_system(
    character_id: str,
    *,
    studio_asset_path: str | None = None,
) -> dict[str, Any]:
    cid = str(character_id).upper()
    existing = _load_animation_index(studio_asset_path)
    clips: dict[str, Any] = {}
    for name in PERFORMANCE_CLIPS:
        src = None
        if existing:
            # Map engine clip names → existing DOCTOR animation filenames
            src = _map_existing(name, existing)
        clips[name] = {
            "clip_id": f"{cid}_{name}",
            "name": name,
            "reusable": True,
            "loop": name in {"idle", "walking", "typing", "listening"},
            "rig_bound": True,
            "source_file": src,
            "status": "bound" if src else "template",
        }

    return {
        "character_id": cid,
        "clip_count": len(clips),
        "required_clips": list(PERFORMANCE_CLIPS),
        "clips": clips,
        "animation_library_ref": (
            f"{studio_asset_path.rstrip('/')}/ANIMATION/" if studio_asset_path else None
        ),
        "existing_index": existing,
        "philosophy": "Actors own clips. Scenes choose actions. Never regenerate walks per episode.",
        "reusable": True,
    }


def _load_animation_index(studio_asset_path: str | None) -> dict[str, Any] | None:
    if not studio_asset_path:
        return None
    path = ROOT / studio_asset_path / "ANIMATION" / "index.json"
    if not path.is_file():
        # path may already include data/studio_assets/...
        alt = Path(studio_asset_path)
        if not alt.is_absolute():
            alt = ROOT / studio_asset_path
        path = alt / "ANIMATION" / "index.json"
    if path.is_file():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return None
    return None


def _map_existing(name: str, index: dict[str, Any]) -> str | None:
    clips = index.get("clips") or {}
    aliases = {
        "idle": "idle",
        "thinking": "listening",
        "teaching": "teaching",
        "listening": "listening",
        "greeting": "greeting",
        "walking": "walking_cycle",
        "turning": "turning",
        "explaining": "explaining",
        "laughing": "reaction_amusement",
        "typing": "typing",
        "writing": "typing",
        "pointing": "pointing",
        "looking_around": "looking_around",
        "picking_up_objects": "picking_up_objects",
        "opening_doors": "picking_up_objects",
        "sitting": "idle",
        "standing": "idle",
        "reacting": "reaction_curiosity",
    }
    key = aliases.get(name, name)
    rel = clips.get(key)
    return str(rel) if rel else None
