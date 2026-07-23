"""BlenderRuntime — first concrete AnimationRuntime backend."""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.animation_runtime.capability import build_capability_report, discover_blender, doctor_asset_paths
from services.animation_runtime.interface import AnimationRuntime
from services.animation_runtime.models import RuntimeExecutionManifest
from services.animation_runtime.retarget import load_resolved_bone_map

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = Path(__file__).resolve().parent / "scripts" / "golden_motion_blender.py"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class BlenderRuntime(AnimationRuntime):
    runtime_name = "BlenderRuntime"

    def __init__(self, work_dir: Path | None = None) -> None:
        self.work_dir = Path(work_dir) if work_dir else ROOT / "data" / "animation_runtime" / "_work"
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self._blender = discover_blender()
        self._state: dict[str, Any] = {
            "initialized": False,
            "character": None,
            "world": None,
            "props": {},
            "actors": {},
            "clips": [],
            "joint_tracks": {},
            "root_motion": [],
            "ik_targets": [],
            "facial": {},
            "gaze": [],
            "blinks": [],
            "visemes": [],
            "constraints": [],
            "physics": {},
            "cloth": {},
            "secondary": {},
            "camera_plan": [],
            "lighting_plan": {},
            "environment": [],
            "render": {},
            "encode": {},
            "fallbacks": [],
            "approximations": [
                "Coat secondary motion uses coat bones (not full cloth solver)",
                "Eye aim approximated via head bone + visor geometry",
                "Viseme timing derived from dialogue syllable schedule + waveform alignment check",
                "IK for grasp blended via authored joint keyframes + ChildOf constraint",
                "Facial shape keys are procedural Generational deformations, not photogrammetry",
            ],
            "unavailable": [
                "UnrealRuntime",
                "UnityRuntime",
                "GodotRuntime",
                "ExternalAIRuntime",
            ],
            "timestamps": {},
        }
        self._manifest = RuntimeExecutionManifest()

    def initialize_runtime(self) -> dict[str, Any]:
        self._blender = discover_blender()
        self._state["initialized"] = bool(self._blender.get("ok"))
        self._state["timestamps"]["initialize"] = _now()
        self._manifest.blender_executable = str(self._blender.get("path") or "")
        self._manifest.runtime_version = str(self._blender.get("version") or "")
        return {
            "ok": self._state["initialized"],
            "blender": self._blender,
            "script": str(SCRIPT),
            "script_exists": SCRIPT.is_file(),
        }

    def check_capabilities(self) -> dict[str, Any]:
        report = build_capability_report()
        report["script_exists"] = SCRIPT.is_file()
        report["work_dir_writable"] = self.work_dir.exists()
        return report

    def load_character(self, character_rig_package: dict[str, Any]) -> dict[str, Any]:
        paths = doctor_asset_paths()
        self._state["character"] = {
            "package": character_rig_package,
            "asset": str(paths["character_blend"]),
            "exists": paths["character_blend"].is_file(),
        }
        self._manifest.actor_id = str(
            character_rig_package.get("character_id")
            or character_rig_package.get("actor_id")
            or "DOCTOR_001"
        )
        self._manifest.actor_asset_path = str(paths["character_blend"])
        return {"ok": True, **self._state["character"]}

    def load_world(self, world_package: dict[str, Any]) -> dict[str, Any]:
        paths = doctor_asset_paths()
        self._state["world"] = {
            "package": world_package,
            "asset": str(paths["lab_blend"]),
            "exists": paths["lab_blend"].is_file(),
            "world_id": "GENERATIONAL_MEDICAL_LAB",
        }
        self._manifest.world_id = "GENERATIONAL_MEDICAL_LAB"
        self._manifest.world_asset_path = str(paths["lab_blend"])
        return {"ok": True, **self._state["world"]}

    def load_prop(self, prop_package: dict[str, Any]) -> dict[str, Any]:
        prop_id = str(prop_package.get("prop_id") or "SAMPLE_CONTAINER_001")
        paths = doctor_asset_paths()
        entry = {
            "package": prop_package,
            "asset": str(paths["prop_blend"]),
            "exists": paths["prop_blend"].is_file(),
        }
        self._state["props"][prop_id] = entry
        return {"ok": True, "prop_id": prop_id, **entry}

    def place_actor(self, actor_id: str, transform: dict[str, Any]) -> dict[str, Any]:
        self._state["actors"][actor_id] = transform
        return {"ok": True, "actor_id": actor_id, "transform": transform}

    def place_prop(self, prop_id: str, transform: dict[str, Any]) -> dict[str, Any]:
        self._state["props"].setdefault(prop_id, {})["transform"] = transform
        return {"ok": True, "prop_id": prop_id, "transform": transform}

    def bind_skeleton(self, actor_id: str) -> dict[str, Any]:
        mapping = load_resolved_bone_map()
        self._manifest.resolved_bone_mapping = mapping.get("bones") or []
        return {"ok": mapping.get("ok"), "actor_id": actor_id, "bone_map": mapping}

    def apply_animation_clip(self, actor_id: str, clip_id: str) -> dict[str, Any]:
        self._state["clips"].append({"actor_id": actor_id, "clip_id": clip_id})
        self._manifest.animation_clips.append(clip_id)
        return {"ok": True, "actor_id": actor_id, "clip_id": clip_id}

    def apply_joint_keyframes(self, actor_id: str, joint_tracks: list[dict[str, Any]]) -> dict[str, Any]:
        self._state["joint_tracks"][actor_id] = joint_tracks
        self._manifest.joint_keyframe_counts[actor_id] = sum(
            len(t.get("keys") or t.get("keyframes") or []) for t in joint_tracks
        )
        return {"ok": True, "actor_id": actor_id, "track_count": len(joint_tracks)}

    def apply_root_motion(self, actor_id: str, root_motion_track: list[dict[str, Any]]) -> dict[str, Any]:
        self._state["root_motion"] = root_motion_track
        self._manifest.root_motion_track = root_motion_track
        return {"ok": True, "actor_id": actor_id, "samples": len(root_motion_track)}

    def apply_inverse_kinematics(self, actor_id: str, ik_targets: list[dict[str, Any]]) -> dict[str, Any]:
        self._state["ik_targets"] = ik_targets
        self._manifest.ik_targets = ik_targets
        return {"ok": True, "actor_id": actor_id, "targets": len(ik_targets)}

    def apply_facial_animation(self, actor_id: str, facial_tracks: dict[str, Any]) -> dict[str, Any]:
        self._state["facial"] = facial_tracks
        self._manifest.facial_channels = list(facial_tracks.keys())
        return {"ok": True, "actor_id": actor_id, "channels": list(facial_tracks.keys())}

    def apply_gaze(self, actor_id: str, gaze_track: list[dict[str, Any]]) -> dict[str, Any]:
        self._state["gaze"] = gaze_track
        return {"ok": True, "actor_id": actor_id, "samples": len(gaze_track)}

    def apply_blinking(self, actor_id: str, blink_track: list[dict[str, Any]]) -> dict[str, Any]:
        self._state["blinks"] = blink_track
        return {"ok": True, "actor_id": actor_id, "samples": len(blink_track)}

    def apply_lip_sync(self, actor_id: str, viseme_timeline: list[dict[str, Any]]) -> dict[str, Any]:
        self._state["visemes"] = viseme_timeline
        self._manifest.viseme_timeline = viseme_timeline
        return {"ok": True, "actor_id": actor_id, "visemes": len(viseme_timeline)}

    def create_object_constraint(
        self, actor_id: str, body_part: str, object_id: str
    ) -> dict[str, Any]:
        entry = {
            "actor_id": actor_id,
            "body_part": body_part,
            "object_id": object_id,
            "type": "CHILD_OF",
        }
        self._state["constraints"].append(entry)
        self._manifest.object_constraints.append(entry)
        return {"ok": True, **entry}

    def release_object_constraint(
        self, actor_id: str, body_part: str, object_id: str
    ) -> dict[str, Any]:
        return {
            "ok": True,
            "actor_id": actor_id,
            "body_part": body_part,
            "object_id": object_id,
            "released": False,
            "note": "Golden Motion holds grasp through end of shot",
        }

    def apply_physics_state(self, physics_package: dict[str, Any]) -> dict[str, Any]:
        self._state["physics"] = physics_package
        self._manifest.physics_settings = physics_package
        return {"ok": True, "baked": True}

    def apply_cloth_motion(self, actor_id: str, clothing_tracks: dict[str, Any]) -> dict[str, Any]:
        self._state["cloth"] = clothing_tracks
        return {"ok": True, "actor_id": actor_id, "mode": "coat_bones"}

    def apply_secondary_motion(
        self, actor_id: str, secondary_tracks: dict[str, Any]
    ) -> dict[str, Any]:
        self._state["secondary"] = secondary_tracks
        return {"ok": True, "actor_id": actor_id}

    def apply_camera_plan(self, camera_plan: list[dict[str, Any]] | dict[str, Any]) -> dict[str, Any]:
        plan = camera_plan if isinstance(camera_plan, list) else [camera_plan]
        self._state["camera_plan"] = plan
        self._manifest.camera_tracks = plan
        return {"ok": True, "shots": len(plan)}

    def apply_lighting_plan(self, lighting_plan: dict[str, Any]) -> dict[str, Any]:
        self._state["lighting_plan"] = lighting_plan
        self._manifest.light_definitions = list(lighting_plan.get("lights") or [])
        return {"ok": True}

    def apply_environment_animation(
        self, environment_tracks: list[dict[str, Any]]
    ) -> dict[str, Any]:
        self._state["environment"] = environment_tracks
        return {"ok": True, "tracks": len(environment_tracks)}

    def run_blender(
        self,
        *,
        mode: str,
        out_dir: Path,
        audio: str = "",
        samples: int = 16,
        runtime_dir: Path | None = None,
    ) -> dict[str, Any]:
        if not self._blender.get("ok"):
            return {"ok": False, "reason": "blender_unavailable", "blender": self._blender}
        if not SCRIPT.is_file():
            return {"ok": False, "reason": "missing_blender_script", "path": str(SCRIPT)}

        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        log_path = out_dir / "RENDER_LOG.txt"
        cmd = [
            str(self._blender["path"]),
            "--background",
            "--python",
            str(SCRIPT),
            "--",
            "--mode",
            mode,
            "--out",
            str(out_dir),
            "--samples",
            str(samples),
        ]
        if audio:
            cmd.extend(["--audio", audio])
        if runtime_dir:
            cmd.extend(["--runtime-dir", str(runtime_dir)])

        self._state["timestamps"][f"blender_{mode}_start"] = _now()
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        self._state["timestamps"][f"blender_{mode}_end"] = _now()
        log_path.write_text(
            "CMD: "
            + " ".join(cmd)
            + "\n\nSTDOUT:\n"
            + (proc.stdout or "")
            + "\n\nSTDERR:\n"
            + (proc.stderr or "")
            + f"\n\nEXIT: {proc.returncode}\n"
        )
        ok = proc.returncode == 0 and (
            (out_dir / "ASSEMBLE_REPORT.json").is_file()
            or (out_dir / "RENDER_REPORT.json").is_file()
            or (out_dir / "GOLDEN_MOTION_SCENE.blend").is_file()
        )
        report = {}
        for name in ("ASSEMBLE_REPORT.json", "RENDER_REPORT.json"):
            p = out_dir / name
            if p.is_file():
                report = json.loads(p.read_text())
                break
        return {
            "ok": ok,
            "returncode": proc.returncode,
            "log": str(log_path),
            "report": report,
            "blend": str(out_dir / "GOLDEN_MOTION_SCENE.blend"),
            "frame_dir": str(out_dir / "frames"),
        }

    def render_frame_range(self, start_frame: int, end_frame: int) -> dict[str, Any]:
        self._state["render"] = {"start": start_frame, "end": end_frame}
        return {"ok": True, "delegated_to": "run_blender", **self._state["render"]}

    def encode_video(self, output_path: str) -> dict[str, Any]:
        out = Path(output_path)
        frame_dir = Path(self._state.get("render", {}).get("frame_dir") or (out.parent / "frames"))
        audio = str(self._state.get("audio_path") or "")
        fps = int(self._state.get("render", {}).get("fps") or 24)
        if not shutil.which("ffmpeg"):
            return {"ok": False, "reason": "ffmpeg_missing"}
        frames = sorted(frame_dir.glob("frame_*.png"))
        if not frames:
            return {"ok": False, "reason": "no_frames", "frame_dir": str(frame_dir)}
        sample = frames[0].name
        duration_sec = len(frames) / float(fps)
        # Pad short narration (e.g. 3s line) into full timeline so -shortest does not truncate video
        audio_for_mux = audio
        if audio and Path(audio).is_file():
            padded = out.parent / "audio_timeline_padded.m4a"
            delay_ms = int(round(10.5 * 1000))  # speech window for Golden Motion delivery beat
            pad = subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    audio,
                    "-af",
                    f"adelay={delay_ms}|{delay_ms},apad=whole_dur={duration_sec:.3f}",
                    "-t",
                    f"{duration_sec:.3f}",
                    str(padded),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            if pad.returncode == 0 and padded.is_file():
                audio_for_mux = str(padded)

        start_num = 1
        try:
            start_num = int(frames[0].stem.split("_")[-1])
        except Exception:
            start_num = 1
        cmd = [
            "ffmpeg",
            "-y",
            "-framerate",
            str(fps),
            "-start_number",
            str(start_num),
            "-i",
            str(frame_dir / "frame_%04d.png"),
        ]
        if audio_for_mux and Path(audio_for_mux).is_file():
            cmd.extend(
                ["-i", audio_for_mux, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest"]
            )
        else:
            cmd.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p"])
        cmd.append(str(out))
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)

        ok = proc.returncode == 0 and out.is_file() and out.stat().st_size > 10_000
        self._state["encode"] = {
            "ok": ok,
            "path": str(out),
            "returncode": proc.returncode,
            "stderr_tail": (proc.stderr or "")[-2000:],
            "frame_count": len(frames),
            "sample_frame": sample,
            "duration_sec": duration_sec,
            "audio_for_mux": audio_for_mux,
        }
        self._manifest.output_path = str(out)
        return self._state["encode"]

    def inspect_render(self, output_path: str) -> dict[str, Any]:
        from services.animation_runtime.inspect_render import inspect_mp4_and_frames

        frame_dir = Path(self._state.get("render", {}).get("frame_dir") or Path(output_path).parent / "frames")
        result = inspect_mp4_and_frames(Path(output_path), frame_dir)
        self._manifest.validation_results = result
        return result

    def write_execution_manifest(self) -> dict[str, Any]:
        self._manifest.runtime_name = self.runtime_name
        self._manifest.fallbacks = list(self._state.get("fallbacks") or [])
        self._manifest.approximations = list(self._state.get("approximations") or [])
        self._manifest.unavailable_features = list(self._state.get("unavailable") or [])
        self._manifest.execution_timestamps = dict(self._state.get("timestamps") or {})
        self._manifest.render_settings = dict(self._state.get("render") or {})
        self._manifest.audio_source = dict(self._state.get("audio_meta") or {})
        return self._manifest.to_dict()

    def set_audio(self, path: str, meta: dict[str, Any]) -> None:
        self._state["audio_path"] = path
        self._state["audio_meta"] = meta
        if meta.get("fallback"):
            self._state["fallbacks"].append(str(meta.get("fallback")))
