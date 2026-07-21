"""Optimization Lab director — multi-variant experiment → pick winner → revise ≥98."""

from __future__ import annotations

from services.optimization_lab.comparison import compare_variants
from services.optimization_lab.continuous import extract_lessons, improve_future_priors
from services.optimization_lab.critic import critique_production
from services.optimization_lab.history import record_experiment
from services.optimization_lab.human_review import build_human_review_packet
from services.optimization_lab.knowledge import apply_patterns_to_axes, load_patterns
from services.optimization_lab.models import (
    DEFAULT_VARIANT_COUNT,
    OPTIMIZATION_PASS_THRESHOLD,
    OptimizationPackage,
)
from services.optimization_lab.predictor import predict_variant_performance
from services.optimization_lab.revision import run_revision_loop
from services.optimization_lab.variants import apply_winner_to_candidate, generate_variants


def build_optimization_package(
    candidate: dict,
    *,
    variant_count: int = DEFAULT_VARIANT_COUNT,
    max_revision_rounds: int = 4,
    record_history: bool = True,
    require_human_review: bool = False,
) -> tuple[OptimizationPackage, dict]:
    """Full V4 experiment cycle. Returns (package, updated_candidate)."""
    patterns = load_patterns()
    raw_variants = generate_variants(candidate, count=variant_count)

    # Bias each variant slightly with knowledge patterns
    knowledge_applied: list[dict] = []
    for v in raw_variants:
        axes, applied = apply_patterns_to_axes(v.get("axes") or {}, patterns)
        v["axes"] = axes
        knowledge_applied.extend(applied)

    comparison = compare_variants(raw_variants, candidate)
    variants = comparison["variants"]
    leaderboard = comparison["leaderboard"]
    winner = comparison["winner"]

    baseline_score = int(winner.get("overall_score") or 0)
    # Baseline = version A if present
    baseline_variant = next((v for v in variants if v.get("baseline")), variants[-1] if variants else {})
    baseline_overall = int(baseline_variant.get("overall_score") or baseline_score)

    critique = critique_production(candidate, winner, leaderboard)
    revision = run_revision_loop(
        winner,
        critique_production,
        candidate,
        max_rounds=max_revision_rounds,
        threshold=OPTIMIZATION_PASS_THRESHOLD,
    )
    winner = revision["winner"]
    critique = critique_production(candidate, winner, leaderboard)

    predictions = predict_variant_performance(candidate, winner)
    lessons = extract_lessons(winner, critique, revision["revisions"])
    improve_future_priors(winner)

    rejected = [v for v in variants if v.get("variant_id") != winner.get("variant_id")]
    experiment_id = ""
    if record_history:
        entry = record_experiment(
            topic=str(candidate.get("title") or candidate.get("topic") or ""),
            platform=str(candidate.get("platform") or "youtube_shorts"),
            production_score=int(winner.get("overall_score") or 0),
            winner=winner,
            rejected=rejected,
            critique=critique,
            improvements=revision.get("fixes") or [],
            lessons=lessons,
            predictions=predictions,
        )
        experiment_id = entry.get("experiment_id") or ""

    human_review = build_human_review_packet(
        variants=variants,
        leaderboard=leaderboard,
        winner=winner,
        predictions=predictions,
        critique=critique,
    )
    if not require_human_review:
        human_review["status"] = "auto_approved"

    scores = winner.get("scores") or {}
    improvements = {
        k: round(float(scores.get(k) or 0) - float((baseline_variant.get("scores") or {}).get(k) or 0), 1)
        for k in scores
    }
    improvements["overall"] = round(
        float(winner.get("overall_score") or 0) - float(baseline_overall), 1
    )

    package = OptimizationPackage(
        version="4.0.0",
        overall_score=int(winner.get("overall_score") or 0),
        passed=bool(revision.get("passed") or int(winner.get("overall_score") or 0) >= OPTIMIZATION_PASS_THRESHOLD),
        revision_rounds=int(revision.get("revision_rounds") or 0),
        variants=variants,
        leaderboard=leaderboard,
        winner=winner,
        critique=critique,
        revisions=revision.get("revisions") or [],
        predictions=predictions,
        knowledge_applied=knowledge_applied[:20],
        experiment_id=experiment_id,
        human_review=human_review,
        improvements_vs_baseline=improvements,
        lessons_learned=lessons,
    )

    updated = apply_winner_to_candidate(candidate, winner)
    updated["optimization_package"] = package.to_dict()
    updated["optimization_score"] = package.overall_score
    updated["optimization_passed"] = package.passed
    updated["optimization_winner"] = {
        "label": winner.get("label"),
        "variant_id": winner.get("variant_id"),
        "overall": winner.get("overall_score"),
    }
    return package, updated
