"""Quality analysis — every asset validated, findings never exceptions.

Per-asset (`validate_asset`): resolution against the configured quality
tier, aspect-ratio match, brand/style compliance, prompt completeness,
provider errors, safety flags, duplicate detection, and a 0-100
generation confidence. Per-package (`validate_asset_package` +
`package_readiness`): aggregate QC and the readiness score downstream
stages can gate on — same conventions as the Creative Studio and Render
quality layers.
"""

from __future__ import annotations

from services.asset_generation.config import (
    QUALITY_TIER_MIN_PIXELS,
    AssetGenerationConfig,
    get_asset_generation_config,
)
from services.asset_generation.models import AssetStatus, readiness_status
from services.asset_generation.prompts import prompt_completeness


def check_safety(request: dict, spec: dict, config: "AssetGenerationConfig | None" = None) -> list:
    """Safety flags raised by one request (empty list = safe)."""
    config = config or get_asset_generation_config()
    text = " ".join(
        str(value).lower()
        for value in (
            request.get("prompt", ""),
            request.get("description", ""),
            spec.get("prompt", ""),
        )
    )
    banned = list(config.safety_rules) + list(config.brand_rules.get("banned_terms", []))
    return [term for term in banned if term and str(term).lower() in text]


def validate_asset(
    asset: dict,
    request: dict,
    spec: dict,
    config: "AssetGenerationConfig | None" = None,
    duplicate_of: str = "",
) -> dict:
    """One ASSET_QUALITY_FIELDS dict for one generated asset."""
    config = config or get_asset_generation_config()
    checks: "dict[str, bool]" = {}
    warnings: "list[str]" = []
    blockers: "list[str]" = []

    # Provider errors.
    error = str(asset.get("error", "") or "")
    checks["provider_ok"] = not error and bool(asset.get("uri"))
    if error:
        blockers.append(f"provider error: {error}")
    elif not asset.get("uri"):
        blockers.append("no asset URI produced")

    # Resolution vs quality tier.
    width = int(asset.get("width", 0) or 0)
    height = int(asset.get("height", 0) or 0)
    min_pixels = QUALITY_TIER_MIN_PIXELS.get(config.quality_tier, 0)
    checks["resolution_ok"] = width * height >= min_pixels
    if not checks["resolution_ok"]:
        warnings.append(
            f"resolution {width}x{height} below the '{config.quality_tier}' tier minimum"
        )

    # Aspect ratio match.
    requested_ratio = str(request.get("aspect_ratio", "") or "")
    checks["aspect_ratio_ok"] = _ratio_matches(requested_ratio, width, height)
    if not checks["aspect_ratio_ok"]:
        warnings.append(f"output does not match requested aspect ratio {requested_ratio}")

    # Brand/style compliance.
    style_required = bool(config.brand_rules.get("require_style", True))
    checks["brand_ok"] = bool(spec.get("style")) or not style_required
    if not checks["brand_ok"]:
        warnings.append("no style attached — brand compliance cannot be guaranteed")

    # Prompt completeness.
    completeness = prompt_completeness(spec)
    checks["prompt_complete"] = completeness >= 60
    if not checks["prompt_complete"]:
        warnings.append(f"compiled prompt only {completeness}% specified")

    # Safety.
    safety_flags = check_safety(request, spec, config)
    checks["safety_ok"] = not safety_flags
    if safety_flags:
        blockers.append("safety rules triggered: " + ", ".join(safety_flags))

    # Duplicates.
    checks["unique"] = not duplicate_of
    if duplicate_of:
        warnings.append(f"duplicate of existing asset {duplicate_of}")

    # Placeholder awareness (a warning, never a blocker in Demo Mode).
    if asset.get("placeholder"):
        warnings.append("placeholder output (Demo Mode provider)")

    confidence = _confidence(checks, completeness, asset)
    status = "failed" if blockers else ("warning" if warnings else "passed")
    return {
        "status": status,
        "confidence": confidence,
        "checks": checks,
        "warnings": warnings,
        "blockers": blockers,
        "safety_flags": safety_flags,
        "duplicate_of": duplicate_of,
    }


def validate_asset_package(package: dict) -> dict:
    """Aggregate package-level QC (same shape idea as creative QC)."""
    assets = package.get("assets", [])
    warnings: "list[str]" = []
    blockers: "list[str]" = []

    failed_required = [
        asset["asset_id"]
        for asset in assets
        if asset.get("priority") == "required" and asset.get("status") in (AssetStatus.FAILED, AssetStatus.BLOCKED)
    ]
    if failed_required:
        blockers.append("required assets not produced: " + ", ".join(sorted(failed_required)))

    failed_optional = sum(
        1
        for asset in assets
        if asset.get("priority") != "required" and asset.get("status") in (AssetStatus.FAILED, AssetStatus.BLOCKED)
    )
    if failed_optional:
        warnings.append(f"{failed_optional} non-required asset(s) not produced")

    placeholders = sum(1 for asset in assets if asset.get("placeholder"))
    if placeholders == len(assets) and assets:
        warnings.append("every asset is a placeholder (Demo Mode)")

    quality_failures = sum(1 for asset in assets if asset.get("quality", {}).get("status") == "failed")
    if quality_failures:
        warnings.append(f"{quality_failures} asset(s) failed quality analysis")

    if not assets:
        warnings.append("no assets were requested or produced")

    status = "FAILED" if blockers else ("WARNING" if warnings else "SUCCESS")
    return {
        "status": status,
        "warnings": warnings,
        "blockers": blockers,
        "checks": {
            "assets": len(assets),
            "failed_required": len(failed_required),
            "quality_failures": quality_failures,
            "placeholders": placeholders,
        },
    }


def package_readiness(package: dict, validation: dict) -> dict:
    """{score, status, blockers} — the number Render can gate on."""
    assets = package.get("assets", [])
    blockers = list(validation.get("blockers", []))

    if not assets:
        return {"score": 0, "status": readiness_status(0, blockers or ["no assets"]), "blockers": blockers or ["no assets"]}

    produced = sum(
        1 for asset in assets if asset.get("status") not in (AssetStatus.FAILED, AssetStatus.BLOCKED)
    )
    confidences = [int(asset.get("quality", {}).get("confidence", 0)) for asset in assets]
    average_confidence = sum(confidences) / len(confidences) if confidences else 0

    score = int(round(0.6 * (100 * produced / len(assets)) + 0.4 * average_confidence))
    score = max(0, min(100, score))
    if blockers:
        score = min(score, 50)
    return {"score": score, "status": readiness_status(score, blockers), "blockers": blockers}


# ------------------------------------------------------------------ helpers


def _ratio_matches(requested: str, width: int, height: int) -> bool:
    if not requested or not width or not height:
        return True  # nothing specified → nothing violated
    try:
        ratio_w, ratio_h = (float(part) for part in requested.split(":", 1))
    except ValueError:
        return True
    expected = ratio_w / ratio_h
    actual = width / height
    return abs(expected - actual) / expected <= 0.05


def _confidence(checks: dict, completeness: int, asset: dict) -> int:
    """0-100 generation confidence from the deterministic signals."""
    passed = sum(1 for ok in checks.values() if ok)
    base = 100 * passed / len(checks) if checks else 0
    confidence = 0.7 * base + 0.3 * completeness
    if asset.get("placeholder"):
        confidence = min(confidence, 75.0)
    return int(round(max(0.0, min(100.0, confidence))))
