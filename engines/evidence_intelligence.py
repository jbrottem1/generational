"""Evidence & Visual Intelligence Engine.

Gathers authentic visual evidence AFTER script + attention, BEFORE Visual
Intelligence / Scene Builder. Prefer real photographs and scientific media
over AI. Never replaces Visual Intelligence — enriches candidates with
`evidence_package` and Scene Builder plans.
"""

from __future__ import annotations

from core.log import get_logger, log_event
from engines.base import Engine
from services.evidence_intelligence.gather import build_evidence_package

logger = get_logger(__name__)


class EvidenceIntelligenceEngine(Engine):
    key = "evidence_intelligence"
    label = "Evidence & Visual Intelligence"
    icon = "🔎"
    description = (
        "Gather authentic visual evidence (NASA, NOAA, Wikimedia, Reality Catalog, Atlas) "
        "before scene generation — real photos preferred over AI."
    )
    version = "1.0.0"

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        candidates = list(context.get("candidates") or [])
        if not candidates:
            return {}

        niche = str(context.get("niche") or context.get("trend_category") or "general")
        subject = str(context.get("subject") or context.get("trend_subject") or "")
        packages: list[dict] = []

        for candidate in candidates:
            attention = candidate.get("attention_graph") or context.get("attention_graph") or {}
            package = build_evidence_package(
                candidate,
                topic=str(candidate.get("title") or subject),
                domain=niche if niche != "general" else "general",
                attention=attention if isinstance(attention, dict) else {},
            )
            data = package.to_dict()
            candidate["evidence_package"] = data
            candidate["evidence_confidence"] = package.overall_evidence_confidence
            candidate["scene_builder_plans"] = data.get("scene_builder_plans") or []
            # Seed reality/atlas ids for downstream Visual Intelligence
            ids: list[str] = []
            reality: list[str] = []
            for scene in package.scenes:
                ids.extend(scene.atlas_asset_ids)
                reality.extend(scene.reality_image_ids)
            if ids:
                candidate["atlas_asset_ids"] = list(dict.fromkeys(ids))
            if reality:
                candidate["reality_image_ids"] = list(dict.fromkeys(reality))
            packages.append(data)

        authentic = sum(p.get("authentic_hit_count") or 0 for p in packages)
        ai_fb = sum(p.get("ai_fallback_count") or 0 for p in packages)
        avg_conf = int(
            sum(p.get("overall_evidence_confidence") or 0 for p in packages) / max(1, len(packages))
        )

        summary = {
            "candidates": len(candidates),
            "authentic_scene_hits": authentic,
            "ai_fallback_scenes": ai_fb,
            "average_evidence_confidence": avg_conf,
            "prefer_real_over_ai": True,
        }
        log_event(
            logger,
            "evidence_intelligence.completed",
            candidates=len(candidates),
            authentic=authentic,
            ai_fallback=ai_fb,
            confidence=avg_conf,
        )
        return {
            "candidates": candidates,
            "evidence_intelligence_summary": summary,
            "evidence_packages": packages,
        }
