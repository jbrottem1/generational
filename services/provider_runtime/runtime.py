"""ProviderRuntime — unified execution surface for all AI operations."""

from __future__ import annotations

from services.provider_runtime import capabilities as cap
from services.provider_runtime.adapter import ProviderAdapter
from services.provider_runtime.config import load_dotenv_if_available, load_runtime_config
from services.provider_runtime.cost import ProviderCostEstimator
from services.provider_runtime.execution import RateLimiter, execute_with_retry
from services.provider_runtime.fallback import ProviderFallbackManager
from services.provider_runtime.health import ProviderHealthMonitor
from services.provider_runtime.models import ProviderRequest, ProviderResponse
from services.provider_runtime.parallel import ParallelExecutor
from services.provider_runtime.registry import ensure_registered, provider_catalog
from services.provider_runtime.selection import ProviderSelectionEngine


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
        self._selector = ProviderSelectionEngine()
        self._fallback = ProviderFallbackManager(self._selector)
        self._health = ProviderHealthMonitor(
            failure_threshold=int(self._config.get("failure_threshold", 5)),
            recovery_timeout_sec=float(self._config.get("recovery_timeout_sec", 60)),
        )
        self._cost = ProviderCostEstimator()
        self._parallel = ParallelExecutor(self._selector)
        self._rate_limiter = RateLimiter(default_rpm=int(self._config.get("rate_limit_rpm", 60)))
        ensure_registered()
        self._apply_credential_overrides()

    def _apply_credential_overrides(self) -> None:
        from services.provider_runtime.registry import all_providers

        for provider in all_providers():
            if hasattr(provider, "set_credential_overrides"):
                provider.set_credential_overrides(self._credential_overrides)

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

    def execute(self, request: ProviderRequest) -> ProviderResponse:
        """Low-level entry for custom operations."""
        capability = request.capability or cap.OPERATION_CAPABILITIES.get(request.operation, (cap.LLM,))[0]
        return self._execute(request.operation, capability, request.payload, **self._request_kwargs(request))

    def catalog(self) -> list[dict]:
        return provider_catalog()

    def health_report(self) -> dict:
        return self._health.health_report()

    def usage_summary(self) -> dict:
        return self._cost.usage_summary()

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

        self._cost.log_usage(response)
        return response

    def _invoke_with_retry(
        self,
        provider: ProviderAdapter,
        request: ProviderRequest,
    ) -> ProviderResponse:
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
        else:
            self._health.record_failure(provider.name, response.error)
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


_runtime: "ProviderRuntime | None" = None


def get_provider_runtime(**kwargs) -> ProviderRuntime:
    global _runtime
    if _runtime is None or kwargs:
        _runtime = ProviderRuntime(**kwargs)
    return _runtime
