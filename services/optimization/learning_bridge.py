"""Learning bridge — how history makes future rankings smarter.

Reads (never writes) Agent 9's cumulative intelligence — the analytics
store, the mined-insight recommendations, and concluded laboratory
experiments — and turns it into `historical_priors`: value → 0-100 prior
scores the scoring engine blends into rankings. Winning experiments and
proven historical winners lift matching future variants; confirmed losers
sink them.

Concluded experiments are also remembered in Agent 9's append-only
long-term memory (EXPERIMENT_OUTCOMES category) so every other consumer of
that memory benefits too. This module never imports or calls an engine
(Architecture Directive #1) — it consumes stores and shared services only.
"""

from __future__ import annotations

from core.log import get_logger, log_event
from services.analytics.store import get_analytics_store
from services.learning.memory import MEMORY_CATEGORY, HistoricalMemory, get_memory
from services.learning.patterns import mine_patterns
from services.optimization.config import get_optimization_config

logger = get_logger(__name__)

# analytics insight dimension → the laboratory experiment type it informs.
_DIMENSION_TO_EXPERIMENT_TYPE = {
    "hook": "hook",
    "title": "title",
    "thumbnail_version": "thumbnail",
    "voice_version": "narration_style",
    "posting_hour": "publishing_time",
    "platform": "platform_formatting",
    "keyword": "title",
}


def historical_priors(experiment_type: str, records: "list | None" = None) -> dict:
    """value → 0-100 prior score for one experiment type.

    Built from mined analytics insights (winners above baseline score
    higher, losers below it lower) — the same insight math the Learning
    Engine trusts. Returns {} until enough history exists, so cold starts
    rank purely on predictions.
    """
    config = get_optimization_config()
    if records is None:
        records = get_analytics_store().list_records(metrics_status="collected")
    if len(records) < config.min_history_samples:
        return {}

    priors: dict = {}
    for insight in mine_patterns(records):
        if _DIMENSION_TO_EXPERIMENT_TYPE.get(insight["dimension"]) != experiment_type:
            continue
        if insight["samples"] < config.min_history_samples:
            continue
        # Center on 50, move by lift, scale trust by insight confidence.
        trust = insight["confidence"] / 100.0
        priors[str(insight["value"])] = max(0, min(100, 50 + insight["lift"] * trust))
    return priors


def experiment_winner_priors(history, experiment_type: str) -> dict:
    """label/content → prior score from concluded laboratory experiments.

    Past winners get their winning confidence as a prior; recorded losers
    a mirrored penalty — historical winners influence future rankings.
    """
    priors: dict = {}
    for experiment in history.concluded(experiment_type=experiment_type):
        result = experiment.get("result", {})
        winner = result.get("winner", {})
        confidence = float(result.get("confidence", 0))
        if winner:
            key = winner.get("label", "") or str(winner.get("content", ""))
            priors[key] = max(priors.get(key, 0), 50 + confidence / 2)
        for loser in result.get("losers", [])[-2:]:   # only confirmed worst
            key = loser.get("label", "") or str(loser.get("content", ""))
            priors.setdefault(key, max(0, 50 - confidence / 2))
    return priors


def combined_priors(history, experiment_type: str, records: "list | None" = None) -> dict:
    """Analytics-history priors overlaid with experiment-winner priors
    (experiment outcomes are the stronger, more controlled signal)."""
    priors = historical_priors(experiment_type, records=records)
    priors.update(experiment_winner_priors(history, experiment_type))
    return priors


def remember_experiment_outcome(experiment: dict, memory: "HistoricalMemory | None" = None) -> bool:
    """Persist one concluded experiment into Agent 9's long-term memory.

    Memory failures never break the laboratory — returns False and logs.
    """
    result = experiment.get("result", {})
    if not result.get("winner"):
        return False
    memory = memory or get_memory()
    try:
        memory.remember(
            MEMORY_CATEGORY.EXPERIMENT_OUTCOMES,
            {
                "experiment_id": experiment["experiment_id"],
                "kind": experiment["experiment_type"],
                "name": experiment.get("name", ""),
                "winner": {
                    "label": result["winner"].get("label", ""),
                    "confidence": result.get("confidence", 0),
                    "lift": result.get("expected_lift", 0),
                },
            },
            confidence=int(result.get("confidence", 0)),
            evidence={
                "variants": len(result.get("ranked", [])),
                "method": result.get("method", "predicted"),
                "expected_lift": result.get("expected_lift", 0),
            },
            source="experiment",
        )
        return True
    except Exception as exc:  # noqa: BLE001 - memory failures never break the lab
        log_event(logger, "optimization.memory_write_failed", level=30, error=str(exc)[:120])
        return False


def historical_trend_summary(records: "list | None" = None, limit: int = 8) -> list:
    """Top historical insights the report surfaces as `historical_trends`."""
    if records is None:
        records = get_analytics_store().list_records(metrics_status="collected")
    insights = mine_patterns(records)
    return [
        {
            "dimension": i["dimension"],
            "value": i["value"],
            "lift": i["lift"],
            "confidence": i["confidence"],
            "samples": i["samples"],
        }
        for i in insights[:limit]
    ]
