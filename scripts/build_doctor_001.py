#!/usr/bin/env python3
"""Build permanent DOCTOR_001 production asset via Blender."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SCRIPT = (
    ROOT
    / "services"
    / "production_asset_studio"
    / "blender"
    / "scripts"
    / "build_doctor_001_asset.py"
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build DOCTOR_001 production asset")
    parser.add_argument("--skip-validate", action="store_true", help="Skip 20-shot validation renders")
    args = parser.parse_args()

    from services.animation_runtime.capability import discover_blender, doctor_asset_paths

    blender = discover_blender()
    if not blender.get("ok"):
        print(json.dumps({"ok": False, "reason": "blender_unavailable", "blender": blender}, indent=2))
        return 1

    out = ROOT / "data" / "studio_assets" / "DOCTOR_001" / "CHARACTER_PRODUCTION"
    out.mkdir(parents=True, exist_ok=True)
    runtime = doctor_asset_paths()["runtime_dir"]
    log = out / "BUILD_LOG.txt"
    cmd = [
        str(blender["path"]),
        "--background",
        "--python",
        str(SCRIPT),
        "--",
        "--out",
        str(out),
        "--runtime-dir",
        str(runtime),
        "--validate",
        "0" if args.skip_validate else "1",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    log.write_text("CMD: " + " ".join(cmd) + "\n\nSTDOUT:\n" + (proc.stdout or "") + "\n\nSTDERR:\n" + (proc.stderr or "") + f"\nEXIT:{proc.returncode}\n")
    report_path = out / "DOCTOR_001_BUILD_REPORT.json"
    report = json.loads(report_path.read_text()) if report_path.is_file() else {}
    # Sync contract maps into RUNTIME (Blender script may already have copied the blend)
    for name in (
        "RIG_BONE_MAP.json",
        "FACIAL_CHANNEL_MAP.json",
        "VISEME_MAP.json",
        "HAND_ATTACHMENT_POINTS.json",
        "FOOT_CONTACT_MARKERS.json",
        "CANONICAL_MEASUREMENTS.json",
        "VERSION.json",
        "ASSET_ORIGIN.json",
    ):
        src = out / name
        dst = runtime / name
        if src.is_file() and src.resolve() != dst.resolve():
            shutil.copy2(src, dst)

    summary = {
        "ok": proc.returncode == 0 and bool(report.get("ok")),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "out": str(out),
        "runtime": str(runtime),
        "report": report,
        "log": str(log),
    }
    (out / "BUILD_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"ok": summary["ok"], "out": str(out), "bones": report.get("bones"), "validation_shots": report.get("validation_shots")}, indent=2))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
