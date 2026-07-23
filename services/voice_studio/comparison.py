"""Full-account voice comparison for Voice Studio (no publishing)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.elevenlabs.voices import list_elevenlabs_voices
from services.voice_studio.profiles import list_profile_catalog
from services.voice_studio.recommend import apply_recommendations_to_config, recommend_voices_for_profiles
from services.voice_studio.sampler import COMPARISON_TEXT, generate_voice_sample
from services.voice_studio.scoring import educational_shorts_score, score_voice_dimensions

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "data" / "voice_studio" / "comparisons"


def run_voice_comparison(
    *,
    text: str = "",
    apply_config: bool = True,
    limit: int = 100,
) -> dict[str, Any]:
    """Synthesize the same text with every available voice; score, rank, recommend."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = OUT_DIR / f"run_{stamp}"
    samples_dir = run_dir / "samples"
    samples_dir.mkdir(parents=True, exist_ok=True)

    listed = list_elevenlabs_voices(limit=limit)
    if not listed.get("ok"):
        return {"ok": False, "error": listed.get("error") or "voice list failed", "voices": []}

    voices = listed.get("voices") or []
    script = (text or COMPARISON_TEXT).strip()
    rows: list[dict[str, Any]] = []

    for voice in voices:
        sample = generate_voice_sample(voice, text=script, out_dir=samples_dir, mode="comparison")
        scored = score_voice_dimensions(voice, audio_path=sample.get("path") or "")
        scored["shorts_score"] = educational_shorts_score(scored)
        scored["sample"] = {
            "ok": sample.get("ok"),
            "path": sample.get("path"),
            "duration_sec": sample.get("duration_sec"),
            "provider": sample.get("provider"),
            "placeholder": sample.get("placeholder"),
            "error": sample.get("error") or "",
            "audio_qa_ok": (sample.get("audio_qa") or {}).get("ok"),
        }
        rows.append(scored)

    rows.sort(key=lambda r: (-float(r.get("shorts_score") or 0), -float(r.get("overall") or 0)))
    for i, row in enumerate(rows, start=1):
        row["rank"] = i

    recommendations = recommend_voices_for_profiles(rows, top_n=3)
    applied = {}
    if apply_config:
        applied = apply_recommendations_to_config(recommendations, write_default=True)

    report = {
        "ok": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "publishing": "disabled",
        "text": script,
        "voice_count": len(rows),
        "voices_source": listed.get("source"),
        "profiles": list_profile_catalog(),
        "ranking": [
            {
                "rank": r.get("rank"),
                "name": r.get("name"),
                "voice_id": r.get("voice_id"),
                "overall": r.get("overall"),
                "shorts_score": r.get("shorts_score"),
                "dimensions": r.get("dimensions"),
                "sample_path": (r.get("sample") or {}).get("path"),
                "sample_ok": (r.get("sample") or {}).get("ok"),
                "duration_sec": (r.get("sample") or {}).get("duration_sec"),
            }
            for r in rows
        ],
        "recommendations": recommendations,
        "config_applied": applied,
        "artifacts_dir": str(run_dir),
    }

    (run_dir / "COMPARISON_REPORT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (run_dir / "COMPARISON_REPORT.md").write_text(_to_markdown(report), encoding="utf-8")
    # Convenience copies at voice_studio root
    latest = OUT_DIR / "LATEST_COMPARISON_REPORT.json"
    latest_md = ROOT / "VOICE_COMPARISON_REPORT.md"
    latest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    latest_md.write_text(_to_markdown(report), encoding="utf-8")
    report["latest_report_json"] = str(latest)
    report["latest_report_md"] = str(latest_md)
    return report


def _to_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Voice Studio Comparison Report",
        "",
        f"Generated: `{report.get('generated_at')}`",
        "",
        "Publishing: **disabled**",
        "",
        "## Comparison text",
        "",
        f"> {report.get('text')}",
        "",
        f"Voices scored: **{report.get('voice_count')}**",
        "",
        "## Ranking (all voices)",
        "",
        "| Rank | Voice | Overall | Shorts score | Clarity | Edu tone | Energy | Professional | Long-form |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in report.get("ranking") or []:
        d = r.get("dimensions") or {}
        lines.append(
            f"| {r.get('rank')} | {r.get('name')} | {r.get('overall')} | {r.get('shorts_score')} | "
            f"{d.get('clarity')} | {d.get('educational_tone')} | {d.get('energy')} | "
            f"{d.get('professionalism')} | {d.get('long_form_comfort')} |"
        )

    lines += ["", "## Top 3 for educational YouTube Shorts", ""]
    for row in (report.get("recommendations") or {}).get("educational_youtube_shorts_top3") or []:
        lines.append(
            f"{row.get('rank')}. **{row.get('name')}** (`{row.get('voice_id')}`) — shorts_score={row.get('shorts_score')}"
        )

    lines += ["", "## Recommended voice per narrator profile", ""]
    by_profile = (report.get("recommendations") or {}).get("by_profile") or {}
    for key, rows in by_profile.items():
        best = rows[0] if rows else {}
        lines.append(
            f"- **{key}**: {best.get('name')} (`{best.get('voice_id')}`) fit={best.get('profile_fit')}"
        )

    lines += [
        "",
        "## Configuration",
        "",
        "Profile mappings written to `data/voice_studio/PROFILE_VOICES.json` when apply_config=true.",
        "To change defaults without code edits, update that JSON or set `ELEVENLABS_DEFAULT_VOICE_ID` / `ELEVENLABS_VOICE_*` in `.env`.",
        "",
        f"Artifacts: `{report.get('artifacts_dir')}`",
        "",
    ]
    return "\n".join(lines) + "\n"
