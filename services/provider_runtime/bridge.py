"""Bridge legacy provider interfaces into the unified ProviderRegistry."""

from __future__ import annotations

from services.provider_runtime.adapter import ProviderAdapter
from services.provider_runtime import capabilities as cap
from services.provider_runtime.models import ProviderProfile, ProviderRequest, ProviderResponse
from services.provider_runtime.registry import register_provider


class _LegacyGenerationBridge(ProviderAdapter):
    """Wraps providers.asset_generation GenerationProvider adapters."""

    def __init__(self, legacy) -> None:
        self._legacy = legacy
        self.name = legacy.name
        self.label = getattr(legacy, "label", legacy.name)
        self.capabilities = self._map_capabilities(legacy)
        prof = getattr(legacy, "profile", {}) or {}
        self.profile = ProviderProfile(
            quality=float(prof.get("quality", 50)),
            cost_per_unit=float(prof.get("cost_per_asset", 0)),
            speed=float(prof.get("speed", 50)),
            consistency=float(prof.get("consistency", 50)),
            latency_ms=int(prof.get("latency_ms", 0)),
        )
        self.api_key_env = getattr(legacy, "api_key_env", "")
        self.offline = getattr(legacy, "offline", False)
        self.local = getattr(legacy, "local", False)

    def is_available(self) -> bool:
        return self._legacy.is_available()

    def execute(self, request: ProviderRequest) -> ProviderResponse:
        prompt_spec = request.payload.get("prompt_spec", {})
        gen_request = request.payload.get("request", request.payload)
        result = self._legacy.generate(prompt_spec, gen_request)
        if result.get("error"):
            return ProviderResponse(
                success=False,
                operation=request.operation,
                provider=self.name,
                error=str(result["error"]),
                data=result,
            )
        return ProviderResponse(
            success=True,
            operation=request.operation,
            provider=self.name,
            data=result,
            demo_mode=bool(result.get("placeholder")),
            cost_usd=self.estimate_cost(request),
        )

    @staticmethod
    def _map_capabilities(legacy) -> tuple:
        caps = set()
        for asset_class in getattr(legacy, "asset_classes", ()):
            if asset_class == "image":
                caps.add(cap.IMAGE_GENERATION)
                caps.add(cap.THUMBNAIL)
            elif asset_class == "video":
                caps.add(cap.VIDEO_GENERATION)
            elif asset_class == "animation":
                caps.add(cap.ANIMATION)
            elif asset_class == "audio":
                caps.update((cap.SPEECH, cap.MUSIC, cap.SOUND_EFFECTS))
            elif asset_class == "three_d":
                caps.add(cap.THREE_D_GENERATION)
            elif asset_class == "motion_graphics":
                caps.add(cap.MOTION)
        for tag in getattr(legacy, "capabilities", ()):
            tag_map = {
                "image-gen": cap.IMAGE_GENERATION,
                "video-gen": cap.VIDEO_GENERATION,
                "animation": cap.ANIMATION,
                "voice": cap.SPEECH,
                "music": cap.MUSIC,
                "sfx": cap.SOUND_EFFECTS,
            }
            if tag in tag_map:
                caps.add(tag_map[tag])
        return tuple(caps) if caps else (cap.IMAGE_GENERATION,)


class _LegacyLLMBridge(ProviderAdapter):
    """Wraps core.ai AIProvider for script/metadata operations."""

    name = "core_ai"
    label = "Core AI Provider"
    capabilities = (cap.LLM, cap.SCRIPT, cap.REASONING, cap.CAPTION, cap.METADATA)

    def __init__(self) -> None:
        from core.ai import get_provider
        self._provider = get_provider()
        self.name = f"core_{self._provider.name}"
        self.profile = ProviderProfile(quality=85, cost_per_unit=0.02, speed=75)

    def is_available(self) -> bool:
        return self._provider.is_available()

    def execute(self, request: ProviderRequest) -> ProviderResponse:
        op = request.operation
        if op in ("generate_script", "generate_caption", "generate_metadata"):
            system = request.payload.get("system_prompt", "")
            user = request.payload.get("user_prompt", request.payload.get("prompt", ""))
            model = request.payload.get("model", "gpt-4o-mini")
            data, tokens = self._provider.generate_json(system, user, model)
            if data is None:
                return ProviderResponse(
                    success=False,
                    operation=op,
                    provider=self.name,
                    error="LLM call failed or unavailable",
                    demo_mode=getattr(self._provider, "name", "") == "demo",
                )
            return ProviderResponse(
                success=True,
                operation=op,
                provider=self.name,
                data=data if isinstance(data, dict) else {"result": data},
                tokens_used=tokens,
                demo_mode=getattr(self._provider, "name", "") == "demo",
            )
        if op == "generate_image":
            return ProviderResponse(
                success=False,
                operation=op,
                provider=self.name,
                error="Use image-capable provider for generate_image",
            )
        return ProviderResponse(
            success=False,
            operation=op,
            provider=self.name,
            error=f"Unsupported operation {op!r} for core AI bridge",
        )


def register_legacy_providers() -> int:
    """Bridge existing provider registries into the unified runtime."""
    from services.provider_runtime.registry import all_providers, get_provider

    existing = {p.name for p in all_providers()}
    count = 0
    try:
        from providers.asset_generation import all_generation_providers

        for legacy in all_generation_providers():
            if legacy.name in ("mock_generation",) or legacy.name in existing:
                continue
            register_provider(_LegacyGenerationBridge(legacy))
            existing.add(legacy.name)
            count += 1
    except ImportError:
        pass

    if not get_provider("core_demo") and not any(p.name.startswith("core_") for p in all_providers()):
        register_provider(_LegacyLLMBridge())
        count += 1
    return count
