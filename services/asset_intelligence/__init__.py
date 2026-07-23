"""Universal Asset Intelligence — selection layer feeding the existing renderer.

Does not create a rendering engine. Does not modify the production pipeline.
"""

from __future__ import annotations

from services.asset_intelligence.index import (
    all_assets,
    collection_assets,
    get_asset,
    record_usage,
    seed_from_existing_sources,
    upsert_asset,
)
from services.asset_intelligence.models import ASSET_KINDS, COLLECTIONS, PACKAGE_VERSION
from services.asset_intelligence.cache import prefer_cached_media, resolve_cached_uri, resolve_fingerprint_cache
from services.asset_intelligence.package import (
    attach_package_to_candidate,
    build_asset_intelligence_package,
    validate_asset_intelligence_package,
)
from services.asset_intelligence.search import score_asset_quality, semantic_search

__all__ = [
    "ASSET_KINDS",
    "COLLECTIONS",
    "PACKAGE_VERSION",
    "all_assets",
    "attach_package_to_candidate",
    "build_asset_intelligence_package",
    "collection_assets",
    "get_asset",
    "prefer_cached_media",
    "record_usage",
    "resolve_cached_uri",
    "resolve_fingerprint_cache",
    "score_asset_quality",
    "seed_from_existing_sources",
    "semantic_search",
    "upsert_asset",
    "validate_asset_intelligence_package",
]
