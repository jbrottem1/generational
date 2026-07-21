"""Category 7 — Recovery tests (simulated failures)."""

from __future__ import annotations

import time
from typing import Any

from services.production_acceptance.models import TestResult


def run_recovery_tests(mode: str = "smoke") -> list[TestResult]:
    results: list[TestResult] = []
    # Always-fast simulated recoveries
    results.append(_case("api_timeout", _api_timeout))
    results.append(_case("disk_full", _disk_full))
    results.append(_case("corrupted_asset", _corrupted_asset))
    results.append(_case("renderer_failure", _renderer_failure))
    if mode == "smoke":
        # One live pipeline recovery probe in smoke
        results.append(_case("missing_images", _missing_images))
        results.append(_case("network_interruption", _network_interruption))
    else:
        results.append(_case("missing_images", _missing_images))
        results.append(_case("missing_audio", _missing_audio))
        results.append(_case("network_interruption", _network_interruption))
        results.append(_case("llm_failure", _llm_failure))
    return results


def _case(name: str, fn) -> TestResult:
    t0 = time.time()
    try:
        ok, message, metrics = fn()
        return TestResult(
            category="recovery",
            name=name,
            passed=ok,
            duration_ms=int((time.time() - t0) * 1000),
            message=message,
            metrics=metrics,
        )
    except Exception as exc:  # noqa: BLE001
        return TestResult(
            category="recovery",
            name=name,
            passed=False,
            duration_ms=int((time.time() - t0) * 1000),
            errors=[str(exc)],
            message=str(exc),
        )


def _missing_images() -> tuple[bool, str, dict]:
    from services.production_operations import run_studio_ops

    # Inject empty visual assets; ops must still complete
    ctx = {
        "force_no_images": True,
        "candidates": [{"title": "Missing images recovery", "script": "Test.", "visual_package": {"scenes": []}}],
    }
    out = run_studio_ops(topic="Recovery missing images topic", length_sec=20, context=ctx)
    return bool(out.get("succeeded")), "continued_without_images", {"production_id": out.get("production_id")}


def _missing_audio() -> tuple[bool, str, dict]:
    from services.production_operations import run_studio_ops

    ctx = {"candidates": [{"title": "No audio", "script": "Silent test.", "audio_package": {}}]}
    out = run_studio_ops(topic="Recovery missing audio topic", length_sec=20, context=ctx)
    return bool(out.get("succeeded")), "continued_without_audio", {"production_id": out.get("production_id")}


def _network_interruption() -> tuple[bool, str, dict]:
    # Simulate by marking research settings offline; engines have fallbacks
    from services.production_operations import run_studio_ops

    ctx = {"research_settings": {"offline": True, "force_fallback": True}}
    out = run_studio_ops(topic="Recovery network interruption topic", length_sec=20, context=ctx)
    return bool(out.get("succeeded")), "offline_fallback", {"production_id": out.get("production_id")}


def _api_timeout() -> tuple[bool, str, dict]:
    from services.production_operations.resilience import run_engine_with_retries

    class _TimeoutEngine:
        key = "fake_timeout"
        version = "0.0.0"
        label = "Fake Timeout"
        description = "acceptance probe"
        def is_ready(self):
            return True
        def run(self, context):
            raise TimeoutError("simulated API timeout")

    import engines  # noqa: F401
    from engines import registry

    # Temporarily register then remove
    eng = _TimeoutEngine()
    try:
        registry.register(eng)
        result = run_engine_with_retries("fake_timeout", {}, max_retries=1)
    finally:
        # registry may not support unregister — leave benign stub
        pass
    ok = result.get("status") == "failed_continued" and result.get("fallback") is True
    return ok, "timeout_retried_and_continued", result


def _llm_failure() -> tuple[bool, str, dict]:
    from services.production_operations import run_studio_ops

    ctx = {"model": "force_demo_fallback", "provider_force_demo": True}
    out = run_studio_ops(topic="Recovery LLM failure topic", length_sec=20, context=ctx)
    return bool(out.get("succeeded")), "demo_fallback", {"production_id": out.get("production_id")}


def _disk_full() -> tuple[bool, str, dict]:
    # Simulate write failure by pointing export to an invalid nested path, then confirming ops still returns
    from services.production_operations.services_steps import export_and_validate

    ctx: dict[str, Any] = {"candidates": [{"title": "Disk", "script": "x"}], "export_mp4": "/no/such/volume/file.mp4"}
    result = export_and_validate(ctx, production_id="acc_disk_full", topic="Disk full sim")
    ok = result.get("success") is True  # never terminate
    return ok, "export_degraded_continued", {"status": result.get("status"), "warnings": result.get("warnings")}


def _corrupted_asset() -> tuple[bool, str, dict]:
    from pathlib import Path
    from tempfile import TemporaryDirectory
    from services.media_production.verified_export import assess_export_technical_validity

    with TemporaryDirectory() as td:
        bad = Path(td) / "corrupt.mp4"
        bad.write_bytes(b"not-an-mp4")
        tech = assess_export_technical_validity(bad)
        # Detection of corrupt is success for the acceptance system
        ok = tech.get("ok") is False and bool(tech.get("hard_fails"))
        return ok, f"detected={tech.get('hard_fails')}", tech


def _renderer_failure() -> tuple[bool, str, dict]:
    from services.production_operations.resilience import run_engine_with_retries

    class _Boom:
        key = "fake_renderer"
        version = "0.0.0"
        label = "Fake Renderer"
        description = "acceptance probe"
        def is_ready(self):
            return True
        def run(self, context):
            raise RuntimeError("renderer crashed")

    from engines import registry

    registry.register(_Boom())
    result = run_engine_with_retries("fake_renderer", {}, max_retries=2)
    ok = result.get("fallback") is True and int(result.get("retries") or 0) >= 1
    return ok, "renderer_retries_exhausted_continued", result
