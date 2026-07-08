"""System diagnostics — health checks across every service.

Each check returns {"name", "status" ("ok"|"warn"|"error"), "detail"}.
Consumed by the Settings tab and by tests; a future ops dashboard or CLI
can reuse `run_diagnostics()` as-is.
"""

from __future__ import annotations

import os
import tempfile

from core.log import get_logger, log_event

logger = get_logger(__name__)

OK = "ok"
WARN = "warn"
ERROR = "error"


def _check(name: str, status: str, detail: str) -> dict:
    return {"name": name, "status": status, "detail": detail}


def _check_ai_provider() -> dict:
    from core.ai import get_provider, is_demo_mode

    provider = get_provider()
    if is_demo_mode():
        return _check("AI Provider", WARN, "Demo provider active — no OpenAI API key configured.")
    return _check("AI Provider", OK, f"'{provider.name}' provider connected.")


def _check_storage() -> dict:
    from core.storage import get_store, project_count

    store = get_store()
    directory = getattr(store, "directory", None)
    try:
        if directory:
            os.makedirs(directory, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=directory, suffix=".tmp"):
                pass
        return _check("Project Storage", OK, f"Writable · {project_count()} project(s) stored.")
    except OSError as exc:
        return _check("Project Storage", ERROR, f"Not writable: {exc}")


def _check_engines() -> dict:
    from engines import registry

    engines = registry.all_engines()
    ready = [engine.key for engine in engines if engine.is_ready()]
    if not engines:
        return _check("Engines", ERROR, "No engines registered.")
    return _check(
        "Engines",
        OK,
        f"{len(engines)} registered · {len(ready)} ready ({', '.join(ready) or 'none'}).",
    )


def _check_job_queue() -> dict:
    from core.jobs import get_queue

    stats = get_queue().stats()
    status = WARN if stats.get("failed") else OK
    return _check(
        "Job Queue",
        status,
        f"{stats['total']} job(s) this session · {stats['succeeded']} succeeded · "
        f"{stats['failed']} failed · {stats['pending']} pending.",
    )


def _check_channels() -> dict:
    from services.channels import get_channel_manager

    count = get_channel_manager().channel_count()
    return _check("Channel Manager", OK, f"{count} channel(s) configured.")


def _check_knowledge_base() -> dict:
    from services.knowledge import get_knowledge_base

    total = get_knowledge_base().count()
    return _check("Knowledge Base", OK, f"{total} entries stored.")


def run_diagnostics() -> list:
    """Run every health check; never raises."""
    checks = []
    for check_fn in (
        _check_ai_provider,
        _check_storage,
        _check_engines,
        _check_job_queue,
        _check_channels,
        _check_knowledge_base,
    ):
        try:
            checks.append(check_fn())
        except Exception as exc:  # noqa: BLE001 - diagnostics must never crash the app
            name = check_fn.__name__.replace("_check_", "").replace("_", " ").title()
            checks.append(_check(name, ERROR, f"Check crashed: {exc}"))
    log_event(
        logger,
        "diagnostics.completed",
        ok=sum(1 for c in checks if c["status"] == OK),
        warn=sum(1 for c in checks if c["status"] == WARN),
        error=sum(1 for c in checks if c["status"] == ERROR),
    )
    return checks
