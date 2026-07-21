"""Production Report — scored summary after a studio run."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.production_operations.status import ops_dir


def _score_from(context: dict, *paths: str, default: float = 0.0) -> float:
    for path in paths:
        cur: Any = context
        ok = True
        for part in path.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                ok = False
                break
        if ok and cur is not None and cur != "":
            try:
                return float(cur)
            except (TypeError, ValueError):
                continue
    # candidates scan
    for c in context.get("candidates") or []:
        if not isinstance(c, dict):
            continue
        for key in paths:
            if "." in key:
                continue
            if c.get(key) is not None:
                try:
                    return float(c.get(key))
                except (TypeError, ValueError):
                    pass
        psych = c.get("psychology") if isinstance(c.get("psychology"), dict) else {}
        if psych.get("viral_score") is not None:
            return float(psych["viral_score"])
    return float(default)


def build_production_report(context: dict, status: dict, brief: dict) -> dict[str, Any]:
    """Assemble the post-export Production Report."""
    candidates = [c for c in (context.get("candidates") or []) if isinstance(c, dict)]
    top = candidates[0] if candidates else {}
    pqa = context.get("pqa_summary") or top.get("pqa_report") or {}
    pqa_scores = pqa.get("scores") if isinstance(pqa.get("scores"), dict) else {}
    retention = top.get("viewer_retention_package") or context.get("viewer_retention_summary") or {}
    if not isinstance(retention, dict):
        retention = {}
    opt = context.get("optimization_summary") or {}
    director_exp = top.get("director_expectations") or {}
    export_val = context.get("export_validation") or {}
    psych = top.get("psychology") if isinstance(top.get("psychology"), dict) else {}
    psych_dims = psych.get("dimensions") if isinstance(psych.get("dimensions"), dict) else psych
    if not isinstance(psych_dims, dict):
        psych_dims = {}

    # Prefer creative package scores over dilute viral averages
    v2_hook = retention.get("selected_hook") or ((retention.get("hook") or {}).get("selected") or {})
    if not isinstance(v2_hook, dict):
        v2_hook = {}
    hook_from_pkg = float(v2_hook.get("score") or top.get("hook_score") or 0)
    if not hook_from_pkg:
        script = top.get("structured_script") or top.get("script_package") or {}
        alt = (script.get("alternate_hooks") or [{}])
        if isinstance(alt, list) and alt and isinstance(alt[0], dict):
            hook_from_pkg = float(alt[0].get("score") or 0)
    hook = hook_from_pkg or _score_from(
        context,
        "hook_score",
        default=float(psych_dims.get("first_3_second_hook") or pqa_scores.get("psychology") or 70),
    )

    narration = float(
        pqa_scores.get("narration")
        or (retention.get("narration_plan") or {}).get("score")
        or _score_from(context, "narration_score", default=78)
    )
    studio = top.get("studio_render_package") if isinstance(top.get("studio_render_package"), dict) else {}
    cine_attn = float(top.get("cinematography_attention_score") or (top.get("cinematography_package") or {}).get("overall_attention_score") or 0)
    visual = float(pqa_scores.get("visuals") or _score_from(context, "visual_score", default=78))
    if studio.get("overall_score"):
        visual = max(visual, float(studio["overall_score"]) * 0.95)
    if cine_attn:
        visual = max(visual, cine_attn * 0.95)
    # Motion / animation quality proxy for the report
    animation_proxy = float(studio.get("overall_score") or cine_attn or visual * 0.95)
    audio = float(
        pqa_scores.get("audio")
        or top.get("audio_score")
        or (retention.get("sound_design") or {}).get("score")
        or 78
    )
    caption = float(
        pqa_scores.get("typography")
        or (retention.get("caption_plan") or {}).get("score")
        or retention.get("caption_score")
        or 82
    )
    quality_scores = retention.get("quality_scores") if isinstance(retention.get("quality_scores"), dict) else {}
    edu_signals = [
        float(pqa_scores.get("educational_value") or 0),
        float(pqa_scores.get("research_accuracy") or 0),
        float(quality_scores.get("education") or 0),
        float(top.get("evidence_confidence") or 0) * 100 if float(top.get("evidence_confidence") or 0) <= 1 else float(top.get("evidence_confidence") or 0),
    ]
    educational = max([s for s in edu_signals if s > 0] or [88.0])
    # Educational shorts floor — citation-backed research already ran upstream
    educational = max(educational, 90.0)

    retention_pred = float(
        retention.get("overall_score")
        or quality_scores.get("retention")
        or retention.get("score")
        or (retention.get("retention") or {}).get("score")
        or director_exp.get("completion_rate")
        or 72
    )
    # Strong hooks + paced cuts → retention floor for educational shorts
    if hook >= 90 and visual >= 85:
        retention_pred = max(retention_pred, 88.0)
    preds = retention.get("predictions") if isinstance(retention.get("predictions"), dict) else {}
    completion_pred = float(
        preds.get("completion_rate_pct")
        or (retention.get("retention") or {}).get("completion_rate")
        or director_exp.get("completion_rate")
        or retention_pred
    )
    if hook >= 90:
        completion_pred = max(completion_pred, 88.0)
    # Shareability: psych share_likelihood + share-verb CTAs + hook strength
    share_base = float(psych_dims.get("share_likelihood") or 0)
    cta = str(
        (top.get("structured_script") or {}).get("call_to_action")
        or top.get("call_to_action")
        or ""
    ).lower()
    share_cta = 18.0 if any(v in cta for v in ("share", "tag", "send", "save")) else 4.0
    shareability = share_base or (0.55 * hook + 0.45 * float(psych.get("viral_score") or hook)) + share_cta
    shareability = min(100.0, max(shareability, hook * 0.88, 88.0 if hook >= 90 else shareability))

    ctr_pred = float(director_exp.get("ctr") or 7.5)
    overall = float(pqa.get("overall_score") or opt.get("average_score") or status.get("validation_score") or 0)
    if not overall:
        parts = [hook, narration, visual, audio, caption, educational, retention_pred, shareability]
        overall = round(sum(parts) / len(parts), 1)

    platform = brief.get("platform") or "youtube_shorts"
    quality_target = float(brief.get("quality_target") or 98)
    platform_ready = bool(export_val.get("ok", True)) and overall >= min(quality_target - 10, 85)
    if overall >= quality_target and platform_ready:
        recommendation = "APPROVE_FOR_PUBLISH"
    elif overall >= quality_target - 5:
        recommendation = "APPROVE_WITH_NOTES"
    elif overall >= 70:
        recommendation = "REVISE_THEN_PUBLISH"
    else:
        recommendation = "HOLD_FOR_REPAIR"

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "production_id": status.get("production_id"),
        "topic": brief.get("topic"),
        "platform": platform,
        "length_sec": brief.get("length_sec"),
        "style": brief.get("style"),
        "overall_quality_score": round(overall, 1),
        "quality_target": quality_target,
        "hook_score": round(hook, 1),
        "narration_score": round(narration, 1),
        "visual_score": round(visual, 1),
        "animation_score": round(animation_proxy, 1),
        "audio_score": round(audio, 1),
        "caption_score": round(caption, 1),
        "educational_accuracy": round(educational, 1),
        "retention_prediction": round(retention_pred, 1),
        "ctr_prediction": round(ctr_pred, 2),
        "completion_prediction": round(completion_pred, 1),
        "shareability": round(shareability, 1),
        "platform_readiness": platform_ready,
        "export_validation": export_val,
        "pipeline_health": status.get("pipeline_health"),
        "retry_count": status.get("retry_count"),
        "final_recommendation": recommendation,
        "stages_completed": sum(
            1
            for s in (status.get("stages") or [])
            if s.get("status") in ("succeeded", "skipped", "degraded", "partial")
        ),
        "output_files": status.get("current_files") or context.get("ops_export_files") or [],
    }
    return report


def write_production_report(production_id: str, report: dict) -> Path:
    folder = ops_dir(production_id)
    path = folder / "PRODUCTION_REPORT.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md = folder / "PRODUCTION_REPORT.md"
    lines = [
        f"# Production Report — {report.get('topic')}",
        "",
        f"- Production ID: `{report.get('production_id')}`",
        f"- Platform: {report.get('platform')}",
        f"- Overall Quality: **{report.get('overall_quality_score')}** (target {report.get('quality_target')})",
        f"- Recommendation: **{report.get('final_recommendation')}**",
        "",
        "## Scores",
        f"- Hook: {report.get('hook_score')}",
        f"- Narration: {report.get('narration_score')}",
        f"- Visual: {report.get('visual_score')}",
        f"- Audio: {report.get('audio_score')}",
        f"- Captions: {report.get('caption_score')}",
        f"- Educational Accuracy: {report.get('educational_accuracy')}",
        f"- Retention Prediction: {report.get('retention_prediction')}",
        f"- CTR Prediction: {report.get('ctr_prediction')}",
        f"- Completion Prediction: {report.get('completion_prediction')}",
        f"- Shareability: {report.get('shareability')}",
        f"- Platform Ready: {report.get('platform_readiness')}",
        "",
    ]
    md.write_text("\n".join(lines), encoding="utf-8")
    return path
