"""RC1 certification — five complete production runs, no architecture changes."""

from __future__ import annotations

import json
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

from core.env import load_application_env

load_application_env()

from core.script_models import PIPELINE_STAGE_KEYS
from services.asset_production.executor import run_asset_production
from services.media_production import ffmpeg_available
from services.provider_runtime.config import has_credential

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "data" / "productions" / "_validation" / "rc1"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# Rough public list prices for estimation when ledger is empty (USD).
TTS_PER_1K_CHARS = 0.015  # OpenAI TTS
CHAT_PER_RUN = 0.01  # gpt-4o-mini short script estimate
IMAGE_PER = 0.04  # dall-e-3 standard estimate

TOPICS = [
    {
        "asset_id": "rc1_bioluminescence_001",
        "title": "Secrets of Bioluminescence",
        "hook": "The ocean is hiding living light — and science just explained why.",
        "description": "A short educational video revealing how and why animals glow in the dark.",
        "hashtags": ["#bioluminescence", "#ocean", "#science", "#shorts"],
        "cta": "Follow for more nature secrets",
        "niche": "science",
        "music_style": "curious ambient underwater",
    },
    {
        "asset_id": "rc1_black_holes_001",
        "title": "Black Holes Explained",
        "hook": "Nothing escapes a black hole — except the truth about how they work.",
        "description": "A 60-second explainer on gravity, event horizons, and spacetime.",
        "hashtags": ["#blackholes", "#space", "#science", "#shorts"],
        "cta": "Follow for more cosmic science",
        "niche": "science",
        "music_style": "deep space ambient",
    },
    {
        "asset_id": "rc1_octopuses_001",
        "title": "Why Octopuses Are So Intelligent",
        "hook": "An octopus has nine brains — and that is only the start.",
        "description": "How octopuses solve puzzles, use tools, and rethink intelligence.",
        "hashtags": ["#octopus", "#animals", "#science", "#shorts"],
        "cta": "Follow for more animal intelligence",
        "niche": "science",
        "music_style": "curious underwater pulse",
    },
    {
        "asset_id": "rc1_rome_001",
        "title": "The History of Rome in 60 Seconds",
        "hook": "From a muddy village to an empire that shaped the world — in one minute.",
        "description": "A rapid tour of Rome from founding myths to fall.",
        "hashtags": ["#rome", "#history", "#shorts"],
        "cta": "Follow for more history in 60 seconds",
        "niche": "history",
        "music_style": "epic historical underscore",
    },
    {
        "asset_id": "rc1_trees_001",
        "title": "How Trees Communicate Underground",
        "hook": "Forests talk — through a hidden fungal internet under your feet.",
        "description": "The wood-wide web: how trees share nutrients and warnings underground.",
        "hashtags": ["#trees", "#nature", "#science", "#shorts"],
        "cta": "Follow for more nature science",
        "niche": "science",
        "music_style": "forest ambient",
    },
]

REQUIRED_ARTIFACTS = (
    "idea.json",
    "script.json",
    "scenes.json",
    "visual_prompts.json",
    "voice.mp3",
    "captions.srt",
    "timeline.json",
    "render.mp4",
    "metadata.json",
    "production_report.json",
)

CORE_STAGES = (
    "idea",
    "script",
    "scenes",
    "visual_prompts",
    "voice",
    "render",
    "quality",
    "export",
)


def _estimate_cost(result: dict, voice_chars: int, image_count: int) -> dict:
    tts = round((voice_chars / 1000.0) * TTS_PER_1K_CHARS, 4)
    chat = CHAT_PER_RUN
    images = round(image_count * IMAGE_PER, 4)
    return {
        "estimated_cost_usd": round(tts + chat + images, 4),
        "breakdown": {
            "openai_tts_usd": tts,
            "openai_chat_usd": chat,
            "openai_images_usd": images,
        },
        "note": "Estimate from public list prices; ledger may be empty for direct connectors.",
    }


def _stage_rows(result: dict) -> list[dict]:
    stages = ((result.get("production_pipeline") or {}).get("stages") or {})
    rows = []
    for key in PIPELINE_STAGE_KEYS:
        raw = stages.get(key) or {}
        if isinstance(raw, str):
            raw = {"status": raw}
        rows.append(
            {
                "stage": key,
                "status": raw.get("status"),
                "retry_count": int(raw.get("retry_count") or 0),
                "execution_time_sec": raw.get("execution_time_sec") or 0,
                "artifacts": raw.get("artifacts") or [],
                "error": raw.get("error") or "",
            }
        )
    return rows


