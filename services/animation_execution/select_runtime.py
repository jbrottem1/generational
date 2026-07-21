"""Select an AnimationExecutionAdapter — never silently fall back to stills."""

from __future__ import annotations

from typing import Any

from services.animation_execution.adapter import AnimationExecutionAdapter
from services.animation_execution.capability import audit_capabilities
from services.animation_execution.runtimes.insufficient import InsufficientRuntimeAdapter


def select_runtime() -> tuple[AnimationExecutionAdapter, dict[str, Any]]:
    """Return best available skeletal runtime, or insufficient adapter."""
    audit = audit_capabilities()
    # Future: if blender + skinned mesh → BlenderAdapter()
    # Future: if godot + gltf → GodotAdapter()
    if audit.get("skeletal_runtime_ready"):
        # Placeholder — no concrete adapter implemented yet even if apps appear
        adapter: AnimationExecutionAdapter = InsufficientRuntimeAdapter()
        return adapter, {
            **audit,
            "selected": adapter.runtime_id,
            "note": "External app detected path incomplete — skeletal adapter not yet implemented",
        }

    adapter = InsufficientRuntimeAdapter()
    return adapter, {
        **audit,
        "selected": adapter.runtime_id,
        "note": "No skeletal runtime/assets — Golden Motion MP4 refused",
    }
