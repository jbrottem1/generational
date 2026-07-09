"""AssetPackage assembly — the engine's single deliverable.

`build_asset_package()` turns one ContentPackage-style item into one
complete AssetPackage (ASSET_PACKAGE_FIELDS): request collection →
per-request generation (cache → selection → compilation → generation →
QC → registry) → classification (scene / character / thumbnail /
marketing / video) → provider usage + cache + cost reports → package QC →
readiness. `generate_items()` runs it across everything in the context
and writes each item's `asset_package` slot (Agent 14's write zone — no
other slot is mutated).

Cost governance: each job's estimated cost accumulates against
`max_cost_per_package`; once the budget is reached, remaining requests are
rerouted to offline (free) providers instead of silently overspending —
recorded in the package's `cost_report`.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

from services.asset_generation.config import AssetGenerationConfig, get_asset_generation_config
from services.asset_generation.generator import generate_asset
from services.asset_generation.models import (
    ASSET_GENERATION_ENGINE_VERSION,
    ASSET_PACKAGE_VERSION,
    AssetStatus,
    JobStatus,
)
from services.asset_generation.quality import package_readiness, validate_asset_package
from services.asset_generation.registry import AssetRegistry, get_asset_registry
from services.asset_generation.requests import collect_generation_requests

_MARKETING_CATEGORIES = ("logo", "marketing", "branding")


def collect_generation_items(context: dict) -> "tuple[list, str]":
    """Items this run should generate, preferring canonical ContentPackage
    dicts (same collection order as Creative Studio, SEO, Publishing)."""
    packages = context.get("unified_packages") or []
    if packages:
        return list(packages), "unified_packages"
    for key in ("ideas", "selected_ideas"):
        items = context.get(key) or []
        if items:
            return list(items), key
    return [], ""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_asset_package(
    item: dict,
    context: "dict | None" = None,
    config: "AssetGenerationConfig | None" = None,
    registry: "AssetRegistry | None" = None,
) -> dict:
    """One AssetPackage for one content item. Never raises."""
    config = config or get_asset_generation_config()
    registry = registry or get_asset_registry()
    requests = collect_generation_requests(item, config)

    assets: "list[dict]" = []
    jobs: "list[dict]" = []
    estimated_total = 0.0
    rerouted = 0
    offline_config: "AssetGenerationConfig | None" = None

    for request in requests:
        active = config
        if estimated_total >= config.max_cost_per_package:
            if offline_config is None:
                offline_config = replace(config, offline_only=True)
            active = offline_config
            rerouted += 1
        asset, job = generate_asset(request, item, active, registry)
        estimated_total += float(job.get("cost_estimate", 0.0))
        assets.append(asset)
        jobs.append(job)

    package = {
        "asset_package_version": ASSET_PACKAGE_VERSION,
        "engine_version": ASSET_GENERATION_ENGINE_VERSION,
        "project_id": str(item.get("project_id", "")),
        "assets": assets,
        "scene_assets": _scene_assets(assets),
        "character_assets": [a["asset_id"] for a in assets if a.get("category") == "character"],
        "thumbnail_assets": [a["asset_id"] for a in assets if a.get("category") == "thumbnail"],
        "marketing_assets": [
            a["asset_id"] for a in assets if a.get("category") in _MARKETING_CATEGORIES
        ],
        "video_assets": [a["asset_id"] for a in assets if a.get("asset_class") == "video"],
        "generation_jobs": jobs,
        "provider_usage": _provider_usage(assets),
        "selection_strategy": config.selection_strategy,
        "cache_report": _cache_report(jobs),
        "cost_report": {
            "estimated_total": round(estimated_total, 4),
            "limit": config.max_cost_per_package,
            "within_budget": estimated_total <= config.max_cost_per_package,
            "rerouted_to_offline": rerouted,
        },
        "quality_report": _quality_report(assets),
        "generated_at": _now_iso(),
    }

    validation = validate_asset_package(package)
    package["validation"] = validation
    package["readiness"] = package_readiness(package, validation)
    package["asset_diagnostics"] = _diagnostics(assets, requests)
    return package


def generate_items(
    items: "list[dict]",
    context: "dict | None" = None,
    config: "AssetGenerationConfig | None" = None,
    registry: "AssetRegistry | None" = None,
) -> "list[dict]":
    """Generate every item's assets: writes each item's `asset_package`
    slot and returns the packages. Only Agent 14's slot is mutated —
    script, visual, audio, creative, render, seo, publishing, and
    analytics slots are read, never written."""
    packages = []
    for item in items:
        package = build_asset_package(item, context, config, registry)
        item["asset_package"] = package
        packages.append(package)
    return packages


# ------------------------------------------------------------------ helpers


def _scene_assets(assets: "list[dict]") -> "dict[str, list]":
    scene_map: "dict[str, list]" = {}
    for asset in assets:
        scene_id = str(asset.get("scene_id", ""))
        if scene_id:
            scene_map.setdefault(scene_id, []).append(asset["asset_id"])
    return scene_map


def _provider_usage(assets: "list[dict]") -> "dict[str, int]":
    usage: "dict[str, int]" = {}
    for asset in assets:
        provider = str(asset.get("provider", "")) or "(none)"
        usage[provider] = usage.get(provider, 0) + 1
    return usage


def _cache_report(jobs: "list[dict]") -> dict:
    hits = sum(1 for job in jobs if job.get("status") == JobStatus.CACHE_HIT)
    total = len(jobs)
    return {
        "hits": hits,
        "misses": total - hits,
        "reuse_ratio": round(hits / total, 3) if total else 0.0,
    }


def _quality_report(assets: "list[dict]") -> dict:
    statuses = [asset.get("quality", {}).get("status", "") for asset in assets]
    confidences = [int(asset.get("quality", {}).get("confidence", 0)) for asset in assets]
    return {
        "passed": statuses.count("passed"),
        "warnings": statuses.count("warning"),
        "failed": statuses.count("failed"),
        "average_confidence": int(round(sum(confidences) / len(confidences))) if confidences else 0,
        "safety_flagged": sum(
            1 for asset in assets if asset.get("quality", {}).get("safety_flags")
        ),
        "duplicates": sum(
            1 for asset in assets if asset.get("quality", {}).get("duplicate_of")
        ),
    }


def _diagnostics(assets: "list[dict]", requests: "list[dict]") -> dict:
    by_type: "dict[str, int]" = {}
    by_class: "dict[str, int]" = {}
    by_status: "dict[str, int]" = {}
    for asset in assets:
        by_type[asset.get("asset_type", "")] = by_type.get(asset.get("asset_type", ""), 0) + 1
        by_class[asset.get("asset_class", "")] = by_class.get(asset.get("asset_class", ""), 0) + 1
        by_status[asset.get("status", "")] = by_status.get(asset.get("status", ""), 0) + 1
    return {
        "requested": len(requests),
        "produced": sum(
            1 for asset in assets
            if asset.get("status") not in (AssetStatus.FAILED, AssetStatus.BLOCKED)
        ),
        "reusable": sum(1 for asset in assets if asset.get("reusable")),
        "by_type": dict(sorted(by_type.items())),
        "by_class": dict(sorted(by_class.items())),
        "by_status": dict(sorted(by_status.items())),
    }
