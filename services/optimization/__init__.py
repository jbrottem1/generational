"""Optimization service — Agent 13's Experimentation & Optimization Laboratory.

Public surface:
    from services.optimization import run_optimization, get_optimization_lab
    from services.optimization import generate_variants, score_variant, rank_variants
    from services.optimization import ExperimentManager, ExperimentHistory, ExperimentScheduler
    from services.optimization import build_optimization_report, render_report_text
    from services.optimization import get_optimization_config, configure
"""

from services.optimization.config import (
    OptimizationConfig,
    all_experiment_types,
    configure,
    get_optimization_config,
    reset_optimization_config,
)
from services.optimization.experiments import (
    ExperimentHistory,
    ExperimentManager,
    ExperimentScheduler,
    get_experiment_manager,
)
from services.optimization.lab import (
    OptimizationLab,
    collect_optimization_items,
    get_optimization_lab,
    optimize_item,
    run_optimization,
)
from services.optimization.learning_bridge import (
    combined_priors,
    experiment_winner_priors,
    historical_priors,
    historical_trend_summary,
    remember_experiment_outcome,
)
from services.optimization.models import (
    DEFAULT_SCORING_WEIGHTS,
    EXPERIMENT_MODES,
    EXPERIMENT_RESULT_FIELDS,
    EXPERIMENT_RUN_FIELDS,
    EXPERIMENT_TYPES,
    LAB_EXPERIMENT_FIELDS,
    OPTIMIZATION_ENGINE_VERSION,
    OPTIMIZATION_PACKAGE_FIELDS,
    OPTIMIZATION_RECOMMENDATION_FIELDS,
    OPTIMIZATION_REPORT_FIELDS,
    SCORING_INPUTS,
    VARIANT_FIELDS,
    VARIANT_GROUP_FIELDS,
    ExperimentStatus,
    target_slot,
)
from services.optimization.predictions import (
    PREDICTION_KEYS,
    HeuristicPredictionModel,
    PredictionModel,
    get_prediction_model,
    prediction_model_keys,
    register_prediction_model,
)
from services.optimization.providers import (
    ExperimentProvider,
    MockExperimentProvider,
    experiment_provider_keys,
    get_experiment_provider,
    register_experiment_provider,
)
from services.optimization.recommendations import (
    best_caption,
    best_content_package,
    best_cta,
    best_hook,
    best_narration_style,
    best_publishing_window,
    best_thumbnail,
    best_title,
    best_variant,
    build_optimization_package,
    build_recommendation,
    recommendations_by_type,
    resolve_conflicts,
)
from services.optimization.report import build_optimization_report, render_report_text
from services.optimization.scoring import rank_variants, score_variant
from services.optimization.variants import (
    dedupe_variants,
    find_duplicates,
    generate_variants,
    make_variant,
    validate_variant_group,
)

__all__ = [
    "DEFAULT_SCORING_WEIGHTS",
    "EXPERIMENT_MODES",
    "EXPERIMENT_RESULT_FIELDS",
    "EXPERIMENT_RUN_FIELDS",
    "EXPERIMENT_TYPES",
    "ExperimentHistory",
    "ExperimentManager",
    "ExperimentProvider",
    "ExperimentScheduler",
    "ExperimentStatus",
    "HeuristicPredictionModel",
    "LAB_EXPERIMENT_FIELDS",
    "MockExperimentProvider",
    "OPTIMIZATION_ENGINE_VERSION",
    "OPTIMIZATION_PACKAGE_FIELDS",
    "OPTIMIZATION_RECOMMENDATION_FIELDS",
    "OPTIMIZATION_REPORT_FIELDS",
    "OptimizationConfig",
    "OptimizationLab",
    "PREDICTION_KEYS",
    "PredictionModel",
    "SCORING_INPUTS",
    "VARIANT_FIELDS",
    "VARIANT_GROUP_FIELDS",
    "all_experiment_types",
    "best_caption",
    "best_content_package",
    "best_cta",
    "best_hook",
    "best_narration_style",
    "best_publishing_window",
    "best_thumbnail",
    "best_title",
    "best_variant",
    "build_optimization_package",
    "build_optimization_report",
    "build_recommendation",
    "collect_optimization_items",
    "combined_priors",
    "configure",
    "dedupe_variants",
    "experiment_provider_keys",
    "experiment_winner_priors",
    "find_duplicates",
    "generate_variants",
    "get_experiment_manager",
    "get_experiment_provider",
    "get_optimization_config",
    "get_optimization_lab",
    "get_prediction_model",
    "historical_priors",
    "historical_trend_summary",
    "make_variant",
    "optimize_item",
    "prediction_model_keys",
    "rank_variants",
    "recommendations_by_type",
    "register_experiment_provider",
    "register_prediction_model",
    "remember_experiment_outcome",
    "render_report_text",
    "reset_optimization_config",
    "resolve_conflicts",
    "run_optimization",
    "score_variant",
    "target_slot",
    "validate_variant_group",
]
