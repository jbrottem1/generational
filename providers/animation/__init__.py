"""Animation provider registry — swappable cinematic backends.

Real video / animation backends implement `AnimationProvider` and register
here; the Animation Engine resolves providers by id / capability and never
talks to a vendor SDK directly. Until real backends land, every capability
resolves to the deterministic `MockAnimationProvider`.
"""

from __future__ import annotations

from providers.animation.adapters import ALL_ADAPTERS
from providers.animation.mock import MockAnimationProvider
from providers.animation_provider import (
    ANIMATION_CAPABILITIES,
    ANIMATION_PROVIDER_IDS,
    AnimationProvider,
)

_mock = MockAnimationProvider()

# provider_id → provider instance. Real backends replace the mock via
# register_animation_provider() — nothing in the engine changes.
_providers: "dict[str, AnimationProvider]" = {
    "mock_animation": _mock,
}

# Register adapter stubs (unavailable until API keys are set).
for _adapter_cls in ALL_ADAPTERS:
    _adapter = _adapter_cls()
    _providers[_adapter.provider_id] = _adapter


def register_animation_provider(provider_id: str, provider: AnimationProvider) -> None:
    _providers[provider_id] = provider


def get_animation_provider(provider_id: str = "mock_animation") -> AnimationProvider:
    provider = _providers.get(provider_id)
    if provider is not None and provider.is_available():
        return provider
    return _mock


def available_providers() -> "list[AnimationProvider]":
    found = [p for p in _providers.values() if p.is_available()]
    return found or [_mock]


def provider_for_capability(capability: str, priority: "list[str] | None" = None) -> AnimationProvider:
    order = list(priority or ANIMATION_PROVIDER_IDS)
    for provider_id in order:
        provider = _providers.get(provider_id)
        if provider and provider.is_available() and provider.supports(capability):
            return provider
    # Fall back to any available provider that supports the capability.
    for provider in available_providers():
        if provider.supports(capability):
            return provider
    return _mock


def provider_plan(config) -> dict:
    """capability → provider id, for the package's routing plan."""
    priority = list(getattr(config, "provider_priority", None) or ANIMATION_PROVIDER_IDS)
    return {
        capability: provider_for_capability(capability, priority).provider_id
        for capability in ANIMATION_CAPABILITIES
    }


def build_provider_instructions(
    camera_plan: dict,
    character_motion: list,
    lip_sync_plan: list,
    visual_effects: list,
    config,
) -> "list[dict]":
    """Emit provider-agnostic briefs the adapters can later execute."""
    priority = list(getattr(config, "provider_priority", None) or ANIMATION_PROVIDER_IDS)
    instructions: "list[dict]" = []

    camera_provider = provider_for_capability("camera", priority)
    for shot in camera_plan.get("shots", []):
        brief = {
            "id": shot.get("shot_id"),
            "capability": "camera",
            "brief": {
                "shot_type": shot.get("shot_type"),
                "movement": shot.get("movement"),
                "keyframes": shot.get("keyframes"),
                "duration_sec": shot.get("duration_sec"),
                "motion_curve": shot.get("motion_curve"),
            },
            "refs": [shot.get("shot_id"), shot.get("scene_id")],
            "priority": "required",
        }
        planned = camera_provider.plan(brief) or {}
        instructions.append({
            "provider_id": camera_provider.provider_id,
            "capability": "camera",
            "brief": brief["brief"],
            "refs": brief["refs"],
            "priority": "required",
            "adapter_result": planned,
        })

    motion_provider = provider_for_capability("character", priority)
    for motion in character_motion[:40]:
        brief = {
            "id": motion.get("motion_id"),
            "capability": "character",
            "brief": {
                "character_id": motion.get("character_id"),
                "actions": motion.get("actions"),
                "blocking": motion.get("blocking"),
            },
            "refs": [motion.get("motion_id"), motion.get("scene_id")],
            "priority": "required",
        }
        planned = motion_provider.plan(brief) or {}
        instructions.append({
            "provider_id": motion_provider.provider_id,
            "capability": "character",
            "brief": brief["brief"],
            "refs": brief["refs"],
            "priority": "required",
            "adapter_result": planned,
        })

    lip_provider = provider_for_capability("lip_sync", priority)
    for plan in lip_sync_plan:
        brief = {
            "id": plan.get("lip_sync_id"),
            "capability": "lip_sync",
            "brief": {
                "phonemes": plan.get("phonemes"),
                "words": plan.get("words"),
                "audio_ref": plan.get("audio_ref"),
            },
            "refs": [plan.get("lip_sync_id"), plan.get("character_id")],
            "priority": "required",
        }
        planned = lip_provider.plan(brief) or {}
        instructions.append({
            "provider_id": lip_provider.provider_id,
            "capability": "lip_sync",
            "brief": brief["brief"],
            "refs": brief["refs"],
            "priority": "required",
            "adapter_result": planned,
        })

    fx_provider = provider_for_capability("effects", priority)
    for effect in visual_effects:
        brief = {
            "id": effect.get("effect_id"),
            "capability": "effects",
            "brief": effect,
            "refs": [effect.get("effect_id"), effect.get("scene_id")],
            "priority": "recommended",
        }
        planned = fx_provider.plan(brief) or {}
        instructions.append({
            "provider_id": fx_provider.provider_id,
            "capability": "effects",
            "brief": brief["brief"],
            "refs": brief["refs"],
            "priority": "recommended",
            "adapter_result": planned,
        })

    return instructions


__all__ = [
    "ANIMATION_CAPABILITIES",
    "ANIMATION_PROVIDER_IDS",
    "AnimationProvider",
    "MockAnimationProvider",
    "available_providers",
    "build_provider_instructions",
    "get_animation_provider",
    "provider_for_capability",
    "provider_plan",
    "register_animation_provider",
]
