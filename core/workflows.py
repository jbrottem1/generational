"""Workflow engine — executes configurable pipelines of engines.

A workflow is just an ordered list of engine keys, so pipelines are data,
not code: define a new list (or edit an existing one) and the engine
executes it. Engines that are not ready are skipped and recorded, meaning
workflows can already reference every planned stage — they light up as
engines get implemented.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from core.log import get_logger, log_event
from engines import registry

logger = get_logger(__name__)


class StepStatus:
    SUCCEEDED = "succeeded"
    SKIPPED = "skipped"
    FAILED = "failed"


# Named pipeline definitions. New workflows are added here (or passed
# directly to execute() as a list of engine keys).
WORKFLOWS = {
    "ideation": ["ideation"],
    # The intelligence pipeline: trend discovery → opportunity ranking →
    # trend forecasting (Agent 11: forecasts, classifications, structured
    # recommendations, and quality control over the ranked opportunities) →
    # research → 20 candidates → psychology scoring → script generation
    # (multiple scored variants per candidate, immediately after psychology)
    # → attention graph (12-dimension radar + recommendations, Phase 2) →
    # visual intelligence (the Cinematic AI Director: directed storyboard,
    # shot list, style presets, retention prediction, AI prompts, asset
    # requests, thumbnails, render package — consumes trend, psychology,
    # structured script, and attention graph signals) → voice & audio (Audio
    # Production Package: narration plan, voice style, pacing/pauses/emphasis,
    # SFX, music direction, mood, scene cues, retention notes — planning
    # only, before any rendering) → weighted ranking (psychology +
    # opportunity + script quality) → script fallback for anything
    # unscripted → critic → revision → citation → SEO packaging → threat
    # detection (10 failure modes, Phase 3) → final quality scores +
    # publish gate.
    "intelligence": [
        "trend_discovery",
        "opportunity_ranking",
        "trend_forecasting",
        "research",
        "ideation",
        "psychology",
        "script_generation",
        "attention_graph",
        "visual_intelligence",
        "voice_audio",
        "ranking",
        "script",
        "critic",
        "revision",
        "citation",
        "seo",
        "threat_detection",
        "quality",
    ],
    "full_content": [
        "trend_discovery",
        "opportunity_ranking",
        "trend_forecasting",
        "research",
        "ideation",
        "psychology",
        "script_generation",
        "attention_graph",
        "visual_intelligence",
        "voice_audio",
        "ranking",
        "script",
        "critic",
        "revision",
        "citation",
        "seo",
        "threat_detection",
        "quality",
        "voice",
        "image",
        "video",
        "publishing",
    ],
    # v4.0 media production pipeline — runs on approved scripts only,
    # coordinated separately so the intelligence workflow stays untouched.
    "media_production": [
        "scene_planning",
        "narration",
        "visual_planning",
        "asset_manager",
        "subtitle",
        "timeline",
        "render_package",
        "publishing_queue",
    ],
}


@dataclass
class StepResult:
    engine_key: str
    status: str
    error: str = ""
    duration_ms: int = 0
    problems: list = field(default_factory=list)   # contract-validation findings


@dataclass
class WorkflowRun:
    workflow: str
    context: dict
    steps: "list[StepResult]" = field(default_factory=list)

    @property
    def succeeded(self) -> bool:
        return all(step.status != StepStatus.FAILED for step in self.steps)

    def summary(self) -> dict:
        return {
            "workflow": self.workflow,
            "succeeded": self.succeeded,
            "steps": [
                {
                    "engine": step.engine_key,
                    "status": step.status,
                    "error": step.error,
                    "duration_ms": step.duration_ms,
                    "problems": list(step.problems),
                }
                for step in self.steps
            ],
        }


def _validate_contract(engine, method: str, payload: dict) -> list:
    """Contract validation findings for one engine — never raises.

    Classic engines have no contracts (no findings); ContractEngine
    subclasses declare input/output keys and report what is missing. The
    orchestrator surfaces findings as stage diagnostics, never failures.
    """
    validator = getattr(engine, method, None)
    if validator is None:
        return []
    try:
        return [f"{engine.key}: {problem}" for problem in (validator(payload) or [])]
    except Exception as exc:  # noqa: BLE001 - validation must never break a run
        return [f"{engine.key}: {method} raised {exc}"]


class WorkflowEngine:
    def execute(self, workflow, context: dict) -> WorkflowRun:
        """Run a workflow (a registered name or a list of engine keys).

        The context dict flows through every step; each engine's output is
        merged back into it. A failing step stops the run (partial context
        is preserved); unready engines are skipped.
        """
        if isinstance(workflow, str):
            name, steps = workflow, WORKFLOWS[workflow]
        else:
            name, steps = "custom", list(workflow)

        run = WorkflowRun(workflow=name, context=context)
        log_event(logger, "workflow.started", workflow=name, steps=len(steps))

        for key in steps:
            engine = registry.get_engine(key)
            if engine is None or not engine.is_ready():
                run.steps.append(StepResult(engine_key=key, status=StepStatus.SKIPPED))
                log_event(logger, "workflow.step_skipped", workflow=name, engine=key)
                continue

            problems = _validate_contract(engine, "validate_input", context)
            started = time.time()
            try:
                updates = engine.run(context) or {}
                context.update(updates)
                problems += _validate_contract(engine, "validate_output", updates)
                duration = int((time.time() - started) * 1000)
                run.steps.append(
                    StepResult(engine_key=key, status=StepStatus.SUCCEEDED, duration_ms=duration, problems=problems)
                )
                log_event(logger, "workflow.step_succeeded", workflow=name, engine=key, duration_ms=duration)
            except Exception as exc:  # noqa: BLE001 - one bad step must not crash the app
                duration = int((time.time() - started) * 1000)
                run.steps.append(
                    StepResult(engine_key=key, status=StepStatus.FAILED, error=str(exc), duration_ms=duration, problems=problems)
                )
                log_event(logger, "workflow.step_failed", workflow=name, engine=key, error=str(exc))
                break

        log_event(logger, "workflow.finished", workflow=name, succeeded=run.succeeded)
        return run


WORKFLOW_JOB_TYPE = "run_workflow"


def _run_workflow_job(payload: dict) -> dict:
    """Job-queue handler: payload = {"workflow": name_or_steps, "context": dict}."""
    run = WorkflowEngine().execute(payload["workflow"], payload.get("context", {}))
    return {"run": run.summary(), "context": run.context}


def ensure_workflow_handler(queue) -> None:
    """Register the workflow job handler on a queue (idempotent)."""
    if not queue.has_handler(WORKFLOW_JOB_TYPE):
        queue.register_handler(WORKFLOW_JOB_TYPE, _run_workflow_job)
