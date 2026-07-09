"""Asset metadata — structured, additive fields on every generated asset.

`build_asset_metadata()` folds request + prompt-spec + provider result into
one `ASSET_METADATA_FIELDS` dict. Callers may pass overrides via
`request["metadata"]`; unknown keys land in `extra` so future fields never
break older readers.
"""

from __future__ import annotations

from services.asset_generation.models import ASSET_METADATA_FIELDS

_MIME_BY_FORMAT = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
    "mp4": "video/mp4",
    "webm": "video/webm",
    "glb": "model/gltf-binary",
    "gltf": "model/gltf+json",
    "wav": "audio/wav",
    "mp3": "audio/mpeg",
    "bin": "application/octet-stream",
}


def build_asset_metadata(
    request: dict,
    spec: "dict | None" = None,
    result: "dict | None" = None,
) -> dict:
    """One ASSET_METADATA_FIELDS dict for one generated (or blocked) asset."""
    spec = spec or {}
    result = result or {}
    overrides = dict(request.get("metadata") or {})
    extra = dict(overrides.pop("extra", {}) or {})

    tags = list(request.get("tags") or [])
    for tag in overrides.pop("tags", []) or []:
        if tag not in tags:
            tags.append(tag)

    fmt = str(result.get("format") or "")
    mime = str(overrides.pop("mime_type", "") or _MIME_BY_FORMAT.get(fmt, ""))

    license_value = str(
        overrides.pop("license", "")
        or ("placeholder" if result.get("placeholder") else "original")
    )

    metadata = {
        "title": str(
            overrides.pop("title", "")
            or request.get("description")
            or request.get("asset_id")
            or ""
        )[:200],
        "description": str(
            overrides.pop("description", "") or request.get("description") or ""
        )[:500],
        "tags": tags,
        "brand_id": str(overrides.pop("brand_id", "") or request.get("brand_id") or ""),
        "style": str(overrides.pop("style", "") or request.get("style") or spec.get("style") or ""),
        "character_ids": list(
            overrides.pop("character_ids", None) or request.get("character_ids") or []
        ),
        "source": str(overrides.pop("source", "") or request.get("source") or ""),
        "license": license_value,
        "mime_type": mime,
        "file_size_bytes": int(overrides.pop("file_size_bytes", 0) or result.get("file_size_bytes", 0) or 0),
        "extra": extra,
    }
    # Any remaining override keys fold into extra (forward-compat).
    for key, value in overrides.items():
        if key not in ASSET_METADATA_FIELDS:
            metadata["extra"][key] = value
    return metadata
