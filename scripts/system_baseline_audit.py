"""Phase 1 baseline capture — tests, readiness, integrations, validation reports."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.env import load_application_env

load_application_env()

BASELINE_DIR = ROOT / "data" / "audit"
BASELINE_PATH = BASELINE_DIR / "baseline_snapshot.json"


def _git(cmd: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *cmd], cwd=ROOT, text=True).strip()
    except Exception:  # noqa: BLE001
        return ""


def run_pytest_summary() -> dict:
    t0 = time.perf_counter()
    proc = subprocess.run(
        [str(ROOT / "venv" / "bin" / "python"), "-m", "pytest", "tests/", "-q", "--tb=no"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=600,
    )
    elapsed = round(time.perf_counter() - t0, 2)
    tail = (proc.stdout or "") + (proc.stderr or "")
    passed = failed = 0
    for line in tail.splitlines():
        if " passed" in line and " in " in line:
            parts = line.strip().split()
            for i, p in enumerate(parts):
                if p == "passed," and i > 0:
                    try:
                        passed = int(parts[i - 1])
                    except ValueError:
                        pass
                if p == "failed" and i > 0:
                    try:
                        failed = int(parts[i - 1])
                    except ValueError:
                        pass
    return {
        "exit_code": proc.returncode,
        "passed": passed,
        "failed": failed,
        "duration_sec": elapsed,
        "summary_tail": tail.splitlines()[-3:],
    }


def collect_validation_reports() -> list[dict]:
    val_dir = ROOT / "data" / "productions" / "_validation"
    reports = []
    if not val_dir.exists():
        return reports
    for path in sorted(val_dir.rglob("*REPORT*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            reports.append(
                {
                    "path": str(path.relative_to(ROOT)),
                    "success": data.get("success"),
                    "duration_sec": data.get("duration_sec") or data.get("batch_runtime_sec"),
                    "export_path": data.get("export_path"),
                }
            )
        except Exception:  # noqa: BLE001
            continue
    return reports[-20:]


def main() -> dict:
    from services.readiness.report import build_readiness_report
    from services.provider_runtime.config import has_credential

    print("=== SYSTEM BASELINE AUDIT ===", flush=True)
    pytest = run_pytest_summary()
    readiness = build_readiness_report()

    snapshot = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "git": {
            "branch": _git(["branch", "--show-current"]),
            "commit": _git(["rev-parse", "HEAD"]),
            "commit_short": _git(["log", "-1", "--oneline"]),
        },
        "tests": pytest,
        "readiness": {
            "engines_ready": readiness.get("engines_ready"),
            "engines_total": readiness.get("engines_total"),
            "readiness_pct": readiness.get("readiness_pct"),
            "publishing": readiness.get("publishing"),
            "credentials_configured": sum(
                1 for v in (readiness.get("credentials") or {}).values() if v
            ),
        },
        "credentials_present": {
            k: has_credential(k)
            for k in (
                "OPENAI_API_KEY",
                "ANTHROPIC_API_KEY",
                "YOUTUBE_ACCESS_TOKEN",
                "ELEVENLABS_API_KEY",
            )
        },
        "validation_reports": collect_validation_reports(),
        "active_tracks": [
            "Distribution",
            "Visual Universe",
            "Animation Studio",
            "GCIS",
            "MacroCenter",
            "Project Excellence",
            "Project Fluid Motion",
        ],
    }
    BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    BASELINE_PATH.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(snapshot, indent=2), flush=True)
    print(f"\nSaved → {BASELINE_PATH}", flush=True)
    return snapshot


if __name__ == "__main__":
    main()
