"""Production-ready vendor adapters and remaining stubs.

Real connectors live in `services.provider_runtime.connectors` and replace
the Phase-2 stubs for supported vendors. Local / platform stubs remain for
Ollama, ComfyUI, Replicate, and Fal until dedicated connectors land.
"""

from __future__ import annotations

from services.provider_runtime import capabilities as cap
from services.provider_runtime.adapters.stub import DemoAdapter, StubAdapter
from services.provider_runtime.connectors import PRODUCTION_CONNECTOR_CLASSES
from services.provider_runtime.factory import ProviderFactory
from services.provider_runtime.models import ProviderProfile

# ------------------------------------------------------------------ Local / platform stubs (not yet production-wired)


class OllamaAdapter(StubAdapter):
    name = "ollama"
    label = "Ollama"
    api_key_env = "OLLAMA_HOST"
    offline = True
    local = True
    capabilities = (cap.LLM, cap.REASONING, cap.SCRIPT, cap.CAPTION, cap.METADATA)
    profile = ProviderProfile(quality=70, cost_per_unit=0.0, speed=60, consistency=75, latency_ms=8000)


class LocalLLMAdapter(StubAdapter):
    name = "local_llm"
    label = "Local LLM"
    api_key_env = "LOCAL_LLM_ENDPOINT"
    offline = True
    local = True
    capabilities = (cap.LLM, cap.REASONING, cap.SCRIPT)
    profile = ProviderProfile(quality=65, cost_per_unit=0.0, speed=55, consistency=70, latency_ms=10000)


class ReplicateAdapter(StubAdapter):
    name = "replicate"
    label = "Replicate"
    api_key_env = "REPLICATE_API_TOKEN"
    capabilities = (
        cap.IMAGE_GENERATION, cap.VIDEO_GENERATION, cap.UPSCALING,
        cap.IMAGE_EDITING, cap.ANIMATION,
    )
    profile = ProviderProfile(quality=80, cost_per_unit=0.08, speed=65, consistency=72, latency_ms=15000)


class FalAIAdapter(StubAdapter):
    name = "fal_ai"
    label = "Fal.ai"
    api_key_env = "FAL_KEY"
    capabilities = (
        cap.IMAGE_GENERATION, cap.VIDEO_GENERATION, cap.ANIMATION,
        cap.UPSCALING, cap.LIP_SYNC,
    )
    profile = ProviderProfile(quality=83, cost_per_unit=0.06, speed=70, consistency=74, latency_ms=12000)


class ComfyUIAdapter(StubAdapter):
    name = "comfyui"
    label = "ComfyUI"
    api_key_env = "COMFYUI_ENDPOINT"
    offline = True
    local = True
    capabilities = (
        cap.IMAGE_GENERATION, cap.VIDEO_GENERATION, cap.UPSCALING,
        cap.IMAGE_EDITING, cap.RENDERING,
    )
    profile = ProviderProfile(quality=78, cost_per_unit=0.0, speed=50, consistency=82, latency_ms=20000)


class RuntimeDemoAdapter(DemoAdapter):
    capabilities = tuple(cap.ALL_CAPABILITIES)


# Production connectors first (override stub names), then remaining stubs + demo.
STUB_ADAPTER_CLASSES = (
    OllamaAdapter,
    LocalLLMAdapter,
    ReplicateAdapter,
    FalAIAdapter,
    ComfyUIAdapter,
    RuntimeDemoAdapter,
)

VENDOR_ADAPTER_CLASSES = PRODUCTION_CONNECTOR_CLASSES + STUB_ADAPTER_CLASSES


def register_vendor_adapters() -> int:
    count = 0
    for adapter_class in VENDOR_ADAPTER_CLASSES:
        ProviderFactory.register_class(adapter_class)
        count += 1
    return count
