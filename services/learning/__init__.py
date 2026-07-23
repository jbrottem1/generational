"""Learning service — Continuous Learning & Self-Improvement Engine.

Public surface:
    from services.learning import run_learning, consult_context, get_optimization_api
    from services.learning import build_learning_dashboard, predict_performance
"""

from services.learning.api import (
    SelfOptimizationAPI,
    for_animation,
    for_discovery,
    for_psychology,
    for_script,
    for_seo,
    for_visual,
    for_voice,
    get_optimization_api,
)
from services.learning.consult import build_learning_brief, consult_context
from services.learning.dashboard import build_learning_dashboard
from services.learning.experiments import (
    EXPERIMENT_FIELDS,
    EXPERIMENT_KINDS,
    ExperimentManager,
    ExperimentStatus,
    compare_variants,
    get_experiment_manager,
)
from services.learning.graph import KnowledgeGraph, get_knowledge_graph
from services.learning.loop import (
    build_learning_metadata,
    collect_learning_items,
    grow_memory,
    run_learning,
)
from services.learning.memory import (
    MEMORY_CATEGORY,
    MEMORY_ENTRY_FIELDS,
    HistoricalMemory,
    get_memory,
)
from services.learning.models import (
    DIMENSION_TARGETS,
    INSIGHT_FIELDS,
    LEARNING_ENGINE_VERSION,
    LEARNING_METADATA_FIELDS,
    LEARNING_REPORT_FIELDS,
    PATTERN_DIMENSIONS,
    PERFORMANCE_REPORT_FIELDS,
    RECOMMENDATION_FIELDS,
    REPORT_PERIODS,
    TARGET_ENGINES,
)
from services.learning.patterns import (
    best_performers,
    mine_patterns,
    platform_breakdown,
    worst_performers,
)
from services.learning.predictions import predict_performance
from services.learning.productions import (
    PRODUCTION_RECORD_FIELDS,
    ProductionMemory,
    get_production_memory,
    record_productions_from_context,
)
from services.learning.recommendations import (
    build_recommendations,
    guidance_for_engine,
    psychology_guidance,
    recommendations_by_engine,
    recommendations_from_records,
    script_guidance,
    seo_guidance,
    visual_guidance,
    voice_guidance,
)
from services.learning.reports import build_performance_report, render_report_text

__all__ = [
    "DIMENSION_TARGETS",
    "EXPERIMENT_FIELDS",
    "EXPERIMENT_KINDS",
    "ExperimentManager",
    "ExperimentStatus",
    "HistoricalMemory",
    "INSIGHT_FIELDS",
    "KnowledgeGraph",
    "LEARNING_ENGINE_VERSION",
    "LEARNING_METADATA_FIELDS",
    "LEARNING_REPORT_FIELDS",
    "MEMORY_CATEGORY",
    "MEMORY_ENTRY_FIELDS",
    "PATTERN_DIMENSIONS",
    "PERFORMANCE_REPORT_FIELDS",
    "PRODUCTION_RECORD_FIELDS",
    "ProductionMemory",
    "RECOMMENDATION_FIELDS",
    "REPORT_PERIODS",
    "SelfOptimizationAPI",
    "TARGET_ENGINES",
    "best_performers",
    "build_learning_brief",
    "build_learning_dashboard",
    "build_learning_metadata",
    "build_performance_report",
    "build_recommendations",
    "collect_learning_items",
    "compare_variants",
    "consult_context",
    "for_animation",
    "for_discovery",
    "for_psychology",
    "for_script",
    "for_seo",
    "for_visual",
    "for_voice",
    "get_experiment_manager",
    "get_knowledge_graph",
    "get_memory",
    "get_optimization_api",
    "get_production_memory",
    "grow_memory",
    "guidance_for_engine",
    "mine_patterns",
    "platform_breakdown",
    "predict_performance",
    "psychology_guidance",
    "recommendations_by_engine",
    "recommendations_from_records",
    "record_productions_from_context",
    "render_report_text",
    "run_learning",
    "script_guidance",
    "seo_guidance",
    "visual_guidance",
    "voice_guidance",
    "worst_performers",
]
