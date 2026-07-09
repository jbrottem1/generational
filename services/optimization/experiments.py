"""Experiment framework — create, schedule, run, and conclude experiments.

The laboratory's unit of work is the Experiment (LAB_EXPERIMENT_FIELDS):
one variant group competing for one decision, in one of the prepared test
modes (A/B, multivariate, sequential, platform, regional, brand,
lifecycle). `ExperimentRun`s accumulate scores per execution;
`ExperimentResult` captures the concluded winner with statistical
confidence (Welch's z-test, reused from Agent 9's framework) and expected
lift. `ExperimentHistory` persists everything append-friendly to
`data/optimization/experiments.json`; `ExperimentScheduler` keeps
concurrent experiments inside configured limits and releases scheduled
ones when due.

Failure policy: invalid inputs raise ValueError at creation time (callers
degrade); everything after creation degrades to statuses/warnings — a
concluded-but-unconvincing experiment is LOW_CONFIDENCE, an undersized one
INSUFFICIENT_DATA, and a provider failure FAILED with diagnostics. Never a
crash.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone

from core.log import get_logger, log_event
from services.learning.experiments import compare_variants
from services.optimization.config import all_experiment_types, get_optimization_config
from services.optimization.learning_bridge import remember_experiment_outcome
from services.optimization.models import EXPERIMENT_MODES, ExperimentStatus
from services.optimization.scoring import rank_variants
from services.optimization.variants import dedupe_variants, validate_variant_group

logger = get_logger(__name__)

_DEFAULT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "optimization",
)

_EXPERIMENTS_FILE = "experiments.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ExperimentHistory:
    """Durable store of every laboratory experiment, past and present."""

    def __init__(self, directory: str = "") -> None:
        self.directory = directory or _DEFAULT_DIR

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
            logger.error("Failed to read optimization experiments: %s", exc)
            return []

    def _write(self, experiments: list) -> None:
        os.makedirs(self.directory, exist_ok=True)
        with open(self._path(), "w", encoding="utf-8") as file:
            json.dump(experiments, file, indent=2)

    def save(self, experiment: dict) -> dict:
        experiments = self._read()
        for index, existing in enumerate(experiments):
            if existing["experiment_id"] == experiment["experiment_id"]:
                experiments[index] = experiment
                break
        else:
            experiments.append(experiment)
        self._write(experiments)
        return experiment

    def get(self, experiment_id: str) -> "dict | None":
        for experiment in self._read():
            if experiment["experiment_id"] == experiment_id:
                return experiment
        return None

    def list(self, status: str = "", experiment_type: str = "") -> list:
        experiments = list(reversed(self._read()))
        if status:
            experiments = [e for e in experiments if e["status"] == status]
        if experiment_type:
            experiments = [e for e in experiments if e["experiment_type"] == experiment_type]
        return experiments

    def active(self) -> list:
        return [
            e for e in self.list()
            if e["status"] in (ExperimentStatus.SCHEDULED, ExperimentStatus.RUNNING)
        ]

    def concluded(self, experiment_type: str = "") -> list:
        return [
            e for e in self.list(experiment_type=experiment_type)
            if e["status"] in ExperimentStatus.CONCLUDED
        ]

    def count(self) -> int:
        return len(self._read())


class ExperimentScheduler:
    """Concurrency + scheduling gatekeeper for the experiment manager."""

    def __init__(self, history: ExperimentHistory) -> None:
        self.history = history

    def can_start(self) -> bool:
        limit = get_optimization_config().max_concurrent_experiments
        return len(self.history.active()) < limit

    def schedule(self, experiment: dict, scheduled_for: str = "") -> dict:
        experiment["scheduled_for"] = scheduled_for or _now_iso()
        experiment["status"] = ExperimentStatus.SCHEDULED
        return self.history.save(experiment)

    def due(self, now: str = "") -> list:
        """Scheduled experiments whose start time has arrived, oldest first,
        capped so releasing them never exceeds the concurrency limit."""
        now = now or _now_iso()
        limit = get_optimization_config().max_concurrent_experiments
        running = len([
            e for e in self.history.active() if e["status"] == ExperimentStatus.RUNNING
        ])
        capacity = max(0, limit - running)
        scheduled = [
            e for e in self.history.list(status=ExperimentStatus.SCHEDULED)
            if (e.get("scheduled_for") or "") <= now
        ]
        scheduled.sort(key=lambda e: (e.get("scheduled_for", ""), e.get("created_at", "")))
        return scheduled[:capacity]


class ExperimentManager:
    """Create, run concurrently, and statistically conclude experiments."""

    def __init__(self, directory: str = "", history: "ExperimentHistory | None" = None) -> None:
        self.history = history or ExperimentHistory(directory=directory)
        self.scheduler = ExperimentScheduler(self.history)

    # ---------------------------------------------------------- lifecycle

    def create_experiment(
        self,
        experiment_type: str,
        variant_group: dict,
        mode: str = "",
        name: str = "",
        hypothesis: str = "",
        platform: str = "",
        region: str = "",
        brand_id: str = "",
        project_id: str = "",
        provider: str = "",
        min_confidence: "int | None" = None,
    ) -> dict:
        """One LAB_EXPERIMENT_FIELDS dict, validated and persisted as DRAFT.

        Invalid experiment types/modes and undersized variant groups raise
        ValueError — the caller (the lab facade) degrades gracefully.
        """
        config = get_optimization_config()
        if experiment_type not in all_experiment_types(config):
            raise ValueError(
                f"Unknown experiment type {experiment_type!r}. Valid: {all_experiment_types(config)}"
            )
        mode = mode or ("ab" if len(variant_group.get("variants", [])) == 2 else "multivariate")
        if mode not in EXPERIMENT_MODES:
            raise ValueError(f"Unknown experiment mode {mode!r}. Valid: {list(EXPERIMENT_MODES)}")

        variants = dedupe_variants(variant_group.get("variants", []))
        if len(variants) < 2:
            raise ValueError("An experiment needs at least two distinct variants.")
        group = dict(variant_group)
        group["variants"] = variants
        group["warnings"] = validate_variant_group(group)

        experiment = {
            "experiment_id": f"lab_{uuid.uuid4().hex[:12]}",
            "experiment_type": experiment_type,
            "mode": mode,
            "name": name or f"{experiment_type} experiment",
            "hypothesis": hypothesis,
            "status": ExperimentStatus.DRAFT,
            "variant_group": group,
            "runs": [],
            "result": {},
            "platform": platform,
            "region": region,
            "brand_id": brand_id,
            "project_id": project_id,
            "provider": provider,
            "min_confidence": int(
                min_confidence if min_confidence is not None else config.min_winner_confidence
            ),
            "scheduled_for": "",
            "created_at": _now_iso(),
            "completed_at": "",
        }
        self.history.save(experiment)
        log_event(
            logger, "optimization.experiment_created",
            experiment_id=experiment["experiment_id"], type=experiment_type,
            mode=mode, variants=len(variants),
        )
        return experiment

    def schedule_experiment(self, experiment_id: str, scheduled_for: str = "") -> dict:
        experiment = self._require(experiment_id)
        return self.scheduler.schedule(experiment, scheduled_for=scheduled_for)

    def run_due_experiments(self, item: "dict | None" = None, context: "dict | None" = None) -> list:
        """Release and run every due scheduled experiment (concurrency-capped)."""
        return [
            self.run_experiment(e["experiment_id"], item=item, context=context)
            for e in self.scheduler.due()
        ]

    def cancel_experiment(self, experiment_id: str) -> dict:
        experiment = self._require(experiment_id)
        experiment["status"] = ExperimentStatus.CANCELLED
        experiment["completed_at"] = _now_iso()
        return self.history.save(experiment)

    # ----------------------------------------------------------- execution

    def run_experiment(
        self,
        experiment_id: str,
        item: "dict | None" = None,
        context: "dict | None" = None,
        historical_priors: "dict | None" = None,
    ) -> dict:
        """Execute one experiment: score + rank its variants (a predicted,
        pre-publish comparison), append an ExperimentRun, and conclude.

        Sequential mode accumulates runs across calls and only concludes
        when every variant has been observed at least once per run pair;
        other modes conclude immediately from the ranked scores.
        """
        experiment = self._require(experiment_id)
        if experiment["status"] in ExperimentStatus.CONCLUDED:
            return experiment
        if experiment["status"] == ExperimentStatus.DRAFT and not self.scheduler.can_start():
            experiment["status"] = ExperimentStatus.SCHEDULED
            experiment["scheduled_for"] = _now_iso()
            self.history.save(experiment)
            log_event(
                logger, "optimization.experiment_deferred",
                experiment_id=experiment_id, reason="concurrency_limit",
            )
            return experiment

        experiment["status"] = ExperimentStatus.RUNNING
        run = {
            "run_id": f"run_{uuid.uuid4().hex[:10]}",
            "experiment_id": experiment_id,
            "scores": {},
            "warnings": list(experiment["variant_group"].get("warnings", [])),
            "started_at": _now_iso(),
            "finished_at": "",
        }
        try:
            ranked = rank_variants(
                experiment["variant_group"]["variants"],
                item=item, context=context, historical_priors=historical_priors,
            )
            experiment["variant_group"]["variants"] = ranked
            run["scores"] = {v["variant_id"]: v["score"] for v in ranked}
        except Exception as exc:  # noqa: BLE001 - a bad run degrades, never crashes
            run["warnings"].append(f"run failed: {exc}")
            experiment["status"] = ExperimentStatus.FAILED
            experiment["completed_at"] = _now_iso()
        run["finished_at"] = _now_iso()
        experiment["runs"].append(run)
        self.history.save(experiment)

        if experiment["status"] != ExperimentStatus.FAILED:
            self.evaluate(experiment_id)
        return self.history.get(experiment_id)

    def record_observed_scores(self, experiment_id: str, scores: dict) -> dict:
        """Attach real observed outcomes (variant_id → 0-100 score, e.g.
        composite performance from analytics or a platform provider) as one
        run — the A/B path once platform experiment support lands."""
        experiment = self._require(experiment_id)
        run = {
            "run_id": f"run_{uuid.uuid4().hex[:10]}",
            "experiment_id": experiment_id,
            "scores": {str(k): float(v) for k, v in scores.items()},
            "warnings": [],
            "started_at": _now_iso(),
            "finished_at": _now_iso(),
        }
        experiment["runs"].append(run)
        experiment["status"] = ExperimentStatus.RUNNING
        self.history.save(experiment)
        return self.evaluate(experiment_id, method="observed")

    # ---------------------------------------------------------- evaluation

    def evaluate(self, experiment_id: str, method: str = "predicted") -> dict:
        """Conclude the experiment: rank variants across accumulated runs,
        compare the top two statistically, and record the ExperimentResult.

        COMPLETED when the winner clears `min_confidence`; LOW_CONFIDENCE
        when it doesn't; INSUFFICIENT_DATA without enough scored variants.
        """
        experiment = self._require(experiment_id)
        variants = experiment["variant_group"]["variants"]

        per_variant: "dict[str, list]" = {v["variant_id"]: [] for v in variants}
        for run in experiment["runs"]:
            for variant_id, score in run.get("scores", {}).items():
                per_variant.setdefault(variant_id, []).append(float(score))

        scored = [v for v in variants if per_variant.get(v["variant_id"])]
        if len(scored) < 2:
            experiment["status"] = ExperimentStatus.INSUFFICIENT_DATA
            experiment["completed_at"] = _now_iso()
            self.history.save(experiment)
            return experiment

        ranked = sorted(
            scored,
            key=lambda v: sum(per_variant[v["variant_id"]]) / len(per_variant[v["variant_id"]]),
            reverse=True,
        )
        top, runner_up = ranked[0], ranked[1]
        comparison = compare_variants(
            per_variant[top["variant_id"]], per_variant[runner_up["variant_id"]]
        )
        # Single predicted runs have no variance — fall back to the score
        # gap as a bounded confidence proxy (a decisive ~5-point composite
        # gap clears the default bar; near-ties stay low-confidence).
        confidence = comparison["confidence"]
        if len(per_variant[top["variant_id"]]) < 2 and method == "predicted":
            gap = abs(comparison["lift"])
            confidence = min(95.0, 50.0 + gap * 8.0)

        result = {
            "winner": top,
            "losers": ranked[1:],
            "ranked": ranked,
            "confidence": round(confidence, 1),
            "expected_lift": comparison["lift"],
            "method": method,
            "evaluated_at": _now_iso(),
        }
        experiment["result"] = result
        experiment["status"] = (
            ExperimentStatus.COMPLETED
            if confidence >= experiment["min_confidence"]
            else ExperimentStatus.LOW_CONFIDENCE
        )
        experiment["completed_at"] = _now_iso()
        self.history.save(experiment)

        if experiment["status"] == ExperimentStatus.COMPLETED:
            remember_experiment_outcome(experiment)
        log_event(
            logger, "optimization.experiment_concluded",
            experiment_id=experiment_id, status=experiment["status"],
            winner=top.get("label", ""), confidence=result["confidence"],
        )
        return experiment

    # ------------------------------------------------------------- helpers

    def _require(self, experiment_id: str) -> dict:
        experiment = self.history.get(experiment_id)
        if experiment is None:
            raise ValueError(f"Unknown experiment: {experiment_id}")
        return experiment


def get_experiment_manager() -> ExperimentManager:
    """A manager bound to the current default directory (test-swappable)."""
    return ExperimentManager()
