"""Permanent Generational Studio Assets — versioned company IP.

Architecture remains frozen. These are reference libraries productions cast into —
not a new renderer and not a pipeline redesign.
"""

from __future__ import annotations

from services.studio_assets.founder_voice import (
    ASSET_ID as VOICE_ASSET_ID,
    ensure_founder_voice_asset,
    get_founder_voice_id,
    run_founder_voice_qa,
)
from services.studio_assets.registry import get_asset, list_assets, load_registry
from services.studio_assets.doctor_001 import (
    CHARACTER_ID as DOCTOR_001_ID,
    doctor_001_host_profile,
    ensure_doctor_001_asset,
)
from services.studio_assets.the_doctor import (
    ASSET_ID,
    ensure_the_doctor_asset,
    the_doctor_host_profile,
)

__all__ = [
    "ASSET_ID",
    "DOCTOR_001_ID",
    "VOICE_ASSET_ID",
    "doctor_001_host_profile",
    "ensure_doctor_001_asset",
    "ensure_founder_voice_asset",
    "ensure_the_doctor_asset",
    "get_asset",
    "get_founder_voice_id",
    "list_assets",
    "load_registry",
    "run_founder_voice_qa",
    "the_doctor_host_profile",
]
