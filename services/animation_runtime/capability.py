"""RuntimeCapabilityReport builders."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def discover_blender() -> dict[str, Any]:
    # Prefer app bundle binary on macOS — Homebrew wrapper can segfault under some sandboxes.
    app = Path("/Applications/Blender.app/Contents/MacOS/Blender")
    path = str(app) if app.is_file() else shutil.which("blender")
    version = None
    python_ok = False
    if path:
        try:
            proc = subprocess.run(
                [path, "--background", "--python-expr", "import bpy; print(bpy.app.version_string)"],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
            out = (proc.stdout or "") + (proc.stderr or "")
            for line in out.splitlines():
                if line.strip() and not line.startswith("ArchWarn") and "Blender" not in line[:20]:
                    # version_string like 4.5.11
                    if any(c.isdigit() for c in line):
                        version = line.strip().split()[0]
                        python_ok = True
                        break
            if "Blender" in out and version is None:
                for line in out.splitlines():
                    if line.startswith("Blender "):
                        version = line.replace("Blender", "").strip().split()[0]
                        python_ok = True
                        break
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "path": path, "error": str(exc)}
    return {
        "ok": bool(path and python_ok),
        "path": path,
        "version": version,
        "python_execution": python_ok,
        "ffmpeg": bool(shutil.which("ffmpeg")),
        "render_engines_expected": ["BLENDER_EEVEE_NEXT", "CYCLES", "BLENDER_WORKBENCH"],
    }


def doctor_asset_paths() -> dict[str, Path]:
    base = ROOT / "data" / "studio_assets" / "DOCTOR_001" / "RUNTIME"
    return {
        "runtime_dir": base,
        "character_blend": base / "DOCTOR_001_SKINNED.blend",
        "character_glb": base / "DOCTOR_001_SKINNED.glb",
        "lab_blend": base / "GENERATIONAL_MEDICAL_LAB.blend",
        "prop_blend": base / "SAMPLE_CONTAINER_001.blend",
        "rig_map": base / "RIG_BONE_MAP.json",
    }


def build_capability_report() -> dict[str, Any]:
    blender = discover_blender()
    paths = doctor_asset_paths()
    assets = {
        name: {
            "path": str(path),
            "exists": path.is_file() if path.suffix else path.is_dir(),
        }
        for name, path in paths.items()
    }
    mandatory = {
        "blender_executable": blender.get("ok"),
        "ffmpeg": blender.get("ffmpeg"),
        "skinned_character_blend": assets["character_blend"]["exists"],
        "lab_world_blend": assets["lab_blend"]["exists"],
        "sample_container_blend": assets["prop_blend"]["exists"],
    }
    return {
        "report_type": "RuntimeCapabilityReport",
        "runtime_name": "BlenderRuntime",
        "blender": blender,
        "assets": assets,
        "mandatory": mandatory,
        "ready_to_render": all(mandatory.values()),
        "output_writable": True,
    }
