"""The Optimization Laboratory facade — one call optimizes a whole run.

`run_optimization(context)` does the full cycle for every content item in
the context:

1. Collect items (unified_packages → ideas → selected_ideas → candidates).
2. For each active experiment type: generate variants (control + upstream
   variants already produced by other engines + heuristic alternatives),
   validate them (duplicates, empty content), and create an experiment.
3. Score and rank every variant (configurable weighted scoring blended
   with historical priors from the learning bridge).
4. Conclude experiments statistically; winners with enough confidence
   become structured recommendations; conflicts are resolved explicitly.
5. Write each item's `optimization_package` slot and return the
   `optimization_report` + `optimization_recommendations` context keys.

The laboratory reads other engines' outputs and returns recommendations —
it NEVER rewrites another engine's fields or calls another engine
(Architecture Directive #1). Failure policy: optimization never crashes
the pipeline; empty context → "no_items" report, per-experiment failures
degrade to warnings.
"""

from __future__ import annotations

from core.log import get_logger, log_event
from services.optimization.config import get_optimization_config
from services.optimization.experiments import ExperimentManager
from services.optimization.learning_bridge import combined_priors
from services.optimization.recommendations import (
    best_caption,
    best_content_package,
    best_cta,
    best_hook,
    best_narration_style,
    best_publishing_window,
    best_thumbnail,
    best_title,
    build_optimization_package,
    build_recommendation,
    recommendations_by_type,
    resolve_conflicts,
)
from services.optimization.report import build_optimization_report
from services.optimization.variants import generate_variants

logger = get_logger(__name__)


def collect_optimization_items(context: dict) -> "tuple[list, str]":
    """Items this run should optimize, preferring canonical ContentPackage
    dicts (same collection order as the SEO, Publishing, and Analytics
    engines), falling back to intelligence-stage candidates."""
    packages = context.get("unified_packages") or []
    if packages:
        return list(packages), "unified_packages"
    for key in ("ideas", "selected_ideas", "candidates"):
        items = context.get(key) or []
        if items:
            return list(items), key
    return [], ""


def _base_content(item: dict, experiment_type: str):
    """The incumbent content this experiment measures against."""
    if experiment_type == "hook":
        return item.get("hook", "")
    if experiment_type == "title":
        return item.get("title", "") or item.get("extras", {}).get("title", "")
    if experiment_type == "description":
        return item.get("description", "") or item.get("seo_package", {}).get("description", "")
    if experiment_type == "caption":
        return item.get("caption", "")
    if experiment_type == "cta_placement":
        return ""
    return ""


def _upstream_variants(item: dict, experiment_type: str) -> list:
    """Alternatives other engines already produced — the laboratory ranks
    them alongside its own instead of regenerating that work."""
    if experiment_type == "hook":
        return [
            {"content": v.get("hook", ""), "label": v.get("style", "script_variant"),
             "confidence": v.get("score", 55)}
            for v in (item.get("script_variants") or item.get("script_package", {}).get("variants") or [])
            if isinstance(v, dict) and v.get("hook")
        ]
    if experiment_type == "title":
        return [
            {"content": t.get("title", t) if isinstance(t, dict) else str(t),
             "label": (t.get("archetype", "seo_title") if isinstance(t, dict) else "seo_title"),
             "confidence": (t.get("overall", 55) if isinstance(t, dict) else 55)}
            for t in item.get("seo_package", {}).get("optimized_titles", [])
        ]
    if experiment_type == "thumbnail":
        return [
            {"content": c if isinstance(c, dict) else {"concept": str(c)},
             "label": (c.get("style", "concept") if isinstance(c, dict) else "concept"),
             "confidence": 55}
            for c in (item.get("thumbnail_concepts") or item.get("thumbnail_plan") or [])
        ]
    return []


