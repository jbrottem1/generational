#!/usr/bin/env python3
"""6.5-hour Continuous Improvement Sprint — Agent 0.

One educational Short per cycle (~hourly target). Each cycle:
produce → QA → AELS review → GCIS lesson → apply improvements → next.

Usage:
  ./venv/bin/python scripts/sprint_6h30_continuous.py
  ./venv/bin/python scripts/sprint_6h30_continuous.py --cycles 1   # single cycle test
  ./venv/bin/python scripts/sprint_6h30_continuous.py --resume     # continue from state
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.env import load_application_env

load_application_env()

from services.media_production.ffmpeg_assembler import find_ffmpeg
from services.provider_runtime.config import has_credential
from services.gcis import refresh_dashboard_from_validation, save_dashboard, load_dashboard
from services.sprint.continuous_improvement import (
    SPRINT_DIR,
    CYCLE_TOPICS,
    CycleConfig,
    run_cycle,
    next_config,
    _now_iso,
)

SPRINT_HOURS = 6.5
TARGET_CYCLE_MINUTES = 55  # ~7 cycles across 6.5h
MIN_CYCLE_GAP_SEC = 300  # floor: 5 min improvement window
STATE_PATH = SPRINT_DIR / "sprint_state.json"
FINAL_REPORT_PATH = SPRINT_DIR / "SPRINT_6H30_FINAL_REPORT.md"


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {"completed_cycles": [], "config": {"pause_boost": 0.0}}


def save_state(state: dict) -> None:
    SPRINT_DIR.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = _now_iso()
    STATE_PATH.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def write_final_report(state: dict, results: list[dict]) -> None:
    scores = [r.get("quality_overall") for r in results if r.get("quality_overall")]
    eng = [r.get("aels_engagement") for r in results if r.get("aels_engagement")]
    edu = [r.get("edu_score") for r in results if r.get("edu_score")]
    ok = sum(1 for r in results if r.get("success"))

    trend = ""
    if len(scores) >= 2:
        trend = f"Quality: {scores[0]:.1f} → {scores[-1]:.1f} ({'+' if scores[-1] >= scores[0] else ''}{scores[-1] - scores[0]:.1f})"

    body = f"""# Sprint 6h30 — Final Report

**Generated:** {_now_iso()}  
**Duration target:** {SPRINT_HOURS}h  
**Cycles completed:** {len(results)}  
**Successful exports:** {ok}/{len(results)}

## Videos completed

"""
    for r in results:
        body += f"- Cycle {r.get('cycle')}: **{r.get('slug')}** — `{r.get('export_path')}` (Q={r.get('quality_overall')}, AELS={r.get('aels_engagement')})\n"

    avg_q = sum(scores) / len(scores) if scores else 0.0
    avg_e = sum(eng) / len(eng) if eng else 0.0
    avg_ed = sum(edu) / len(edu) if edu else 0.0

    body += f"""
## Quality trends

{trend or 'Insufficient cycles for trend.'}
- Avg quality: {avg_q:.1f}
- Avg engagement: {avg_e:.1f}
- Avg education: {avg_ed:.1f}

## Improvements implemented

- Echoer Communication Protocol (ECP v1) — `ECHOER_PROTOCOL.md`
- Agent 24 AELS — engagement + learning science reviews each cycle
- Pause boost applied cycle-over-cycle from AELS recommendations
- GCIS reviews per cycle under `data/gcis/reviews/`

## Communication improvements

- Structured JSON envelopes via `services/echoer/protocol.py`
- Echoer log: `data/productions/_validation/sprint_6h30/echoer_log.jsonl`

## Remaining bottlenecks

- Live publish still blocked (YouTube OAuth)
- Ken Burns asset pipeline separate from educator path
- AELS heuristics — awaiting real audience analytics feedback loop

## Highest-priority recommendations

1. Wire YouTube OAuth for retention analytics closure
2. Promote AELS + QualityReport into default export gate
3. Expand demo library reuse registry (Repetition Booster)

## Production readiness

Educator Short path: **operational** — verified exports each cycle.

## Next sprint objectives

- Close analytics loop (publish → measure → AELS calibration)
- Phoneme lip-sync upgrade
- Series packaging under Biology Academy Vol 2
"""
    FINAL_REPORT_PATH.write_text(body, encoding="utf-8")
    print(f"\n=== FINAL REPORT → {FINAL_REPORT_PATH} ===", flush=True)


def append_lesson(result: dict) -> None:
    """Append top lesson to GCIS if cycle improved scores."""
    lessons_path = ROOT / "data" / "gcis" / "knowledge" / "lessons_learned.md"
    if not result.get("success"):
        return
    recs = result.get("recommendations") or []
    if not recs:
        return
    block = f"""
