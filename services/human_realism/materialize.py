"""Persist framework + per-character inherited packages under data/human_realism/."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.human_realism.base import FRAMEWORK_ID, FRAMEWORK_VERSION, GOLD_STANDARD_CHARACTER_ID, base_framework
from services.human_realism.characters import list_character_ids
from services.human_realism.resolve import profile_views, resolve_character

ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = ROOT / "data" / "human_realism"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str) + "\n", encoding="utf-8")


def _write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def continuity_md(resolved: dict[str, Any]) -> str:
    cid = resolved["character_id"]
    name = resolved.get("name") or cid
    ref = resolved.get("reference_implementation") or GOLD_STANDARD_CHARACTER_ID
    return f"""# Character Continuity Rules — {name} (`{cid}`)

Inherits **{FRAMEWORK_ID}** v{FRAMEWORK_VERSION}.

1. Never regenerate this character from scratch.  
2. Inherit shared Human Realism systems; override only identity fields.  
3. Gold-standard reference implementation: `{GOLD_STANDARD_CHARACTER_ID}` (The Doctor).  
4. This character's reference: `{ref}`.  
5. Style mode: **{resolved.get("style_mode")}** — cinematic realism.  
6. Require PerformancePlan on every scene featuring this character.  
7. Reject robotic stillness, sliding feet, lifeless eyes, identity drift.  
8. Version changes must remain silhouette-recognizable.
"""


def materialize_character(character_id: str, *, also_to: Path | None = None) -> dict[str, Any]:
    resolved = resolve_character(character_id)
    views = profile_views(resolved)
    char_dir = DATA_ROOT / "characters" / resolved["character_id"]
    for name, data in views.items():
        _write_json(char_dir / name, data)
    _write_md(char_dir / "CHARACTER_CONTINUITY_RULES.md", continuity_md(resolved))

    if also_to is not None:
        also_to.mkdir(parents=True, exist_ok=True)
        hr = also_to / "HUMAN_REALISM"
        for name, data in views.items():
            if name == "RESOLVED_PACKAGE.json":
                continue
            _write_json(also_to / name, data)
            _write_json(hr / name, data)
        _write_md(also_to / "CHARACTER_CONTINUITY_RULES.md", continuity_md(resolved))
        _write_md(hr / "CHARACTER_CONTINUITY_RULES.md", continuity_md(resolved))
        _write_json(hr / "RESOLVED_PACKAGE.json", resolved)
        _write_json(
            also_to / "HUMAN_REALISM_INDEX.json",
            {
                "character_id": resolved["character_id"],
                "framework_id": FRAMEWORK_ID,
                "framework_version": FRAMEWORK_VERSION,
                "is_gold_standard": resolved.get("is_gold_standard"),
                "profiles": list(views.keys()) + ["CHARACTER_CONTINUITY_RULES.md"],
            },
        )

    return {
        "character_id": resolved["character_id"],
        "path": str(char_dir),
        "is_gold_standard": resolved.get("is_gold_standard"),
    }


def materialize_framework(*, include_characters: bool = True) -> dict[str, Any]:
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    framework = base_framework()
    _write_json(
        DATA_ROOT / "FRAMEWORK_V1.json",
        {
            **framework,
            "gold_standard_character_id": GOLD_STANDARD_CHARACTER_ID,
            "materialized_at": _now(),
            "characters": list_character_ids(),
        },
    )
    _write_json(
        DATA_ROOT / "PERFORMANCE_PLAN.schema.json",
        {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "generational://human_realism/PERFORMANCE_PLAN.schema.json",
            "title": "PerformancePlan",
            "type": "object",
            "required": framework["performance_plan_required_fields"],
            "properties": {
                "character_id": {"type": "string"},
                "scene_id": {"type": "string"},
                "objective": {"type": "string"},
                "emotion": {"type": "object"},
                "gaze": {"type": "object"},
                "body_language": {"type": "object"},
                "gesture": {"type": "object"},
                "walking_style": {"type": "string"},
                "breathing": {"type": "object"},
                "facial_performance": {"type": "object"},
                "interaction_targets": {"type": "array"},
                "camera_awareness": {"type": "object"},
                "environmental_reactions": {"type": "object"},
                "foot_contact_required": {"type": "boolean"},
            },
        },
    )

    char_reports = []
    if include_characters:
        doctor_root = ROOT / "data" / "studio_assets" / "DOCTOR_001"
        for cid in list_character_ids():
            also = doctor_root if cid == GOLD_STANDARD_CHARACTER_ID else None
            char_reports.append(materialize_character(cid, also_to=also))

    index = {
        "framework_id": FRAMEWORK_ID,
        "framework_version": FRAMEWORK_VERSION,
        "gold_standard": GOLD_STANDARD_CHARACTER_ID,
        "characters": char_reports,
        "updated_at": _now(),
        "inheritance": "BASE_HUMAN_REALISM <- character identity overrides",
        "architecture": {
            "no_new_renderer": True,
            "no_pipeline_redesign": True,
            "structured_data_and_soft_bindings_only": True,
        },
    }
    _write_json(DATA_ROOT / "INDEX.json", index)
    return index
