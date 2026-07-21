"""Evidence Intelligence — public API."""

from __future__ import annotations

from services.evidence_intelligence.bind import (
    bind_evidence_to_scene_dict,
    bind_package_to_visual_scenes,
    scene_builder_payload,
)
from services.evidence_intelligence.gather import (
    TRUSTED_SOURCES,
    build_evidence_package,
    gather_evidence_hits,
    plan_scene_evidence,
)
from services.evidence_intelligence.models import (
    AnnotationSpec,
    EvidenceHit,
    EvidencePackage,
    ModalityDecision,
    MotionPlan,
    SceneEvidencePlan,
)

__all__ = [
    "TRUSTED_SOURCES",
    "AnnotationSpec",
    "EvidenceHit",
    "EvidencePackage",
    "ModalityDecision",
    "MotionPlan",
    "SceneEvidencePlan",
    "bind_evidence_to_scene_dict",
    "bind_package_to_visual_scenes",
    "build_evidence_package",
    "gather_evidence_hits",
    "plan_scene_evidence",
    "scene_builder_payload",
]
