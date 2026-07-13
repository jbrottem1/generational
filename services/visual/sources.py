"""Asset source adapters — where every visual comes from.

The Director never hardcodes a provider. Every scene declares a recommended
`asset_type`, and this module turns that into a provider-agnostic **asset
request** through a registered adapter. Renderers (and future engines) fulfil
requests with whichever concrete backend is wired at that time — swapping
Midjourney for Flux, or one stock library for another, never touches the
Director.

Built-in adapters:

- `ai_image` — AI image generation (prompt-driven)
- `ai_video` — AI video generation (prompt-driven)
- `stock_footage` — licensed stock libraries (query-driven)
- `user_asset` — user-uploaded footage/images (tag-driven lookup)
- `brand_asset` — brand kits: logos, intros, lower-thirds (slot-driven)
- `avatar` — future AI avatar/presenter assets (stub, not yet available)

Register new sources at runtime via `register_source()` — the Visual
Intelligence Engine never changes when the source library grows.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class AssetSourceAdapter(ABC):
    """One place visual assets can come from."""

    key: str = "base"
    label: str = "Base Source"
    asset_kind: str = "image"  # image / video / any

    def is_available(self) -> bool:
        """Whether a concrete backend exists for this source today."""
        return True

    @abstractmethod
    def build_request(self, scene: dict) -> dict:
        """Provider-agnostic asset request for one scene (JSON-safe dict)."""

    def _base_request(self, scene: dict) -> dict:
        return {
            "source": self.key,
            "asset_kind": self.asset_kind,
            "scene_number": scene.get("scene_number", 0),
            "duration_sec": scene.get("length_sec", 0),
            "aspect_ratio": scene.get("aspect_ratio", "9:16"),
        }


class AIImageSource(AssetSourceAdapter):
    key = "ai_image"
    label = "AI Image Generation"
    asset_kind = "image"

    def build_request(self, scene: dict) -> dict:
        request = self._base_request(scene)
        request["prompt"] = scene.get("ai_image_prompt", "")
        request["style"] = scene.get("visual_style", "cinematic")
        return request


class AIVideoSource(AssetSourceAdapter):
    key = "ai_video"
    label = "AI Video Generation"
    asset_kind = "video"

    def build_request(self, scene: dict) -> dict:
        request = self._base_request(scene)
        request["prompt"] = scene.get("ai_video_prompt", "")
        request["camera_motion"] = scene.get("camera_motion", "")
        request["style"] = scene.get("visual_style", "cinematic")
        return request


class StockFootageSource(AssetSourceAdapter):
    key = "stock_footage"
    label = "Licensed Stock Footage"
    asset_kind = "video"

    def build_request(self, scene: dict) -> dict:
        request = self._base_request(scene)
        request["query"] = scene.get("stock_footage_query", "")
        request["mood"] = scene.get("emotion", "")
        request["license"] = "commercial"
        return request


class UserAssetSource(AssetSourceAdapter):
    key = "user_asset"
    label = "User Uploaded Assets"
    asset_kind = "any"

    def build_request(self, scene: dict) -> dict:
        request = self._base_request(scene)
        request["tags"] = scene.get("stock_footage_query", "").split()
        request["fallback_source"] = "stock_footage"
        return request


class BrandAssetSource(AssetSourceAdapter):
    key = "brand_asset"
    label = "Brand Assets"
    asset_kind = "any"

    def build_request(self, scene: dict) -> dict:
        request = self._base_request(scene)
        request["slot"] = "outro_branding" if scene.get("purpose") == "cta" else "watermark"
        return request


class AvatarSource(AssetSourceAdapter):
    key = "avatar"
    label = "AI Avatar Assets"
    asset_kind = "video"

    def is_available(self) -> bool:
        return False  # future engine — interface reserved

    def build_request(self, scene: dict) -> dict:
        request = self._base_request(scene)
        request["presenter_action"] = scene.get("visual_description", "")
        request["status"] = "not_implemented"
        return request


class AtlasImageSource(AssetSourceAdapter):
    """Knowledge Atlas — licensed authentic visual evidence."""

    key = "atlas_image"
    label = "Knowledge Atlas Evidence"
    asset_kind = "image"

    def build_request(self, scene: dict) -> dict:
        request = self._base_request(scene)
        request["asset_ids"] = scene.get("atlas_asset_ids") or scene.get("reality_image_ids") or []
        request["concepts"] = scene.get("concepts") or []
        request["layout"] = scene.get("atlas_layout", "evidence_tray")
        request["license"] = "atlas_curated"
        return request


_SOURCES: "dict[str, AssetSourceAdapter]" = {}


def register_source(adapter: AssetSourceAdapter) -> AssetSourceAdapter:
    """Register (or replace) an asset source adapter at runtime."""
    _SOURCES[adapter.key] = adapter
    return adapter


def get_source(key: str) -> "AssetSourceAdapter | None":
    return _SOURCES.get(key)


def source_keys() -> list:
    return list(_SOURCES)


for _adapter_class in (
    AIImageSource,
    AIVideoSource,
    StockFootageSource,
    UserAssetSource,
    BrandAssetSource,
    AvatarSource,
    AtlasImageSource,
):
    if _adapter_class.key not in _SOURCES:
        register_source(_adapter_class())


def build_asset_requests(scenes: list) -> list:
    """One asset request per scene, routed through the recommended adapter.

    Unavailable sources (e.g. the future avatar adapter) fall back to
    AI image generation so the render plan is always fulfillable.
    """
    requests = []
    for scene in scenes:
        adapter = get_source(scene.get("asset_type", "ai_image")) or get_source("ai_image")
        if not adapter.is_available():
            adapter = get_source("ai_image")
        requests.append(adapter.build_request(scene))
    return requests
