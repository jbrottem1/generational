"""Evidence & Visual Intelligence — structured scene evidence contracts.

Prefer authentic photographs / scientific media over AI. Output is JSON-safe
only and feeds Scene Builder / Visual Intelligence / media production.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


def _clamp(value: float, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, int(round(value))))


VISUAL_TYPES = (
    "photograph",
    "historical_image",
    "scientific_illustration",
    "diagram",
    "map",
    "satellite",
    "museum_artifact",
    "microscope",
    "ct_scan",
    "chart",
    "graph",
    "manufacturing_photo",
    "public_domain",
    "video_footage",
    "animation",
    "visualization_3d",
    "ai_generated",
)

ANNOTATION_KINDS = (
    "label",
    "arrow",
    "circle",
    "bracket",
    "measurement",
    "timeline",
    "comparison_overlay",
    "highlight",
)

CAMERA_MOTIONS = (
    "ken_burns_in",
    "ken_burns_out",
    "slow_pan_left",
    "slow_pan_right",
    "static_hold",
    "push_in_highlight",
    "pull_back_reveal",
)

TRANSITION_TYPES = (
    "hard_cut",
    "crossfade",
    "match_cut",
    "dip_to_black",
    "wipe_soft",
)


@dataclass
class EvidenceHit:
    """One trusted visual evidence candidate."""

    source: str = ""  # NASA | Wikimedia | Reality Catalog | …
    image_id: str = ""
    asset_id: str = ""
    title: str = ""
    path: str = ""
    url: str = ""
    license_status: str = "unknown"  # public_domain | CC-BY | NASA | …
    visual_type: str = "photograph"
    evidence_confidence: int = 50
    credit: str = ""
    concepts: list[str] = field(default_factory=list)
    is_video: bool = False
    provider_tier: int = 3  # 1=photo … 5=AI

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvidenceHit":
        data = data or {}
        return cls(
            source=str(data.get("source") or ""),
            image_id=str(data.get("image_id") or data.get("asset_id") or ""),
            asset_id=str(data.get("asset_id") or data.get("image_id") or ""),
            title=str(data.get("title") or data.get("topic") or ""),
            path=str(data.get("path") or ""),
            url=str(data.get("url") or data.get("source_url") or ""),
            license_status=str(data.get("license_status") or data.get("license") or "unknown"),
            visual_type=str(data.get("visual_type") or "photograph"),
            evidence_confidence=_clamp(
                data.get("evidence_confidence")
                if data.get("evidence_confidence") is not None
                else (float(data.get("relevance") or 0) * 100 if float(data.get("relevance") or 0) <= 1 else data.get("relevance", 50))
            ),
            credit=str(data.get("credit") or ""),
            concepts=list(data.get("concepts") or []),
            is_video=bool(data.get("is_video")),
            provider_tier=int(data.get("provider_tier") or data.get("priority_rank") or 3),
        )


@dataclass
class AnnotationSpec:
    """Narration-tied annotation — never decorative / random."""

    kind: str  # label | arrow | circle | …
    target: str  # semantic target e.g. keyword:… | panel:…
    narration_cue: str
    start_sec: float = 0.0
    end_sec: float = 0.0
    label_text: str = ""
    highlight_region: dict[str, float] = field(default_factory=dict)  # normalized x0,y0,x1,y1
    callout_target: str = ""
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AnnotationSpec":
        data = data or {}
        kind = str(data.get("kind") or "label")
        if kind not in ANNOTATION_KINDS:
            kind = "label"
        return cls(
            kind=kind,
            target=str(data.get("target") or ""),
            narration_cue=str(data.get("narration_cue") or ""),
            start_sec=float(data.get("start_sec") or 0),
            end_sec=float(data.get("end_sec") or 0),
            label_text=str(data.get("label_text") or ""),
            highlight_region=dict(data.get("highlight_region") or {}),
            callout_target=str(data.get("callout_target") or data.get("target") or ""),
            extras=dict(data.get("extras") or {}),
        )


@dataclass
class MotionPlan:
    camera_motion: str = "ken_burns_in"
    suggested_zooms: list[dict[str, Any]] = field(default_factory=list)
    # each zoom: {at_sec, scale, focus_x, focus_y, reason}
    intensity: int = 40

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MotionPlan":
        data = data or {}
        motion = str(data.get("camera_motion") or "ken_burns_in")
        if motion not in CAMERA_MOTIONS:
            motion = "ken_burns_in"
        return cls(
            camera_motion=motion,
            suggested_zooms=list(data.get("suggested_zooms") or []),
            intensity=_clamp(data.get("intensity", 40)),
        )


@dataclass
class ModalityDecision:
    real_image_available: bool = False
    video_footage_available: bool = False
    diagram_preferred: bool = False
    animation_required: bool = False
    visualization_3d_required: bool = False
    ai_generation_fallback_only: bool = True
    chosen_modality: str = "ai_generated"  # photograph | diagram | animation | …

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModalityDecision":
        data = data or {}
        return cls(
            real_image_available=bool(data.get("real_image_available")),
            video_footage_available=bool(data.get("video_footage_available")),
            diagram_preferred=bool(data.get("diagram_preferred")),
            animation_required=bool(data.get("animation_required")),
            visualization_3d_required=bool(data.get("visualization_3d_required")),
            ai_generation_fallback_only=bool(data.get("ai_generation_fallback_only", True)),
            chosen_modality=str(data.get("chosen_modality") or "ai_generated"),
        )


@dataclass
class SceneEvidencePlan:
    """Per-scene evidence package for Scene Builder."""

    scene_id: str = ""
    scene_number: int = 0
    narration: str = ""
    modality: ModalityDecision = field(default_factory=ModalityDecision)
    evidence: EvidenceHit | None = None
    evidence_confidence: int = 0
    image_source: str = ""
    license_status: str = "unknown"
    visual_type: str = "ai_generated"
    motion_plan: MotionPlan = field(default_factory=MotionPlan)
    annotation_plan: list[AnnotationSpec] = field(default_factory=list)
    highlight_regions: list[dict[str, Any]] = field(default_factory=list)
    callout_targets: list[str] = field(default_factory=list)
    annotation_locations: list[dict[str, Any]] = field(default_factory=list)
    narration_timing: dict[str, float] = field(default_factory=dict)  # start_sec, end_sec
    transition_type: str = "crossfade"
    expected_attention_score: int = 50
    # Scene Builder handoff aliases
    image: dict[str, Any] = field(default_factory=dict)
    atlas_asset_ids: list[str] = field(default_factory=list)
    reality_image_ids: list[str] = field(default_factory=list)
    asset_type: str = "ai_image"

    def to_dict(self) -> dict[str, Any]:
        return {
            "scene_id": self.scene_id,
            "scene_number": self.scene_number,
            "narration": self.narration,
            "modality": self.modality.to_dict(),
            "evidence": self.evidence.to_dict() if self.evidence else None,
            "evidence_confidence": int(self.evidence_confidence),
            "image_source": self.image_source,
            "license_status": self.license_status,
            "visual_type": self.visual_type,
            "motion_plan": self.motion_plan.to_dict(),
            "annotation_plan": [a.to_dict() for a in self.annotation_plan],
            "highlight_regions": list(self.highlight_regions),
            "callout_targets": list(self.callout_targets),
            "annotation_locations": list(self.annotation_locations),
            "narration_timing": dict(self.narration_timing),
            "transition_type": self.transition_type,
            "expected_attention_score": int(self.expected_attention_score),
            "image": dict(self.image),
            "atlas_asset_ids": list(self.atlas_asset_ids),
            "reality_image_ids": list(self.reality_image_ids),
            "asset_type": self.asset_type,
            # Scene Builder bundle
            "scene_builder": {
                "image": dict(self.image),
                "motion_plan": self.motion_plan.to_dict(),
                "annotation_plan": [a.to_dict() for a in self.annotation_plan],
                "narration_timing": dict(self.narration_timing),
                "transition_type": self.transition_type,
                "expected_attention_score": int(self.expected_attention_score),
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SceneEvidencePlan":
        data = data or {}
        ev = data.get("evidence")
        return cls(
            scene_id=str(data.get("scene_id") or ""),
            scene_number=int(data.get("scene_number") or 0),
            narration=str(data.get("narration") or ""),
            modality=ModalityDecision.from_dict(data.get("modality") or {}),
            evidence=EvidenceHit.from_dict(ev) if isinstance(ev, dict) else None,
            evidence_confidence=_clamp(data.get("evidence_confidence", 0)),
            image_source=str(data.get("image_source") or ""),
            license_status=str(data.get("license_status") or "unknown"),
            visual_type=str(data.get("visual_type") or "ai_generated"),
            motion_plan=MotionPlan.from_dict(data.get("motion_plan") or {}),
            annotation_plan=[AnnotationSpec.from_dict(a) for a in (data.get("annotation_plan") or [])],
            highlight_regions=list(data.get("highlight_regions") or []),
            callout_targets=list(data.get("callout_targets") or []),
            annotation_locations=list(data.get("annotation_locations") or []),
            narration_timing=dict(data.get("narration_timing") or {}),
            transition_type=str(data.get("transition_type") or "crossfade"),
            expected_attention_score=_clamp(data.get("expected_attention_score", 50)),
            image=dict(data.get("image") or {}),
            atlas_asset_ids=list(data.get("atlas_asset_ids") or []),
            reality_image_ids=list(data.get("reality_image_ids") or []),
            asset_type=str(data.get("asset_type") or "ai_image"),
        )


@dataclass
class EvidencePackage:
    """Candidate-level evidence package."""

    topic: str = ""
    scenes: list[SceneEvidencePlan] = field(default_factory=list)
    trusted_sources_queried: list[str] = field(default_factory=list)
    authentic_hit_count: int = 0
    ai_fallback_count: int = 0
    overall_evidence_confidence: int = 0
    reasoning: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "topic": self.topic,
            "scenes": [s.to_dict() for s in self.scenes],
            "trusted_sources_queried": list(self.trusted_sources_queried),
            "authentic_hit_count": int(self.authentic_hit_count),
            "ai_fallback_count": int(self.ai_fallback_count),
            "overall_evidence_confidence": int(self.overall_evidence_confidence),
            "reasoning": self.reasoning,
            "scene_builder_plans": [s.to_dict()["scene_builder"] for s in self.scenes],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvidencePackage":
        data = data or {}
        return cls(
            topic=str(data.get("topic") or ""),
            scenes=[SceneEvidencePlan.from_dict(s) for s in (data.get("scenes") or [])],
            trusted_sources_queried=list(data.get("trusted_sources_queried") or []),
            authentic_hit_count=int(data.get("authentic_hit_count") or 0),
            ai_fallback_count=int(data.get("ai_fallback_count") or 0),
            overall_evidence_confidence=_clamp(data.get("overall_evidence_confidence", 0)),
            reasoning=str(data.get("reasoning") or ""),
        )
