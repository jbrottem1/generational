"""Renderer-neutral Animation Execution adapter interface.

Translates studio packages into a selected skeletal runtime.
Does not replace Orchestrator / planning engines.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AnimationExecutionAdapter(ABC):
    """Required operations for genuine skeletal character animation."""

    runtime_id: str = "abstract"
    supports_skeletal: bool = False

    @abstractmethod
    def capability_report(self) -> dict[str, Any]:
        ...

    @abstractmethod
    def load_world(self, world_package: dict[str, Any]) -> dict[str, Any]:
        ...

    @abstractmethod
    def load_actor(self, character_rig_package: dict[str, Any]) -> dict[str, Any]:
        ...

    @abstractmethod
    def place_actor(self, transform: dict[str, Any]) -> dict[str, Any]:
        ...

    @abstractmethod
    def apply_animation_clip(self, clip_id: str) -> dict[str, Any]:
        ...

    @abstractmethod
    def apply_joint_keyframes(self, joint_tracks: list[dict[str, Any]]) -> dict[str, Any]:
        ...

    @abstractmethod
    def apply_facial_performance(self, facial_tracks: dict[str, Any]) -> dict[str, Any]:
        ...

    @abstractmethod
    def apply_gaze_target(self, target: dict[str, Any] | str) -> dict[str, Any]:
        ...

    @abstractmethod
    def apply_lip_sync(self, phoneme_timeline: list[dict[str, Any]]) -> dict[str, Any]:
        ...

    @abstractmethod
    def attach_object(self, actor_hand: str, object_id: str) -> dict[str, Any]:
        ...

    @abstractmethod
    def execute_interaction(self, interaction_package: dict[str, Any]) -> dict[str, Any]:
        ...

    @abstractmethod
    def apply_physics(self, physics_state: dict[str, Any]) -> dict[str, Any]:
        ...

    @abstractmethod
    def apply_camera(self, camera_plan: dict[str, Any]) -> dict[str, Any]:
        ...

    @abstractmethod
    def apply_lighting(self, lighting_plan: dict[str, Any]) -> dict[str, Any]:
        ...

    @abstractmethod
    def render_frames(self) -> dict[str, Any]:
        ...

    @abstractmethod
    def encode_mp4(self) -> dict[str, Any]:
        ...

    def execute_scene(self, executable_scene: dict[str, Any]) -> dict[str, Any]:
        """Default orchestration of adapter ops from EXECUTABLE_ANIMATION_SCENE."""
        log: list[dict[str, Any]] = []
        world = executable_scene.get("world_package") or {}
        actor = executable_scene.get("character_rig_package") or {}
        log.append({"op": "load_world", **self.load_world(world)})
        log.append({"op": "load_actor", **self.load_actor(actor)})
        log.append(
            {
                "op": "place_actor",
                **self.place_actor(executable_scene.get("actor_transform") or {"x": 0, "y": 0, "z": 0}),
            }
        )
        for clip in executable_scene.get("animation_clips") or []:
            log.append({"op": "apply_animation_clip", **self.apply_animation_clip(str(clip))})
        if executable_scene.get("joint_tracks"):
            log.append(
                {
                    "op": "apply_joint_keyframes",
                    **self.apply_joint_keyframes(list(executable_scene["joint_tracks"])),
                }
            )
        if executable_scene.get("facial_tracks"):
            log.append(
                {
                    "op": "apply_facial_performance",
                    **self.apply_facial_performance(dict(executable_scene["facial_tracks"])),
                }
            )
        if executable_scene.get("gaze_target"):
            log.append(
                {"op": "apply_gaze_target", **self.apply_gaze_target(executable_scene["gaze_target"])}
            )
        if executable_scene.get("phoneme_timeline"):
            log.append(
                {
                    "op": "apply_lip_sync",
                    **self.apply_lip_sync(list(executable_scene["phoneme_timeline"])),
                }
            )
        for att in executable_scene.get("attachments") or []:
            log.append(
                {
                    "op": "attach_object",
                    **self.attach_object(str(att.get("hand") or "hand_right"), str(att.get("object_id"))),
                }
            )
        for ix in executable_scene.get("interactions") or []:
            log.append({"op": "execute_interaction", **self.execute_interaction(dict(ix))})
        if executable_scene.get("physics_state"):
            log.append(
                {"op": "apply_physics", **self.apply_physics(dict(executable_scene["physics_state"]))}
            )
        for cam in executable_scene.get("camera_plan") or []:
            log.append({"op": "apply_camera", **self.apply_camera(dict(cam))})
        if executable_scene.get("lighting_plan"):
            log.append(
                {"op": "apply_lighting", **self.apply_lighting(dict(executable_scene["lighting_plan"]))}
            )
        frames = self.render_frames()
        log.append({"op": "render_frames", **frames})
        encode = self.encode_mp4()
        log.append({"op": "encode_mp4", **encode})
        return {
            "ok": bool(encode.get("ok") and frames.get("ok")),
            "runtime_id": self.runtime_id,
            "supports_skeletal": self.supports_skeletal,
            "log": log,
            "frames": frames,
            "encode": encode,
            "capability": self.capability_report(),
        }
