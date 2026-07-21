"""Pre-publish variant comparison — predictions clearly labeled."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.creative_performance_lab.store import experiment_path


def build_prepublish_comparison(experiment: dict[str, Any], variants: list[dict[str, Any]]) -> dict[str, Any]:
    """Rank variants with internal metrics. Never frame as real audience results."""
    ranked = sorted(variants, key=lambda v: (-float(v.get("overall_score") or 0), -float((v.get("prediction") or {}).get("completion_rate_pct") or 0)))
    predicted_winner = ranked[0] if ranked else {}

    rows = []
    for v in ranked:
        pred = v.get("prediction") or {}
        rows.append(
            {
                "label": v.get("label"),
                "hook_style": v.get("hook_style"),
                "what_changed": ["hook_structure", "hook_wording"],
                "what_remained_constant": experiment.get("variables_held_constant"),
                "overall_score": v.get("overall_score"),
                "hook_score": (v.get("scores") or {}).get("hook_quality"),
                "predicted_ctr_pct": pred.get("ctr_pct"),
                "predicted_completion_pct": pred.get("completion_rate_pct"),
                "predicted_share_probability": pred.get("share_probability"),
                "predicted_retention_proxy": (v.get("scores") or {}).get("retention"),
                "render_time_sec": v.get("render_time_sec"),
                "qa_failures": [] if v.get("audio_qa_ok") and v.get("mux_ok") else ["audio_or_mux"],
                "mp4_path": v.get("mp4_path"),
                "prediction_label": "PREDICTION — not real audience results",
            }
        )

    report = {
        "experiment_id": experiment.get("experiment_id"),
        "topic": experiment.get("topic"),
        "disclaimer": "All scores and rankings below are INTERNAL PREDICTIONS, not real platform analytics.",
        "variables_tested": experiment.get("variables_tested"),
        "variables_held_constant": experiment.get("variables_held_constant"),
        "variants": rows,
        "predicted_winner": {
            "label": predicted_winner.get("label"),
            "hook_style": predicted_winner.get("hook_style"),
            "overall_score": predicted_winner.get("overall_score"),
            "reason": _predict_reason(predicted_winner, ranked),
            "status": "PREDICTION",
        },
        "recommended_variant": predicted_winner.get("label"),
        "publishing": "disabled",
    }

    out = experiment_path(str(experiment["experiment_id"])).parent
    out.mkdir(parents=True, exist_ok=True)
    (out / "COMPARISON_REPORT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (out / "COMPARISON_REPORT.md").write_text(_md(report), encoding="utf-8")
    (out / "PREDICTED_WINNER.json").write_text(
        json.dumps(report["predicted_winner"], indent=2) + "\n", encoding="utf-8"
    )
    return report


def _predict_reason(winner: dict, ranked: list[dict]) -> str:
    if not winner:
        return "No variants"
    pred = winner.get("prediction") or {}
    hook = (winner.get("scores") or {}).get("hook_quality")
    return (
        f"PREDICTION: variant {winner.get('label')} ({winner.get('hook_style')}) leads on "
        f"hook_score={hook}, predicted completion={pred.get('completion_rate_pct')}%. "
        "Await human review and real analytics before treating as proof."
    )


def _md(report: dict[str, Any]) -> str:
    lines = [
        "# Creative Performance Lab — Pre-Publish Comparison",
        "",
        f"**Experiment:** `{report.get('experiment_id')}`",
        f"**Topic:** {report.get('topic')}",
        "",
        f"> {report.get('disclaimer')}",
        "",
        "## Predicted winner (NOT real audience results)",
        "",
        f"- Label: **{report.get('recommended_variant')}**",
        f"- Reason: {(report.get('predicted_winner') or {}).get('reason')}",
        "",
        "## Variants",
        "",
        "| Label | Hook style | Overall | Hook | Pred CTR | Pred completion | Pred share | QA |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in report.get("variants") or []:
        qa = "pass" if not r.get("qa_failures") else "fail"
        lines.append(
            f"| {r.get('label')} | {r.get('hook_style')} | {r.get('overall_score')} | {r.get('hook_score')} | "
            f"{r.get('predicted_ctr_pct')} | {r.get('predicted_completion_pct')} | "
            f"{r.get('predicted_share_probability')} | {qa} |"
        )
    lines += ["", "## Held constant", ""]
    for c in report.get("variables_held_constant") or []:
        lines.append(f"- {c}")
    lines.append("")
    return "\n".join(lines)
