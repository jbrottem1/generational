"""Module 8 — Human Review Mode (optional approval gate)."""

from __future__ import annotations


def build_human_review_packet(
    *,
    variants: list[dict],
    leaderboard: list[dict],
    winner: dict,
    predictions: dict,
    critique: dict,
) -> dict:
    """Packet for UI: compare versions, scores, predicted performance, recommendation."""
    diffs = []
    if len(variants) >= 2:
        w_axes = winner.get("axes") or {}
        for v in variants:
            if v.get("variant_id") == winner.get("variant_id"):
                continue
            a = v.get("axes") or {}
            changed = [k for k in w_axes if w_axes.get(k) != a.get(k)]
            diffs.append(
                {
                    "vs_label": v.get("label"),
                    "changed_axes": changed[:8],
                    "score_delta": int(winner.get("overall_score") or 0) - int(v.get("overall_score") or 0),
                }
            )

    return {
        "mode": "optional_human_review",
        "status": "pending_review",  # pending_review | approved | rejected | edited
        "recommended_winner": {
            "label": winner.get("label"),
            "variant_id": winner.get("variant_id"),
            "overall": winner.get("overall_score"),
            "title": (winner.get("axes") or {}).get("title"),
            "hook": (winner.get("axes") or {}).get("hook"),
        },
        "leaderboard": leaderboard,
        "key_differences": diffs[:5],
        "scores": winner.get("scores") or {},
        "predicted_performance": predictions,
        "critique_summary": critique.get("summary"),
        "actions": ["approve", "reject", "edit_custom"],
        "instructions": (
            "Approve the recommended winner, reject to keep baseline, "
            "or supply custom edits before publishing."
        ),
    }


def apply_human_decision(packet: dict, *, decision: str, edits: dict | None = None) -> dict:
    """Apply human decision onto review packet."""
    out = dict(packet)
    decision = (decision or "").lower().strip()
    if decision in ("approve", "approved"):
        out["status"] = "approved"
    elif decision in ("reject", "rejected"):
        out["status"] = "rejected"
    elif decision in ("edit", "edited", "edit_custom"):
        out["status"] = "edited"
        out["custom_edits"] = edits or {}
    else:
        out["status"] = "pending_review"
    return out
