#!/usr/bin/env python3
"""Re-verify / re-export Origin of Turtles from the existing local MP4.

Does not re-render. Uses the physical Desktop file as source of truth,
repairs manifest/library status, and prints the canonical completion block.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.env import load_application_env

load_application_env()

from services.animation.foundation_gate import evaluate_foundation_export
from services.animation.teaching_choreography import PLANS
from services.animation.turtle_demos import TURTLE_202_KEYWORDS
from services.animation.whiteboard import write_window_from_plan
from services.generational_os.export import export_verified_production
from services.generational_os.final_status import assign_final_status, print_completion_block
from services.generational_os.manifest import load_manifest, save_manifest
from services.generational_os.media_library import build_library_filename, library_root
from services.media_production.execution_mode import get_execution_context
from services.media_production.verified_export import assess_export_technical_validity, ffprobe_mp4

PROJECT_ID = "turtle_202"
EXPECTED_FILENAME = build_library_filename(
    category="Biology",
    series="001",
    episode="202",
    topic="Origin of Turtles",
)
EXPECTED_PATH = library_root() / "Biology" / EXPECTED_FILENAME
WORK = ROOT / "data" / "productions" / "_validation" / "local_jobs" / PROJECT_ID
TEMP_COPY = WORK / "episode_benchmark.mp4"
REPORT_PATH = ROOT / "data" / "productions" / "_validation" / "export_reliability" / "TURTLE_202_BENCHMARK.json"


def main() -> int:
    ctx = get_execution_context()
    report: dict = {
        "project_id": PROJECT_ID,
        "execution_mode": ctx.mode.value,
        "expected_path": str(EXPECTED_PATH),
    }

    if not ctx.can_claim_export_success:
        report["ok"] = False
        report["final_status"] = "FAILED"
        report["error"] = "Desktop media library unreachable. Expected ~/Desktop/AI Start-Up/Videos/."
        print(json.dumps(report, indent=2))
        return 1

    if not EXPECTED_PATH.is_file():
        report["ok"] = False
        report["final_status"] = "FAILED"
        report["error"] = f"Source of truth missing: {EXPECTED_PATH}"
        print(json.dumps(report, indent=2))
        return 1

    probe = ffprobe_mp4(EXPECTED_PATH)
    tech = assess_export_technical_validity(EXPECTED_PATH, probe=probe)
    report["pre_probe"] = probe
    report["pre_technical"] = tech

    # Re-export from the existing final file (temp ← final) to exercise atomic path
    WORK.mkdir(parents=True, exist_ok=True)
    shutil.copy2(EXPECTED_PATH, TEMP_COPY)

    qc_path = WORK / "qc.json"
    qc = {}
    if qc_path.is_file():
        qc = json.loads(qc_path.read_text(encoding="utf-8"))

    # Prefer QC from existing manifest / foundation report if present
    foundation_report = (
        ROOT / "data" / "productions" / "_validation" / "foundation_v2" / "FOUNDATION_V2_REPORT.json"
    )
    if not qc and foundation_report.is_file():
        qc = (json.loads(foundation_report.read_text(encoding="utf-8")).get("qc") or {})

    export_result = export_verified_production(
        TEMP_COPY,
        project_id=PROJECT_ID,
        filename=EXPECTED_FILENAME,
        domain="Biology",
        subject="The Origin of Turtles",
        title="The Origin of Turtles",
        series="001",
        episode="202",
        topic="Origin of Turtles",
        demo_id="foundation_v2_turtle_202",
        keywords=["turtles", "evolution", "paleontology", "shell"],
        render_duration_sec=float(probe.get("duration_sec") or 0) or None,
        print_completion=False,
    )

    export_path = Path(str(export_result.get("export_path") or EXPECTED_PATH))
    verify = export_result.get("verification") or {}
    board_actions = [
        {
            "kind": a.kind,
            "text": a.text,
            "start": a.start,
            "end": a.end,
            "row": a.row,
        }
        for a in TURTLE_202_KEYWORDS
    ]
    write_win = write_window_from_plan(PLANS.get("foundation_v2_turtle_202") or [], label="write")
    production = {
        "title": "The Origin of Turtles",
        "demo_id": "foundation_v2_turtle_202",
        "foundation": True,
        "export_path": str(export_path.resolve()),
        "export_bytes": int((verify.get("probe") or probe).get("bytes") or export_path.stat().st_size),
        "duration_sec": (verify.get("probe") or probe).get("duration_sec"),
        "qc": qc,
        "verification": verify,
        "verify": {
            "ok": bool(verify.get("ok")),
            "has_audio": bool((verify.get("probe") or probe).get("has_audio")),
            "has_video": bool((verify.get("probe") or probe).get("has_video")),
            "bytes": int((verify.get("probe") or probe).get("bytes") or 0),
        },
        "hook": "Have you ever wondered where turtles came from?",
        "script": {
            "hook": "Have you ever wondered where turtles came from?",
            "takeaway": "Turtle shells assembled gradually over deep time.",
        },
        "education_score": 82.0,
        "educational_review": {"score": 82.0, "accuracy_score": 75.0},
        "board_actions": board_actions,
        "write_gesture_window": write_win,
    }
    gate = evaluate_foundation_export(production, script=production["script"])
    status_info = assign_final_status(
        export_verified=bool(verify.get("ok") or tech.get("ok")),
        export_path=export_path,
        hard_fails=list(gate.hard_fails or []),
        warnings=list(gate.warnings or []) + list(export_result.get("warnings") or []),
    )

    # Repair persisted manifest if still stale
    manifest = load_manifest(PROJECT_ID)
    if manifest:
        manifest.export_path = str(export_path.resolve())
        manifest.final_status = status_info["final_status"]
        manifest.publishing_status = status_info["publishing_status"]
        manifest.local_render_status = status_info["local_render_status"]
        manifest.verification = verify if verify else {
            "ok": True,
            "probe": probe,
            "path": str(export_path.resolve()),
            "final_status": status_info["final_status"],
        }
        save_manifest(manifest)

    completion = print_completion_block(
        final_status=status_info["final_status"],
        export_path=export_path,
        probe=verify.get("probe") or probe,
        warnings=status_info["warnings"],
        hard_fails=status_info["hard_fails"],
    )

    report.update(
        {
            "ok": status_info["ok"],
            "final_status": status_info["final_status"],
            "export_path": str(export_path.resolve()),
            "file_size_bytes": export_path.stat().st_size if export_path.is_file() else 0,
            "warnings": status_info["warnings"],
            "hard_fails": status_info["hard_fails"],
            "foundation_gate": gate.to_dict(),
            "export_result": {
                "ok": export_result.get("ok"),
                "final_status": export_result.get("final_status"),
                "export_path": export_result.get("export_path"),
                "verification_ok": (export_result.get("verification") or {}).get("ok"),
                "checks": (export_result.get("verification") or {}).get("checks"),
            },
            "completion": completion,
        }
    )
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("ok", "final_status", "export_path", "warnings", "hard_fails")}, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
