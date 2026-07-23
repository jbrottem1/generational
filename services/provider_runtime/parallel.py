"""Parallel provider execution — race, compare, vote."""

from __future__ import annotations

import concurrent.futures
from typing import Callable

from services.provider_runtime.adapter import ProviderAdapter
from services.provider_runtime.models import ProviderRequest, ProviderResponse
from services.provider_runtime.selection import ProviderSelectionEngine


class ParallelExecutor:
    """Run multiple providers in parallel and select the best result."""

    def __init__(self, selector: "ProviderSelectionEngine | None" = None) -> None:
        self._selector = selector or ProviderSelectionEngine()

    def execute_parallel(
        self,
        request: ProviderRequest,
        executor: Callable[[ProviderAdapter, ProviderRequest], ProviderResponse],
        capability: str = "",
        max_workers: int = 3,
    ) -> ProviderResponse:
        cap = capability or request.capability
        ranked = self._selector.rank_all(cap, request.optimize_for)
        available = [p for p in ranked if p.is_available()]
        if not available:
            return ProviderResponse(
                success=False,
                operation=request.operation,
                error=f"No available providers for {cap!r}",
            )

        count = request.parallel_candidates or min(max_workers, len(available))
        candidates = available[:count]

        if len(candidates) == 1:
            return executor(candidates[0], request)

        results: list[ProviderResponse] = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(candidates)) as pool:
            futures = {pool.submit(executor, p, request): p for p in candidates}
            for future in concurrent.futures.as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as exc:  # noqa: BLE001
                    provider = futures[future]
                    results.append(ProviderResponse(
                        success=False,
                        operation=request.operation,
                        provider=provider.name,
                        error=str(exc),
                    ))

        return self._select_best(results, request.optimize_for)

    def _select_best(self, results: list[ProviderResponse], optimize_for: str) -> ProviderResponse:
        successful = [r for r in results if r.success]
        if not successful:
            return results[0] if results else ProviderResponse(success=False, error="No results")

        if optimize_for == "speed":
            return min(successful, key=lambda r: r.latency_ms)
        if optimize_for == "cost":
            return min(successful, key=lambda r: r.cost_usd)
        # Default: quality vote — prefer non-demo, lowest latency among successes
        non_demo = [r for r in successful if not r.demo_mode]
        pool = non_demo or successful
        return min(pool, key=lambda r: r.latency_ms)
