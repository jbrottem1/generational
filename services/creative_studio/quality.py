"""Creative Quality Control — is this blueprint actually producible?

Validates missing assets, broken continuity, scene completeness, timing,
provider compatibility, and overall production readiness. Findings are
warnings/blockers in a validation dict — QC never raises and never crashes
the pipeline (same failure policy as every distribution engine).
"""

from __future__ import annotations

from providers.creative import get_creative_provider
from services.creative_studio.models import (
    STORYBOARD_SCENE_FIELDS,
    readiness_status,
)

# Scene fields that must be non-empty for a scene to count as complete.
_REQUIRED_SCENE_CONTENT = (
    "scene_id",
    "purpose",
    "narration",
    "visual_description",
    "camera_angle",
    "estimated_duration_sec",
)

# Duration sanity bounds per scene (seconds).
_MIN_SCENE_SEC = 0.5
_MAX_SCENE_SEC = 30.0


def validate_package(package: dict) -> dict:
    """One validation dict for one CreativeProductionPackage draft:
    {status, warnings, blockers, checks} — warnings degrade, blockers
    mean not renderable yet."""
    warnings: "list[str]" = []
    blockers: "list[str]" = []
    checks: dict = {}

    storyboard = package.get("storyboard", [])
    requirements = package.get("asset_requirements", [])

    # Scene completeness — every scene carries the full contract and the
    # load-bearing fields are filled.
    incomplete = []
    for scene in storyboard:
        missing_fields = [field for field in STORYBOARD_SCENE_FIELDS if field not in scene]
        empty = [field for field in _REQUIRED_SCENE_CONTENT if not scene.get(field)]
        if missing_fields or empty:
            incomplete.append(f"{scene.get('scene_id', '?')}: missing {missing_fields + empty}")
    checks["scene_completeness"] = {"scenes": len(storyboard), "incomplete": len(incomplete)}
    if not storyboard:
        blockers.append("storyboard is empty — nothing to produce")
    elif incomplete:
        warnings.extend(incomplete)

    # Missing assets — every scene's asset ids must exist in the
    # requirements list; unfulfillable references break rendering.
    known_assets = {req.get("asset_id") for req in requirements}
    missing_assets = [
        f"{scene.get('scene_id', '?')} references unknown asset {asset_id}"
        for scene in storyboard
        for asset_id in scene.get("asset_requirements", [])
        if asset_id not in known_assets
    ]
    checks["missing_assets"] = {"required": len(requirements), "unresolved": len(missing_assets)}
    warnings.extend(missing_assets)

    # Broken continuity — breaks detected by the continuity tracker.
    continuity = package.get("continuity_report", {})
    breaks = continuity.get("breaks", [])
    checks["continuity"] = {
        "score": continuity.get("continuity_score", 0),
        "breaks": len(breaks),
    }
    warnings.extend(f"continuity: {issue}" for issue in breaks)

    # Timing — per-scene bounds and total vs the blueprint's target.
    timing_issues = [
        f"{scene.get('scene_id', '?')}: duration {scene.get('estimated_duration_sec', 0)}s out of bounds"
        for scene in storyboard
        if not _MIN_SCENE_SEC <= float(scene.get("estimated_duration_sec", 0) or 0) <= _MAX_SCENE_SEC
    ]
    total = round(sum(float(scene.get("estimated_duration_sec", 0) or 0) for scene in storyboard), 1)
    target = float(package.get("creative_blueprint", {}).get("target_duration_sec", 0) or 0)
    checks["timing"] = {"total_sec": total, "target_sec": target, "issues": len(timing_issues)}
    warnings.extend(timing_issues)
    if target and total > target * 2:
        warnings.append(f"total duration {total}s is more than double the {target}s target")

    # Provider compatibility — every required asset type must have a
    # provider that supports it (mock supports everything today).
    unsupported = sorted(
        {
            req.get("asset_type", "")
            for req in requirements
            if not get_creative_provider(req.get("asset_type", "")).supports(req.get("asset_type", ""))
        }
    )
    checks["provider_compatibility"] = {"unsupported_asset_types": unsupported}
    if unsupported:
        warnings.append(f"no provider supports asset types: {unsupported}")

    status = "FAILED" if blockers else ("WARNING" if warnings else "SUCCESS")
    return {"status": status, "warnings": warnings, "blockers": blockers, "checks": checks}


def production_readiness(package: dict, validation: dict) -> dict:
    """The 0-100 readiness score + status the Render Engine can gate on."""
    score = 100
    score -= 10 * len(validation.get("blockers", []))
    score -= 3 * min(len(validation.get("warnings", [])), 10)
    continuity_score = package.get("continuity_report", {}).get("continuity_score", 100)
    score = int(round(score * (50 + continuity_score / 2) / 100))
    score = max(0, min(100, score))
    return {
        "score": score,
        "status": readiness_status(score, validation.get("blockers", [])),
        "blockers": list(validation.get("blockers", [])),
    }
