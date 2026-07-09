"""Provider Integration & Runtime Engine tests (Agent 19)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from services.provider_runtime import (
    ProviderAdapter,
    ProviderRequest,
    ProviderResponse,
    ProviderRuntime,
    RuntimeExecutionEngine,
    all_providers,
    ensure_registered,
    get_provider,
    get_provider_runtime,
    provider_catalog,
    register_provider,
    unregister_provider,
)
from services.provider_runtime.adapter import ProviderAdapter as BaseAdapter
from services.provider_runtime.capabilities import IMAGE_GENERATION, LLM, SCRIPT
from services.provider_runtime.config import get_credential, has_credential, load_runtime_config
from services.provider_runtime.cost import ProviderCostEstimator
from services.provider_runtime.execution import RateLimiter, execute_with_retry
from services.provider_runtime.fallback import ProviderFallbackManager
from services.provider_runtime.health import ProviderHealthMonitor
from services.provider_runtime.models import ProviderProfile
from services.provider_runtime.registry import reset_registry
from services.provider_runtime.selection import ProviderSelectionEngine


class _MockSuccessAdapter(BaseAdapter):
    name = "mock_success"
    label = "Mock Success"
    capabilities = (LLM, SCRIPT, IMAGE_GENERATION)

    def is_available(self) -> bool:
        return True

    def execute(self, request: ProviderRequest) -> ProviderResponse:
        return ProviderResponse(
            success=True,
            operation=request.operation,
            provider=self.name,
            data={"result": "ok", **request.payload},
        )


class _MockFailAdapter(BaseAdapter):
    name = "mock_fail"
    label = "Mock Fail"
    capabilities = (IMAGE_GENERATION,)

    def is_available(self) -> bool:
        return True

    def execute(self, request: ProviderRequest) -> ProviderResponse:
        return ProviderResponse(
            success=False,
            operation=request.operation,
            provider=self.name,
            error="simulated failure",
        )


@pytest.fixture(autouse=True)
def _isolate_registry():
    """Tests that mutate registry get a clean slate."""
    reset_registry()
    yield
    reset_registry()


# ---------------------------------------------------- registration


def test_ensure_registered_loads_vendor_adapters():
    ensure_registered()
    names = {p.name for p in all_providers()}
    assert "openai" in names
    assert "anthropic" in names
    assert "runway" in names
    assert "elevenlabs" in names
    assert "demo" in names


def test_provider_catalog_returns_descriptions():
    ensure_registered()
    catalog = provider_catalog()
    assert len(catalog) >= 18
    assert all("name" in entry and "capabilities" in entry for entry in catalog)


def test_register_and_unregister_provider():
    ensure_registered()
    adapter = _MockSuccessAdapter()
    register_provider(adapter)
    assert get_provider("mock_success") is adapter
    unregister_provider("mock_success")
    assert get_provider("mock_success") is None


# ---------------------------------------------------- capability selection


def test_selection_engine_picks_highest_quality():
    high = _MockSuccessAdapter()
    high.profile = ProviderProfile(quality=99)
    register_provider(high)
    low = _MockSuccessAdapter()
    low.name = "mock_low"
    low.profile = ProviderProfile(quality=10)
    register_provider(low)

    selector = ProviderSelectionEngine()
    chosen = selector.select(ProviderRequest(operation="generate_image", capability=IMAGE_GENERATION))
    assert chosen.name == "mock_success"


def test_selection_respects_preferred_provider():
    register_provider(_MockSuccessAdapter())
    selector = ProviderSelectionEngine()
    req = ProviderRequest(
        operation="generate_image",
        capability=IMAGE_GENERATION,
        preferred_provider="mock_success",
    )
    assert selector.select(req).name == "mock_success"


# ---------------------------------------------------- fallback


def test_fallback_tries_alternate_provider():
    fail = _MockFailAdapter()
    fail.profile = ProviderProfile(quality=99)
    register_provider(fail)
    register_provider(_MockSuccessAdapter())
    manager = ProviderFallbackManager()
    req = ProviderRequest(operation="generate_image", capability=IMAGE_GENERATION, allow_fallback=True)

    def executor(provider, request):
        return provider.execute(request)

    response = manager.execute_with_fallback(req, executor, IMAGE_GENERATION)
    assert response.success is True
    assert "mock_fail" in response.fallbacks_used


# ---------------------------------------------------- retry & rate limit


def test_execute_with_retry_recovers_on_second_attempt():
    register_provider(_MockSuccessAdapter())
    attempts = {"count": 0}

    class FlakyAdapter(BaseAdapter):
        name = "flaky"
        capabilities = (IMAGE_GENERATION,)

        def is_available(self):
            return True

        def execute(self, request):
            attempts["count"] += 1
            if attempts["count"] < 2:
                return ProviderResponse(success=False, operation=request.operation, provider=self.name, error="retry")
            return ProviderResponse(success=True, operation=request.operation, provider=self.name, data={})

    adapter = FlakyAdapter()
    req = ProviderRequest(operation="generate_image", max_retries=2)
    response = execute_with_retry(adapter, req, lambda p, r: p.execute(r))
    assert response.success is True
    assert response.attempts == 2


def test_rate_limiter_blocks_excess_calls():
    limiter = RateLimiter(default_rpm=2)
    assert limiter.allow("test") is True
    assert limiter.allow("test") is True
    assert limiter.allow("test") is False


# ---------------------------------------------------- health & cost


def test_circuit_breaker_opens_after_failures():
    monitor = ProviderHealthMonitor(failure_threshold=2, recovery_timeout_sec=60)
    adapter = _MockSuccessAdapter()
    monitor.record_failure(adapter.name, "err1")
    assert monitor.is_healthy(adapter) is True
    monitor.record_failure(adapter.name, "err2")
    assert monitor.is_healthy(adapter) is False


def test_cost_estimator_logs_usage():
    estimator = ProviderCostEstimator()
    response = ProviderResponse(success=True, provider="test", operation="generate_image", cost_usd=0.05)
    estimator.log_usage(response)
    assert estimator.total_cost() == pytest.approx(0.05)
    assert "test" in estimator.usage_summary()


# ---------------------------------------------------- runtime execution


def test_runtime_generate_image_uses_demo_without_keys(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("BFL_API_KEY", raising=False)
    runtime = ProviderRuntime()
    response = runtime.generate_image({"prompt": "test sunset"})
    assert response.operation == "generate_image"
    # Demo or mock bridge should succeed
    assert response.success is True or response.demo_mode is True


def test_runtime_all_operations_exist():
    runtime = ProviderRuntime()
    for method in (
        "generate_script", "generate_image", "generate_video", "generate_animation",
        "generate_voice", "generate_music", "generate_sound_effects", "generate_thumbnail",
        "generate_caption", "generate_subtitles", "generate_metadata",
    ):
        assert hasattr(runtime, method)
        assert callable(getattr(runtime, method))


def test_runtime_health_and_usage_reports():
    runtime = ProviderRuntime()
    runtime.generate_metadata({"title": "test"})
    assert isinstance(runtime.health_report(), dict)
    assert isinstance(runtime.usage_summary(), dict)


# ---------------------------------------------------- config


def test_credential_loading_from_env(monkeypatch):
    monkeypatch.setenv("TEST_PROVIDER_KEY", "secret-value")
    assert has_credential("TEST_PROVIDER_KEY") is True
    assert get_credential("TEST_PROVIDER_KEY") == "secret-value"


def test_load_runtime_config_empty_when_missing(tmp_path):
    assert load_runtime_config(tmp_path / "nonexistent.json") == {}


# ---------------------------------------------------- long-form


def test_longform_checkpoint_save_and_resume(tmp_path):
    engine = RuntimeExecutionEngine(checkpoint_dir=tmp_path)
    checkpoint = engine.start_production("Create a documentary about space", production_type="documentary")
    assert checkpoint.job_id
    loaded = engine.resume_production(checkpoint.job_id)
    assert loaded is not None
    assert loaded.command == checkpoint.command


def test_longform_list_checkpoints(tmp_path):
    engine = RuntimeExecutionEngine(checkpoint_dir=tmp_path)
    engine.start_production("Test production")
    assert len(engine.list_checkpoints()) == 1


def test_longform_run_produces_checkpoint(tmp_path, monkeypatch):
    monkeypatch.setenv("GENERATIONAL_TEST_MODE", "1")
    engine = RuntimeExecutionEngine(checkpoint_dir=tmp_path)
    result = engine.run("Create 1 psychology short", options={"count": 1})
    assert "job_id" in result
    assert result["checkpoint"]["completed_stages"]


# ---------------------------------------------------- mock provider execution


def test_mock_provider_execution():
    register_provider(_MockSuccessAdapter())
    runtime = ProviderRuntime()
    response = runtime.generate_script(
        {"prompt": "Write about focus"},
        preferred_provider="mock_success",
    )
    assert response.success is True
    assert response.data.get("result") == "ok"


def test_get_provider_runtime_singleton():
    import services.provider_runtime.runtime as runtime_mod

    runtime_mod._runtime = None
    ensure_registered()
    r1 = get_provider_runtime()
    r2 = get_provider_runtime()
    assert r1 is r2
