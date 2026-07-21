"""Permanent Generational Studio Character — DOCTOR_001 (The Doctor)."""

from __future__ import annotations

from services.studio_assets.doctor_001.build import ensure_doctor_001_asset
from services.studio_assets.doctor_001.catalog import (
    ASSET_VERSION,
    CHARACTER_ID,
    DISPLAY_NAME,
    LEGACY_ALIAS,
)
from services.studio_assets.doctor_001.identity import identity_core


def doctor_001_host_profile() -> dict:
    """CWS-compatible host profile — canonical medical educator."""
    from services.studio_assets.the_doctor.profile import COLOR_SYSTEM, the_doctor_host_profile

    base = the_doctor_host_profile()
    pal = COLOR_SYSTEM
    return {
        **base,
        "id": CHARACTER_ID,
        "legacy_alias": LEGACY_ALIAS,
        "canonical_studio_character_id": CHARACTER_ID,
        "name": DISPLAY_NAME,
        "short_name": "Doctor",
        "role": "canonical_medical_educator",
        "version": ASSET_VERSION,
        "studio_asset_path": f"data/studio_assets/{CHARACTER_ID}/",
        "character_rig_ref": (
            f"data/studio_assets/{CHARACTER_ID}/CHARACTER_RIG/CHARACTER_RIG_PACKAGE.json"
        ),
        "permanent_digital_actor": True,
        "permanent_ip": True,
        "flagship_science_educator": True,
        "is_gold_standard": True,
        "style_mode": "cinematic_realism",
        "human_realism_framework": "HUMAN_REALISM_FRAMEWORK_V1",
        "human_realism_path": f"data/human_realism/characters/{CHARACTER_ID}/",
        "palette": {
            "skin": tuple(pal["primary"]["rgb"]),
            "hair": tuple(pal["secondary"]["rgb"]),
            "coat": tuple(pal["primary"]["rgb"]),
            "accent": tuple(pal["accent"]["rgb"]),
            "titanium": tuple(pal["secondary"]["rgb"]),
            "eyes": tuple(pal["visors"]["rgb"]),
            "shadow": tuple(pal["chassis_shadow"]["rgb"]),
        },
        "identity": identity_core(),
    }


__all__ = [
    "ASSET_VERSION",
    "CHARACTER_ID",
    "DISPLAY_NAME",
    "LEGACY_ALIAS",
    "doctor_001_host_profile",
    "ensure_doctor_001_asset",
    "identity_core",
]