def _verify_artifacts(asset_id: str) -> dict:
    prod = ROOT / "data" / "productions" / asset_id
    missing = []
    present = []
    for name in REQUIRED_ARTIFACTS:
        path = prod / name
        if path.exists() and path.stat().st_size > 0:
            present.append(name)
        else:
            missing.append(name)
    files = sorted(str(p.relative_to(ROOT)) for p in prod.rglob("*") if p.is_file()) if prod.exists() else []
    return {"present": present, "missing": missing, "files": files, "file_count": len(files)}


def run_one(topic: dict, index: int) -> dict:
    project = {
        "name": f"RC1 — {topic['title']}",
        "model": "gpt-4o-mini",
        "niche": topic.get("niche") or "science",
        "platform": "youtube_shorts",
        "provider": "openai",
    }
    events: list[dict] = []
    recovery_events: list[dict] = []
    t0 = time.perf_counter()

    def on_progress(event: dict) -> None:
        slim = {k: v for k, v in event.items() if k != "asset"}
        slim["at"] = datetime.now(timezone.utc).isoformat()
        events.append(slim)
        retry = int(event.get("retry_count") or 0)
        status = str(event.get("status") or "")
        if retry > 0 or status == "failed":
            recovery_events.append(slim)
        print(
            f"  [{index}/5][{status}] {event.get('label')}: {event.get('message')} "
            f"(retry={retry}, t={event.get('execution_time_sec')}s)"
        )

    print(f"\n=== RUN {index}/5: {topic['title']} ===")
    try:
        result = run_asset_production(topic, project, on_progress=on_progress, max_images=4)
    except Exception as exc:  # noqa: BLE001
        result = {
            **topic,
            "production_ok": False,
            "production_error": str(exc),
            "traceback": traceback.format_exc(),
        }

    elapsed = round(time.perf_counter() - t0, 2)
    rows = _stage_rows(result)
    arts = _verify_artifacts(topic["asset_id"])
    render = result.get("render_package") or {}
    qc = result.get("production_qc") or {}
    voice = result.get("voice_package") or {}
    script = result.get("video_script") or {}
    voiceover = str(script.get("full_voiceover") or result.get("script") or "")
    images = result.get("generated_images") or []
    real_images = [i for i in images if i.get("path") and not i.get("placeholder")]
    mp4 = render.get("mp4_path") or result.get("mp4_path") or ""
    mp4_bytes = 0
    if mp4:
        mp = Path(mp4) if Path(mp4).is_absolute() else ROOT / mp4
        if mp.exists():
            mp4_bytes = mp.stat().st_size

    retries = sum(int(r.get("retry_count") or 0) for r in rows)
    failed = [r for r in rows if r.get("status") == "failed"]
    core_ok = all(
        next((r for r in rows if r["stage"] == key), {}).get("status") in {"completed", "skipped"}
        for key in CORE_STAGES
    )
    # Core stages must be completed (not skipped) for RC1 certification of the path.
    core_completed = all(
        next((r for r in rows if r["stage"] == key), {}).get("status") == "completed"
        for key in CORE_STAGES
    )
    cost = _estimate_cost(result, len(voiceover), len(real_images))
    apis = []
    if has_credential("OPENAI_API_KEY"):
        apis.append("openai_chat")
        apis.append("openai_tts")
        if real_images:
            apis.append("openai_images")

    success = bool(
        result.get("production_ok")
        and core_completed
        and qc.get("passed")
        and mp4_bytes > 500
        and not render.get("mock", True)
        and not arts["missing"]
        and not failed
    )

    report = {
        "run_index": index,
        "topic": topic["title"],
        "asset_id": topic["asset_id"],
        "runtime_sec": elapsed,
        "production_ok": bool(result.get("production_ok")),
        "production_error": result.get("production_error") or "",
        "certification_success": success,
        "core_stages_ok": core_ok,
        "core_stages_completed": core_completed,
        "qc_score": qc.get("score"),
        "qc_passed": qc.get("passed"),
        "retry_count_total": retries,
        "failed_stages": failed,
        "recovery_events": recovery_events,
        "stages": rows,
        "apis_called": apis,
        "cost": cost,
        "mp4_path": mp4,
        "mp4_bytes": mp4_bytes,
        "mock_render": bool(render.get("mock", True)),
        "voice_path": voice.get("path") or "",
        "captions": result.get("caption_file") or "",
        "thumbnail": result.get("thumbnail_path") or "",
        "artifacts": arts,
        "progress_event_count": len(events),
        "publish_status": (result.get("publish_package") or {}).get("status"),
    }

    out = REPORT_DIR / f"run_{index:02d}_{topic['asset_id']}.json"
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(
        f"  RESULT ok={success} runtime={elapsed}s qc={qc.get('score')} "
        f"mp4_bytes={mp4_bytes} retries={retries} missing={arts['missing']}"
    )
    return report


