"""Generational Animation Runtime Integration Layer.

Renderer-neutral AnimationRuntime interface with BlenderRuntime as the first
executable backend. Future Unreal/Unity/Godot/ExternalAI adapters are stubs only.
"""

from __future__ import annotations

from services.animation_runtime.capability import build_capability_report
from services.animation_runtime.interface import AnimationRuntime
from services.animation_runtime.models import (
    RuntimeCapabilityReport,
    RuntimeExecutionManifest,
    RuntimeFailureReport,
)

__all__ = [
    "AnimationRuntime",
    "RuntimeCapabilityReport",
    "RuntimeExecutionManifest",
    "RuntimeFailureReport",
    "build_capability_report",
    "get_blender_runtime",
    "UnrealRuntime",
    "UnityRuntime",
    "GodotRuntime",
    "ExternalAIRuntime",
]


def __getattr__(name: str):
    if name in {"UnrealRuntime", "UnityRuntime", "GodotRuntime", "ExternalAIRuntime"}:
        from services.animation_runtime import stubs

        return getattr(stubs, name)
    raise AttributeError(name)


def get_blender_runtime():
    from services.animation_runtime.blender.runtime import BlenderRuntime

    return BlenderRuntime()
