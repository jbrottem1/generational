"""Build CHARACTER_RIG_PACKAGE — permanent digital actor contract."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.character_rig_studio.body_rig import build_body_mechanics, build_body_rig
from services.character_rig_studio.cast_catalog import get_cast_definition
from services.character_rig_studio.face_systems import build_eye_system, build_facial_rig
from services.character_rig_studio.hands import build_hand_system
from services.character_rig_studio.models import ENGINE_ID, PACKAGE_TYPE, PACKAGE_VERSION
from services.character_rig_studio.performance_system import build_performance_system
from services.character_rig_studio.validation import validate_character_rig
from services.character_rig_studio.wardrobe import build_wardrobe

ROOT = Path(__file__).resolve().parents[2]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> dict[str, Any] | None:
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else None
        except Exception:  # noqa: BLE001
            return None
    return None


def _asset_root(studio_asset_path: str | None, character_id: str) -> Path:
    if studio_asset_path:
        p = Path(studio_asset_path)
        return p if p.is_absolute() else ROOT / p
    return ROOT / "data" / "studio_assets" / character_id


def build_character_rig(
    character_id: str,
    *,
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compose a full CHARACTER_RIG_PACKAGE for a cast member."""
    cid = str(character_id or "").upper()
    definition = dict(get_cast_definition(cid) or {})
    if overrides:
        definition.update(overrides)
    if not definition:
        definition = {
            "canonical_name": cid,
            "role": "generational_actor",
            "age_appearance": "adult",
            "body_type": "adult",
            "height_cm": 175,
            "proportions": "standard",
            "continuity_version": "0.1.0",
            "personality": ["present"],
            "wardrobe_outfits": ["default"],
            "default_outfit": "default",
            "studio_asset_path": f"data/studio_assets/{cid}/",
            "status": "draft",
        }

    asset_root = _asset_root(definition.get("studio_asset_path"), cid)
    existing_identity = _read_json(asset_root / "CHARACTER_IDENTITY.json")
    existing_skeleton = _read_json(asset_root / "SKELETON_PROFILE.json")
    existing_face = _read_json(asset_root / "FACE_RIG_PROFILE.json")
    existing_wardrobe = _read_json(asset_root / "WARDROBE_PROFILE.json")
    existing_gestures = _read_json(asset_root / "GESTURE_LIBRARY.json")
    existing_hr = _read_json(asset_root / "HUMAN_REALISM" / "RESOLVED_PACKAGE.json")

    height = float(
        definition.get("height_cm")
        or (existing_identity or {}).get("canonical_height_cm")
        or 175
    )
    body_type = str(definition.get("body_type") or "adult")

    identity = {
        "character_id": cid,
        "canonical_name": definition.get("canonical_name")
        or (existing_identity or {}).get("name")
        or cid,
        "role": definition.get("role") or (existing_identity or {}).get("role"),
        "age_appearance": definition.get("age_appearance")
        or (existing_identity or {}).get("age_range"),
        "body_type": body_type,
        "height_cm": height,
        "proportions": definition.get("proportions") or "canonical",
        "continuity_version": definition.get("continuity_version") or "1.0.0",
        "forbid_regenerate_per_scene": True,
        "permanent_digital_actor": True,
        "is_gold_standard": bool(definition.get("is_gold_standard")),
        "status": definition.get("status") or "permanent",
        "studio_asset_path": str(definition.get("studio_asset_path") or f"data/studio_assets/{cid}/"),
        "voice_ref": definition.get("voice_ref"),
        "composed_from_existing": bool(existing_identity or existing_skeleton),
    }

    body_rig = build_body_rig(
        cid,
        height_cm=height,
        body_type=body_type,
        existing_skeleton=existing_skeleton,
    )
    facial_rig = build_facial_rig(cid, existing_face_rig=existing_face)
    eye_system = build_eye_system(cid)
    hand_system = build_hand_system(cid, existing_gestures=existing_gestures)
    body_mechanics = build_body_mechanics(cid)
    wardrobe = build_wardrobe(
        cid,
        outfits=list(definition.get("wardrobe_outfits") or ["default"]),
        default_outfit=str(definition.get("default_outfit") or "default"),
        existing_wardrobe=existing_wardrobe,
    )
    performance = build_performance_system(
        cid, studio_asset_path=str(definition.get("studio_asset_path") or "")
    )

    materials = {
        "character_id": cid,
        "skin": (existing_hr or {}).get("skin")
        or {"type": "cinematic_skin", "subsurface": True},
        "hair": (existing_hr or {}).get("hair")
        or {"type": "organic_or_styled", "secondary_motion": True},
        "eyes": {"wetness": True, "catchlights": True, "iris_detail": True},
        "metal_or_props": (existing_identity or {}).get("palette") or {},
        "wardrobe_materials_follow_outfit": True,
        "reusable": True,
    }

    personality = {
        "character_id": cid,
        "traits": list(
            definition.get("personality")
            or (existing_identity or {}).get("personality")
            or ["present"]
        ),
        "default_performance_energy": "measured_teach"
        if "educat" in str(identity.get("role") or "")
        else "grounded",
        "camera_awareness": True,
        "reusable": True,
    }

    package: dict[str, Any] = {
        "package_type": PACKAGE_TYPE,
        "package_version": PACKAGE_VERSION,
        "engine_id": ENGINE_ID,
        "created_at": _now(),
        "character_id": cid,
        "philosophy": {
            "not_a_renderer": True,
            "not_an_image_generator": True,
            "not_a_video_generator": True,
            "rule": "Scenes reference the actor. Scenes never recreate the actor.",
            "pipeline": [
                "scene_director_chooses_actors",
                "performance_engine_chooses_actions",
                "character_rig_studio_executes_movement",
                "renderer_records_performance",
            ],
        },
        "identity": identity,
        "body_rig": body_rig,
        "facial_rig": facial_rig,
        "eye_system": eye_system,
        "hand_system": hand_system,
        "body_mechanics": body_mechanics,
        "wardrobe": wardrobe,
        "materials": materials,
        "performance_system": performance,
        "personality": personality,
        "asset_refs": {
            "studio_root": str(definition.get("studio_asset_path") or ""),
            "skeleton": "SKELETON_PROFILE.json" if existing_skeleton else None,
            "face_rig": "FACE_RIG_PROFILE.json" if existing_face else None,
            "wardrobe": "WARDROBE_PROFILE.json" if existing_wardrobe else None,
            "animation": "ANIMATION/" if (asset_root / "ANIMATION").is_dir() else None,
            "character_rig_dir": "CHARACTER_RIG/",
        },
        "architecture": {
            "frozen": True,
            "no_new_renderer": True,
            "no_pipeline_redesign": True,
            "feeds": [
                "character_world_studio",
                "character_performance_engine",
                "character_performance",
                "animation_engine",
                "true_motion",
            ],
        },
    }
    package["validation"] = validate_character_rig(package)
    package["scene_ref"] = {
        "character_id": cid,
        "character_rig_ref": f"data/studio_assets/{cid}/CHARACTER_RIG/CHARACTER_RIG_PACKAGE.json",
        "continuity_version": identity["continuity_version"],
        "do_not_regenerate": True,
    }
    return package
