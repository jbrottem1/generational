"""ExperimentManager — A/B and multivariate experimentation framework.

Supports thumbnail, hook, script, posting-time, caption, and voice
experiments (plus generic A/B tests): create an experiment with variants,
assign content deterministically, record observed metrics per variant, and
determine a statistical winner (Welch's z-test over composite performance
scores, confidence via the normal CDF).

Experiments persist to `data/analytics/experiments.json`. Records link
back through the `experiment_id` / `variant_id` fields on every analytics
record (`services.analytics.attach_experiment`).
"""

from __future__ import annotations

import json
import math
import os
import uuid
from datetime import datetime, timezone

from core.log import get_logger, log_event
from services.analytics import store as _store_module
from services.analytics.models import performance_score
from services.learning.memory import MEMORY_CATEGORY, HistoricalMemory

logger = get_logger(__name__)

_EXPERIMENTS_FILE = "experiments.json"

EXPERIMENT_KINDS = (
    "ab",
    "thumbnail",
    "hook",
    "script",
    "posting_time",
    "caption",
    "voice",
)


class ExperimentStatus:
    RUNNING = "running"
    COMPLETED = "completed"
    INSUFFICIENT_DATA = "insufficient_data"

    ALL = (RUNNING, COMPLETED, INSUFFICIENT_DATA)


EXPERIMENT_FIELDS = (
    "experiment_id",
    "kind",               # EXPERIMENT_KINDS value
    "name",
    "hypothesis",
    "metric",             # what decides the winner (composite score today)
    "min_samples",        # per-variant floor before a winner can be called
    "status",             # ExperimentStatus value
    "variants",           # [{variant_id, label, payload, results: [scores]}]
    "assignments",        # content_id → variant_id
    "winner",             # {variant_id, label, confidence, lift} or {}
    "created_at",
    "completed_at",
)

