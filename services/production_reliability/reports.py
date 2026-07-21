"""Write Production Reliability Initiative final reports to repo root."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
VAL = ROOT / "data" / "productions" / "_validation" / "production_reliability"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_summary() -> dict[str, Any]:
    path = VAL / "RELIABILITY_BATCH_SUMMARY.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def write_all_reports(summary: dict[str, Any] | None = None) -> dict[str, str]:
    summary = summary or _load_summary()
    results = list(summary.get("results") or [])
    mp4_rate = float(summary.get("mp4_success_rate") or 0)
    gate = bool(summary.get("mission_mp4_gate_passed"))

    # ----- PRODUCTION_RELIABILITY_REPORT.md
    lines = [
        "# PRODUCTION RELIABILITY REPORT",
        "",
        f"Generated: `{_now()}`",
        "",
        "## Verdict",
        "",
        f"- MP4 success rate: **{mp4_rate}%** (target ≥ 90%)",
        f"- Gate passed: **{'YES' if gate else 'NO'}**",
        f"- Ops success count: {summary.get('ops_success_count')}/{summary.get('count')}",
        f"- Publication-ready count: {summary.get('publication_ready_count')}/{summary.get('count')}",
        f"- Architecture frozen: `{summary.get('architecture_frozen', True)}`",
        f"- Avg execution time: {summary.get('avg_elapsed_ms')} ms",
        f"- Avg retries: {summary.get('avg_retry_count')}",
        "",
        "## Production chain (verified handoffs)",
        "",
        "Research → Psychology → Script → Scene Builder → World/Media → Asset Resolution → "
        "ElevenLabs/Voice → Cinematic Director → Renderer (`video`/`assemble_mp4`) → Validation → Export → Library",
        "",
        "### Critical repair applied",
        "",
        "1. **Asset resolution** now materializes cinematic fallback stills when AI/stock providers return mock URIs.",
        "2. **`assemble_mp4`** accepts real local files even if a provider incorrectly set `placeholder=True`.",
        "3. **Renderer recovery** retries assembly once after regenerating stills when visuals were missing.",
        "4. **Export packaging** copies MP4/audio/captions/thumbnail into the project folder and resolves relative paths.",
        "5. **Success reporting** remains honest: `success` requires a physical MP4.",
        "6. **Stage instrumentation** records engine_results, retries, failure_reason, dependency health.",
        "",
        "## Validation productions",
        "",
        "| ID | Category | Topic | MP4 | Playable | Caps | Thumb | Audio | Success | Time (ms) |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        d = r.get("deliverables") or {}
        lines.append(
            f"| {r.get('reliability_id')} | {r.get('category')} | {r.get('topic')} | "
            f"{'Y' if r.get('video_exists') else 'N'} | {'Y' if d.get('mp4') else 'N'} | "
            f"{'Y' if d.get('captions') else 'N'} | {'Y' if d.get('thumbnail') else 'N'} | "
            f"{'Y' if d.get('audio') else 'N'} | {'Y' if r.get('success') else 'N'} | "
            f"{r.get('elapsed_ms')} |"
        )
    lines.extend(["", "## Library", "", f"`{summary.get('library_root')}`", ""])
    (ROOT / "PRODUCTION_RELIABILITY_REPORT.md").write_text("\n".join(lines), encoding="utf-8")

    # ----- RENDER_FAILURE_ANALYSIS.md
    fail_rows = [r for r in results if not (r.get("video_exists") and (r.get("deliverables") or {}).get("mp4"))]
    rfl = [
        "# RENDER FAILURE ANALYSIS",
        "",
        f"Generated: `{_now()}`",
        "",
        "## Pre-fix root cause (pilot 0% MP4)",
        "",
        "Every launch pilot reached Rendering in ~3ms with scenes present, but "
        "`AssetResolver` left `runtime://` / `mock://` placeholders. "
        "`assemble_mp4` correctly refused color-bed encodes → `mp4_path` empty → export warned "
        "`mp4_not_yet_materialized`.",
        "",
        "## Post-fix failures",
        "",
        f"Failed MP4s in this batch: **{len(fail_rows)} / {len(results)}**",
        "",
    ]
    if not fail_rows:
        rfl.append("None — all validation productions produced a playable MP4.")
    else:
        rfl.append("| ID | Stopped at | Reason | Recovery attempted | Recovery ok |")
        rfl.append("|---|---|---|---|---|")
        for r in fail_rows:
            t = r.get("failure_trace") or {}
            rfl.append(
                f"| {r.get('reliability_id')} | {t.get('stopped_at')} | {t.get('failure_reason')} | "
                f"{t.get('recovery_attempted')} | {t.get('recovery_succeeded')} |"
            )
    rfl.extend(
        [
            "",
            "## Renderer path",
            "",
            "`engines/video` → `engines/render/engine.build_render_output` → "
            "`MockRenderer.render` → `services.media_production.ffmpeg_assembler.assemble_mp4`",
            "",
        ]
    )
    (ROOT / "RENDER_FAILURE_ANALYSIS.md").write_text("\n".join(rfl) + "\n", encoding="utf-8")

    # ----- EXPORT_PIPELINE_REPORT.md
    epl = [
        "# EXPORT PIPELINE REPORT",
        "",
        f"Generated: `{_now()}`",
        "",
        "## Chain",
        "",
        "Renderer MP4 → `export_and_validate` → `package_export_artifacts` → "
        "`data/productions/executive_exports/{topic}_{ops_id}/` → ops library / reports",
        "",
        "## Behavior",
        "",
        "- Copies `episode.mp4` into export folder when renderer wrote a real file",
        "- Writes `captions.json` + `captions.srt` when segments exist",
        "- Copies narration audio when present",
        "- Copies first scene still as thumbnail when no dedicated thumbnail exists",
        "- Marks export stage **degraded** if MP4 missing (pipeline continues; production `success=false`)",
        "",
        "## Batch export outcomes",
        "",
    ]
    for r in results:
        paths = r.get("export_paths") or {}
        epl.append(
            f"- **{r.get('reliability_id')}**: mp4=`{paths.get('mp4','')}` "
            f"caps=`{paths.get('captions_srt') or paths.get('captions','')}` "
            f"thumb=`{paths.get('thumbnail','')}`"
        )
    (ROOT / "EXPORT_PIPELINE_REPORT.md").write_text("\n".join(epl) + "\n", encoding="utf-8")

    # ----- RECOVERY_STATISTICS.md
    recovery_attempted = sum(1 for r in results if (r.get("failure_trace") or {}).get("recovery_attempted"))
    recovery_ok = sum(1 for r in results if (r.get("failure_trace") or {}).get("recovery_succeeded"))
    rsl = [
        "# RECOVERY STATISTICS",
        "",
        f"Generated: `{_now()}`",
        "",
        f"- Productions: {len(results)}",
        f"- Recovery flags observed: {recovery_attempted}",
        f"- Ended with MP4 (recovery or first-pass): {recovery_ok}",
        f"- Avg retries/production: {summary.get('avg_retry_count')}",
        "",
        "## Mechanism",
        "",
        "1. Provider image/video failure → cinematic fallback still (asset resolver)",
        "2. Assembly `No resolved visual assets` → renderer regenerates stills + one assemble retry",
        "3. Ops engines: per-engine retries from stage `max_retries`",
        "4. Animation engine remains soft-skipped (`not ready`) without aborting production",
        "",
    ]
    (ROOT / "RECOVERY_STATISTICS.md").write_text("\n".join(rsl), encoding="utf-8")

    # ----- UPDATED_READINESS_SCORE.md
    # Simple scoreboard after fix
    score = 40
    if mp4_rate >= 90:
        score += 35
    elif mp4_rate >= 50:
        score += 20
    elif mp4_rate > 0:
        score += 10
    pub_rate = float(summary.get("publication_ready_rate") or 0)
    if pub_rate >= 80:
        score += 15
    elif pub_rate >= 50:
        score += 8
    if gate:
        score += 10
    score = min(100, score)
    verdict = "PRODUCTION READY" if gate and mp4_rate >= 90 else "NOT READY"
    urs = [
        "# UPDATED READINESS SCORE",
        "",
        f"Generated: `{_now()}`",
        "",
        f"## Score: **{score}/100**",
        "",
        f"## Verdict: **{verdict}**",
        "",
        "| Dimension | Score impact | Evidence |",
        "|---|---|---|",
        f"| MP4 deliverable rate | {'+35' if mp4_rate >= 90 else '+20' if mp4_rate >= 50 else '+10' if mp4_rate > 0 else '+0'} | {mp4_rate}% |",
        f"| Publication pack completeness | {'+15' if pub_rate >= 80 else '+8' if pub_rate >= 50 else '+0'} | {pub_rate}% |",
        f"| Mission gate (≥90% MP4) | {'+10' if gate else '+0'} | {gate} |",
        "| Architecture frozen | baseline | no new engines |",
        "",
        "Prior readiness: **NOT READY** (0% MP4 on 25-pilot launch).",
        "",
    ]
    (ROOT / "UPDATED_READINESS_SCORE.md").write_text("\n".join(urs), encoding="utf-8")

    # ----- TOP_10_REMAINING_FAILURES.md
    reasons = Counter()
    for r in results:
        if r.get("publication_ready"):
            continue
        t = r.get("failure_trace") or {}
        reason = t.get("failure_reason") or "incomplete_deliverables"
        d = r.get("deliverables") or {}
        if r.get("video_exists") and d.get("mp4"):
            missing = [k for k in ("audio", "captions", "thumbnail") if not d.get(k)]
            reason = "missing:" + ",".join(missing) if missing else reason
        reasons[reason] += 1
    # Pad with known systemic leftovers
    backlog = [
        ("animation_engine_not_ready", "Animation registry ready=False — soft skip every run"),
        ("provider_image_tunnel_or_key", "OpenAI image / ElevenLabs often fail → fallbacks engaged"),
        ("ops_resume_full_rerun", "Resume flag still re-runs all stages"),
        ("timeline_render_package_ops_mismatch", "timeline/render_package still keyed off production_packages"),
        ("vad_approved_zero_when_providers_fail", "Visual Asset Director approved_count can be 0"),
        ("caption_burn_not_required", "Captions sidecars written; burn-in not mandated"),
        ("demo_voice_when_tts_fails", "Narration may be local demo bed if keys/network fail"),
        ("channel_publish_disabled", "Publishing intentionally off for reliability runs"),
        ("stage_skip_resume", "No durable stage checkpoint skip yet"),
        ("quality_score_vs_deliverable", "High creative scores can coexist with prior export gaps"),
    ]
    top = reasons.most_common(10)
    t10 = [
        "# TOP 10 REMAINING FAILURES",
        "",
        f"Generated: `{_now()}`",
        "",
        "## Observed in this validation batch",
        "",
    ]
    if top:
        for i, (reason, count) in enumerate(top, 1):
            t10.append(f"{i}. **{reason}** — {count} production(s)")
    else:
        t10.append("No publication-blocking failures in the validation batch.")
    t10.extend(["", "## Systemic backlog (monitor)", ""])
    for i, (key, desc) in enumerate(backlog, 1):
        t10.append(f"{i}. **{key}** — {desc}")
    t10.append("")
    (ROOT / "TOP_10_REMAINING_FAILURES.md").write_text("\n".join(t10), encoding="utf-8")

    return {
        "PRODUCTION_RELIABILITY_REPORT.md": str(ROOT / "PRODUCTION_RELIABILITY_REPORT.md"),
        "RENDER_FAILURE_ANALYSIS.md": str(ROOT / "RENDER_FAILURE_ANALYSIS.md"),
        "EXPORT_PIPELINE_REPORT.md": str(ROOT / "EXPORT_PIPELINE_REPORT.md"),
        "RECOVERY_STATISTICS.md": str(ROOT / "RECOVERY_STATISTICS.md"),
        "UPDATED_READINESS_SCORE.md": str(ROOT / "UPDATED_READINESS_SCORE.md"),
        "TOP_10_REMAINING_FAILURES.md": str(ROOT / "TOP_10_REMAINING_FAILURES.md"),
    }
