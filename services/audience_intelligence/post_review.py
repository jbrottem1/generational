"""Post-production Audience Intelligence review — one highest-impact lesson into memory."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.audience_intelligence.analytics_interfaces import get_analytics_provider, list_analytics_interfaces
from services.audience_intelligence.memory import REVIEW_DIR, add_lesson, ensure_dirs


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _category_from_recommendation(text: str) -> str:
    t = (text or "").lower()
    if any(k in t for k in ("hook", "open", "curiosity", "wrong belief", "three-beat")):
        return "curiosity_gaps" if "curiosity" in t or "belief" in t else "hook_patterns"
    if any(k in t for k in ("thumb", "ctr", "click")):
        return "thumbnail_characteristics"
    if any(k in t for k in ("caption", "subtitle", "text on")):
        return "caption_styles"
    if any(k in t for k in ("narrat", "voice", "audio", "professor")):
        return "narration_styles"
    if any(k in t for k in ("camera", "zoom", "orbit", "push", "pan")):
        return "camera_movement_styles"
    if any(k in t for k in ("pace", "cut", "density", "scene")):
        return "scene_density" if "scene" in t or "density" in t else "visual_pacing"
    if any(k in t for k in ("emotion", "share", "feel")):
        return "emotional_triggers"
    if any(k in t for k in ("platform", "shorts", "tiktok", "reels")):
        return "platform_recommendations"
    return "subject_best_practices"


def _scores_from_sources(
    *,
    creative_excellence: dict[str, Any] | None,
    production_report: dict[str, Any] | None,
    candidate: dict[str, Any] | None,
) -> dict[str, float]:
    ce = creative_excellence or {}
    sc = ce.get("scorecard") or ce.get("v2_scorecard") or {}
    craft = sc.get("craft_scores") or sc.get("dimensions") or {}
    # Prefer V2 craft names when present
    def g(*keys: str, default: float = 70.0) -> float:
        for k in keys:
            if k in craft and craft[k] is not None:
                try:
                    return float(craft[k])
                except (TypeError, ValueError):
                    pass
            if k in sc and sc[k] is not None:
                try:
                    return float(sc[k])
                except (TypeError, ValueError):
                    pass
        return default

    fallback_overall = 70.0
    if ce.get("creative_excellence_score") is not None:
        try:
            fallback_overall = float(ce["creative_excellence_score"])
        except (TypeError, ValueError):
            pass
    elif production_report and production_report.get("creative_excellence_score") is not None:
        try:
            fallback_overall = float(production_report["creative_excellence_score"])
        except (TypeError, ValueError):
            pass
    overall = g("overall_professionalism", "creative_excellence_score", default=fallback_overall)
    scores = {
        "hook_effectiveness": g("hook", "hook_strength", "curiosity"),
        "visual_engagement": g("visual", "visual_engagement", "motion"),
        "story_clarity": g("storytelling", "story_clarity", "educational_clarity"),
        "audio_quality": g("audio", "audio_quality"),
        "educational_value": g("educational_clarity", "educational_value"),
        "emotional_impact": g("emotional_impact", "storytelling"),
        "retention_prediction": g("retention", "retention_prediction"),
        "shareability_prediction": g("shareability", "shareability_prediction", default=65.0),
        "overall": overall,
    }
    # Soft fill from AI attach if CE missing
    ai = (candidate or {}).get("audience_intelligence") or {}
    eng = ai.get("engagement") or {}
    if eng.get("retention_probability") and scores["retention_prediction"] == 70.0:
        scores["retention_prediction"] = float(eng["retention_probability"])
    if eng.get("shareability") and scores["shareability_prediction"] == 65.0:
        scores["shareability_prediction"] = float(eng["shareability"])
    return {k: round(float(v), 1) for k, v in scores.items()}


def review_production_audience(
    *,
    topic: str = "",
    niche: str = "",
    platform: str = "youtube_shorts",
    production_id: str = "",
    candidate: dict[str, Any] | None = None,
    production_report: dict[str, Any] | None = None,
    creative_excellence: dict[str, Any] | None = None,
    published_video_id: str = "",
    analytics_provider: str = "youtube_analytics",
) -> dict[str, Any]:
    """Evaluate completed production; write ONE lesson to creative memory."""
    ensure_dirs()
    cand = dict(candidate or {})
    report = dict(production_report or {})
    topic = topic or str(cand.get("topic") or report.get("topic") or "")
    platform = platform or str(cand.get("platform") or "youtube_shorts")
    production_id = production_id or str(report.get("production_id") or cand.get("production_id") or "")

    ce = creative_excellence
    if ce is None and cand.get("creative_excellence"):
        ce = cand.get("creative_excellence")
    if ce is None:
        # Best effort: re-run CE if available (compose, don't fork)
        try:
            from services.creative_excellence import review_production_creative_excellence

            ce = review_production_creative_excellence(
                cand or {"topic": topic, "platform": platform},
                production_report=report or None,
                production_id=production_id,
                topic=topic,
            )
        except Exception:  # noqa: BLE001
            ce = {}

    scores = _scores_from_sources(
        creative_excellence=ce if isinstance(ce, dict) else {},
        production_report=report,
        candidate=cand,
    )

    rec = {}
    if isinstance(ce, dict):
        rec = ce.get("single_recommendation") or {}
    if not rec and report.get("creative_recommendation"):
        rec = {"recommendation": report.get("creative_recommendation"), "dimension": "creative"}

    improvement = str(rec.get("recommendation") or rec.get("action") or "").strip()
    if not improvement:
        # Derive from weakest score
        dims = {k: v for k, v in scores.items() if k != "overall"}
        weakest = min(dims, key=dims.get) if dims else "hook_effectiveness"
        improvement = f"Raise {weakest.replace('_', ' ')} — that is the highest-leverage gap on this production."
        rec = {"recommendation": improvement, "dimension": weakest, "derived": True}

    statement = improvement
    # Make durable lesson form when CE gives actionable text
    if not statement.endswith(".") and len(statement) < 200:
        statement = statement.rstrip(".") + "."

    category = _category_from_recommendation(statement + " " + str(rec.get("dimension") or ""))
    confidence = 0.55
    if not rec.get("derived"):
        confidence = 0.68
    if float(scores.get("overall") or 0) >= 85:
        confidence = min(0.85, confidence + 0.08)

    evidence = [
        {
            "type": "creative_excellence",
            "production_id": production_id,
            "overall": scores.get("overall"),
            "scores": scores,
            "single_recommendation": rec,
        }
    ]
    if report.get("validation_score") is not None:
        evidence.append({"type": "production_ops", "validation_score": report.get("validation_score")})

    # Future analytics — stub only unless connected
    analytics_snapshot = None
    if published_video_id:
        try:
            provider = get_analytics_provider(analytics_provider)
            analytics_snapshot = provider.fetch_video_metrics(published_video_id)
            if analytics_snapshot.get("connected") and analytics_snapshot.get("metrics"):
                evidence.append({"type": "platform_analytics", "provider": analytics_provider, "metrics": analytics_snapshot.get("metrics")})
                confidence = min(0.95, confidence + 0.12)
        except Exception as exc:  # noqa: BLE001
            analytics_snapshot = {"error": str(exc)[:160]}

    lesson = add_lesson(
        statement=statement,
        category=category,
        evidence=evidence,
        confidence=confidence,
        platform=platform,
        niche=niche or str(cand.get("category") or ""),
        topic=topic,
        production_id=production_id,
        source="post_production_review",
        tags=[t for t in [niche, platform.split("_")[0], "post_review"] if t],
    )

    summary = {
        "package_type": "audience_intelligence_post_review",
        "version": "2.0.0",
        "generated_at": _now(),
        "topic": topic,
        "niche": niche,
        "platform": platform,
        "production_id": production_id,
        "evaluations": scores,
        "highest_impact_improvement": {
            "statement": statement,
            "dimension": rec.get("dimension"),
            "category": category,
        },
        "lesson_recorded": {
            "lesson_id": lesson.get("lesson_id"),
            "statement": lesson.get("statement"),
            "confidence": lesson.get("confidence"),
            "category": lesson.get("category"),
            "evidence_count": len(lesson.get("evidence") or []),
        },
        "analytics_interfaces": list_analytics_interfaces(),
        "analytics_snapshot": analytics_snapshot,
        "creative_excellence_score": scores.get("overall"),
        "note": "Composes Creative Excellence + ops reports; does not replace Psychology/CPL/Publishing",
    }

    path = REVIEW_DIR / f"{production_id or 'review'}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    summary["path"] = str(path)
    summary["markdown"] = format_review_markdown(summary)
    md_path = path.with_suffix(".md")
    md_path.write_text(summary["markdown"], encoding="utf-8")
    summary["markdown_path"] = str(md_path)
    return summary


def format_review_markdown(summary: dict[str, Any]) -> str:
    ev = summary.get("evaluations") or {}
    hi = summary.get("highest_impact_improvement") or {}
    lesson = summary.get("lesson_recorded") or {}
    lines = [
        "# Audience Intelligence — Production Summary",
        "",
        f"**Topic:** {summary.get('topic')}",
        f"**Production:** {summary.get('production_id')}",
        f"**Platform:** {summary.get('platform')}",
        f"**Generated:** {summary.get('generated_at')}",
        "",
        "## Evaluations",
        "",
        f"| Dimension | Score |",
        f"|-----------|------:|",
    ]
    for k, v in ev.items():
        lines.append(f"| {k.replace('_', ' ').title()} | {v} |")
    lines += [
        "",
        "## Highest-impact improvement",
        "",
        f"{hi.get('statement')}",
        "",
        f"- Category: `{hi.get('category')}`",
        f"- Dimension: `{hi.get('dimension')}`",
        "",
        "## Lesson recorded in creative memory",
        "",
        f"- **ID:** `{lesson.get('lesson_id')}`",
        f"- **Confidence:** {lesson.get('confidence')}",
        f"- **Statement:** {lesson.get('statement')}",
        "",
        "_Audience Intelligence advises; existing production systems execute._",
        "",
    ]
    return "\n".join(lines)
