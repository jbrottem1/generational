"""AssetResolver — turns provider-agnostic asset requests into concrete assets.

The Visual Intelligence Director emits asset *requests* (source + prompt/
query, never a vendor). This module fulfils them through swappable
`AssetFulfiller` adapters, one per footage source:

- `ai_image` / `ai_video` — mock generation via providers/ (real backends
  swap in behind `set_image_provider()` / `set_video_provider()`)
- `stock_footage` — licensed stock libraries (mock search result today)
- `user_asset` — user-uploaded footage slots (reserved, reported missing)
- `brand_asset` — brand kit slots (mock watermark/outro placeholder)
- `avatar` — AI avatar/presenter footage (future — reported missing)
- `reaction` — AI reaction footage (future — reported missing)

Register real fulfillers at runtime via `register_fulfiller()` — the
resolver, engine, and orchestrator never change when providers arrive.
Unavailable sources degrade to an AI-image placeholder and are reported in
`missing_assets` so nothing downstream crashes on an empty slot.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from services.provider_runtime.engine_api import runtime_generate_image, runtime_generate_video


class AssetFulfiller(ABC):
    """One way an asset request becomes a concrete render asset."""

    source: str = "base"
    asset_kind: str = "image"  # image / video / any

    def is_available(self) -> bool:
        """Whether a concrete backend exists for this source today."""
        return True

    @abstractmethod
    def fulfil(self, request: dict) -> dict:
        """Concrete asset for one request (JSON-safe dict)."""

    def _base_asset(self, request: dict) -> dict:
        return {
            "asset_id": f"{self.source}_{uuid.uuid4().hex[:10]}",
            "source": self.source,
            "asset_kind": self.asset_kind,
            "scene_number": request.get("scene_number", 0),
            "duration_sec": request.get("duration_sec", 0),
            "status": "mock",
            "placeholder": True,
        }


class AIImageFulfiller(AssetFulfiller):
    source = "ai_image"
    asset_kind = "image"

    def fulfil(self, request: dict) -> dict:
        asset = self._base_asset(request)
        generated = runtime_generate_image(
            request.get("prompt", ""), {"width": 1080, "height": 1920}
        ) or {}
        asset.update(generated)
        asset["source"] = self.source
        return asset


class AIVideoFulfiller(AssetFulfiller):
    source = "ai_video"
    asset_kind = "video"

    def fulfil(self, request: dict) -> dict:
        asset = self._base_asset(request)
        generated = runtime_generate_video(
            request.get("prompt", ""),
            float(request.get("duration_sec", 0) or 0),
            {"width": 1080, "height": 1920},
        ) or {}
        asset.update(generated)
        asset["source"] = self.source
        return asset


class StockFootageFulfiller(AssetFulfiller):
    source = "stock_footage"
    asset_kind = "video"

    def fulfil(self, request: dict) -> dict:
        asset = self._base_asset(request)
        asset["path"] = f"mock://assets/stock/{asset['asset_id']}.mp4"
        asset["query"] = request.get("query", "")
        asset["license"] = request.get("license", "commercial")
        return asset


class UserAssetFulfiller(AssetFulfiller):
    """User-uploaded footage — slot reserved, nothing uploaded yet."""

    source = "user_asset"
    asset_kind = "any"

    def is_available(self) -> bool:
        return False  # lights up when an upload library lands

    def fulfil(self, request: dict) -> dict:
        asset = self._base_asset(request)
        asset["status"] = "awaiting_upload"
        asset["tags"] = request.get("tags", [])
        return asset


class BrandAssetFulfiller(AssetFulfiller):
    source = "brand_asset"
    asset_kind = "any"

    def fulfil(self, request: dict) -> dict:
        asset = self._base_asset(request)
        asset["path"] = f"mock://assets/brand/{request.get('slot', 'watermark')}.png"
        asset["slot"] = request.get("slot", "watermark")
        return asset


class AvatarFulfiller(AssetFulfiller):
    """AI avatar/presenter footage — future provider, interface reserved."""

    source = "avatar"
    asset_kind = "video"

    def is_available(self) -> bool:
        return False

    def fulfil(self, request: dict) -> dict:
        asset = self._base_asset(request)
        asset["status"] = "not_implemented"
        return asset


class ReactionFulfiller(AssetFulfiller):
    """AI reaction footage — future provider, interface reserved."""

    source = "reaction"
    asset_kind = "video"

    def is_available(self) -> bool:
        return False

    def fulfil(self, request: dict) -> dict:
        asset = self._base_asset(request)
        asset["status"] = "not_implemented"
        return asset


_FULFILLERS: "dict[str, AssetFulfiller]" = {}


def register_fulfiller(fulfiller: AssetFulfiller) -> AssetFulfiller:
    """Register (or replace) an asset fulfiller — how real providers plug in."""
    _FULFILLERS[fulfiller.source] = fulfiller
    return fulfiller


def get_fulfiller(source: str) -> "AssetFulfiller | None":
    return _FULFILLERS.get(source)


def fulfiller_keys() -> list:
    return list(_FULFILLERS)


for _fulfiller_class in (
    AIImageFulfiller,
    AIVideoFulfiller,
    StockFootageFulfiller,
    UserAssetFulfiller,
    BrandAssetFulfiller,
    AvatarFulfiller,
    ReactionFulfiller,
):
    if _fulfiller_class.source not in _FULFILLERS:
        register_fulfiller(_fulfiller_class())


class AssetResolver:
    """Fulfils every asset request; unavailable sources degrade safely."""

    fallback_source = "ai_image"

    def resolve(self, asset_requests: list) -> dict:
        """{assets, missing_assets, warnings} for a list of asset requests."""
        assets = []
        missing = []
        warnings = []
        for request in asset_requests:
            source = request.get("source", self.fallback_source)
            fulfiller = get_fulfiller(source)
            if fulfiller is None or not fulfiller.is_available():
                missing.append(
                    {
                        "scene_number": request.get("scene_number", 0),
                        "source": source,
                        "reason": "no provider available for this source yet",
                        "fallback": self.fallback_source,
                    }
                )
                warnings.append(
                    f"Scene {request.get('scene_number', 0)}: {source} unavailable — "
                    f"filled with {self.fallback_source} placeholder."
                )
                fallback_request = dict(request)
                fallback_request.setdefault("prompt", request.get("query", ""))
                asset = get_fulfiller(self.fallback_source).fulfil(fallback_request)
                asset["fallback_for"] = source
            else:
                asset = fulfiller.fulfil(request)
            assets.append(asset)
        return {"assets": assets, "missing_assets": missing, "warnings": warnings}