def aggregate(runs: list[dict], batch_runtime: float) -> dict:
    successes = [r for r in runs if r.get("certification_success")]
    n = len(runs) or 1
    avg_runtime = round(sum(r.get("runtime_sec") or 0 for r in runs) / n, 2)
    avg_cost = round(sum((r.get("cost") or {}).get("estimated_cost_usd") or 0 for r in runs) / n, 4)
    total_cost = round(sum((r.get("cost") or {}).get("estimated_cost_usd") or 0 for r in runs), 4)
    total_retries = sum(r.get("retry_count_total") or 0 for r in runs)
    recovery_count = sum(len(r.get("recovery_events") or []) for r in runs)
    failed_stage_names: dict[str, int] = {}
    for r in runs:
        for f in r.get("failed_stages") or []:
            failed_stage_names[f["stage"]] = failed_stage_names.get(f["stage"], 0) + 1
        if not r.get("certification_success") and r.get("production_error"):
            failed_stage_names["_error"] = failed_stage_names.get("_error", 0) + 1

    common_failures = sorted(failed_stage_names.items(), key=lambda x: -x[1])
    success_rate = round(100.0 * len(successes) / n, 1)
    avg_qc = round(
        sum(float(r.get("qc_score") or 0) for r in runs) / n,
        1,
    )

    remaining_integrations = []
    if not has_credential("ELEVENLABS_API_KEY"):
        remaining_integrations.append("ElevenLabs (music/SFX)")
    if not (has_credential("RUNWAY_API_KEY") or has_credential("FAL_KEY")):
        remaining_integrations.append("Runway/Fal (video clips)")
    if not has_credential("YOUTUBE_ACCESS_TOKEN"):
        remaining_integrations.append("YouTube OAuth (live publish)")

    remaining_blockers = list(remaining_integrations)
    image_gaps = [r["topic"] for r in runs if not r.get("thumbnail")]
    if image_gaps:
        remaining_blockers.append(
            f"Thumbnails missing on {len(image_gaps)}/{n} runs (image gen optional for RC1 core path)"
        )

    # Readiness: core export path proven across batch; deduct for missing integrations.
    readiness = 70
    readiness += min(20, int(success_rate * 0.2))
    if success_rate == 100:
        readiness = max(readiness, 92)
    if remaining_integrations:
        readiness = min(readiness, 94)
    if success_rate < 100:
        readiness = min(readiness, int(60 + success_rate * 0.3))

    rc1_ready = success_rate == 100.0 and all(r.get("certification_success") for r in runs)

    return {
        "report_type": "Release Candidate 1 Certification",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "topics_requested": 5,
        "runs_completed": len(runs),
        "success_rate_percent": success_rate,
        "rc1_ready": rc1_ready,
        "declaration": (
            "Release Candidate 1 Ready"
            if rc1_ready
            else "NOT Release Candidate 1 Ready — production test revealed issues"
        ),
        "batch_runtime_sec": batch_runtime,
        "average_runtime_sec": avg_runtime,
        "average_cost_usd": avg_cost,
        "total_estimated_cost_usd": total_cost,
        "average_qc_score": avg_qc,
        "total_retries": total_retries,
        "recovery_events": recovery_count,
        "common_failures": [{"stage": k, "count": v} for k, v in common_failures],
        "remaining_blockers": remaining_blockers,
        "remaining_integrations": remaining_integrations,
        "production_readiness_percent": readiness,
        "preflight": {
            "ffmpeg": ffmpeg_available(),
            "openai": has_credential("OPENAI_API_KEY"),
            "elevenlabs": has_credential("ELEVENLABS_API_KEY"),
            "runway": has_credential("RUNWAY_API_KEY"),
            "fal": has_credential("FAL_KEY"),
            "youtube_oauth": has_credential("YOUTUBE_ACCESS_TOKEN"),
        },
        "runs": runs,
        "recommendation": (
            "Freeze feature work. Proceed to RC1 packaging / staging publish dry-run with OAuth."
            if rc1_ready
            else "Repair failed stages only, re-run failed topics, then re-certify."
        ),
    }


