"""Production Acceptance runner — prove production readiness."""

from __future__ import annotations

from typing import Any

from core.log import get_logger, log_event
from services.production_acceptance.catalog import ACCEPTANCE_VERSION, MODES
from services.production_acceptance.dashboard import build_acceptance_dashboard
from services.production_acceptance.generation import (
    run_duration_tests,
    run_platform_tests,
    run_video_generation,
)
from services.production_acceptance.integrity import run_pipeline_integrity
from services.production_acceptance.models import AcceptanceRun, new_run, persist_run
from services.production_acceptance.output import run_output_validation
from services.production_acceptance.quality import run_quality_tests
from services.production_acceptance.recovery import run_recovery_tests
from services.production_acceptance.stress import run_stress_tests

logger = get_logger(__name__)


def run_acceptance_suite(
    mode: str = "smoke",
    *,
    include: list[str] | None = None,
) -> dict[str, Any]:
    """Execute acceptance categories and persist run + dashboard.

    mode: smoke | full | stress
    include: optional subset of category names
    """
    mode = (mode or "smoke").lower()
    if mode not in MODES:
        mode = "smoke"

    run: AcceptanceRun = new_run(mode, version=ACCEPTANCE_VERSION)
    log_event(logger, "acceptance.started", run_id=run.run_id, mode=mode)

    catalog = {
        "pipeline_integrity": run_pipeline_integrity,
        "video_generation": lambda: run_video_generation(mode),
        "duration": lambda: run_duration_tests(mode),
        "platform": lambda: run_platform_tests(mode),
        "stress": lambda: run_stress_tests(mode),
        "quality": lambda: run_quality_tests(mode),
        "recovery": lambda: run_recovery_tests(mode),
        "output_validation": lambda: run_output_validation(mode),
    }
    selected = include or list(catalog.keys())

    for name in selected:
        fn = catalog.get(name)
        if not fn:
            continue
        log_event(logger, "acceptance.category_started", run_id=run.run_id, category=name)
        for result in fn():
            run.add(result)
            log_event(
                logger,
                "acceptance.test_finished",
                run_id=run.run_id,
                category=result.category,
                name=result.name,
                passed=result.passed,
                duration_ms=result.duration_ms,
            )

    path = persist_run(run)
    dash = build_acceptance_dashboard(run)
    summary = run.summary()
    log_event(
        logger,
        "acceptance.finished",
        run_id=run.run_id,
        mode=mode,
        pass_pct=summary.get("pass_pct"),
        ok=summary.get("ok"),
    )
    return {
        "run_id": run.run_id,
        "mode": mode,
        "version": ACCEPTANCE_VERSION,
        "summary": summary,
        "dashboard": dash,
        "run_path": str(path),
        "passed": bool(summary.get("ok")),
        "results": [r.to_dict() for r in run.results],
    }
