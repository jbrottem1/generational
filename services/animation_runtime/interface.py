"""Renderer-neutral AnimationRuntime interface.

Upstream packages stay Blender-agnostic. Only concrete runtimes speak to engines.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AnimationRuntime(ABC):
    runtime_name: str = "abstract"

    @abstractmethod
    def initialize_runtime(self) -> dict[str, Any]:
        ...

    @abstractmethod
    def check_capabilities(self) -> dict[str, Any]:
        ...

    @abstractmethod
    def load_character(self, character_rig_package: dict[str, Any]) -> dict[str, Any]:
        ...

    @abstractmethod
    def load_world(self, world_package: dict[str, Any]) -> dict[str, Any]:
        ...

    @abstractmethod
    def load_prop(self, prop_package: dict[str, Any]) -> dict[str, Any]:
        ...

    @abstractmethod
    def place_actor(self, actor_id: str, transform: dict[str, Any]) -> dict[str, Any]:
        ...

    @abstractmethod
    def place_prop(self, prop_id: str, transform: dict[str, Any]) -> dict[str, Any]:
        ...

    @abstractmethod
    def bind_skeleton(self, actor_id: str) -> dict[str, Any]:
        ...

    @abstractmethod
    def apply_animation_clip(self, actor_id: str, clip_id: str) -> dict[str, Any]:
        ...

    @abstractmethod
    def apply_joint_keyframes(self, actor_id: str, joint_tracks: list[dict[str, Any]]) -> dict[str, Any]:
        ...

    @abstractmethod
    def apply_root_motion(self, actor_id: str, root_motion_track: list[dict[str, Any]]) -> dict[str, Any]:
        ...

    @abstractmethod
    def apply_inverse_kinematics(self, actor_id: str, ik_targets: list[dict[str, Any]]) -> dict[str, Any]:
        ...

    @abstractmethod
    def apply_facial_animation(self, actor_id: str, facial_tracks: dict[str, Any]) -> dict[str, Any]:
        ...

    @abstractmethod
    def apply_gaze(self, actor_id: str, gaze_track: list[dict[str, Any]]) -> dict[str, Any]:
        ...

    @abstractmethod
    def apply_blinking(self, actor_id: str, blink_track: list[dict[str, Any]]) -> dict[str, Any]:
        ...

    @abstractmethod
    def apply_lip_sync(self, actor_id: str, viseme_timeline: list[dict[str, Any]]) -> dict[str, Any]:
        ...

    @abstractmethod
    def create_object_constraint(
        self, actor_id: str, body_part: str, object_id: str
    ) -> dict[str, Any]:
        ...

    @abstractmethod
    def release_object_constraint(
        self, actor_id: str, body_part: str, object_id: str
    ) -> dict[str, Any]:
        ...

    @abstractmethod
    def apply_physics_state(self, physics_package: dict[str, Any]) -> dict[str, Any]:
        ...

    @abstractmethod
    def apply_cloth_motion(self, actor_id: str, clothing_tracks: dict[str, Any]) -> dict[str, Any]:
        ...

    @abstractmethod
    def apply_secondary_motion(
        self, actor_id: str, secondary_tracks: dict[str, Any]
    ) -> dict[str, Any]:
        ...

    @abstractmethod
    def apply_camera_plan(self, camera_plan: list[dict[str, Any]] | dict[str, Any]) -> dict[str, Any]:
        ...

    @abstractmethod
    def apply_lighting_plan(self, lighting_plan: dict[str, Any]) -> dict[str, Any]:
        ...

    @abstractmethod
    def apply_environment_animation(
        self, environment_tracks: list[dict[str, Any]]
    ) -> dict[str, Any]:
        ...

    @abstractmethod
    def render_frame_range(self, start_frame: int, end_frame: int) -> dict[str, Any]:
        ...

    @abstractmethod
    def encode_video(self, output_path: str) -> dict[str, Any]:
        ...

    @abstractmethod
    def inspect_render(self, output_path: str) -> dict[str, Any]:
        ...

    @abstractmethod
    def write_execution_manifest(self) -> dict[str, Any]:
        ...
