"""Human review for CPL — stored separately from automated scores."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.creative_performance_lab.models import HUMAN_ISSUE_TAGS
from services.creative_performance_lab.store import experiment_path, load_experiment, save_experiment


def _apply_human_decision(packet: dict, *, decision: str, edits: dict | None = None) -> dict:
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


def build_lab_human_review_package(experiment: dict[str, Any], variants: list[dict[str, Any]], comparison: dict[str, Any]) -> dict[str, Any]:
    """Side-by-side review packet for play / score / override."""
    winner = comparison.get("predicted_winner") or {}
    leaderboard = [
        {
            "label": v.get("label"),
            "variant_id": v.get("variant_id"),
            "overall_score": v.get("overall_score"),
            "hook_style": v.get("hook_style"),
            "mp4_path": v.get("mp4_path"),
            "narration_path": v.get("narration_path"),
        }
        for v in variants
    ]
    packet = {
        "mode": "optional_human_review",
        "status": "pending_review",
        "recommended_winner": {
            "label": winner.get("label"),
            "overall": winner.get("overall_score"),
            "hook_style": winner.get("hook_style"),
            "status": "PREDICTION",
        },
        "leaderboard": leaderboard,
        "predicted_performance": {
            "note": "PREDICTION — not real audience results",
            "by_variant": {v.get("label"): v.get("prediction") for v in variants},
        },
        "critique_summary": winner.get("reason"),
        "actions": ["approve", "reject", "edit_custom"],
        "experiment_id": experiment.get("experiment_id"),
        "topic": experiment.get("topic"),
        "human_scores": {},  # label → 1-10
        "human_notes": {},
        "human_issues": {},  # label → [tags]
        "preferred_winner": "",
        "override_system_prediction": False,
        "playable_paths": {v.get("label"): v.get("mp4_path") for v in variants},
        "allowed_issue_tags": list(HUMAN_ISSUE_TAGS),
        "storage": "human_review — separate from automated scoring",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    out = experiment_path(str(experiment["experiment_id"])).parent / "HUMAN_REVIEW.json"
    out.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
    return packet


def record_human_review(
    experiment_id: str,
    *,
    scores: dict[str, float] | None = None,
    notes: dict[str, str] | None = None,
    issues: dict[str, list[str]] | None = None,
    preferred_winner: str = "",
    override_prediction: bool = False,
    decision: str = "pending_review",
) -> dict[str, Any]:
    """Record human judgment separately from automated scores."""
    exp = load_experiment(experiment_id)
    if not exp:
        raise FileNotFoundError(experiment_id)
    path = experiment_path(experiment_id).parent / "HUMAN_REVIEW.json"
    packet = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    if scores:
        packet["human_scores"] = {**(packet.get("human_scores") or {}), **{k: float(v) for k, v in scores.items()}}
    if notes:
        packet["human_notes"] = {**(packet.get("human_notes") or {}), **notes}
    if issues:
        cleaned = {}
        for label, tags in issues.items():
            cleaned[label] = [t for t in tags if t in HUMAN_ISSUE_TAGS]
        packet["human_issues"] = {**(packet.get("human_issues") or {}), **cleaned}
    if preferred_winner:
        packet["preferred_winner"] = preferred_winner
        packet["override_system_prediction"] = bool(override_prediction)
    packet = _apply_human_decision(packet, decision=decision)
    packet["updated_at"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
    exp["status"] = "awaiting_publishing" if packet.get("status") == "approved" else "awaiting_human_review"
    exp["meta"] = {**(exp.get("meta") or {}), "human_review_status": packet.get("status"), "human_preferred_winner": packet.get("preferred_winner")}
    save_experiment(exp)
    return packet
