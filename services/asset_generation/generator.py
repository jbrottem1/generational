"""The generation core — one structured request in, one asset out.

`generate_asset()` runs the full lifecycle for one request:

    safety gate → cache lookup → provider selection → prompt compilation
    (canonical, then provider-optimized) → generation with retries and
    fallback chain → quality analysis → registry + cache write → usage

Failure policy: NEVER raises into the pipeline. Safety violations return
blocked assets; provider errors walk the fallback chain (which always
ends in the deterministic offline mock); a total failure returns a failed
asset with diagnostics. Every outcome is recorded as a generation job so
the registry's history stays auditable.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone

from core.log import get_logger, log_event
from services.asset_generation.cache import cached_copy, compute_fingerprint, lookup_cached_asset
from services.asset_generation.config import AssetGenerationConfig, get_asset_generation_config
from services.asset_generation.metadata import build_asset_metadata
from services.asset_generation.models import AssetStatus, JobStatus
from services.asset_generation.prompts import compile_prompt, optimize_for_provider
from services.asset_generation.quality import check_safety, validate_asset
from services.asset_generation.registry import AssetRegistry, get_asset_registry
from services.asset_generation.selection import select_providers
from services.asset_generation.usage import get_usage_tracker
from services.provider_runtime import get_provider, get_provider_runtime
from services.provider_runtime import capabilities as cap

logger = get_logger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def generate_asset(
    request: dict,
    item: "dict | None" = None,
    config: "AssetGenerationConfig | None" = None,
    registry: "AssetRegistry | None" = None,
) -> "tuple[dict, dict]":
    """One (asset, job) pair for one GENERATION_REQUEST_FIELDS dict."""
    config = config or get_asset_generation_config()
    registry = registry or get_asset_registry()
    spec = compile_prompt(request, item)
    job = {
        "job_id": f"genjob_{uuid.uuid4().hex[:10]}",
        "asset_id": str(request.get("asset_id", "")),
        "asset_type": str(request.get("asset_type", "")),
        "asset_class": str(request.get("asset_class", "image")),
        "provider": "",
        "providers_tried": [],
        "attempts": 0,
        "status": JobStatus.FAILED,
        "cache_hit": False,
        "cost_estimate": 0.0,
        "latency_ms": 0,
        "error": "",
        "created_at": _now_iso(),
    }

    # Safety gate — blocked requests never reach a provider.
    safety_flags = check_safety(request, spec, config)
    if safety_flags:
        asset = _base_asset(request, spec, status=AssetStatus.BLOCKED)
        asset["quality"] = validate_asset(asset, request, spec, config)
        job["status"] = JobStatus.BLOCKED
        job["error"] = "safety rules triggered: " + ", ".join(safety_flags)
        _finalize(registry, job, asset, config)
        return asset, job

    # Cache — identical requests are never generated twice.
    fingerprint = compute_fingerprint(request, spec)
    if config.cache_enabled:
        cached = lookup_cached_asset(registry, fingerprint)
        if cached:
            asset = cached_copy(cached, request)
            asset.setdefault("metadata", build_asset_metadata(request, spec, cached))
            asset["quality"] = validate_asset(asset, request, spec, config)
            job["status"] = JobStatus.CACHE_HIT
            job["cache_hit"] = True
            job["provider"] = str(asset.get("provider", ""))
            _finalize(registry, job, asset, config, register=False)
            return asset, job

    # Provider selection + generation with retries and fallback chain.
    plan = select_providers(request, config)
    chain = [plan["primary"]] + list(plan["fallbacks"]) if plan["primary"] else []
    last_error = "no provider available for this request"

    for provider_name in chain:
        # Prefer legacy generation registry for asset-gen selection chains,
        # then ProviderRuntime adapters of the same name.
        provider = None
        try:
            from providers.asset_generation import get_generation_provider

            provider = get_generation_provider(provider_name)
        except Exception:  # noqa: BLE001
            provider = None
        if provider is None or not provider.is_available():
            runtime_provider = get_provider(provider_name)
            if runtime_provider is None or not runtime_provider.is_available():
                continue
            provider = runtime_provider
        optimized = optimize_for_provider(spec, provider)
        for _attempt in range(max(1, int(config.max_retries))):
            job["attempts"] += 1
            if provider_name not in job["providers_tried"]:
                job["providers_tried"].append(provider_name)
            started = time.time()
            try:
                result = _generate_via_runtime(provider_name, optimized, request, provider)
            except Exception as exc:  # noqa: BLE001 - adapters must not kill the pipeline
                result = {"error": str(exc)[:200], "provider": provider_name}
            elapsed_ms = int((time.time() - started) * 1000)
            if result and not result.get("error"):
                asset = _base_asset(request, optimized, status=AssetStatus.GENERATED)
                asset.update(
                    {
                        "uri": str(result.get("uri", "") or result.get("image_url", "") or result.get("video_url", "")),
                        "provider": str(result.get("provider", provider_name)),
                        "model": str(result.get("model", "")),
                        "format": str(result.get("format", "")),
                        "width": int(result.get("width", 0) or 0),
                        "height": int(result.get("height", 0) or 0),
                        "duration_sec": float(result.get("duration_sec", 0.0) or 0.0),
                        "placeholder": bool(result.get("placeholder", False)),
                        "fingerprint": fingerprint,
                        "metadata": build_asset_metadata(request, optimized, result),
                    }
                )
                if asset["placeholder"]:
                    if not config.allow_placeholders:
                        last_error = (
                            f"{provider_name} produced a placeholder but "
                            "placeholders are disabled"
                        )
                        continue
                    asset["status"] = AssetStatus.PLACEHOLDER
                duplicate_of = _duplicate_of(registry, fingerprint, asset["asset_id"])
                asset["quality"] = validate_asset(asset, request, optimized, config, duplicate_of)
                job["status"] = JobStatus.SUCCEEDED
                job["provider"] = asset["provider"]
                job["cost_estimate"] = float(provider.estimate_cost(request))
                job["latency_ms"] = elapsed_ms
                _finalize(registry, job, asset, config)
                return asset, job
            last_error = (
                str(result.get("error", "unknown provider error"))
                if result else "empty provider response"
            )

    # Every provider failed.
    asset = _base_asset(request, spec, status=AssetStatus.FAILED)
    asset["fingerprint"] = fingerprint
    asset["error"] = last_error
    asset["quality"] = validate_asset(asset, request, spec, config)
    asset.pop("error", None)
    job["error"] = last_error
    _finalize(registry, job, asset, config, register=False)
    log_event(
        logger, "asset_generation.request_failed", level=30,
        asset_id=asset["asset_id"], error=last_error[:120],
    )
    return asset, job


def _generate_via_runtime(provider_name: str, optimized: dict, request: dict, provider) -> dict:
    """Route asset generation through ProviderRuntime when the named adapter is live.

    Legacy GenerationProvider adapters (mock / test doubles) keep calling
    ``provider.generate()`` directly so selection/fallback chains stay intact.
    """
    runtime_adapter = get_provider(provider_name)
    use_runtime = (
        runtime_adapter is not None
        and runtime_adapter is provider
        and runtime_adapter.is_available()
        and hasattr(runtime_adapter, "execute")
        and not hasattr(provider, "generate")
    )
    if not use_runtime and hasattr(provider, "execute") and not hasattr(provider, "generate"):
        use_runtime = True

    if hasattr(provider, "generate") and not use_runtime:
        return provider.generate(optimized, request)

    asset_class = str(request.get("asset_class", "image") or "image")
    op_map = {
        "image": "generate_image",
        "video": "generate_video",
        "animation": "generate_animation",
        "audio": "generate_voice",
        "thumbnail": "generate_thumbnail",
        "music": "generate_music",
        "sfx": "generate_sound_effects",
    }
    operation = op_map.get(asset_class, "generate_image")
    runtime = get_provider_runtime()
    payload = {
        "prompt": optimized.get("prompt") or request.get("prompt") or "",
        "prompt_spec": optimized,
        "request": request,
        "width": request.get("width") or optimized.get("width") or 1080,
        "height": request.get("height") or optimized.get("height") or 1920,
        "duration_sec": request.get("duration_sec") or 0,
        "negative_prompt": optimized.get("negative_prompt") or "",
    }
    method = getattr(runtime, operation, None)
    if callable(method):
        response = method(payload, preferred_provider=provider_name, allow_fallback=False)
        if response.success and response.provider == provider_name:
            data = dict(response.data or {})
            data.setdefault("provider", response.provider or provider_name)
            data.setdefault("placeholder", bool(response.demo_mode))
            data.setdefault(
                "uri",
                data.get("image_url") or data.get("video_url") or data.get("uri") or data.get("path") or "",
            )
            return data
        if hasattr(provider, "generate"):
            return provider.generate(optimized, request)
        return {"error": response.error or "runtime generation failed", "provider": provider_name}

    if hasattr(provider, "generate"):
        return provider.generate(optimized, request)
    return {"error": f"no generate path for {provider_name}", "provider": provider_name}


def _finalize(
    registry: AssetRegistry,
    job: dict,
    asset: dict,
    config: AssetGenerationConfig,
    register: bool = True,
) -> None:
    """Persist job (+ optional asset) and optionally record usage."""
    if register and asset.get("uri"):
        registry.register_asset(asset)
    registry.record_job(job)
    if getattr(config, "usage_tracking_enabled", True):
        try:
            get_usage_tracker().record(job, project_id=str(asset.get("project_id", "")))
        except Exception as exc:  # noqa: BLE001 - usage must never break generation
            log_event(logger, "asset_generation.usage_failed", level=30, error=str(exc)[:120])


def _base_asset(request: dict, spec: dict, status: str) -> dict:
    return {
        "asset_id": str(request.get("asset_id", "")) or f"asset_{uuid.uuid4().hex[:10]}",
        "asset_type": str(request.get("asset_type", "")),
        "asset_class": str(request.get("asset_class", "image")),
        "scene_id": str(request.get("scene_id", "")),
        "project_id": str(request.get("project_id", "")),
        "uri": "",
        "provider": "",
        "model": "",
        "format": "",
        "width": 0,
        "height": 0,
        "duration_sec": 0.0,
        "prompt_spec": dict(spec),
        "fingerprint": "",
        "version": 1,
        "status": status,
        "placeholder": False,
        "cached": False,
        "quality": {},
        "reusable": bool(request.get("reusable", False)),
        "priority": str(request.get("priority", "recommended")),
        "category": str(request.get("category", "")),
        "metadata": build_asset_metadata(request, spec),
        "created_at": _now_iso(),
    }


def _duplicate_of(registry: AssetRegistry, fingerprint: str, asset_id: str) -> str:
    """The asset_id an identical fingerprint is already registered under."""
    existing = registry.find_by_fingerprint(fingerprint)
    if existing and existing.get("asset_id") != asset_id:
        return str(existing.get("asset_id", ""))
    return ""
