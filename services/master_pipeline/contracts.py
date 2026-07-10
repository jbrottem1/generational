"""Package contract normalization for the master production pipeline.

Repairs safe mismatches between ContentPackage slots, media production
packages, and asset-workspace script shapes — without deleting content.
"""

from __future__ import annotations

from typing import Any

from services.orchestrator.models import PRODUCTION_PACKAGE_FIELDS

# Canonical slot names expected on unified / content packages.
CANONICAL_PACKAGE_SLOTS = (
    "script_package",
    "visual_package",
    "audio_package",
    "seo_package",
    "render_package",
    "publishing_package",
    "analytics_package",
    "learning_metadata",
    "director_package",
    "creative_package",
    "character_universe_package",
    "asset_package",
    "animation_package",
    "post_production_package",
    "optimization_package",
)


def normalize_content_package(package: dict | None) -> dict[str, Any]:
    """Ensure a package dict has canonical slots (empty dicts when missing)."""
    data = dict(package or {})
    for slot in CANONICAL_PACKAGE_SLOTS:
        if slot not in data or data[slot] is None:
            data[slot] = {}
    # Alias repairs
    if not data.get("script") and isinstance(data.get("script_package"), dict):
        data["script"] = (
            data["script_package"].get("full_script")
            or data["script_package"].get("script")
            or data["script_package"].get("narration")
            or ""
        )
    if not data.get("hook") and isinstance(data.get("script_package"), dict):
        data["hook"] = data["script_package"].get("hook") or ""
    # video_script (asset workspace) → script_package bridge
    video_script = data.get("video_script") if isinstance(data.get("video_script"), dict) else {}
    if video_script and isinstance(data.get("script_package"), dict):
        sp = dict(data["script_package"])
        if not sp.get("full_script") and video_script.get("full_voiceover"):
            sp["full_script"] = video_script.get("full_voiceover")
        if not sp.get("hook") and video_script.get("hook"):
            sp["hook"] = video_script.get("hook")
        data["script_package"] = sp
        if not data.get("script"):
            data["script"] = video_script.get("full_voiceover") or ""
    # learning_package alias
    if data.get("learning_package") and not data.get("learning_metadata"):
        data["learning_metadata"] = data.get("learning_package")
    return data


def normalize_pipeline_context(context: dict | None) -> dict[str, Any]:
    """Normalize orchestrator context packages in place-friendly copy."""
    ctx = dict(context or {})
    packages = ctx.get("unified_packages") or ctx.get("packages") or []
    if isinstance(packages, list):
        ctx["unified_packages"] = [
            normalize_content_package(p if isinstance(p, dict) else getattr(p, "to_dict", lambda: {})())
            for p in packages
        ]
    for key in ("production_packages", "publishing_packages"):
        items = ctx.get(key)
        if isinstance(items, list):
            ctx[key] = [dict(item) if isinstance(item, dict) else item for item in items]
    # Ensure summary slots exist
    for slot in ("script_package", "visual_package", "audio_package", "render_package", "seo_package"):
        if slot not in ctx:
            # Lift from first unified package when present
            unified = ctx.get("unified_packages") or []
            if unified and isinstance(unified[0], dict) and unified[0].get(slot):
                ctx[slot] = unified[0].get(slot)
    return ctx


def contract_audit(package: dict | None) -> dict[str, Any]:
    """Report which canonical slots are present vs empty."""
    data = normalize_content_package(package)
    present = []
    empty = []
    for slot in CANONICAL_PACKAGE_SLOTS:
        value = data.get(slot)
        if value in (None, "", {}, []):
            empty.append(slot)
        else:
            present.append(slot)
    known_fields = [f for f in PRODUCTION_PACKAGE_FIELDS if f in data and data.get(f) not in (None, "", {}, [])]
    return {
        "slots_present": present,
        "slots_empty": empty,
        "fields_populated": known_fields,
        "completeness": round(100 * len(present) / max(len(CANONICAL_PACKAGE_SLOTS), 1), 1),
    }
