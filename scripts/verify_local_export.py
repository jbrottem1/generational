#!/usr/bin/env python3
"""Verify Origin of Turtles export on local Mac — run AFTER run_render_package."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.env import load_application_env

load_application_env()

from services.generational_os.media_library import build_library_filename, library_root
from services.media_production.execution_mode import get_execution_context
from services.media_production.verified_export import ffprobe_mp4, reveal_export_in_finder

EXPECTED_FILENAME = build_library_filename(
    category="Biology",
    series="001",
    episode="202",
    topic="Origin of Turtles",
)
EXPECTED_DIR = library_root() / "Biology"
EXPECTED_PATH = EXPECTED_DIR / EXPECTED_FILENAME


def main() -> int:
    ctx = get_execution_context()
    report: dict = {
        "execution_environment": ctx.mode.value,
        "platform": ctx.platform,
        "home": ctx.home,
        "expected_path": str(EXPECTED_PATH),
        "expected_filename": EXPECTED_FILENAME,
    }

    if not ctx.can_claim_export_success:
        report["ok"] = False
        report["status"] = "export_root_unreachable"
        report["message"] = "Desktop media library unreachable. Expected ~/Desktop/AI Start-Up/Videos/."
        print(json.dumps(report, indent=2))
        return 1

    if not EXPECTED_PATH.is_file():
        report["ok"] = False
        report["status"] = "file_missing"
        report["message"] = f"Expected file not found: {EXPECTED_PATH}"
        print(json.dumps(report, indent=2))
        return 1

    probe = ffprobe_mp4(EXPECTED_PATH)
    size = EXPECTED_PATH.stat().st_size
    report.update(
        {
            "ok": bool(probe.get("ok")) and size > 50_000,
            "status": "verified" if probe.get("ok") else "probe_failed",
            "absolute_path": str(EXPECTED_PATH.resolve()),
            "filename": EXPECTED_FILENAME,
            "file_size_bytes": size,
            "duration_sec": probe.get("duration_sec"),
            "width": probe.get("width"),
            "height": probe.get("height"),
            "video_codec": probe.get("video_codec"),
            "audio_codec": probe.get("audio_codec"),
            "has_video": probe.get("has_video"),
            "has_audio": probe.get("has_audio"),
            "probe": probe,
        }
    )

    if report["ok"]:
        report["finder_revealed"] = reveal_export_in_finder(EXPECTED_PATH)

    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
