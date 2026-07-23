"""Audience Intelligence Engine — why humans click, watch, and share.

Additional scoring layer AFTER Discovery / Ideation and BEFORE Agent 3
Script Generation. Never replaces Discovery Engine outputs — only adds:

- audience_intelligence (full report)
- audience_script_guidance (compact Agent 3 hints)
- human_attention_score on candidates

Logic lives in `services/audience_intelligence/`.
"""

from __future__ import annotations

from core.log import get_logger, log_event
from engines.base import Engine
from services.audience_intelligence.adapters import (
    apply_guidance_to_script_context,
    script_generation_guidance,
)
from services.audience_intelligence.builder import analyze_topic, enrich_candidate
from services.audience_intelligence.models import AudienceIntelligenceReport

logger = get_logger(__name__)


class AudienceIntelligenceEngine(Engine):
    key = "audience_intelligence"
    label = "Audience Intelligence"
    icon = "🧠"
    description = "Psychological & behavioral enrichment before scripting — Human Attention Score, hooks, format."
    version = "1.0.0"

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        category = str(context.get("trend_category") or context.get("category") or "general")
        yt = context.get("youtube_search_intelligence")
        discovery = context.get("discovery") if isinstance(context.get("discovery"), dict) else {}
        google_news = context.get("google_news") or discovery.get("google_news")

        candidates = list(context.get("candidates") or [])
        reports: list[dict] = []

        if candidates:
            enriched = []
            for cand in candidates:
                enrich_candidate(cand, category=category, context=context)
                reports.append(cand.get("audience_intelligence") or {})
                enriched.append(cand)
            candidates = enriched
        else:
            handoff = context.get("discovery_script_handoff") or {}
            topic = str(
                context.get("trend_subject")
                or context.get("subject")
                or handoff.get("subject")
                or ""
            )
            brief: dict = {}
            if handoff.get("candidates"):
                brief = dict((handoff["candidates"][0] or {}).get("discovery_brief") or {})
            top = context.get("discovery_top") or {}
            if isinstance(top, dict) and top.get("production_brief"):
                brief = dict(top["production_brief"])
            report = analyze_topic(
                topic or "science education",
                category=category,
                angle=str(brief.get("reasoning") or ""),
                discovery_type=str(
                    (top or {}).get("recommended_video_type")
                    or brief.get("recommended_video_type")
                    or ""
                )
                or None,
                youtube_intelligence=yt if isinstance(yt, dict) else None,
                google_news=google_news if isinstance(google_news, dict) else None,
                production_brief=brief,
                cross_reference=brief.get("cross_reference") or {},
            )
            reports = [report.to_dict()]
            if topic:
                candidates = [
                    {
                        "title": topic[:120],
                        "hook": report.creative.suggested_opening_hook,
                        "angle": report.reasoning[:280],
                        "audience_intelligence": report.to_dict(),
                        "human_attention_score": report.human_attention_score,
                        "recommended_video_format": report.creative.recommended_video_format,
                        "estimated_runtime_hint_sec": report.engagement.average_watch_time_sec,
                    }
                ]

        primary = reports[0] if reports else {}
        out: dict = {
            "candidates": candidates,
            "audience_intelligence": primary,
            "audience_intelligence_reports": reports,
            "audience_script_guidance": script_generation_guidance(primary) if primary else {},
            "human_attention_score": int(primary.get("human_attention_score") or 0),
        }

        handoff = context.get("discovery_script_handoff")
        if isinstance(handoff, dict) and primary:
            out["discovery_script_handoff"] = apply_guidance_to_script_context(dict(handoff), primary)

        log_event(
            logger,
            "audience_intelligence.completed",
            candidates=len(candidates),
            attention=out["human_attention_score"],
            format=(out.get("audience_script_guidance") or {}).get("recommended_video_format"),
        )
        return out
