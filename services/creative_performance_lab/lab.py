"""Creative Performance Lab orchestration façade (no new engines)."""

from __future__ import annotations

from typing import Any

from services.creative_performance_lab.comparison import build_prepublish_comparison
from services.creative_performance_lab.experiment import create_experiment, update_experiment
from services.creative_performance_lab.human_review import build_lab_human_review_package
from services.creative_performance_lab.produce import produce_experiment_variants
from services.creative_performance_lab.store import load_experiment, save_experiment


def run_controlled_experiment(
    *,
    topic: str,
    platform: str = "youtube_shorts",
    audience: str = "general_public",
    video_length_sec: int = 45,
    variables_tested: list[str] | None = None,
    hypothesis: str = "",
    number_of_variants: int = 3,
    narrator_profile: str = "professor",
    style: str = "educational",
    publish: bool = False,
    voice_id: str = "",
    meta: dict | None = None,
) -> dict[str, Any]:
    """Create experiment, produce variants, compare, open human review. Never auto-publishes."""
    if publish:
        raise ValueError("Creative Performance Lab refuses automatic publishing during lab runs")

    exp = create_experiment(
        topic=topic,
        platform=platform,
        audience=audience,
        video_length_sec=video_length_sec,
        variables_tested=variables_tested or ["hook_structure"],
        hypothesis=hypothesis,
        number_of_variants=number_of_variants,
        meta={
            **(meta or {}),
            "narrator_profile": narrator_profile,
            "style": style,
            "category": "biology" if "octopus" in topic.lower() else "general",
        },
    )
    produced = produce_experiment_variants(exp, voice_id=voice_id)
    variants = produced["variants"]
    comparison = build_prepublish_comparison(exp, variants)
    review = build_lab_human_review_package(exp, variants, comparison)

    exp["variants"] = variants
    exp["production_ids"] = [v.get("production_id") for v in variants]
    exp["status"] = "awaiting_human_review"
    exp["meta"] = {
        **(exp.get("meta") or {}),
        "comparison_path": f"data/creative_performance_lab/experiments/{exp['experiment_id']}/COMPARISON_REPORT.json",
        "human_review_path": f"data/creative_performance_lab/experiments/{exp['experiment_id']}/HUMAN_REVIEW.json",
        "predicted_winner_label": comparison.get("recommended_variant"),
    }
    save_experiment(exp)

    return {
        "experiment": exp,
        "variants": variants,
        "comparison": comparison,
        "human_review": review,
        "publishing": "disabled",
    }


def get_experiment(experiment_id: str) -> dict[str, Any] | None:
    return load_experiment(experiment_id)


def mark_status(experiment_id: str, status: str) -> dict[str, Any]:
    return update_experiment(experiment_id, status=status)
