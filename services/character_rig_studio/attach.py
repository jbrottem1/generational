"""Soft-attach Character Rig refs onto scene bindings — never regenerate actors."""

from __future__ import annotations

from typing import Any

from services.character_rig_studio.library import resolve_character_rig


def attach_character_rigs(
    scenes: list[dict[str, Any]],
    *,
    hosts_by_id: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Stamp character_rig_ref / package onto each scene from studio_character_id."""
    hosts_by_id = hosts_by_id or {}
    cache: dict[str, dict[str, Any]] = {}
    out: list[dict[str, Any]] = []
    for scene in scenes:
        row = dict(scene)
        cid = str(
            row.get("studio_character_id")
            or (hosts_by_id and next(iter(hosts_by_id), ""))
            or "DOCTOR_001"
        ).upper()
        if cid not in cache:
            cache[cid] = resolve_character_rig(cid)
        pkg = cache[cid]
        row["studio_character_id"] = cid
        row["character_rig_package"] = {
            "character_id": cid,
            "continuity_version": (pkg.get("identity") or {}).get("continuity_version"),
            "scene_ref": pkg.get("scene_ref"),
            "validation": pkg.get("validation"),
            "body_capabilities": (pkg.get("body_rig") or {}).get("capabilities"),
            "performance_clips": list(((pkg.get("performance_system") or {}).get("clips") or {}).keys()),
            "wardrobe_default": (pkg.get("wardrobe") or {}).get("default_outfit"),
            "do_not_regenerate": True,
        }
        # Keep full package available but prefer ref for large payloads in downstream
        row["character_rig_ref"] = (pkg.get("scene_ref") or {}).get("character_rig_ref")
        row["character_continuity_version"] = (pkg.get("identity") or {}).get(
            "continuity_version"
        )
        host = hosts_by_id.get(cid)
        if host and not host.get("character_rig_ref"):
            # non-mutating convenience on scene only
            pass
        if not row.get("studio_asset_path"):
            row["studio_asset_path"] = (pkg.get("identity") or {}).get("studio_asset_path")
        out.append(row)
    return out
