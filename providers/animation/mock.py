"""Deterministic mock animation provider — Demo Mode default."""

from __future__ import annotations

from providers.animation_provider import ANIMATION_CAPABILITIES, AnimationProvider


class MockAnimationProvider(AnimationProvider):
    name = "mock_animation"
    provider_id = "mock_animation"
    capabilities = ANIMATION_CAPABILITIES

    def is_available(self) -> bool:
        return True

    def plan(self, brief: dict) -> dict:
        return {
            "provider": self.provider_id,
            "capability": brief.get("capability", "animation"),
            "status": "planned",
            "placeholder": True,
            "instruction": brief.get("brief", {}),
            "refs": list(brief.get("refs") or []),
            "uri": f"mock://animation/{brief.get('capability', 'animation')}/{brief.get('id', 'plan')}",
        }
