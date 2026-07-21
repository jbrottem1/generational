"""Character Asset #0001 — THE DOCTOR — permanent Generational IP."""

from __future__ import annotations

from services.studio_assets.the_doctor.build import ensure_the_doctor_asset
from services.studio_assets.the_doctor.profile import ASSET_ID, ASSET_VERSION, the_doctor_host_profile

__all__ = [
    "ASSET_ID",
    "ASSET_VERSION",
    "ensure_the_doctor_asset",
    "the_doctor_host_profile",
]
