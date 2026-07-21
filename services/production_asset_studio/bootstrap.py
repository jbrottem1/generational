"""Bootstrap Phase II: catalogs + Blender production asset build."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.animation_runtime.capability import discover_blender, doctor_asset_paths
from services.production_asset_studio.materialize import materialize_phase_ii_catalog

ROOT = Path(__file__).resolve().parents[2]
BUILDER = (
    Path(__file__).resolve().parent / "blender" / "scripts" / "build_production_assets.py"
)
OUT_ROOT = ROOT / "data" / "production_asset_studio"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def bootstrap_phase_ii(*, write: bool = True, build_blender: bool = True) -> dict[str, Any]:
    catalog = materialize_phase_ii_catalog(write=write)
    result: dict[str, Any] = {
        "ok": False,
        "phase": "II",
        "timestamp": _now(),
        "catalog": catalog,
        "blender_build": None,
        "runtime_export": None,
    }
    if not build_blender:
        result["ok"] = bool(catalog.get("ok"))
        return result

    blender = discover_blender()
    if not blender.get("ok"):
        result["blender_build"] = {"ok": False, "reason": "blender_unavailable", "blender": blender}
        (OUT_ROOT / "PHASE_II_BOOTSTRAP_REPORT.json").write_text(json.dumps(result, indent=2) + "\n")
        return result

    if not BUILDER.is_file():
        result["blender_build"] = {"ok": False, "reason": "missing_builder", "path": str(BUILDER)}
        (OUT_ROOT / "PHASE_II_BOOTSTRAP_REPORT.json").write_text(json.dumps(result, indent=2) + "\n")
        return result

    runtime = doctor_asset_paths()["runtime_dir"]
    staging = OUT_ROOT / "library" / "_blender_build"
    staging.mkdir(parents=True, exist_ok=True)
    log_path = staging / "BUILD_LOG.txt"
    cmd = [
        str(blender["path"]),
        "--background",
        "--python",
        str(BUILDER),
        "--",
        "--out",
        str(staging),
        "--runtime-dir",
        str(runtime),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    log_path.write_text(
        "CMD: " + " ".join(cmd) + "\n\nSTDOUT:\n" + (proc.stdout or "") + "\n\nSTDERR:\n" + (proc.stderr or "")
        + f"\n\nEXIT: {proc.returncode}\n"
    )
    report_path = staging / "PRODUCTION_BUILD_REPORT.json"
    report = json.loads(report_path.read_text()) if report_path.is_file() else {}
    result["blender_build"] = {
        "ok": proc.returncode == 0 and bool(report.get("ok")),
        "returncode": proc.returncode,
        "log": str(log_path),
        "report": report,
    }
    result["runtime_export"] = {
        "runtime_dir": str(runtime),
        "character_exists": (runtime / "DOCTOR_001_SKINNED.blend").is_file(),
        "lab_exists": (runtime / "GENERATIONAL_MEDICAL_LAB.blend").is_file(),
        "prop_exists": (runtime / "SAMPLE_CONTAINER_001.blend").is_file(),
        "asset_origin": str(runtime / "ASSET_ORIGIN.json"),
    }
    result["ok"] = bool(catalog.get("ok") and result["blender_build"]["ok"])
    if write:
        (OUT_ROOT / "PHASE_II_BOOTSTRAP_REPORT.json").write_text(json.dumps(result, indent=2) + "\n")
        (OUT_ROOT / "HONEST_PHASE_II_NOTES.md").write_text(
            _notes(result),
            encoding="utf-8",
        )
    return result


def _notes(result: dict[str, Any]) -> str:
    return f"""# Phase II — Production Asset Studio

**Status:** {'PASS' if result.get('ok') else 'PARTIAL/FAIL'}  
**Timestamp:** {result.get('timestamp')}

## Architecture (frozen)

Execution engines unchanged. Only assets upgraded.

## Delivered

- Eight department catalogs under `data/production_asset_studio/departments/`
- Production Blender builders for Doctor / Lab / Props / Materials / Lighting / Face / Atmosphere
- RUNTIME exports for Golden Motion consumption

## Honest scope

Phase II assets are Generational-authored production geometry (higher subdivision, PBR materials,
facial eyeballs, richer lab set dressing). They are not scanned photoreal humans or licensed
marketplace characters.

Doctor remains a stylized skinned digital actor — dramatically denser than Phase I greybox
(PBR skin/coat, independent eyes, lab set dressing, holograms, furniture), but not MetaHuman-grade.

## Latest Golden Motion (Phase II assets)

See `data/animation_runtime/golden_motion/LATEST/` — `asset_source: phase_ii_production_asset_studio`.

## Rerun

```bash
python scripts/production_asset_studio.py --bootstrap
python scripts/golden_motion_production.py
```
"""
