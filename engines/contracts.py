"""Shared engine contract for Agents 6-10 and every future engine.

`ContractEngine` extends the classic `Engine` plugin interface with explicit
input/output contracts, dependency and capability declarations, validation,
health checks, and diagnostics. Existing engines keep working unchanged;
NEW engines (Render, Publishing, SEO Optimization, Analytics, Learning,
Brand Management, ...) subclass `ContractEngine` so the orchestrator — and
other agents — can reason about them without reading their code.

Contract semantics:
- `input_contract` / `output_contract`: context keys the engine consumes /
  produces. Keys are the shared-context contract (see DATA_CONTRACTS.md);
  never rename or remove keys other engines rely on.
- `dependencies`: engine keys that must run earlier in the pipeline.
- `capabilities`: free-form tags used for discovery ("render", "gpu",
  "multi-language", ...).
- `validate_input` / `validate_output` return a list of problems (empty =
  valid). The orchestrator records problems as stage warnings — validation
  never crashes a run.
"""

from __future__ import annotations

from engines.base import Engine


class ContractEngine(Engine):
    """Base class for contract-first engines (Agents 6-10 onward)."""

    # Identity — `key` (from Engine) doubles as the registry engine_id.
    version: str = "0.1.0"

    # Contracts — override in subclasses.
    input_contract: "list[str]" = []     # context keys consumed
    output_contract: "list[str]" = []    # context keys produced
    dependencies: "list[str]" = []       # engine keys that must run first
    capabilities: "list[str]" = []       # discovery tags

    @property
    def engine_id(self) -> str:
        return self.key

    @property
    def name(self) -> str:
        return self.label or self.key

    # ------------------------------------------------------------ validation

    def validate_input(self, context: dict) -> "list[str]":
        """Return problems with the incoming context (empty list = valid)."""
        return [f"missing required context key: {key}" for key in self.input_contract if key not in context]

    def validate_output(self, updates: dict) -> "list[str]":
        """Return problems with the produced updates (empty list = valid)."""
        return [f"missing promised output key: {key}" for key in self.output_contract if key not in updates]

    # ------------------------------------------------------------ operations

    def health_check(self) -> dict:
        """Cheap liveness/readiness signal for diagnostics dashboards."""
        return {
            "engine_id": self.engine_id,
            "healthy": True,
            "ready": self.is_ready(),
        }

    def diagnostics(self) -> dict:
        """Full self-description — what this engine is and how it plugs in."""
        return {
            "engine_id": self.engine_id,
            "name": self.name,
            "version": self.version,
            "ready": self.is_ready(),
            "input_contract": list(self.input_contract),
            "output_contract": list(self.output_contract),
            "dependencies": list(self.dependencies),
            "capabilities": list(self.capabilities),
        }


class FutureEngine(ContractEngine):
    """A contract-first engine whose implementation has not landed yet.

    Registers identity + contracts now so the orchestrator, docs, and tests
    know the stage exists; reports NOT_IMPLEMENTED instead of doing work.
    The owning agent later overrides `run()` and `is_ready()` — nothing
    else in the system changes.
    """

    def is_ready(self) -> bool:
        return False

    def run(self, context: dict) -> dict:
        return {f"{self.key}_status": "NOT_IMPLEMENTED"}
