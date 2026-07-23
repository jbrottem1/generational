#!/usr/bin/env python3
"""GenOS CLI — Generational Operating System."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    p = argparse.ArgumentParser(description="Generational Operating System (GenOS)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("dashboard", help="Print GenOS operations dashboard JSON")
    sub.add_parser("state", help="Write SYSTEM_STATE.json + SYSTEM_HEALTH.md")
    sub.add_parser("reports", help="Generate daily/weekly/monthly reports")
    sub.add_parser("departments", help="List managed departments")
    sub.add_parser("queue", help="Show GenOS production queue")

    c = sub.add_parser("cycle", help="Run one operating cycle")
    c.add_argument("--category", default="science")
    c.add_argument("--queue", type=int, default=5)
    c.add_argument("--no-execute", action="store_true")
    c.add_argument("--publish", action="store_true", help="Allow publishing (default off)")

    s = sub.add_parser("selftest", help="Simulated operating day (publishing disabled)")
    s.add_argument("--no-execute", action="store_true", help="Skip full production (faster)")
    s.add_argument("--queue", type=int, default=5)

    n = sub.add_parser("run-next", help="Run next queued GenOS job")
    n.add_argument("--max-retries", type=int, default=2)

    a = sub.add_parser(
        "autonomous",
        help="Delegate to Autonomous Production Scheduler (existing pipeline only)",
    )
    a.add_argument("--queue", type=int, default=3)
    a.add_argument("--execute", type=int, default=1)
    a.add_argument("--category", default="science")
    a.add_argument("--skip-ingest", action="store_true")
    a.add_argument("--publish", action="store_true")

    args = p.parse_args()

    if args.cmd == "departments":
        from services.generational_os.departments import list_departments

        print(json.dumps(list_departments(), indent=2))
        return 0

    if args.cmd == "dashboard":
        from services.generational_os.genos import build_genos_dashboard

        print(json.dumps(build_genos_dashboard(), indent=2, default=str))
        return 0

    if args.cmd == "state":
        from services.generational_os.state import write_system_health, write_system_state

        print(json.dumps({"state": str(write_system_state()), "health": str(write_system_health())}, indent=2))
        return 0

    if args.cmd == "reports":
        from services.generational_os.reports_os import generate_all_reports

        print(json.dumps(generate_all_reports(publishing_enabled=False), indent=2))
        return 0

    if args.cmd == "queue":
        from services.generational_os.scheduler import scheduler_dashboard

        print(json.dumps(scheduler_dashboard(), indent=2, default=str))
        return 0

    if args.cmd == "run-next":
        from services.generational_os.scheduler import run_next_job

        out = run_next_job(max_retries=args.max_retries)
        print(json.dumps(out, indent=2, default=str))
        return 0 if out else 1

    if args.cmd == "cycle":
        from services.generational_os.genos import run_operating_cycle

        out = run_operating_cycle(
            category=args.category,
            queue_count=args.queue,
            execute_one=not args.no_execute,
            publishing_enabled=bool(args.publish),
        )
        print(json.dumps({k: out[k] for k in out if k != "log"}, indent=2, default=str))
        return 0 if out.get("ok") else 1

    if args.cmd == "selftest":
        from services.generational_os.genos import simulate_operating_day

        out = simulate_operating_day(queue_count=args.queue, execute_one=not args.no_execute)
        # Compact summary
        summary = {
            "ok": out.get("ok"),
            "publishing_enabled": out.get("publishing_enabled"),
            "opportunities_ranked": out.get("opportunities_ranked"),
            "queued_ok_count": out.get("queued_ok_count"),
            "execution": out.get("execution"),
            "lesson": (out.get("lesson") or {}).get("highest_impact_lesson"),
            "report_paths": out.get("report_paths"),
            "system_state_path": out.get("system_state_path"),
            "elapsed_ms": out.get("elapsed_ms"),
        }
        report_dir = Path(ROOT) / "data" / "generational_os" / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        (report_dir / "GENOS_SELFTEST.json").write_text(json.dumps(summary, indent=2, default=str) + "\n", encoding="utf-8")
        print(json.dumps(summary, indent=2, default=str))
        return 0 if out.get("ok") else 1

    if args.cmd == "autonomous":
        from services.autonomous_scheduler import run_autonomous_batch

        out = run_autonomous_batch(
            category=args.category,
            subject=f"{args.category} education",
            queue_count=args.queue,
            execute_count=args.execute,
            publishing_enabled=bool(args.publish),
            skip_ingest=bool(args.skip_ingest),
        )
        print(
            json.dumps(
                {
                    "ok": out.get("ok"),
                    "ingest": out.get("ingest"),
                    "executed": out.get("executed"),
                    "succeeded": out.get("succeeded"),
                    "failed": out.get("failed"),
                    "dashboard": out.get("dashboard"),
                    "elapsed_ms": out.get("elapsed_ms"),
                },
                indent=2,
                default=str,
            )
        )
        return 0 if out.get("ok") else 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
