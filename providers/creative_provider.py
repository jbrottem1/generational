"""Creative asset provider interface — how the Creative Studio sources assets.

Never hardcode providers: the studio plans assets against
`CreativeAssetProvider` and asset-type keys only. Real backends (image
models, video models, animation systems, 3D libraries, vector tooling,
stock APIs, user uploads, brand asset stores) implement this interface and
register per asset type in `providers/creative/` — nothing in the studio
changes when a backend swaps in.
"""

from __future__ import annotations

from abc import abstractmethod

from providers.base import Provider

# The creative asset types the studio can plan. Additive-only — future
# formats (spatial assets, interactive scenes, ...) append here.
CREATIVE_ASSET_TYPES = (
    "ai_image",
    "ai_video",
    "animation",
    "asset_3d",
    "vector_graphic",
    "stock_footage",
    "user_asset",
    "brand_asset",
)


class CreativeAssetProvider(Provider):
    """One creative asset backend. `supports()` declares asset types;
    `fulfill()` turns one asset requirement into an asset reference."""

    asset_types: "tuple[str, ...]" = ()

    def supports(self, asset_type: str) -> bool:
        return asset_type in self.asset_types

    @abstractmethod
    def fulfill(self, requirement: dict) -> "dict | None":
        """Fulfil one ASSET_REQUIREMENT_FIELDS dict.

        Returns {asset_id, asset_type, uri, provider, placeholder} or None
        when the requirement cannot be fulfilled.
        """
