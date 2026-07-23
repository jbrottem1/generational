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
from pathlib import Path

from services.provider_runtime.engine_api import runtime_generate_image, runtime_generate_video

ROOT = Path(__file__).resolve().parents[2]
FALLBACK_DIR = ROOT / "data" / "renders" / "_scene_stills"


def _is_usable_media_path(path: str | None) -> bool:
    """True when path points at a real local image/video file."""
    raw = str(path or "").strip()
    if not raw or raw.startswith(("mock://", "runtime://", "http://", "https://")):
        return False
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = ROOT / raw
    try:
        return candidate.is_file() and candidate.stat().st_size >= 500
    except OSError:
        return False


def ensure_renderable_still(asset: dict, request: dict | None = None) -> dict:
    """Guarantee a non-placeholder still when provider output is unusable.

    Uses the existing cinematic_fallback still writer — no new engine.
    """
    request = request or {}
    out = dict(asset or {})
    path = str(out.get("path") or out.get("local_path") or out.get("uri") or "")
    if _is_usable_media_path(path):
        abs_path = Path(path) if Path(path).is_absolute() else ROOT / path
        out["path"] = str(abs_path)
        out["local_path"] = str(abs_path)
        out["placeholder"] = False
        return out

    try:
        from services.asset_production.cinematic_fallback import generate_cinematic_fallback_still

        scene_no = int(out.get("scene_number") or request.get("scene_number") or 0)
        prompt = str(
            request.get("prompt")
            or request.get("query")
            or out.get("prompt")
            or out.get("query")
            or f"Scene {scene_no}"
        )
        title = str(request.get("title") or out.get("title") or prompt)[:80]
        FALLBACK_DIR.mkdir(parents=True, exist_ok=True)
        dest = FALLBACK_DIR / f"scene_{scene_no:02d}_{uuid.uuid4().hex[:10]}.png"
        fallback = generate_cinematic_fallback_still(
            output_path=dest,
            title=title,
            overlay=prompt[:42],
            scene_number=max(1, scene_no),
            seed=f"{title}-{scene_no}-{prompt[:40]}",
        )
        if fallback.get("path") and not fallback.get("placeholder"):
            prior_source = out.get("source") or "ai_image"
            out.update(fallback)
            out["source"] = prior_source
            out.setdefault("fallback_for", prior_source)
            out["placeholder"] = False
            out["status"] = fallback.get("status") or "fallback_still"
            out["scene_number"] = scene_no
            out["asset_kind"] = "image"
            return out
    except Exception:  # noqa: BLE001 — never crash asset resolution
        pass
    return out


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
        if generated.get("path") and not str(generated.get("path")).startswith(("mock://", "runtime://")):
            asset["placeholder"] = bool(generated.get("placeholder", False))
            asset["status"] = generated.get("status") or "generated"
        return ensure_renderable_still(asset, request)


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
        if generated.get("path") and not str(generated.get("path")).startswith(("mock://", "runtime://")):
            asset["placeholder"] = bool(generated.get("placeholder", False))
            asset["status"] = generated.get("status") or "generated"
        # Production reliability: still + Ken Burns when clip providers are mock
        if not _is_usable_media_path(str(asset.get("path") or asset.get("local_path") or "")):
            still = ensure_renderable_still(asset, request)
            still["asset_kind"] = "image"
            still["fallback_for"] = "ai_video"
            return still
        return asset


class StockFootageFulfiller(AssetFulfiller):
    source = "stock_footage"
    asset_kind = "video"

    def fulfil(self, request: dict) -> dict:
        asset = self._base_asset(request)
        asset["query"] = request.get("query", "")
        asset["license"] = request.get("license", "commercial")
        # Honor paths already chosen by Visual Source Intelligence / library attach
        for key in ("resolved_path", "local_path", "path"):
            raw = request.get(key)
            if _is_usable_media_path(str(raw or "")):
                p = Path(str(raw))
                if not p.is_absolute():
                    p = ROOT / p
                asset["path"] = str(p.resolve())
                asset["local_path"] = asset["path"]
                asset["placeholder"] = False
                asset["status"] = "resolved_library"
                asset["provider"] = "visual_source_intelligence"
                suffix = p.suffix.lower()
                asset["asset_kind"] = "video" if suffix in {".mp4", ".mov", ".webm", ".m4v"} else "image"
                if request.get("vsi_fallback_reason"):
                    asset["vsi_fallback_reason"] = request.get("vsi_fallback_reason")
                return asset
        asset["path"] = f"mock://assets/stock/{asset['asset_id']}.mp4"
        # Stock libraries are not wired — cinematic still keeps assembly alive
        still = ensure_renderable_still(asset, request)
        still["fallback_for"] = "stock_footage"
        still["asset_kind"] = "image"
        if request.get("vsi_fallback_reason"):
            still["vsi_fallback_reason"] = request.get("vsi_fallback_reason")
        return still


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
            # Last-line reliability: every scene must materialize a still for assemble_mp4
            usable = _is_usable_media_path(
                str(asset.get("path") or asset.get("local_path") or "")
            )
            if not usable or asset.get("placeholder"):
                repaired = ensure_renderable_still(asset, request)
                if _is_usable_media_path(str(repaired.get("path") or "")):
                    if asset.get("placeholder") or not usable:
                        warnings.append(
                            f"Scene {request.get('scene_number', 0)}: "
                            "provider asset unusable — cinematic fallback still applied."
                        )
                    asset = repaired
            assets.append(asset)
        return {"assets": assets, "missing_assets": missing, "warnings": warnings}
