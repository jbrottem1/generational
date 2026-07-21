"""Machine-readable runtime report types."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class RuntimeCapabilityReport:
    report_type: str = "RuntimeCapabilityReport"
    runtime_name: str = "BlenderRuntime"
    blender: dict[str, Any] = field(default_factory=dict)
    assets: dict[str, Any] = field(default_factory=dict)
    mandatory: dict[str, Any] = field(default_factory=dict)
    ready_to_render: bool = False
    output_writable: bool = True
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RuntimeFailureReport:
    report_type: str = "RuntimeFailureReport"
    ok: bool = False
    stage: str = ""
    reason: str = ""
    missing_dependencies: list[str] = field(default_factory=list)
    remediation: dict[str, Any] = field(default_factory=dict)
    approximations: list[str] = field(default_factory=list)
    unavailable_features: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RuntimeExecutionManifest:
    report_type: str = "RuntimeExecutionManifest"
    runtime_name: str = "BlenderRuntime"
    runtime_version: str = ""
    render_engine: str = ""
    blender_executable: str = ""
    scene_file: str = ""
    actor_id: str = "DOCTOR_001"
    actor_asset_path: str = ""
    rig_version: str = "procedural_v1"
    mesh_version: str = "procedural_v1"
    facial_rig_version: str = "shape_keys_v1"
    resolved_bone_mapping: list[dict[str, Any]] = field(default_factory=list)
    world_id: str = "GENERATIONAL_MEDICAL_LAB"
    world_asset_path: str = ""
    prop_ids: list[str] = field(default_factory=lambda: ["SAMPLE_CONTAINER_001"])
    animation_clips: list[str] = field(default_factory=list)
    joint_keyframe_counts: dict[str, int] = field(default_factory=dict)
    root_motion_track: list[dict[str, Any]] = field(default_factory=list)
    ik_targets: list[dict[str, Any]] = field(default_factory=list)
    facial_channels: list[str] = field(default_factory=list)
    viseme_timeline: list[dict[str, Any]] = field(default_factory=list)
    physics_settings: dict[str, Any] = field(default_factory=dict)
    object_constraints: list[dict[str, Any]] = field(default_factory=list)
    camera_tracks: list[dict[str, Any]] = field(default_factory=list)
    light_definitions: list[dict[str, Any]] = field(default_factory=list)
    render_settings: dict[str, Any] = field(default_factory=dict)
    audio_source: dict[str, Any] = field(default_factory=dict)
    output_path: str = ""
    validation_results: dict[str, Any] = field(default_factory=dict)
    fallbacks: list[str] = field(default_factory=list)
    approximations: list[str] = field(default_factory=list)
    unavailable_features: list[str] = field(default_factory=list)
    execution_timestamps: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