def write_markdown(agg: dict) -> Path:
    lines = [
        "# Release Candidate 1 Report",
        "",
        f"**Generated:** {agg['generated_at']}",
        f"**Declaration:** {agg['declaration']}",
        f"**Success rate:** {agg['success_rate_percent']}% ({sum(1 for r in agg['runs'] if r.get('certification_success'))}/{agg['runs_completed']})",
        f"**Production readiness:** {agg['production_readiness_percent']}%",
        "",
        "## Aggregate metrics",
        "",
        f"| Metric | Value |",
        f"|---|---|",
        f"| Batch runtime | {agg['batch_runtime_sec']}s |",
        f"| Average runtime | {agg['average_runtime_sec']}s |",
        f"| Average estimated cost | ${agg['average_cost_usd']} |",
        f"| Total estimated cost | ${agg['total_estimated_cost_usd']} |",
        f"| Average QC score | {agg['average_qc_score']} |",
        f"| Total retries | {agg['total_retries']} |",
        f"| Recovery events | {agg['recovery_events']} |",
        "",
        "## Per-run results",
        "",
        "| # | Topic | OK | Runtime (s) | Cost ($) | Retries | QC | MP4 bytes | Failed |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in agg["runs"]:
        failed = ",".join(f["stage"] for f in (r.get("failed_stages") or [])) or "—"
        lines.append(
            f"| {r['run_index']} | {r['topic']} | {r.get('certification_success')} | "
            f"{r.get('runtime_sec')} | {(r.get('cost') or {}).get('estimated_cost_usd')} | "
            f"{r.get('retry_count_total')} | {r.get('qc_score')} | {r.get('mp4_bytes')} | {failed} |"
        )
    lines.extend(
        [
            "",
            "## Common failures",
            "",
        ]
    )
    if agg["common_failures"]:
        for item in agg["common_failures"]:
            lines.append(f"- `{item['stage']}` × {item['count']}")
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Remaining integrations",
            "",
        ]
    )
    for item in agg["remaining_integrations"] or ["None"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Remaining blockers",
            "",
        ]
    )
    for item in agg["remaining_blockers"] or ["None"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Recommendation",
            "",
            agg["recommendation"],
            "",
        ]
    )
    path = REPORT_DIR / "RC1_RELEASE_CANDIDATE_REPORT.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main() -> dict:
    print("=== RC1 PREFLIGHT ===")
    print("ffmpeg", ffmpeg_available())
    for env in [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "ELEVENLABS_API_KEY",
        "RUNWAY_API_KEY",
        "FAL_KEY",
        "YOUTUBE_ACCESS_TOKEN",
    ]:
        print(f"  {env}: {'SET' if has_credential(env) else 'MISSING'}")

    if not has_credential("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY required for RC1 certification")
    if not ffmpeg_available():
        raise SystemExit("ffmpeg required for RC1 certification")

    batch_t0 = time.perf_counter()
    runs: list[dict] = []
    for i, topic in enumerate(TOPICS, start=1):
        runs.append(run_one(topic, i))
    batch_runtime = round(time.perf_counter() - batch_t0, 2)

    agg = aggregate(runs, batch_runtime)
    json_path = REPORT_DIR / "RC1_RELEASE_CANDIDATE_REPORT.json"
    json_path.write_text(json.dumps(agg, indent=2, default=str), encoding="utf-8")
    md_path = write_markdown(agg)

    print("\n=== RC1 CERTIFICATION COMPLETE ===")
    print("declaration:", agg["declaration"])
    print("success_rate:", agg["success_rate_percent"])
    print("avg_runtime:", agg["average_runtime_sec"])
    print("avg_cost:", agg["average_cost_usd"])
    print("readiness:", agg["production_readiness_percent"])
    print("report_json:", json_path)
    print("report_md:", md_path)
    return agg


if __name__ == "__main__":
    main()
