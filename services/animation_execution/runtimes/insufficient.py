"""Adapter that refuses to fake skeletal animation with still-image motion."""

from __future__ import annotations

from typing import Any

from services.animation_execution.adapter import AnimationExecutionAdapter
from services.animation_execution.capability import audit_capabilities, audit_true_motion


class InsufficientRuntimeAdapter(AnimationExecutionAdapter):
    """Honest no-op runtime — records intent, refuses misleading MP4."""

    runtime_id = "insufficient_no_skeletal_runtime"
    supports_skeletal = False

    def __init__(self) -> None:
        self._ops: list[dict[str, Any]] = []
        self._world_id: str | None = None
        self._actor_id: str | None = None
        self._refused_reason = (
            "No skeletal animation runtime or skinned mesh is available. "
            "Refusing to encode a Ken Burns / layered-still MP4 as Golden Motion."
        )

    def capability_report(self) -> dict[str, Any]:
        return {
            "runtime_id": self.runtime_id,
            "supports_skeletal": False,
            "audit": audit_capabilities(),
            "true_motion_probe": audit_true_motion(),
            "will_encode_mp4": False,
            "will_use_true_motion_fallback": False,
        }

    def _reject(self, op: str, **extra: Any) -> dict[str, Any]:
        row = {"ok": False, "op": op, "executed_natively": False, "reason": self._refused_reason, **extra}
        self._ops.append(row)
        return row

    def load_world(self, world_package: dict[str, Any]) -> dict[str, Any]:
        self._world_id = str(world_package.get("world_id") or "unknown")
        return self._reject(
            "load_world",
            world_id=self._world_id,
            planned_only=True,
            note="WORLD_PACKAGE accepted as plan; no 3D stage loaded",
        )

    def load_actor(self, character_rig_package: dict[str, Any]) -> dict[str, Any]:
        self._actor_id = str(
            character_rig_package.get("character_id")
            or (character_rig_package.get("identity") or {}).get("character_id")
            or "unknown"
        )
        return self._reject(
            "load_actor",
            character_id=self._actor_id,
            planned_only=True,
            note="CHARACTER_RIG_PACKAGE is JSON hierarchy — no skinned mesh bound",
        )

    def place_actor(self, transform: dict[str, Any]) -> dict[str, Any]:
        return self._reject("place_actor", transform=transform, planned_only=True)

    def apply_animation_clip(self, clip_id: str) -> dict[str, Any]:
        return self._reject("apply_animation_clip", clip_id=clip_id, planned_only=True)

    def apply_joint_keyframes(self, joint_tracks: list[dict[str, Any]]) -> dict[str, Any]:
        return self._reject(
            "apply_joint_keyframes",
            track_count=len(joint_tracks),
            planned_only=True,
        )

    def apply_facial_performance(self, facial_tracks: dict[str, Any]) -> dict[str, Any]:
        return self._reject("apply_facial_performance", planned_only=True)

    def apply_gaze_target(self, target: dict[str, Any] | str) -> dict[str, Any]:
        return self._reject("apply_gaze_target", target=target, planned_only=True)

    def apply_lip_sync(self, phoneme_timeline: list[dict[str, Any]]) -> dict[str, Any]:
        return self._reject(
            "apply_lip_sync",
            phoneme_count=len(phoneme_timeline),
            planned_only=True,
        )

    def attach_object(self, actor_hand: str, object_id: str) -> dict[str, Any]:
        return self._reject(
            "attach_object",
            actor_hand=actor_hand,
            object_id=object_id,
            planned_only=True,
        )

    def execute_interaction(self, interaction_package: dict[str, Any]) -> dict[str, Any]:
        return self._reject(
            "execute_interaction",
            interaction_id=interaction_package.get("interaction_id"),
            planned_only=True,
        )

    def apply_physics(self, physics_state: dict[str, Any]) -> dict[str, Any]:
        return self._reject("apply_physics", planned_only=True)

    def apply_camera(self, camera_plan: dict[str, Any]) -> dict[str, Any]:
        return self._reject("apply_camera", camera_plan=camera_plan, planned_only=True)

    def apply_lighting(self, lighting_plan: dict[str, Any]) -> dict[str, Any]:
        return self._reject("apply_lighting", planned_only=True)

    def render_frames(self) -> dict[str, Any]:
        return self._reject(
            "render_frames",
            frames_written=0,
            note="No skeletal frame buffer — render refused",
        )

    def encode_mp4(self) -> dict[str, Any]:
        return {
            "ok": False,
            "op": "encode_mp4",
            "executed_natively": False,
            "mp4_path": None,
            "refused": True,
            "reason": self._refused_reason,
            "auto_rejection": [
                "no_skeletal_runtime",
                "no_skinned_mesh",
                "true_motion_is_layered_stills_only",
                "no_fallback_stills_permitted_for_golden_motion",
            ],
        }

    def execute_scene(self, executable_scene: dict[str, Any]) -> dict[str, Any]:
        result = super().execute_scene(executable_scene)
        result["ok"] = False
        result["golden_motion_passed"] = False
        result["refused_misleading_mp4"] = True
        result["ops_planned"] = self._ops
        return result
