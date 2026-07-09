"""Experiment provider interfaces — where platform A/B testing plugs in.

No target platform exposes a public split-testing API the system can use
today, so every experiment runs as a predicted (pre-publish) comparison
inside the laboratory. This module prepares the architecture for the day
that changes: an `ExperimentProvider` declares which platforms and
experiment modes it supports, starts a real on-platform test, and fetches
observed per-variant results the manager ingests through
`record_observed_scores()`.

Real backends (e.g. YouTube "Test & Compare" thumbnails) register with
`register_experiment_provider()` — one adapter per file, zero laboratory
changes. The bundled mock provider is a deterministic placeholder that
proves the contract end-to-end.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from engines.heuristics import stable_jitter
from services.optimization.config import get_optimization_config

PROVIDER_RESULT_FIELDS = (
    "provider",
    "external_id",       # the platform's test id
    "status",            # running | completed | failed | unsupported
    "scores",            # variant_id → observed 0-100 score
    "diagnostics",
)


class ExperimentProvider(ABC):
    """Contract for platform-side experiment execution."""

    key: str = "base"
    platforms: "list[str]" = []          # platforms this provider serves
    modes: "list[str]" = ["ab"]          # EXPERIMENT_MODES it can execute

    def supports(self, platform: str, mode: str = "ab") -> bool:
        return platform in self.platforms and mode in self.modes

    @abstractmethod
    def start_experiment(self, experiment: dict) -> dict:
        """Begin the platform test; return a PROVIDER_RESULT_FIELDS dict."""

    @abstractmethod
    def fetch_results(self, external_id: str) -> dict:
        """Current observed results for a started test."""


class MockExperimentProvider(ExperimentProvider):
    """Deterministic placeholder proving the provider contract.

    Serves every platform and mode; "observed" scores derive stably from
    each variant id so tests and demos are reproducible.
    """

    key = "mock"
    platforms = [
        "youtube_shorts", "youtube", "tiktok", "instagram",
        "facebook_reels", "x", "linkedin", "pinterest",
    ]
    modes = ["ab", "multivariate", "sequential", "platform", "regional", "brand", "lifecycle"]

    def start_experiment(self, experiment: dict) -> dict:
        variants = experiment.get("variant_group", {}).get("variants", [])
        return {
            "provider": self.key,
            "external_id": f"mock_{uuid.uuid4().hex[:10]}",
            "status": "completed",
            "scores": {
                v["variant_id"]: 45 + stable_jitter(v["variant_id"], span=50)
                for v in variants
            },
            "diagnostics": {"mock": True, "variants": len(variants)},
        }

    def fetch_results(self, external_id: str) -> dict:
        return {
            "provider": self.key,
            "external_id": external_id,
            "status": "completed",
            "scores": {},
            "diagnostics": {"mock": True, "note": "results returned at start time"},
        }


_providers: "dict[str, ExperimentProvider]" = {}


def register_experiment_provider(provider: ExperimentProvider) -> ExperimentProvider:
    _providers[provider.key] = provider
    return provider


def get_experiment_provider(platform: str = "", mode: str = "ab") -> "ExperimentProvider | None":
    """The first enabled provider supporting the platform/mode, or None —
    callers fall back to predicted (internal) experiments."""
    config = get_optimization_config()
    for key in sorted(_providers):
        provider = _providers[key]
        if not config.provider_allowed(key):
            continue
        if not platform or provider.supports(platform, mode):
            return provider
    return None


def experiment_provider_keys() -> list:
    return sorted(_providers)


register_experiment_provider(MockExperimentProvider())