# Confidence (percent) a winner needs before the experiment auto-completes.
WINNER_CONFIDENCE_THRESHOLD = 90


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normal_cdf(z: float) -> float:
    """Standard normal CDF via erf — no external dependencies."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _mean_and_variance(values: list) -> "tuple[float, float]":
    n = len(values)
    mean = sum(values) / n
    if n < 2:
        return mean, 0.0
    variance = sum((v - mean) ** 2 for v in values) / (n - 1)
    return mean, variance


def compare_variants(scores_a: list, scores_b: list) -> dict:
    """Welch's z-test: is A's mean score really higher than B's?

    Returns {z, confidence, lift}: `confidence` is the one-sided percent
    confidence that A beats B; `lift` the difference in mean scores.
    """
    mean_a, var_a = _mean_and_variance(scores_a)
    mean_b, var_b = _mean_and_variance(scores_b)
    lift = mean_a - mean_b
    standard_error = math.sqrt(
        var_a / max(1, len(scores_a)) + var_b / max(1, len(scores_b))
    )
    if standard_error == 0:
        # Identical spreads — call it decisively only if the means differ.
        confidence = 100.0 if lift > 0 else (0.0 if lift < 0 else 50.0)
        return {"z": 0.0, "confidence": round(confidence, 1), "lift": round(lift, 2)}
    z = lift / standard_error
    return {
        "z": round(z, 3),
        "confidence": round(_normal_cdf(z) * 100, 1),
        "lift": round(lift, 2),
    }


class ExperimentManager:
    """Create, run, and statistically conclude content experiments."""

    def __init__(self, directory: str = "", memory: "HistoricalMemory | None" = None) -> None:
        self.directory = directory or _store_module._DEFAULT_DIR
        self._memory = memory

    # ------------------------------------------------------------ storage

    def _path(self) -> str:
        return os.path.join(self.directory, _EXPERIMENTS_FILE)

    def _read(self) -> list:
        path = self._path()
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Failed to read experiments: %s", exc)
            return []

    def _write(self, experiments: list) -> None:
        os.makedirs(self.directory, exist_ok=True)
        with open(self._path(), "w", encoding="utf-8") as file:
            json.dump(experiments, file, indent=2)

    def _save(self, experiment: dict) -> dict:
        experiments = self._read()
        for index, existing in enumerate(experiments):
            if existing["experiment_id"] == experiment["experiment_id"]:
                experiments[index] = experiment
                break
        else:
            experiments.append(experiment)
        self._write(experiments)
        return experiment

    # ---------------------------------------------------------- lifecycle

    def create_experiment(
        self,
        kind: str,
        name: str,
        variants: list,
        hypothesis: str = "",
        min_samples: int = 3,
    ) -> dict:
        """Start an experiment. `variants` are payload dicts (or labels):
        the thumbnail concepts, hooks, posting times, captions, or voice
        styles under test — at least two."""
        if kind not in EXPERIMENT_KINDS:
            raise ValueError(f"Unknown experiment kind '{kind}'. Valid: {list(EXPERIMENT_KINDS)}")
        if len(variants) < 2:
            raise ValueError("An experiment needs at least two variants.")

        experiment = {
            "experiment_id": f"exp_{uuid.uuid4().hex[:12]}",
            "kind": kind,
            "name": name,
            "hypothesis": hypothesis,
            "metric": "performance_score",
            "min_samples": int(min_samples),
            "status": ExperimentStatus.RUNNING,
            "variants": [
                {
                    "variant_id": f"var_{uuid.uuid4().hex[:8]}",
                    "label": variant.get("label", f"variant_{index}") if isinstance(variant, dict) else str(variant),
                    "payload": variant if isinstance(variant, dict) else {"value": variant},
                    "results": [],
                }
                for index, variant in enumerate(variants)
            ],
            "assignments": {},
            "winner": {},
            "created_at": _now_iso(),
            "completed_at": "",
        }
        self._save(experiment)
        log_event(
            logger, "learning.experiment_created",
            experiment_id=experiment["experiment_id"], kind=kind,
            variants=len(experiment["variants"]),
        )
        return experiment

    def get_experiment(self, experiment_id: str) -> "dict | None":
        for experiment in self._read():
            if experiment["experiment_id"] == experiment_id:
                return experiment
        return None

    def list_experiments(self, status: str = "", kind: str = "") -> list:
        experiments = list(reversed(self._read()))
        if status:
            experiments = [e for e in experiments if e["status"] == status]
        if kind:
            experiments = [e for e in experiments if e["kind"] == kind]
        return experiments

    def assign_variant(self, experiment_id: str, content_id: str) -> dict:
        """Deterministic round-robin assignment; repeat calls for the same
        content return its existing variant."""
        experiment = self.get_experiment(experiment_id)
        if experiment is None:
            raise ValueError(f"Unknown experiment: {experiment_id}")

        assigned_id = experiment["assignments"].get(content_id)
        if assigned_id is None:
            index = len(experiment["assignments"]) % len(experiment["variants"])
            assigned_id = experiment["variants"][index]["variant_id"]
            experiment["assignments"][content_id] = assigned_id
            self._save(experiment)

        return next(v for v in experiment["variants"] if v["variant_id"] == assigned_id)

    def record_result(self, experiment_id: str, variant_id: str, metrics: dict) -> dict:
        """Attach one observed outcome (an ANALYTICS_METRIC dict) to a
        variant, then re-evaluate for a statistical winner."""
        experiment = self.get_experiment(experiment_id)
        if experiment is None:
            raise ValueError(f"Unknown experiment: {experiment_id}")

        for variant in experiment["variants"]:
            if variant["variant_id"] == variant_id:
                variant["results"].append(performance_score(metrics))
                break
        else:
            raise ValueError(f"Unknown variant '{variant_id}' in experiment {experiment_id}")

        self._save(experiment)
        return self.evaluate(experiment_id)

    def ingest_records(self, records: list) -> int:
        """Pull experiment outcomes straight from analytics records that
        carry experiment_id/variant_id linkage. Returns results ingested."""
        ingested = 0
        for record in records:
            experiment_id = record.get("experiment_id", "")
            variant_id = record.get("variant_id", "")
            if experiment_id and variant_id and record.get("metrics_status") == "collected":
                try:
                    self.record_result(experiment_id, variant_id, record.get("metrics", {}))
                    ingested += 1
                except ValueError:
                    continue
        return ingested

    # ---------------------------------------------------------- evaluation

    def evaluate(self, experiment_id: str) -> dict:
        """Statistical evaluation: rank variants, compare the top two, and
        conclude the experiment when the winner clears the confidence bar."""
        experiment = self.get_experiment(experiment_id)
        if experiment is None:
            raise ValueError(f"Unknown experiment: {experiment_id}")

        min_samples = experiment["min_samples"]
        ready = all(len(v["results"]) >= min_samples for v in experiment["variants"])
        if not ready:
            return experiment

        ranked = sorted(
            experiment["variants"],
            key=lambda v: sum(v["results"]) / len(v["results"]),
            reverse=True,
        )
        comparison = compare_variants(ranked[0]["results"], ranked[1]["results"])

        if comparison["confidence"] >= WINNER_CONFIDENCE_THRESHOLD:
            experiment["status"] = ExperimentStatus.COMPLETED
            experiment["completed_at"] = _now_iso()
            experiment["winner"] = {
                "variant_id": ranked[0]["variant_id"],
                "label": ranked[0]["label"],
                "confidence": comparison["confidence"],
                "lift": comparison["lift"],
            }
            self._save(experiment)
            self._remember_outcome(experiment)
            log_event(
                logger, "learning.experiment_completed",
                experiment_id=experiment_id, winner=ranked[0]["label"],
                confidence=comparison["confidence"],
            )
        return experiment

    def _remember_outcome(self, experiment: dict) -> None:
        """Concluded experiments become cumulative long-term memory."""
        memory = self._memory or HistoricalMemory(directory=self.directory)
        try:
            memory.remember(
                MEMORY_CATEGORY.EXPERIMENT_OUTCOMES,
                {
                    "experiment_id": experiment["experiment_id"],
                    "kind": experiment["kind"],
                    "name": experiment["name"],
                    "winner": experiment["winner"],
                },
                confidence=int(experiment["winner"].get("confidence", 0)),
                evidence={
                    "variants": [
                        {"label": v["label"], "samples": len(v["results"])}
                        for v in experiment["variants"]
                    ]
                },
                source="experiment",
            )
        except Exception as exc:  # noqa: BLE001 - memory failures never break experiments
            log_event(logger, "learning.memory_write_failed", level=30, error=str(exc)[:120])


def get_experiment_manager() -> ExperimentManager:
    """A manager bound to the current default directory (test-swappable)."""
    return ExperimentManager()
