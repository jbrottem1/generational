"""Request collection — upstream plans become normalized generation requests.

The engine consumes what the pipeline already decided (it never plans
content): the Creative Studio's `asset_requirements`, storyboard scene
context, character plan, and thumbnail concepts are folded into
provider-agnostic `GENERATION_REQUEST_FIELDS` dicts, enriched with each
scene's lighting, palette, emotion, and camera direction so prompts stay
faithful to the creative blueprint.

Items that never went through the Creative Studio still work: a fallback
derives minimal scene + thumbnail requests from the item's own
`scene_breakdown` / title / hook — the engine never dead-ends on missing
upstream data.
"""

from __future__ import annotations

from services.asset_generation.catalog import resolve_asset_type
from services.asset_generation.config import AssetGenerationConfig, get_asset_generation_config


def collect_generation_requests(
    item: dict, config: "AssetGenerationConfig | None" = None
) -> "list[dict]":
    """Every normalized generation request for one ContentPackage item."""
    config = config or get_asset_generation_config()
    creative = item.get("creative_package") or {}

    if creative.get("asset_requirements") or creative.get("storyboard"):
        requests = _from_creative_package(item, creative, config)
    else:
        requests = _fallback_requests(item, config)

    return requests[: max(1, int(config.max_assets_per_item))]


# ------------------------------------------------------- creative package


def _from_creative_package(item: dict, creative: dict, config: AssetGenerationConfig) -> "list[dict]":
    blueprint = creative.get("creative_blueprint") or {}
    scenes = {
        str(scene.get("scene_id", "")): scene
        for scene in creative.get("storyboard", [])
        if isinstance(scene, dict)
    }
    aspect_ratio = str(blueprint.get("aspect_ratio", "") or config.default_aspect_ratio)
    requests = []

    for requirement in creative.get("asset_requirements", []):
        if not isinstance(requirement, dict):
            continue
        scene = scenes.get(str(requirement.get("scene_id", "")), {})
        entry = resolve_asset_type(str(requirement.get("asset_type", "")))
        asset_class = entry["asset_class"]
        requests.append(
            _request(
                item,
                config,
                asset_id=str(requirement.get("asset_id", "")),
                scene_id=str(requirement.get("scene_id", "")),
                asset_type=str(requirement.get("asset_type", "")) or entry["type_id"],
                asset_class=asset_class,
                category=str(requirement.get("category", "") or ""),
                description=str(requirement.get("description", "")),
                prompt=str(requirement.get("prompt", "")),
                style=str(requirement.get("style", "") or blueprint.get("visual_style", "")),
                priority=str(requirement.get("priority", "recommended")),
                reusable=bool(requirement.get("reusable", False)),
                # Utility assets (icons, logos, textures, props) keep their
                # catalog aspect; scene-tied assets follow the blueprint.
                aspect_ratio=(
                    entry["default_aspect_ratio"]
                    if entry["default_aspect_ratio"] == "1:1"
                    else aspect_ratio
                ),
                resolution=_resolution(entry, asset_class, config),
                duration_sec=float(scene.get("estimated_duration_sec", 0) or 0) if asset_class == "video" else 0.0,
                character_ids=list(scene.get("characters", []) or []),
                lighting=str(scene.get("lighting", "")),
                color_palette=str(scene.get("color_palette", "")),
                mood=str(blueprint.get("tone", "")),
                emotion=str(scene.get("emotion", "")),
                camera=_camera(scene),
                source="creative_studio",
            )
        )

    for concept in creative.get("thumbnail_concepts", []):
        if not isinstance(concept, dict):
            continue
        entry = resolve_asset_type("thumbnail")
        prompt_parts = [str(concept.get("direction", ""))]
        if concept.get("text_overlay"):
            prompt_parts.append(f"bold text overlay: \"{concept['text_overlay']}\"")
        if concept.get("color_strategy"):
            prompt_parts.append(str(concept["color_strategy"]))
        source_scene = scenes.get(str(concept.get("source_scene", "")), {})
        requests.append(
            _request(
                item,
                config,
                asset_id=str(concept.get("concept_id", "")),
                scene_id=str(concept.get("source_scene", "")),
                asset_type="thumbnail",
                asset_class="image",
                category="thumbnail",
                description=str(concept.get("direction", "")),
                prompt=", ".join(part for part in prompt_parts if part),
                style=str(concept.get("style", "") or blueprint.get("visual_style", "")),
                priority="required",
                reusable=False,
                aspect_ratio=entry["default_aspect_ratio"],
                resolution=entry["default_resolution"],
                duration_sec=0.0,
                character_ids=list(source_scene.get("characters", []) or []),
                lighting=str(source_scene.get("lighting", "")),
                color_palette=str(concept.get("color_strategy", "") or source_scene.get("color_palette", "")),
                mood=str(blueprint.get("tone", "")),
                emotion=str(source_scene.get("emotion", "")),
                camera="",
                source="thumbnail",
            )
        )

    return requests


