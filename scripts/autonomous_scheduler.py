#!/usr/bin/env python3
"""CLI — Generational Autonomous Production Scheduler (existing pipeline only)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    p = argparse.ArgumentParser(description="Autonomous Production Scheduler")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("dashboard", help="Show / refresh scheduler dashboard")

    ing = sub.add_parser("ingest", help="Trend Intelligence → GenOS production queue")
    ing.add_argument("--subject", default="science education")
    ing.add_argument("--category", default="science")
    ing.add_argument("--queue", type=int, default=5)
    ing.add_argument("--channel", default="", help="Optional target channel id")
    ing.add_argument("--publish", action="store_true", help="Allow publishing prep flag on jobs")

    tick = sub.add_parser("tick", help="Run one queued production autonomously")
    tick.add_argument("--max-retries", type=int, default=2)
    tick.add_argument("--publish", action="store_true")

    batch = sub.add_parser("run", help="Ingest rankings then drain N jobs")
    batch.add_argument("--subject", default="science education")
    batch.add_argument("--category", default="science")
    batch.add_argument("--queue", type=int, default=3)
    batch.add_argument("--execute", type=int, default=2, help="How many jobs to run")
    batch.add_argument("--channel", default="")
    batch.add_argument("--skip-ingest", action="store_true")
    batch.add_argument("--publish", action="store_true")

    q = sub.add_parser("queue", help="Show GenOS / scheduler queue snapshot")
    q.add_argument("--status", default="", help="Filter status")

    enq = sub.add_parser("enqueue", help="Manually enqueue a topic (no new engines)")
    enq.add_argument("--topic", required=True)
    enq.add_argument("--category", default="General")
    enq.add_argument("--priority", type=int, default=80)
    enq.add_argument("--length", type=int, default=40)
    enq.add_argument("--channel", default="")
    enq.add_argument("--narrator", default="professor")

    args = p.parse_args()

    if args.cmd == "dashboard":
        from services.autonomous_scheduler import build_scheduler_dashboard, write_scheduler_dashboard

        dash = build_scheduler_dashboard()
        paths = write_scheduler_dashboard(dash)
        print(
            json.dumps(
                {
                    "jobs_waiting": dash.get("jobs_waiting"),
                    "jobs_running": dash.get("jobs_running"),
                    "jobs_completed": dash.get("jobs_completed"),
                    "failed_jobs": dash.get("failed_jobs"),
                    "retry_queue": dash.get("retry_queue"),
                    "average_render_time_ms": dash.get("average_render_time_ms"),
                    "average_quality": dash.get("average_quality"),
                    "production_success_rate": dash.get("production_success_rate"),
                    "todays_output": dash.get("todays_output"),
                    "weekly_output": dash.get("weekly_output"),
                    "paths": paths,
                },
                indent=2,
            )
        )
        return 0

    if args.cmd == "ingest":
        from services.autonomous_scheduler import ingest_trend_rankings

        out = ingest_trend_rankings(
            subject=args.subject,
            category=args.category,
            queue_count=args.queue,
            publishing_enabled=bool(args.publish),
            target_channel=args.channel,
        )
        print(
            json.dumps(
                {
                    "ranked": out.get("ranked"),
                    "queued_ok": out.get("queued_ok"),
                    "skipped_duplicates": out.get("skipped_duplicates"),
                    "top_topic": out.get("top_topic"),
                },
                indent=2,
            )
        )
        return 0 if out.get("ok") else 1

    if args.cmd == "tick":
        from services.autonomous_scheduler import run_scheduler_tick

        out = run_scheduler_tick(max_retries=args.max_retries, publishing_enabled=bool(args.publish))
        print(json.dumps({k: out[k] for k in out if k != "job"}, indent=2, default=str))
        return 0

    if args.cmd == "run":
        from services.autonomous_scheduler import run_autonomous_batch

        out = run_autonomous_batch(
            subject=args.subject,
            category=args.category,
            queue_count=args.queue,
            execute_count=args.execute,
            publishing_enabled=bool(args.publish),
            target_channel=args.channel,
            skip_ingest=bool(args.skip_ingest),
        )
        print(
            json.dumps(
                {k: out[k] for k in out if k not in ("tick_results", "scheduler")},
                indent=2,
                default=str,
            )
        )
        print(json.dumps({"tick_results": out.get("tick_results")}, indent=2, default=str))
        return 0 if out.get("ok") else 1

    if args.cmd == "queue":
        from services.generational_os.scheduler import list_genos_jobs, scheduler_dashboard

        dash = scheduler_dashboard()
        jobs = list_genos_jobs(status=args.status) if args.status else list_genos_jobs()
        print(
            json.dumps(
                {
                    "jobs_waiting": dash.get("jobs_waiting"),
                    "jobs_running": dash.get("jobs_running"),
                    "jobs_completed": dash.get("jobs_completed"),
                    "failed_jobs": dash.get("jobs_failed"),
                    "retry_queue": dash.get("jobs_retry"),
                    "jobs": [
                        {
                            "job_id": j.get("job_id"),
                            "topic": j.get("topic"),
                            "category": j.get("category"),
                            "priority": j.get("priority"),
                            "status": j.get("status"),
                            "retry_count": j.get("retry_count"),
                            "quality_score": j.get("quality_score"),
                            "failure_reason": j.get("failure_reason"),
                        }
                        for j in jobs[:40]
                    ],
                },
                indent=2,
                default=str,
            )
        )
        return 0

    if args.cmd == "enqueue":
        from services.generational_os.scheduler import schedule_production
        from services.autonomous_scheduler import write_scheduler_dashboard

        out = schedule_production(
            topic=args.topic,
            category=args.category,
            priority=args.priority,
            length_sec=args.length,
            narrator=args.narrator,
            target_channel=args.channel,
            run_immediately=False,
            constraints={"publishing_enabled": False, "from_autonomous_scheduler": True},
        )
        write_scheduler_dashboard()
        print(json.dumps(out, indent=2, default=str))
        return 0 if out.get("ok") else 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
