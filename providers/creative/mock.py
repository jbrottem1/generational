"""Deterministic mock creative asset provider — no API key, no network.

Serves every creative asset type so the whole Creative Studio runs
end-to-end in Demo Mode today. Real backends replace it per asset type via
`register_creative_provider()` — nothing in the studio changes.
"""

from __future__ import annotations

import hashlib

from providers.creative_provider import CREATIVE_ASSET_TYPES, CreativeAssetProvider


class MockCreativeProvider(CreativeAssetProvider):
    name = "mock_creative"
    asset_types = CREATIVE_ASSET_TYPES

    def is_available(self) -> bool:
        return True

    def fulfill(self, requirement: dict) -> dict:
        asset_id = requirement.get("asset_id") or "asset_unknown"
        asset_type = requirement.get("asset_type", "ai_image")
        # Deterministic URI: the same requirement always yields the same
        # reference, so re-runs and tests are reproducible.
        digest = hashlib.sha1(
            f"{asset_id}|{asset_type}|{requirement.get('prompt', '')}".encode("utf-8")
        ).hexdigest()[:12]
        return {
            "asset_id": asset_id,
            "asset_type": asset_type,
            "uri": f"mock://assets/creative/{asset_type}/{digest}",
            "provider": self.name,
            "placeholder": True,
        }
