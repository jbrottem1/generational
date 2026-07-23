#!/usr/bin/env python3
"""CLI — Facial Performance + Environment Construction Standard."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    p = argparse.ArgumentParser(description="Facial + Environment Standard")
    p.add_argument("command", choices=["ensure", "shot", "selftest"])
    args = p.parse_args()

    from services.character_performance import face_rig_profile, validate_facial_performance_plan
    from services.environment_department import build_environment_package, validate_environment_package
    from services.shot_assembly import build_complete_shot
    from services.studio_assets import ensure_doctor_001_asset

    data = ROOT / "data" / "performance_standards"
    data.mkdir(parents=True, exist_ok=True)

    if args.command == "ensure":
        ensure_doctor_001_asset(force=False)
        rig = face_rig_profile("DOCTOR_001")
        env = build_environment_package("LOC-GMRI", owner="DOCTOR_001")
        (data / "FACE_RIG_PROFILE_DOCTOR_001.json").write_text(
            json.dumps(rig, indent=2) + "\n", encoding="utf-8"
        )
        (data / "ENVIRONMENT_PACKAGE_GMRI_LAB_A.json").write_text(
            json.dumps(env, indent=2) + "\n", encoding="utf-8"
        )
        print(
            json.dumps(
                {
                    "ok": True,
                    "face_rig": str(data / "FACE_RIG_PROFILE_DOCTOR_001.json"),
                    "environment": str(data / "ENVIRONMENT_PACKAGE_GMRI_LAB_A.json"),
                    "doctor_asset": str(ROOT / "data/studio_assets/DOCTOR_001"),
                },
                indent=2,
            )
        )
        return 0

    scene = {
        "scene_number": 3,
        "narration": "Let's look carefully — clarity is part of the care.",
        "subject": "diagnostic hologram",
        "length_sec": 4.0,
        "studio_expression": "teaching",
    }
    shot = build_complete_shot(
        shot_id="scene_003_shot_02",
        story_objective="The Doctor reassures the audience while revealing the diagnosis",
        scene=scene,
        character_id="DOCTOR_001",
        location="LOC-GMRI",
        camera={
            "shot_size": "medium_close_up",
            "lens_mm": 50,
            "movement": "slow_push_in",
            "focus_target": "doctor_001_eyes",
            "lighting_mood": "clinical_warm",
        },
    )

    if args.command == "shot":
        print(json.dumps(shot, indent=2, default=str)[:8000])
        return 0

    # selftest
    facial_ok = validate_facial_performance_plan(
        shot["character_performance"]["facial_performance_plan"]
    )
    env_ok = validate_environment_package(shot["environment"]["package"])
    report = {
        "ok": facial_ok["ok"] and env_ok["ok"],
        "facial_plan_ok": facial_ok["ok"],
        "environment_plan_ok": env_ok["ok"],
        "rendered_inspection_required": True,
        "quality_rule": shot["validation"]["quality_rule"],
        "gaze_events": len(shot["character_performance"]["gaze_plan"] or []),
        "fg_mg_bg": [
            len(shot["environment"]["foreground_elements"] or []),
            len(shot["environment"]["midground_elements"] or []),
            len(shot["environment"]["background_elements"] or []),
        ],
        "caveat": "Plan OK ≠ MP4 quality. Inspect rendered frames.",
    }
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
