"""Parallel production runner with resource limits."""

from __future__ import annotations

import threading
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any, Callable

from core.log import get_logger, log_event

logger = get_logger(__name__)

DEFAULT_MAX_PARALLEL = 2


class ParallelProductionPool:
    """Run multiple Executive productions concurrently under a worker cap."""

    def __init__(self, *, max_workers: int = DEFAULT_MAX_PARALLEL) -> None:
        self.max_workers = max(1, int(max_workers))
        self._executor = ThreadPoolExecutor(
            max_workers=self.max_workers,
            thread_name_prefix="executive-prod",
        )
        self._lock = threading.Lock()
        self._futures: dict[str, Future] = {}

    def submit(self, run_id: str, fn: Callable[[], Any]) -> Future:
        log_event(logger, "executive.parallel_submit", run_id=run_id, max_workers=self.max_workers)

        def _wrapped():
            try:
                return fn()
            except Exception as exc:  # noqa: BLE001
                log_event(logger, "executive.parallel_failed", run_id=run_id, error=str(exc))
                raise

        fut = self._executor.submit(_wrapped)
        with self._lock:
            self._futures[run_id] = fut
        return fut

    def active_count(self) -> int:
        with self._lock:
            return sum(1 for f in self._futures.values() if not f.done())

    def shutdown(self, wait: bool = False) -> None:
        self._executor.shutdown(wait=wait)


_POOL: ParallelProductionPool | None = None
_POOL_LOCK = threading.Lock()


def get_parallel_pool(*, max_workers: int | None = None) -> ParallelProductionPool:
    global _POOL
    with _POOL_LOCK:
        if _POOL is None:
            _POOL = ParallelProductionPool(max_workers=max_workers or DEFAULT_MAX_PARALLEL)
        elif max_workers and max_workers != _POOL.max_workers:
            # Recreate only when idle
            if _POOL.active_count() == 0:
                _POOL.shutdown(wait=False)
                _POOL = ParallelProductionPool(max_workers=max_workers)
        return _POOL