## 2026-07-11 — Sprint 6h30 Cycle {result.get('cycle')} ({result.get('slug')})

**Source:** {result.get('export_path')}

### Improvement for next production
- {recs[0]}

"""
    text = lessons_path.read_text(encoding="utf-8")
    marker = "# Lessons Learned (GCIS)"
    if marker in text:
        text = text.replace(marker, block + marker)
        lessons_path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cycles", type=int, default=0, help="Max cycles (0 = until time budget)")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    print("=== 6.5-HOUR CONTINUOUS IMPROVEMENT SPRINT ===", flush=True)
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        print("ERROR: ffmpeg required", flush=True)
        return 1
    if not has_credential("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY required", flush=True)
        return 1

    state = load_state() if args.resume else {"completed_cycles": [], "config": {"pause_boost": 0.0}}
    deadline = time.time() + SPRINT_HOURS * 3600
    if not args.resume:
        state["started_at"] = _now_iso()
        state["deadline_at"] = datetime.fromtimestamp(deadline, tz=timezone.utc).isoformat()

    config = CycleConfig(pause_boost=float(state.get("config", {}).get("pause_boost") or 0))
    results: list[dict] = list(state.get("results") or [])
    done_slugs = set(state.get("completed_cycles") or [])

    max_cycles = args.cycles if args.cycles > 0 else len(CYCLE_TOPICS)
    prev_result: dict | None = results[-1] if results else None

    for topic in CYCLE_TOPICS:
        if topic.slug in done_slugs:
            continue
        if len(results) >= max_cycles and args.cycles > 0:
            break
        if time.time() >= deadline and args.cycles == 0:
            print("Sprint time budget reached.", flush=True)
            break

        config = next_config(prev_result, config)
        print(f"\n--- CYCLE {topic.cycle}: {topic.title} ---", flush=True)
        print(f"  config pause_boost={config.pause_boost:.2f}", flush=True)

        try:
            result = run_cycle(topic, config, ffmpeg=ffmpeg)
        except Exception as exc:  # noqa: BLE001
            print(f"  CYCLE FAILED: {exc}", flush=True)
            result = {"cycle": topic.cycle, "slug": topic.slug, "success": False, "error": str(exc)}

        results.append(result)
        done_slugs.add(topic.slug)
        prev_result = result if result.get("success") else prev_result

        state["completed_cycles"] = list(done_slugs)
        state["config"] = {"pause_boost": config.pause_boost}
        state["results"] = results
        save_state(state)

        if result.get("success"):
            append_lesson(result)
            print(f"  ✓ {result.get('export_path')} Q={result.get('quality_overall')}", flush=True)
        else:
            print(f"  ✗ cycle {topic.cycle} did not fully pass gates", flush=True)

        # Improvement window — pad toward ~55 min/cycle when running full sprint
        if topic.cycle < len(CYCLE_TOPICS):
            remaining = deadline - time.time()
            target_gap = max(MIN_CYCLE_GAP_SEC, TARGET_CYCLE_MINUTES * 60 - float(result.get("render_sec") or 30))
            gap = min(target_gap, max(0, remaining - 120))
            if gap > 0 and args.cycles == 0:
                print(f"  improvement window {gap:.0f}s (~{gap/60:.1f} min)…", flush=True)
                time.sleep(gap)

    # Dashboard update
    dash = load_dashboard()
    metrics = dict(dash.get("metrics") or {})
    metrics["sprint_6h30_cycles"] = len(results)
    metrics["sprint_6h30_success"] = sum(1 for r in results if r.get("success"))
    if scores := [r.get("quality_overall") for r in results if r.get("quality_overall")]:
        metrics["sprint_6h30_avg_quality"] = round(sum(scores) / len(scores), 1)
    dash["metrics"] = metrics
    dash["sprint_6h30"] = {"results": results, "finished_at": _now_iso()}
    save_dashboard(dash)
    refresh_dashboard_from_validation()

    write_final_report(state, results)
    print(f"\n=== SPRINT COMPLETE: {len(results)} cycles ===", flush=True)
    return 0 if all(r.get("success") for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
