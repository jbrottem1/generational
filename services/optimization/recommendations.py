"""Recommendation engine — concluded experiments become structured advice.

The ONLY thing the laboratory hands back to the pipeline: JSON-safe
OPTIMIZATION_RECOMMENDATION_FIELDS dicts naming the winning content, the
package slot it improves, ranked alternatives, confidence, and expected
lift. Recommendations flow through the orchestrator context
(`optimization_recommendations`) and the ContentPackage
`optimization_package` slot — never engine-to-engine (Architecture
Directive #1). The `best_*` query surface answers the Production
Pipeline's "give me the strongest X" requests from concluded history.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from services.optimization.config import get_optimization_config
from services.optimization.models import (
    OPTIMIZATION_ENGINE_VERSION,
    ExperimentStatus,
    target_slot,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_recommendation(experiment: dict, warnings: "list | None" = None) -> "dict | None":
    """One structured recommendation from one concluded experiment.

    Returns None when the experiment produced no usable winner. A winner
    below the low-confidence threshold still recommends (the pipeline
    decides), but carries an explicit low-confidence warning.
    """
    result = experiment.get("result", {})
    winner = result.get("winner", {})
    if not winner:
        return None

    config = get_optimization_config()
    experiment_type = experiment["experiment_type"]
    confidence = float(result.get("confidence", 0))
    warnings = list(warnings or [])
    if confidence < config.low_confidence_threshold:
        warnings.append(
            f"low confidence ({confidence:.0f} < {config.low_confidence_threshold}) — "
            "treat as a suggestion, not a decision"
        )
    if experiment["status"] == ExperimentStatus.LOW_CONFIDENCE:
        warnings.append("experiment concluded below its winner-confidence bar")

    return {
        "recommendation_id": f"opt_{uuid.uuid4().hex[:12]}",
        "experiment_type": experiment_type,
        "target_slot": target_slot(experiment_type),
        "action": (
            f"Use the '{winner.get('label', 'winning')}' {experiment_type.replace('_', ' ')} "
            f"variant (expected lift {result.get('expected_lift', 0):+.1f})."
        ),
        "content": winner.get("content", ""),
        "variant": winner,
        "alternatives": result.get("losers", [])[:3],
        "confidence": round(confidence, 1),
        "expected_lift": result.get("expected_lift", 0),
        "experiment_id": experiment["experiment_id"],
        "source": "optimization_lab",
        "warnings": warnings,
        "generated_at": _now_iso(),
    }


def resolve_conflicts(recommendations: list) -> list:
    """One recommendation per target slot — when concurrent experiments
    disagree, the higher-confidence winner stands and the loser is kept as
    a flagged alternative signal (conflicting recommendations never reach
    the pipeline silently)."""
    by_slot: "dict[str, dict]" = {}
    resolved = []
    for rec in sorted(recommendations, key=lambda r: r["confidence"], reverse=True):
        slot = rec["target_slot"]
        holder = by_slot.get(slot)
        if holder is None:
            by_slot[slot] = rec
            resolved.append(rec)
        else:
            holder["warnings"].append(
                f"conflicting recommendation {rec['recommendation_id']} "
                f"(confidence {rec['confidence']:.0f}) superseded for slot '{slot}'"
            )
    return resolved


def recommendations_by_type(recommendations: list) -> dict:
    """experiment_type → its recommendation — the shape of the
    `optimization_recommendations` context key."""
    routed: dict = {}
    for rec in recommendations:
        routed.setdefault(rec["experiment_type"], rec)
    return routed


def build_optimization_package(recommendations: list, experiment_ids: list) -> dict:
    """The ContentPackage `optimization_package` slot value for one item."""
    confidences = [r["confidence"] for r in recommendations]
    return {
        "engine_version": OPTIMIZATION_ENGINE_VERSION,
        "status": "optimized" if recommendations else "skipped",
        "recommendations": recommendations,
        "best": {r["experiment_type"]: r["content"] for r in recommendations},
        "experiments": list(experiment_ids),
        "confidence": int(round(sum(confidences) / len(confidences))) if confidences else 0,
        "generated_at": _now_iso(),
    }


# ------------------------------------------------------- pipeline queries
#
# The stable query surface the Production Pipeline (via the orchestrator
# context or on demand) uses to request the strongest version of any
# decision. Answers come from concluded experiment history — structured
# recommendations only, never direct engine calls.


def best_variant(history, experiment_type: str) -> "dict | None":
    """The freshest high-confidence winner for one experiment type."""
    candidates = [
        e for e in history.concluded(experiment_type=experiment_type)
        if e.get("result", {}).get("winner")
    ]
    if not candidates:
        return None
    best = max(
        candidates,
        key=lambda e: (e["result"].get("confidence", 0), e.get("completed_at", "")),
    )
    return build_recommendation(best)


def best_hook(history):
    return best_variant(history, "hook")


def best_title(history):
    return best_variant(history, "title")


def best_thumbnail(history):
    return best_variant(history, "thumbnail")


def best_caption(history):
    return best_variant(history, "caption")


def best_narration_style(history):
    return best_variant(history, "narration_style")


def best_cta(history):
    return best_variant(history, "cta_placement")


def best_publishing_window(history):
    return best_variant(history, "publishing_time")


def best_content_package(history) -> dict:
    """experiment_type → best recommendation across every concluded
    experiment — the strongest overall content package the laboratory can
    currently assemble."""
    package: dict = {}
    seen_types = {e["experiment_type"] for e in history.concluded()}
    for experiment_type in sorted(seen_types):
        recommendation = best_variant(history, experiment_type)
        if recommendation:
            package[experiment_type] = recommendation
    return package
