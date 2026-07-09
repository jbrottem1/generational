"""Asset Cache — never generate the same asset twice.

Content-addressing: every request + canonical prompt spec hashes to one
deterministic fingerprint. Before any provider is called, the fingerprint
is looked up in the Asset Registry — a hit reuses the existing asset (as
`AssetStatus.CACHED`) with zero generation cost; a miss generates and
registers the result under that fingerprint for every future run.

The fingerprint is provider-agnostic on purpose: it captures WHAT is
being asked for (subject, style, characters, palette, aspect, resolution,
type), not which backend happens to serve it — so swapping providers
never silently invalidates the whole cache.
"""

from __future__ import annotations

import hashlib

from services.asset_generation.registry import AssetRegistry

# The request/spec fields that define asset identity. Additive-only —
# appending a field changes future fingerprints (a deliberate, versioned
# cache flush), never breaks old registry entries.
FINGERPRINT_FIELDS = (
    "asset_type",
    "asset_class",
    "prompt",
    "negative_prompt",
    "style",
    "lighting",
    "color_palette",
    "mood",
    "emotion",
    "camera",
    "aspect_ratio",
    "resolution",
    "duration_sec",
    "character_references",
    "environment_references",
    "brand_style",
)


def compute_fingerprint(request: dict, spec: dict) -> str:
    """The deterministic content-address of one generation request."""
    parts = []
    for fieldname in FINGERPRINT_FIELDS:
        value = spec.get(fieldname, request.get(fieldname, ""))
        if isinstance(value, (list, tuple)):
            value = "|".join(str(item) for item in value)
        parts.append(f"{fieldname}={value}")
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def lookup_cached_asset(registry: AssetRegistry, fingerprint: str) -> "dict | None":
    """The reusable registered asset for one fingerprint, if any.

    Only successfully produced assets are served from cache — failed or
    blocked entries never satisfy a lookup.
    """
    asset = registry.find_by_fingerprint(fingerprint)
    if not asset:
        return None
    if asset.get("status") in ("failed", "blocked"):
        return None
    if not asset.get("uri"):
        return None
    return asset


def cached_copy(asset: dict, request: dict) -> dict:
    """A cache-hit asset re-shaped for the requesting item.

    The underlying URI, provider, and fingerprint are shared; identity
    fields (asset_id, scene_id, project_id) belong to the new request so
    packages stay internally consistent.
    """
    copy = dict(asset)
    copy.pop("versions", None)
    copy["asset_id"] = str(request.get("asset_id", asset.get("asset_id", "")))
    copy["scene_id"] = str(request.get("scene_id", ""))
    copy["project_id"] = str(request.get("project_id", ""))
    copy["status"] = "cached"
    copy["cached"] = True
    return copy