# --------------------------------------------------------------- fallback


def _fallback_requests(item: dict, config: AssetGenerationConfig) -> "list[dict]":
    """Minimal scene + thumbnail requests for un-designed items."""
    requests = []
    entry = resolve_asset_type("scene_image")
    breakdown = item.get("scene_breakdown") or []
    for index, scene in enumerate(breakdown, start=1):
        if isinstance(scene, dict):
            text = str(
                scene.get("visual")
                or scene.get("visual_description")
                or scene.get("description")
                or scene.get("narration")
                or ""
            ).strip()
        else:
            text = str(scene).strip()
        if not text:
            continue
        requests.append(
            _request(
                item,
                config,
                asset_id=f"scene_{index:02d}_visual",
                scene_id=f"scene_{index:02d}",
                asset_type="scene_image",
                asset_class="image",
                category="scene_visual",
                description=text[:200],
                prompt=text,
                style=str(item.get("visual_style", "")),
                priority="required",
                reusable=False,
                aspect_ratio=config.default_aspect_ratio,
                resolution=_resolution(entry, "image", config),
                duration_sec=0.0,
                character_ids=[],
                lighting="",
                color_palette="",
                mood="",
                emotion="",
                camera="",
                source="fallback",
            )
        )

    title = str(item.get("title") or item.get("topic") or "").strip()
    hook = str(item.get("hook", "")).strip()
    if title or hook:
        thumb = resolve_asset_type("thumbnail")
        requests.append(
            _request(
                item,
                config,
                asset_id="thumb_fallback",
                scene_id="",
                asset_type="thumbnail",
                asset_class="image",
                category="thumbnail",
                description=f"Thumbnail for: {title or hook}",
                prompt=f"high-contrast thumbnail illustrating {hook or title}",
                style=str(item.get("visual_style", "")),
                priority="required",
                reusable=False,
                aspect_ratio=thumb["default_aspect_ratio"],
                resolution=thumb["default_resolution"],
                duration_sec=0.0,
                character_ids=[],
                lighting="",
                color_palette="",
                mood="",
                emotion="",
                camera="",
                source="fallback",
            )
        )
    return requests


# ------------------------------------------------------------------ shared


def _request(item: dict, config: AssetGenerationConfig, **fields) -> dict:
    request = {
        "asset_id": "",
        "project_id": str(item.get("project_id", "")),
        "scene_id": "",
        "asset_type": "image",
        "asset_class": "image",
        "category": "",
        "description": "",
        "prompt": "",
        "style": "",
        "priority": "recommended",
        "reusable": False,
        "aspect_ratio": config.default_aspect_ratio,
        "resolution": "",
        "duration_sec": 0.0,
        "character_ids": [],
        "lighting": "",
        "color_palette": "",
        "mood": "",
        "emotion": "",
        "camera": "",
        "brand_id": str(item.get("brand_id", "") or item.get("brand", "")),
        "source": "creative_studio",
    }
    request.update(fields)
    if not request["resolution"]:
        request["resolution"] = config.default_resolutions.get(request["asset_class"], "1024x1024")
    return request


def _resolution(entry: dict, asset_class: str, config: AssetGenerationConfig) -> str:
    return entry.get("default_resolution") or config.default_resolutions.get(asset_class, "1024x1024")


def _camera(scene: dict) -> str:
    parts = [str(scene.get("camera_angle", "")), str(scene.get("camera_movement", ""))]
    return ", ".join(part for part in parts if part)
