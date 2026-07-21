"""Future runtime adapters — interfaces only, not implemented."""

from __future__ import annotations

from typing import Any

from services.animation_runtime.interface import AnimationRuntime


class _UnimplementedRuntime(AnimationRuntime):
    runtime_name = "unimplemented"

    def _fail(self, method: str) -> dict[str, Any]:
        return {
            "ok": False,
            "implemented": False,
            "runtime": self.runtime_name,
            "method": method,
            "reason": f"{self.runtime_name} is a future adapter stub only. Use BlenderRuntime.",
        }

    def initialize_runtime(self) -> dict[str, Any]:
        return self._fail("initialize_runtime")

    def check_capabilities(self) -> dict[str, Any]:
        return {
            "ok": False,
            "implemented": False,
            "runtime_name": self.runtime_name,
            "ready_to_render": False,
        }

    def load_character(self, character_rig_package: dict[str, Any]) -> dict[str, Any]:
        return self._fail("load_character")

    def load_world(self, world_package: dict[str, Any]) -> dict[str, Any]:
        return self._fail("load_world")

    def load_prop(self, prop_package: dict[str, Any]) -> dict[str, Any]:
        return self._fail("load_prop")

    def place_actor(self, actor_id: str, transform: dict[str, Any]) -> dict[str, Any]:
        return self._fail("place_actor")

    def place_prop(self, prop_id: str, transform: dict[str, Any]) -> dict[str, Any]:
        return self._fail("place_prop")

    def bind_skeleton(self, actor_id: str) -> dict[str, Any]:
        return self._fail("bind_skeleton")

    def apply_animation_clip(self, actor_id: str, clip_id: str) -> dict[str, Any]:
        return self._fail("apply_animation_clip")

    def apply_joint_keyframes(self, actor_id: str, joint_tracks: list[dict[str, Any]]) -> dict[str, Any]:
        return self._fail("apply_joint_keyframes")

    def apply_root_motion(self, actor_id: str, root_motion_track: list[dict[str, Any]]) -> dict[str, Any]:
        return self._fail("apply_root_motion")

    def apply_inverse_kinematics(self, actor_id: str, ik_targets: list[dict[str, Any]]) -> dict[str, Any]:
        return self._fail("apply_inverse_kinematics")

    def apply_facial_animation(self, actor_id: str, facial_tracks: dict[str, Any]) -> dict[str, Any]:
        return self._fail("apply_facial_animation")

    def apply_gaze(self, actor_id: str, gaze_track: list[dict[str, Any]]) -> dict[str, Any]:
        return self._fail("apply_gaze")

    def apply_blinking(self, actor_id: str, blink_track: list[dict[str, Any]]) -> dict[str, Any]:
        return self._fail("apply_blinking")

    def apply_lip_sync(self, actor_id: str, viseme_timeline: list[dict[str, Any]]) -> dict[str, Any]:
        return self._fail("apply_lip_sync")

    def create_object_constraint(
        self, actor_id: str, body_part: str, object_id: str
    ) -> dict[str, Any]:
        return self._fail("create_object_constraint")

    def release_object_constraint(
        self, actor_id: str, body_part: str, object_id: str
    ) -> dict[str, Any]:
        return self._fail("release_object_constraint")

    def apply_physics_state(self, physics_package: dict[str, Any]) -> dict[str, Any]:
        return self._fail("apply_physics_state")

    def apply_cloth_motion(self, actor_id: str, clothing_tracks: dict[str, Any]) -> dict[str, Any]:
        return self._fail("apply_cloth_motion")

    def apply_secondary_motion(
        self, actor_id: str, secondary_tracks: dict[str, Any]
    ) -> dict[str, Any]:
        return self._fail("apply_secondary_motion")

    def apply_camera_plan(self, camera_plan: list[dict[str, Any]] | dict[str, Any]) -> dict[str, Any]:
        return self._fail("apply_camera_plan")

    def apply_lighting_plan(self, lighting_plan: dict[str, Any]) -> dict[str, Any]:
        return self._fail("apply_lighting_plan")

    def apply_environment_animation(
        self, environment_tracks: list[dict[str, Any]]
    ) -> dict[str, Any]:
        return self._fail("apply_environment_animation")

    def render_frame_range(self, start_frame: int, end_frame: int) -> dict[str, Any]:
        return self._fail("render_frame_range")

    def encode_video(self, output_path: str) -> dict[str, Any]:
        return self._fail("encode_video")

    def inspect_render(self, output_path: str) -> dict[str, Any]:
        return self._fail("inspect_render")

    def write_execution_manifest(self) -> dict[str, Any]:
        return self._fail("write_execution_manifest")


class UnrealRuntime(_UnimplementedRuntime):
    runtime_name = "UnrealRuntime"


class UnityRuntime(_UnimplementedRuntime):
    runtime_name = "UnityRuntime"


class GodotRuntime(_UnimplementedRuntime):
    runtime_name = "GodotRuntime"


class ExternalAIRuntime(_UnimplementedRuntime):
    runtime_name = "ExternalAIRuntime"
