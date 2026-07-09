"""Parallel unit execution for multi-part productions (Agent 23).

Runs independent ProductionJob units concurrently via a thread pool.
Each unit still goes through WorkflowExecutor → Orchestrator (never engines).
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from services.autonomous_production.models import ProductionJob


def run_units_parallel(
    units: list["ProductionJob"],
    execute_fn: Callable[["ProductionJob"], "ProductionJob"],
    *,
    max_workers: int = 4,
) -> list["ProductionJob"]:
    """Execute independent unit jobs in parallel; preserve input order in results."""
    if not units:
        return []
    if len(units) == 1 or max_workers <= 1:
        return [execute_fn(u) for u in units]

    workers = min(max_workers, len(units))
    results: dict[str, "ProductionJob"] = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(execute_fn, unit): unit.job_id for unit in units}
        for fut in as_completed(futures):
            job_id = futures[fut]
            try:
                results[job_id] = fut.result()
            except Exception as exc:  # noqa: BLE001
                unit = next(u for u in units if u.job_id == job_id)
                unit.state = "failed"
                unit.summary.error = str(exc)
                unit.summary.failures.append(
                    {"code": "parallel_unit_failure", "message": str(exc), "job_id": job_id}
                )
                results[job_id] = unit
    return [results[u.job_id] for u in units]
