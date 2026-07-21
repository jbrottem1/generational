"""Creative Excellence review — one scorecard + exactly one recommendation per video."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.creative_excellence.recommendation import pick_single_recommendation
from services.creative_excellence.scorecard import build_creative_excellence_scorecard
from services.creative_excellence.v2_quality import pick_v2_craft_recommendation

ROOT = Path(__file__).resolve().parents[2]
HISTORY_PATH = ROOT / "data" / "analytics" / "creative_excellence_history.json"
OUT_ROOT = ROOT / "data" / "productions" / "_validation" / "creative_excellence"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_history() -> list[dict]:
    if not HISTORY_PATH.exists():
        return []
    try:
        rows = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
        return rows if isinstance(rows, list) else []
    except json.JSONDecodeError:
        return []


def _save_history(rows: list[dict]) -> None:
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_PATH.write_text(json.dumps(rows[-500:], indent=2), encoding="utf-8")


def review_production_creative_excellence(
    candidate: dict | None = None,
    *,
    production_report: dict | None = None,
    production_id: str = "",
    topic: str = "",
    previous_score: float | None = None,
    write_artifacts: bool = True,
) -> dict[str, Any]:
    """Generate Creative Excellence review for one finished production."""
    candidate = dict(candidate or {})
    report = dict(production_report or {})
    topic = topic or str(candidate.get("topic") or candidate.get("title") or report.get("topic") or "")
    pid = production_id or str(report.get("production_id") or candidate.get("production_id") or "")

    scorecard = build_creative_excellence_scorecard(
        candidate,
        production_report=report,
        export_validation=report.get("export_validation"),
    )
    recommendation = pick_single_recommendation(
        segments=scorecard["timeline"],
        craft=scorecard["craft"],
    )
    # Prefer V2 craft recommendation when its expected gain is higher (still exactly ONE)
    v2_rec = pick_v2_craft_recommendation(scorecard.get("v2_quality") or {})
    if v2_rec and float(v2_rec.get("expected_retention_gain") or 0) > float(
        recommendation.get("expected_retention_gain") or 0
    ):
        recommendation = v2_rec

    history = _load_history()
    prior = previous_score
    if prior is None and history:
        prior = float(history[-1].get("creative_excellence_score") or 0)
    current = float(scorecard["creative_excellence_score"])
    vs_previous = None
    if prior is not None:
        vs_previous = {
            "previous_score": prior,
            "delta": round(current - prior, 1),
            "more_engaging_than_previous": current > prior,
        }

    result = {
        "generated_at": _now(),
        "version": "2.0.0",
        "initiative": "generational_v2_creative_quality",
        "production_id": pid,
        "topic": topic,
        "lens": ["Pixar", "Kurzgesagt", "Veritasium", "Mark Rober", "MrBeast retention", "NatGeo Shorts"],
        "scorecard": scorecard,
        "single_recommendation": recommendation,
        "vs_previous": vs_previous,
        "mission": {
            "measure": [
                "stop_scroll",
                "finish",
                "share",
                "subscribe",
                "watch_time",
                "visual_appeal",
                "professional_polish",
                "educational_clarity",
            ],
            "do_not_measure": ["code_quality", "architecture", "engine_count"],
            "rule": "Exactly ONE creative recommendation per video. Do not auto-rebuild.",
            "visual_standard": "educational_documentary_not_slideshow",
        },
    }

    history.append(
        {
            "generated_at": result["generated_at"],
            "production_id": pid,
            "topic": topic,
            "creative_excellence_score": current,
            "recommendation_element": recommendation.get("element"),
            "expected_retention_gain": recommendation.get("expected_retention_gain"),
        }
    )
    _save_history(history)

    if write_artifacts:
        OUT_ROOT.mkdir(parents=True, exist_ok=True)
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in (pid or topic or "review"))[:80]
        folder = OUT_ROOT / safe
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "CREATIVE_EXCELLENCE.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        (folder / "CREATIVE_EXCELLENCE.md").write_text(_markdown(result), encoding="utf-8")
        result["artifact_dir"] = str(folder)
        result["markdown_path"] = str(folder / "CREATIVE_EXCELLENCE.md")
        # Also copy to ops folder when production_id looks like ops_/gold_
        if pid:
            ops = ROOT / "data" / "productions" / "_ops" / pid
            if ops.exists():
                (ops / "CREATIVE_EXCELLENCE.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
                (ops / "CREATIVE_EXCELLENCE.md").write_text(_markdown(result), encoding="utf-8")

    return result


def _markdown(result: dict) -> str:
    sc = result.get("scorecard") or {}
    dims = sc.get("dimensions") or {}
    tl = sc.get("timeline") or {}
    craft = sc.get("craft") or {}
    vo = (sc.get("viewer_outcomes") or {}).get("judgments") or {}
    rec = result.get("single_recommendation") or {}
    lines = [
        f"# Creative Excellence — {result.get('topic')}",
        "",
        f"Production: `{result.get('production_id')}`",
        f"Creative Excellence Score: **{sc.get('creative_excellence_score')}/100**",
        f"Engineering Quality (contrast only): **{dims.get('engineering_quality')}**",
        "",
        "> Software is not the bottleneck. Viewer attention is.",
        "",
        "## Viewer outcomes",
        "",
        f"- Stop scrolling: {'YES' if vo.get('would_stop_scrolling') else 'NO'} ({(sc.get('viewer_outcomes') or {}).get('would_stop_scrolling')})",
        f"- Finish watching: {'YES' if vo.get('would_finish_watching') else 'NO'} ({(sc.get('viewer_outcomes') or {}).get('would_finish_watching')})",
        f"- Share: {'YES' if vo.get('would_share') else 'NO'} ({(sc.get('viewer_outcomes') or {}).get('would_share')})",
        f"- Subscribe: {'YES' if vo.get('would_subscribe') else 'NO'} ({(sc.get('viewer_outcomes') or {}).get('would_subscribe')})",
        "",
        "## Timeline",
        "",
    ]
    for k in ("first_3_seconds", "first_6_seconds", "first_15_seconds", "middle_pacing", "ending"):
        lines.append(f"- **{k.replace('_', ' ')}**: {tl.get(k)}")
    lines.extend(["", "## Craft signals", ""])
    for k, v in craft.items():
        lines.append(f"- **{k.replace('_', ' ')}**: {v}")
    v2 = sc.get("v2_quality") or {}
    v2s = v2.get("scores") or {}
    lines.extend(
        [
            "",
            "## Score dimensions",
            "",
            f"- Creative quality: {dims.get('creative_quality')}",
            f"- Viewer retention: {dims.get('viewer_retention')}",
            f"- Educational value: {dims.get('educational_value')}",
            f"- Entertainment: {dims.get('entertainment')}",
            f"- Shareability: {dims.get('shareability')}",
            f"- Emotional impact: {dims.get('emotional_impact')}",
            f"- Curiosity: {dims.get('curiosity')}",
            "",
            "## V2 Creative Quality craft",
            "",
            f"- Visual quality: {v2s.get('visual_quality')}",
            f"- Motion quality: {v2s.get('motion_quality')}",
            f"- Storytelling: {v2s.get('storytelling')}",
            f"- Educational clarity: {v2s.get('educational_clarity')}",
            f"- Hook: {v2s.get('hook')}",
            f"- Viewer retention: {v2s.get('viewer_retention')}",
            f"- Audio quality: {v2s.get('audio_quality')}",
            f"- Overall professionalism: {v2s.get('overall_professionalism')}",
            f"- Documentary-not-slideshow: **{v2.get('resembles_documentary_not_slideshow')}** "
            f"({v2.get('documentary_standard_passed')}/{v2.get('documentary_standard_total')} standards)",
            "",
            "## THE one recommendation",
            "",
            f"**Element:** `{rec.get('element')}`",
            f"**Expected retention gain:** {rec.get('expected_retention_gain')}",
            "",
            rec.get("recommendation") or "",
            "",
            f"_Why this ranks first:_ {rec.get('why_this_ranks_first')}",
            "",
            "_Do not automatically rebuild from this review._",
            "",
        ]
    )
    if rec.get("do_not_touch"):
        lines.append(f"Do not touch now: {', '.join(rec['do_not_touch'])}")
        lines.append("")
    if result.get("vs_previous"):
        vp = result["vs_previous"]
        lines.extend(
            [
                "## vs previous production",
                "",
                f"- Previous: {vp.get('previous_score')}",
                f"- Delta: {vp.get('delta')}",
                f"- More engaging than previous: **{vp.get('more_engaging_than_previous')}**",
                "",
            ]
        )
    return "\n".join(lines)
