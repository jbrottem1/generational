"""Production-ready adapter stubs for all supported AI providers.

Each adapter declares capabilities and selection profile. Real API calls
are implemented in Phase 2 — adapters report unavailable without keys and
return structured errors when keys are set but calls are not wired yet.
Future providers register via ProviderFactory without architecture changes.
"""

from __future__ import annotations

from services.provider_runtime import capabilities as cap
from services.provider_runtime.adapters.stub import DemoAdapter, StubAdapter
from services.provider_runtime.factory import ProviderFactory
from services.provider_runtime.models import ProviderProfile

# ------------------------------------------------------------------ LLMs


class OpenAIAdapter(StubAdapter):
    name = "openai"
    label = "OpenAI"
    api_key_env = "OPENAI_API_KEY"
    capabilities = (
        cap.LLM, cap.REASONING, cap.SCRIPT, cap.CAPTION, cap.SUBTITLE,
        cap.METADATA, cap.IMAGE_GENERATION,
    )
    profile = ProviderProfile(quality=92, cost_per_unit=0.02, speed=80, consistency=85, latency_ms=3000)


class AnthropicAdapter(StubAdapter):
    name = "anthropic"
    label = "Anthropic"
    api_key_env = "ANTHROPIC_API_KEY"
    capabilities = (cap.LLM, cap.REASONING, cap.SCRIPT, cap.CAPTION, cap.SUBTITLE, cap.METADATA)
    profile = ProviderProfile(quality=91, cost_per_unit=0.025, speed=75, consistency=84, latency_ms=3500)


class GoogleGeminiAdapter(StubAdapter):
    name = "google_gemini"
    label = "Google Gemini"
    api_key_env = "GOOGLE_API_KEY"
    capabilities = (
        cap.LLM, cap.REASONING, cap.SCRIPT, cap.CAPTION, cap.SUBTITLE,
        cap.METADATA, cap.IMAGE_GENERATION,
    )
    profile = ProviderProfile(quality=88, cost_per_unit=0.015, speed=78, consistency=80, latency_ms=4000)


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


# ------------------------------------------------------------------ Image


class FluxAdapter(StubAdapter):
    name = "flux"
    label = "Flux (Black Forest Labs)"
    api_key_env = "BFL_API_KEY"
    capabilities = (cap.IMAGE_GENERATION, cap.THUMBNAIL, cap.IMAGE_EDITING)
    profile = ProviderProfile(quality=89, cost_per_unit=0.05, speed=80, consistency=78, latency_ms=5000)


class IdeogramAdapter(StubAdapter):
    name = "ideogram"
    label = "Ideogram"
    api_key_env = "IDEOGRAM_API_KEY"
    capabilities = (cap.IMAGE_GENERATION, cap.THUMBNAIL)
    profile = ProviderProfile(quality=87, cost_per_unit=0.04, speed=75, consistency=76, latency_ms=6000)


class StabilityAIAdapter(StubAdapter):
    name = "stability_ai"
    label = "Stability AI"
    api_key_env = "STABILITY_API_KEY"
    capabilities = (cap.IMAGE_GENERATION, cap.UPSCALING, cap.IMAGE_EDITING, cap.THUMBNAIL)
    profile = ProviderProfile(quality=82, cost_per_unit=0.03, speed=85, consistency=80, latency_ms=4000)


# ------------------------------------------------------------------ Video


class GoogleVeoAdapter(StubAdapter):
    name = "google_veo"
    label = "Google Veo"
    api_key_env = "GOOGLE_API_KEY"
    capabilities = (cap.VIDEO_GENERATION, cap.ANIMATION, cap.MOTION)
    profile = ProviderProfile(quality=92, cost_per_unit=1.50, speed=35, consistency=70, latency_ms=45000)


class RunwayAdapter(StubAdapter):
    name = "runway"
    label = "Runway"
    api_key_env = "RUNWAY_API_KEY"
    capabilities = (cap.VIDEO_GENERATION, cap.ANIMATION, cap.MOTION, cap.LIP_SYNC)
    profile = ProviderProfile(quality=88, cost_per_unit=1.00, speed=45, consistency=68, latency_ms=35000)


class PikaAdapter(StubAdapter):
    name = "pika"
    label = "Pika"
    api_key_env = "PIKA_API_KEY"
    capabilities = (cap.VIDEO_GENERATION, cap.ANIMATION)
    profile = ProviderProfile(quality=80, cost_per_unit=0.45, speed=60, consistency=60, latency_ms=20000)


class KlingAdapter(StubAdapter):
    name = "kling"
    label = "Kling"
    api_key_env = "KLING_API_KEY"
    capabilities = (cap.VIDEO_GENERATION, cap.ANIMATION, cap.CHARACTER_CONSISTENCY)
    profile = ProviderProfile(quality=85, cost_per_unit=0.70, speed=40, consistency=66, latency_ms=40000)


class LumaAdapter(StubAdapter):
    name = "luma"
    label = "Luma Dream Machine"
    api_key_env = "LUMA_API_KEY"
    capabilities = (cap.VIDEO_GENERATION, cap.ANIMATION, cap.THREE_D_GENERATION)
    profile = ProviderProfile(quality=84, cost_per_unit=0.60, speed=50, consistency=64, latency_ms=30000)


# ------------------------------------------------------------------ Audio


class ElevenLabsAdapter(StubAdapter):
    name = "elevenlabs"
    label = "ElevenLabs"
    api_key_env = "ELEVENLABS_API_KEY"
    capabilities = (cap.SPEECH, cap.VOICE_CLONING, cap.SOUND_EFFECTS, cap.MUSIC)
    profile = ProviderProfile(quality=90, cost_per_unit=0.12, speed=70, consistency=85, latency_ms=6000)


# ------------------------------------------------------------------ Platforms


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


# ------------------------------------------------------------------ Demo


class RuntimeDemoAdapter(DemoAdapter):
    capabilities = tuple(cap.ALL_CAPABILITIES)


# All vendor adapter classes — auto-registered at bootstrap.
VENDOR_ADAPTER_CLASSES = (
    OpenAIAdapter,
    AnthropicAdapter,
    GoogleGeminiAdapter,
    OllamaAdapter,
    LocalLLMAdapter,
    FluxAdapter,
    IdeogramAdapter,
    StabilityAIAdapter,
    GoogleVeoAdapter,
    RunwayAdapter,
    PikaAdapter,
    KlingAdapter,
    LumaAdapter,
    ElevenLabsAdapter,
    ReplicateAdapter,
    FalAIAdapter,
    ComfyUIAdapter,
    RuntimeDemoAdapter,
)


def register_vendor_adapters() -> int:
    count = 0
    for adapter_class in VENDOR_ADAPTER_CLASSES:
        ProviderFactory.register_class(adapter_class)
        count += 1
    return count