def optimize_item(
    item: dict,
    context: dict,
    manager: ExperimentManager,
    experiment_types: "list | None" = None,
) -> "tuple[dict, list, list]":
    """Run every active experiment for one item.

    Returns (optimization_package, experiments, warnings). Per-experiment
    failures degrade to warnings — one bad experiment type never blocks
    the others.
    """
    config = get_optimization_config()
    experiment_types = experiment_types or config.active_experiment_types
    experiments, recommendations, warnings = [], [], []

    for experiment_type in experiment_types[: config.max_experiments_per_run]:
        try:
            group = generate_variants(
                experiment_type,
                base_content=_base_content(item, experiment_type),
                upstream_variants=_upstream_variants(item, experiment_type),
            )
            experiment = manager.create_experiment(
                experiment_type,
                group,
                name=f"{experiment_type} · {item.get('title') or item.get('topic') or item.get('project_id', 'item')}",
                platform=str((item.get("target_platforms") or item.get("platforms") or [""])[0]),
                project_id=str(item.get("project_id", "")),
            )
            priors = combined_priors(manager.history, experiment_type)
            experiment = manager.run_experiment(
                experiment["experiment_id"], item=item, context=context,
                historical_priors=priors,
            )
            experiments.append(experiment)
            recommendation = build_recommendation(
                experiment, warnings=list(group.get("warnings", []))
            )
            if recommendation:
                recommendations.append(recommendation)
            else:
                warnings.append(
                    f"{experiment_type}: no usable winner ({experiment['status']})"
                )
        except ValueError as exc:
            warnings.append(f"{experiment_type}: invalid experiment — {exc}")
        except Exception as exc:  # noqa: BLE001 - degrade, never crash the stage
            warnings.append(f"{experiment_type}: failed — {exc}")
            log_event(
                logger, "optimization.item_experiment_failed", level=30,
                type=experiment_type, error=str(exc)[:120],
            )

    recommendations = resolve_conflicts(recommendations)
    package = build_optimization_package(
        recommendations, [e["experiment_id"] for e in experiments]
    )
    if warnings and recommendations:
        package["status"] = "partial"
    return package, experiments, warnings


def run_optimization(context: dict, manager: "ExperimentManager | None" = None) -> dict:
    """The full laboratory cycle over every item in the context. Returns
    the context updates (`optimization_report`, `optimization_recommendations`)."""
    manager = manager or ExperimentManager()
    items, source_key = collect_optimization_items(context)

    if not items:
        report = build_optimization_report([], [], items=0, warnings=["No content in context — nothing to optimize."])
        return {"optimization_report": report, "optimization_recommendations": {}}

    all_experiments, all_recommendations, all_warnings = [], [], []
    for item in items:
        package, experiments, warnings = optimize_item(item, context, manager)
        item["optimization_package"] = package
        all_experiments.extend(experiments)
        all_recommendations.extend(package["recommendations"])
        all_warnings.extend(warnings)

    report = build_optimization_report(
        all_experiments, all_recommendations, items=len(items), warnings=all_warnings
    )
    log_event(
        logger, "optimization.completed",
        items=len(items), experiments=len(all_experiments),
        recommendations=len(all_recommendations), warnings=len(all_warnings),
        source=source_key or "none",
    )

    updates = {
        "optimization_report": report,
        "optimization_recommendations": recommendations_by_type(all_recommendations),
    }
    if source_key:
        updates[source_key] = context.get(source_key, [])
    return updates


class OptimizationLab:
    """The on-demand query surface for the Production Pipeline.

    Answers "give me the strongest X" from concluded experiment history —
    structured recommendations only, never engine calls.
    """

    def __init__(self, manager: "ExperimentManager | None" = None) -> None:
        self.manager = manager or ExperimentManager()

    @property
    def history(self):
        return self.manager.history

    def optimize(self, context: dict) -> dict:
        return run_optimization(context, manager=self.manager)

    def best_hook(self):
        return best_hook(self.history)

    def best_title(self):
        return best_title(self.history)

    def best_thumbnail(self):
        return best_thumbnail(self.history)

    def best_caption(self):
        return best_caption(self.history)

    def best_narration_style(self):
        return best_narration_style(self.history)

    def best_cta(self):
        return best_cta(self.history)

    def best_publishing_window(self):
        return best_publishing_window(self.history)

    def best_content_package(self):
        return best_content_package(self.history)


def get_optimization_lab() -> OptimizationLab:
    """A laboratory bound to the current default directory (test-swappable)."""
    return OptimizationLab()
