"""Creative asset provider registry — per-asset-type creative backends.

Real generation backends (image models, video models, animation systems,
3D pipelines, vector tooling, stock libraries, user-asset stores, brand
asset managers) implement `CreativeAssetProvider` and register here per
asset type; the Creative Studio resolves providers by asset type and never
talks to a vendor SDK directly. Until real backends land, every asset type
resolves to the deterministic `MockCreativeProvider` so the whole studio
runs end-to-end today.
"""

from __future__ import annotations

from providers.creative.mock import MockCreativeProvider
from providers.creative_provider import CREATIVE_ASSET_TYPES, CreativeAssetProvider

_mock = MockCreativeProvider()

# asset type → provider. Real backends replace the mock per asset type via
# register_creative_provider() — nothing in the studio changes.
_providers: "dict[str, CreativeAssetProvider]" = {}


def register_creative_provider(asset_type: str, provider: CreativeAssetProvider) -> None:
    _providers[asset_type] = provider


def get_creative_provider(asset_type: str) -> CreativeAssetProvider:
    """The provider serving an asset type (deterministic mock by default)."""
    provider = _providers.get(asset_type)
    if provider is not None and provider.is_available():
        return provider
    return _mock


def provider_plan(asset_types: "list[str]") -> dict:
    """asset type → provider name, for the package's provider routing plan."""
    return {asset_type: get_creative_provider(asset_type).name for asset_type in asset_types}


__all__ = [
    "CREATIVE_ASSET_TYPES",
    "CreativeAssetProvider",
    "MockCreativeProvider",
    "get_creative_provider",
    "provider_plan",
    "register_creative_provider",
]
