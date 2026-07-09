"""ProviderRuntime — unified execution surface for all AI operations."""

from __future__ import annotations

from services.provider_runtime import capabilities as cap
from services.provider_runtime.adapter import ProviderAdapter
from services.provider_runtime.cache import ProviderCache
from services.provider_runtime.config import load_dotenv_if_available, load_runtime_config
from services.provider_runtime.cost import ProviderCostEstimator
from services.provider_runtime.execution import RateLimiter, execute_with_retry
from services.provider_runtime.fallback import ProviderFallbackManager
from services.provider_runtime.health import ProviderHealthMonitor
from services.provider_runtime.models import ProviderRequest, ProviderResponse
from services.provider_runtime.parallel import ParallelExecutor
from services.provider_runtime.registry import (
    capability_lookup,
    ensure_registered,
    provider_catalog,
    record_health_score,
)
from services.provider_runtime.observability import emit_provider_metrics
from services.provider_runtime.reliability import ProviderReliabilityManager
from services.provider_runtime.secrets import SecretManager
from services.provider_runtime.selection import ProviderSelectionEngine, get_reliability_manager, set_reliability_manager
from services.provider_runtime.versioning import VersionManager


class ProviderRuntime:
    """Central runtime for provider selection, execution, and recovery.

    The orchestrator and engines request operations through this surface
    without knowing which vendor backend serves them.
    """

    def __init__(
        self,
        credential_overrides: "dict[str, str] | None" = None,
        config: "dict | None" = None,
    ) -> None:
        load_dotenv_if_available()
        self._config = config or load_runtime_config()
        self._credential_overrides = credential_overrides or {}
        self._secrets = SecretManager(overrides=self._credential_overrides)
        # Sync secret-manager values into overrides so adapters see them.
        for key in (
            "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "XAI_API_KEY",
            "ELEVENLABS_API_KEY", "FAL_KEY", "REPLICATE_API_TOKEN",
        ):
            val = self._secrets.get(key)
            if val and key not in self._credential_overrides:
                self._credential_overrides[key] = val
        self._versions = VersionManager(self._config.get("versions"))
        self._cache = ProviderCache(
            ttl_sec=float(self._config.get("cache_ttl_sec", 3600)),
            enabled=bool(self._config.get("cache_enabled", True)),
        )
        self._reliability = get_reliability_manager()
        # Apply configured weights
        for name, weight in (self._config.get("provider_weights") or {}).items():
            self._reliability.set_weight(str(name), float(weight))
        self._selector = ProviderSelectionEngine(self._reliability)
        self._fallback = ProviderFallbackManager(self._selector)
        self._health = ProviderHealthMonitor(
            failure_threshold=int(self._config.get("failure_threshold", 5)),
            recovery_timeout_sec=float(self._config.get("recovery_timeout_sec", 60)),
        )
        self._cost = ProviderCostEstimator()
        self._parallel = ParallelExecutor(self._selector)
        self._rate_limiter = RateLimiter(default_rpm=int(self._config.get("rate_limit_rpm", 60)))
        self._emit_analytics = bool(self._config.get("emit_analytics", True))
        ensure_registered()
        self._apply_credential_overrides()

    def _apply_credential_overrides(self) -> None:
        from services.provider_runtime.registry import all_providers

        for provider in all_providers():
            if hasattr(provider, "set_credential_overrides"):
                provider.set_credential_overrides(self._credential_overrides)
            if hasattr(provider, "_version_manager"):
                provider._version_manager = self._versions

    # ------------------------------------------------------- public API

    def generate_script(self, payload: dict, **kwargs) -> ProviderResponse:
        return self._execute("generate_script", cap.SCRIPT, payload, **kwargs)

    def generate_image(self, payload: dict, **kwargs) -> ProviderResponse:
        return self._execute("generate_image", cap.IMAGE_GENERATION, payload, **kwargs)

    def generate_video(self, payload: dict, **kwargs) -> ProviderResponse:
        return self._execute("generate_video", cap.VIDEO_GENERATION, payload, **kwargs)

    def generate_animation(self, payload: dict, **kwargs) -> ProviderResponse:
        return self._execute("generate_animation", cap.ANIMATION, payload, **kwargs)

    def generate_voice(self, payload: dict, **kwargs) -> ProviderResponse:
        return self._execute("generate_voice", cap.SPEECH, payload, **kwargs)

    def generate_music(self, payload: dict, **kwargs) -> ProviderResponse:
        return self._execute("generate_music", cap.MUSIC, payload, **kwargs)

    def generate_sound_effects(self, payload: dict, **kwargs) -> ProviderResponse:
        return self._execute("generate_sound_effects", cap.SOUND_EFFECTS, payload, **kwargs)

    def generate_thumbnail(self, payload: dict, **kwargs) -> ProviderResponse:
        return self._execute("generate_thumbnail", cap.THUMBNAIL, payload, **kwargs)

    def generate_caption(self, payload: dict, **kwargs) -> ProviderResponse:
        return self._execute("generate_caption", cap.CAPTION, payload, **kwargs)

    def generate_subtitles(self, payload: dict, **kwargs) -> ProviderResponse:
        return self._execute("generate_subtitles", cap.SUBTITLE, payload, **kwargs)

    def generate_metadata(self, payload: dict, **kwargs) -> ProviderResponse:
        return self._execute("generate_metadata", cap.METADATA, payload, **kwargs)

    def publish(self, payload: dict, **kwargs) -> ProviderResponse:
        return self._execute("publish", cap.PUBLISH, payload, **kwargs)

    def execute(self, request: ProviderRequest) -> ProviderResponse:
        """Low-level entry for custom operations."""
        capability = request.capability or cap.OPERATION_CAPABILITIES.get(request.operation, (cap.LLM,))[0]
        return self._execute(request.operation, capability, request.payload, **self._request_kwargs(request))

    def catalog(self) -> list[dict]:
        return provider_catalog()

    def health_report(self) -> dict:
        report = self._health.health_report()
        # Enrich with live adapter health checks / scores.
        from services.provider_runtime.registry import all_providers

        for provider in all_providers():
            entry = report.setdefault(provider.name, {})
            try:
                probe = provider.health_check()
                entry["probe"] = probe
                score = 100.0 if probe.get("healthy") else 0.0
                if entry.get("circuit_open"):
                    score = 0.0
                record_health_score(provider.name, score)
                entry["health_score"] = score
            except Exception as exc:  # noqa: BLE001
                entry["probe_error"] = str(exc)
                record_health_score(provider.name, 0.0)
        return report

    def usage_summary(self) -> dict:
        return self._cost.usage_summary()

    def cache_stats(self) -> dict:
        return self._cache.stats()

    def versions(self) -> list[dict]:
        return self._versions.catalog()

    def secrets_status(self) -> dict:
        return self._secrets.describe()

    def capability_lookup(self, capability: str) -> list[dict]:
        return capability_lookup(capability)

    def best_provider(self, capability: str) -> "ProviderAdapter | None":
        return self._selector.best(capability)

    def cheapest_provider(self, capability: str) -> "ProviderAdapter | None":
        return self._selector.cheapest(capability)

    def fastest_provider(self, capability: str) -> "ProviderAdapter | None":
        return self._selector.fastest(capability)

    def highest_quality_provider(self, capability: str) -> "ProviderAdapter | None":
        return self._selector.highest_quality(capability)

    def fallback_provider(self, capability: str, exclude: str = "") -> "ProviderAdapter | None":
        return self._selector.fallback_provider(capability, exclude=exclude)

    def reliability_report(self) -> dict:
        return self._reliability.report()

    def recover_provider(self, provider: str = "") -> int:
        recovered = self._reliability.recover(provider)
        if provider:
            self._health.reset()
        return recovered

    def blacklist_provider(self, provider: str, ttl_sec: float = 300.0) -> None:
        self._reliability.blacklist(provider, ttl_sec=ttl_sec)

    def set_provider_weight(self, provider: str, weight: float) -> None:
        self._reliability.set_weight(provider, weight)

    def validate_credentials(self) -> list[dict]:
        from services.provider_runtime.security import credential_inventory, validate_credential

        inventory = credential_inventory(self._credential_overrides)
        return [validate_credential(item["provider"], self._credential_overrides) for item in inventory]

    def audit_events(self, action: str = "") -> list[dict]:
        from services.provider_runtime.security import get_audit_log

        return get_audit_log().events(action)

    def metrics_summary(self) -> dict:
        usage = self.usage_summary()
        reliability = self.reliability_report()
        return {
            "usage": usage,
            "reliability": reliability,
            "latency": self._reliability.latency_report(),
            "cache": self.cache_stats(),
        }

    # ------------------------------------------------------- internals

    def _execute(
        self,
        operation: str,
        capability: str,
        payload: dict,
        **kwargs,
    ) -> ProviderResponse:
        request = ProviderRequest(
            operation=operation,
            capability=capability,
            payload=payload,
            **kwargs,
        )

        cached = self._cache.get(request)
        if cached is not None:
            self._cost.log_usage(cached)
            if self._emit_analytics:
                emit_provider_metrics(cached, cache_hit=True)
            return cached

        if request.parallel_candidates > 1:
            response = self._parallel.execute_parallel(
                request, self._invoke_provider, capability,
            )
        elif request.allow_fallback:
            response = self._fallback.execute_with_fallback(
                request, self._invoke_with_retry, capability,
            )
        else:
            provider = self._selector.select(request, capability)
            if not provider:
                response = ProviderResponse(
                    success=False, operation=operation,
                    error=f"No provider for {capability!r}",
                )
            else:
                response = self._invoke_with_retry(provider, request)

        if response.success:
            self._cache.put(request, response)
        self._cost.log_usage(response)
        if self._emit_analytics:
            emit_provider_metrics(response)
        return response

    def _invoke_with_retry(
        self,
        provider: ProviderAdapter,
        request: ProviderRequest,
    ) -> ProviderResponse:
        if self._reliability.is_blacklisted(provider.name):
            return ProviderResponse(
                success=False,
                operation=request.operation,
                provider=provider.name,
                error=f"Provider {provider.name} is blacklisted",
            )
        if not self._health.is_healthy(provider):
            return ProviderResponse(
                success=False,
                operation=request.operation,
                provider=provider.name,
                error=f"Circuit breaker open for {provider.name}",
            )
        response = execute_with_retry(provider, request, self._invoke_provider, self._rate_limiter)
        if response.success:
            self._health.record_success(provider.name)
            self._reliability.record_success(provider.name, response.latency_ms)
            record_health_score(provider.name, min(100.0, health_score_bump(provider.name, +10)))
        else:
            self._health.record_failure(provider.name, response.error)
            self._reliability.record_failure(provider.name, response.error, response.latency_ms)
            record_health_score(provider.name, max(0.0, health_score_bump(provider.name, -20)))
        return response

    @staticmethod
    def _invoke_provider(provider: ProviderAdapter, request: ProviderRequest) -> ProviderResponse:
        return provider.execute(request)

    @staticmethod
    def _request_kwargs(request: ProviderRequest) -> dict:
        return {
            "preferred_provider": request.preferred_provider,
            "optimize_for": request.optimize_for,
            "timeout_sec": request.timeout_sec,
            "max_retries": request.max_retries,
            "allow_fallback": request.allow_fallback,
            "parallel_candidates": request.parallel_candidates,
        }


def health_score_bump(name: str, delta: float) -> float:
    from services.provider_runtime.registry import health_score

    return health_score(name) + delta


_runtime: "ProviderRuntime | None" = None


def get_provider_runtime(**kwargs) -> ProviderRuntime:
    global _runtime
    if _runtime is None or kwargs:
        _runtime = ProviderRuntime(**kwargs)
    return _runtime
