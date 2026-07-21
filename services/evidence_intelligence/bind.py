"""Bind Evidence packages onto Visual Intelligence / Scene Builder scenes."""

from __future__ import annotations

from typing import Any

from services.evidence_intelligence.models import EvidencePackage, SceneEvidencePlan


def bind_evidence_to_scene_dict(scene: dict[str, Any], plan: SceneEvidencePlan) -> dict[str, Any]:
    """Enrich a ScenePlan/scene dict with evidence fields (additive)."""
    out = dict(scene)
    out["asset_type"] = plan.asset_type
    out["atlas_asset_ids"] = list(plan.atlas_asset_ids)
    out["reality_image_ids"] = list(plan.reality_image_ids)
    out["evidence_confidence"] = plan.evidence_confidence
    out["image_source"] = plan.image_source
    out["license_status"] = plan.license_status
    out["evidence_visual_type"] = plan.visual_type
    out["motion_plan"] = plan.motion_plan.to_dict()
    out["annotation_plan"] = [a.to_dict() for a in plan.annotation_plan]
    out["highlight_regions"] = list(plan.highlight_regions)
    out["callout_targets"] = list(plan.callout_targets)
    out["annotation_locations"] = list(plan.annotation_locations)
    out["narration_timing"] = dict(plan.narration_timing)
    out["transition_type"] = plan.transition_type
    out["expected_attention_score"] = plan.expected_attention_score
    out["evidence_image"] = dict(plan.image)
    out["scene_builder"] = plan.to_dict()["scene_builder"]
    # Prefer documentary camera motion from evidence when present
    if plan.motion_plan.camera_motion:
        out["camera_motion"] = plan.motion_plan.camera_motion
    if plan.motion_plan.suggested_zooms:
        out["zoom"] = plan.motion_plan.suggested_zooms[0].get("reason") or out.get("zoom") or ""
    return out


def bind_package_to_visual_scenes(
    visual_package: dict[str, Any],
    evidence: EvidencePackage | dict[str, Any],
) -> dict[str, Any]:
    """Map evidence scene plans onto an existing visual_package.scenes list."""
    if isinstance(evidence, dict):
        evidence = EvidencePackage.from_dict(evidence)
    pkg = dict(visual_package)
    scenes = list(pkg.get("scenes") or [])
    plans = list(evidence.scenes)
    bound = []
    for i, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            bound.append(scene)
            continue
        plan = plans[i] if i < len(plans) else (plans[-1] if plans else None)
        if plan is None:
            bound.append(scene)
        else:
            bound.append(bind_evidence_to_scene_dict(scene, plan))
    pkg["scenes"] = bound
    pkg["evidence_package"] = evidence.to_dict()
    return pkg


def scene_builder_payload(plan: SceneEvidencePlan | dict[str, Any]) -> dict[str, Any]:
    """Canonical Scene Builder input block."""
    if isinstance(plan, dict):
        plan = SceneEvidencePlan.from_dict(plan)
    return plan.to_dict()["scene_builder"]
