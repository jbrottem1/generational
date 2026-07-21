"""Score a completed production and rank weaknesses by impact."""

from __future__ import annotations

from typing import Any

from services.production_validation.catalog import (
    DIMENSION_WEAK_FLOOR,
    PUBLISH_READY_FLOOR,
    SCORE_DIMENSIONS,
    WEAKNESS_CATALOG,
)


def _f(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def evaluate_production(ops_result: dict) -> dict[str, Any]:
    """Map ops report/context into mission scorecard + ranked weaknesses."""
    report = ops_result.get("report") or {}
    context = ops_result.get("context") or {}
    status = ops_result.get("status") or {}
    brief = ops_result.get("brief") or {}
    export = ops_result.get("export_validation") or context.get("export_validation") or {}
    candidates = [c for c in (context.get("candidates") or []) if isinstance(c, dict)]
    top = candidates[0] if candidates else {}
    pqa = context.get("pqa_summary") or top.get("pqa_report") or {}
    pqa_scores = pqa.get("scores") if isinstance(pqa.get("scores"), dict) else {}
    retention = top.get("viewer_retention_package") if isinstance(top.get("viewer_retention_package"), dict) else {}
    studio = top.get("studio_render_package") if isinstance(top.get("studio_render_package"), dict) else {}
    seo = top.get("seo_package") if isinstance(top.get("seo_package"), dict) else context.get("seo_package") or {}

    hook = _f(report.get("hook_score"), _f(pqa_scores.get("psychology"), 70))
    visual = _f(report.get("visual_score"), _f(pqa_scores.get("visuals"), 75))
    narration = _f(report.get("narration_score"), _f(pqa_scores.get("narration"), 75))
    caption = _f(report.get("caption_score"), _f(pqa_scores.get("typography"), 80))
    educational = _f(report.get("educational_accuracy"), 80)
    retention_pred = _f(report.get("retention_prediction"), _f(retention.get("overall_score"), 70))
    audio = _f(report.get("audio_score"), _f(pqa_scores.get("audio"), 75))
    # Animation from studio render / cinematography signals
    animation = _f(
        report.get("animation_score"),
        _f(
            studio.get("overall_score"),
            _f(pqa_scores.get("cinematography"), _f(pqa_scores.get("render_quality"), visual * 0.95)),
        ),
    )
    cine_attn = _f(top.get("cinematography_attention_score"), 0)
    if cine_attn:
        animation = max(animation, cine_attn)
        visual = max(visual, cine_attn * 0.95)
    if studio.get("overall_score"):
        visual = max(visual, _f(studio.get("overall_score")) * 0.95)
        animation = max(animation, _f(studio.get("overall_score")))
    seo_quality = _f(seo.get("score"), _f(top.get("seo_score"), 70 if seo else 60))
    thumb = top.get("thumbnail") or top.get("thumbnail_concepts") or {}
    thumbnail_quality = 85.0 if thumb else 55.0
    if isinstance(thumb, dict) and (thumb.get("path") or thumb.get("layout") or thumb.get("concepts")):
        thumbnail_quality = max(thumbnail_quality, 80.0)
    if isinstance(thumb, list) and thumb:
        topscore = max((_f(t.get("overall"), 0) for t in thumb if isinstance(t, dict)), default=0)
        if topscore:
            thumbnail_quality = max(thumbnail_quality, topscore)
    if export.get("thumbnail_generated"):
        thumbnail_quality = max(thumbnail_quality, 90.0)
    bp_thumb = (top.get("production_blueprint") or {}).get("thumbnail_strategy") or {}
    if bp_thumb.get("contrast") == "high" and bp_thumb.get("claim_words_max", 99) <= 5:
        thumbnail_quality = max(thumbnail_quality, 90.0)
    ctr = _f(report.get("ctr_prediction"), 5.0)
    # Normalize CTR-ish into 0-100 display companion
    ctr_score = min(100.0, ctr * 12.0)
    completion = _f(report.get("completion_prediction"), retention_pred)
    shareability = _f(report.get("shareability"), hook)
    # Mission scorecard owns overall — do not inherit inflated ops report composites.
    parts = [
        hook,
        retention_pred,
        visual,
        animation,
        narration,
        audio,
        caption,
        educational,
        seo_quality,
        thumbnail_quality,
        ctr_score,
        completion,
        shareability,
    ]
    overall = round(sum(parts) / len(parts), 1)
    report_overall = _f(report.get("overall_quality_score"), overall)

    scores = {
        "hook_strength": round(hook, 1),
        "retention_prediction": round(retention_pred, 1),
        "visual_quality": round(visual, 1),
        "animation_quality": round(animation, 1),
        "narration_quality": round(narration, 1),
        "audio_mix": round(audio, 1),
        "caption_quality": round(caption, 1),
        "educational_accuracy": round(educational, 1),
        "seo_quality": round(seo_quality, 1),
        "thumbnail_quality": round(thumbnail_quality, 1),
        "ctr_prediction": round(ctr, 2),
        "ctr_score": round(ctr_score, 1),
        "completion_prediction": round(completion, 1),
        "shareability": round(shareability, 1),
        "overall_production_score": round(overall, 1),
        "ops_report_overall": round(report_overall, 1),
    }

    weaknesses = _rank_weaknesses(scores, status, export)
    publish_ready = (
        overall >= PUBLISH_READY_FLOOR
        and scores["hook_strength"] >= DIMENSION_WEAK_FLOOR - 5
        and bool(ops_result.get("succeeded"))
    )

    return {
        "production_id": ops_result.get("production_id"),
        "domain": brief.get("domain") or (brief.get("raw") or {}).get("domain"),
        "topic": brief.get("topic"),
        "platform": brief.get("platform"),
        "length_sec": brief.get("length_sec"),
        "style": brief.get("style"),
        "audience": brief.get("constraints", {}).get("audience") if isinstance(brief.get("constraints"), dict) else None,
        "voice": brief.get("narrator") or brief.get("voice"),
        "elapsed_ms": ops_result.get("elapsed_ms"),
        "scores": scores,
        "recommendation": report.get("final_recommendation"),
        "publish_ready": publish_ready,
        "weaknesses": weaknesses,
        "export_validation": export,
        "score_dimensions": list(SCORE_DIMENSIONS),
    }


def _rank_weaknesses(scores: dict, status: dict, export: dict) -> list[dict]:
    found: list[dict] = []

    def add(key: str, evidence: str, severity: float | None = None):
        meta = WEAKNESS_CATALOG[key]
        dim = meta["dimension"]
        score = scores.get(dim) if dim != "overall_production_score" else scores.get("overall_production_score")
        if dim == "ctr_prediction":
            score = scores.get("ctr_score")
        found.append(
            {
                "id": key,
                "label": meta["label"],
                "impact": meta["impact"],
                "dimension": dim,
                "score": score,
                "severity": round(severity if severity is not None else max(0.0, DIMENSION_WEAK_FLOOR - float(score or 0)), 1),
                "evidence": evidence,
                "fix_hint": meta["fix_hint"],
            }
        )

    if scores["hook_strength"] < DIMENSION_WEAK_FLOOR:
        add("weak_hook", f"hook_strength={scores['hook_strength']}")
    if scores["visual_quality"] < DIMENSION_WEAK_FLOOR:
        add("static_visuals", f"visual_quality={scores['visual_quality']}")
    if scores["animation_quality"] < DIMENSION_WEAK_FLOOR:
        add("weak_animation", f"animation_quality={scores['animation_quality']}")
    if scores["narration_quality"] < DIMENSION_WEAK_FLOOR:
        add("voice_pacing", f"narration_quality={scores['narration_quality']}")
    if scores["caption_quality"] < DIMENSION_WEAK_FLOOR:
        add("caption_timing", f"caption_quality={scores['caption_quality']}")
    if scores["audio_mix"] < DIMENSION_WEAK_FLOOR:
        add("music_transitions", f"audio_mix={scores['audio_mix']}")
    if scores["thumbnail_quality"] < DIMENSION_WEAK_FLOOR:
        add("thumbnail_clarity", f"thumbnail_quality={scores['thumbnail_quality']}")
    if scores["seo_quality"] < DIMENSION_WEAK_FLOOR:
        add("seo_packaging", f"seo_quality={scores['seo_quality']}")
    if scores["educational_accuracy"] < DIMENSION_WEAK_FLOOR:
        add("educational_depth", f"educational_accuracy={scores['educational_accuracy']}")
    if scores["retention_prediction"] < DIMENSION_WEAK_FLOOR:
        add("retention_drop", f"retention_prediction={scores['retention_prediction']}")
    if scores["shareability"] < DIMENSION_WEAK_FLOOR:
        add("low_shareability", f"shareability={scores['shareability']}")

    elapsed = int(status.get("elapsed_ms") or 0)
    if elapsed > 90_000:
        add("rendering_speed", f"elapsed_ms={elapsed}", severity=min(40.0, elapsed / 5000))

    if not export.get("video_exists") and scores["thumbnail_quality"] < 90:
        if not any(w["id"] == "thumbnail_clarity" for w in found):
            add("thumbnail_clarity", "mp4_absent_thumbnail_plan_only")

    # Sort by impact * severity
    found.sort(key=lambda w: (-(w["impact"] * (1 + w["severity"] / 100)), -w["impact"]))
    for i, w in enumerate(found, start=1):
        w["rank"] = i
    return found


def aggregate_weaknesses(evaluations: list[dict]) -> list[dict]:
    """Cross-production weakness ranking by frequency × impact."""
    bucket: dict[str, dict] = {}
    for ev in evaluations:
        for w in ev.get("weaknesses") or []:
            wid = w["id"]
            row = bucket.setdefault(
                wid,
                {
                    "id": wid,
                    "label": w["label"],
                    "impact": w["impact"],
                    "count": 0,
                    "avg_score": 0.0,
                    "fix_hint": w["fix_hint"],
                    "domains": [],
                },
            )
            row["count"] += 1
            row["avg_score"] += float(w.get("score") or 0)
            dom = ev.get("domain")
            if dom and dom not in row["domains"]:
                row["domains"].append(dom)
    ranked = []
    for row in bucket.values():
        row["avg_score"] = round(row["avg_score"] / max(row["count"], 1), 1)
        row["priority_score"] = round(row["impact"] * row["count"] * (1 + max(0, DIMENSION_WEAK_FLOOR - row["avg_score"]) / 50), 1)
        ranked.append(row)
    ranked.sort(key=lambda r: -r["priority_score"])
    for i, r in enumerate(ranked, start=1):
        r["rank"] = i
    return ranked
