"""Controlled variant production packages — reuses ElevenLabs + ffmpeg; no auto-publish."""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from services.creative_performance_lab.store import experiment_path
from services.elevenlabs.validation import validate_narration_audio
from services.media_production.voice import synthesize_voice
from services.voice_studio.config_store import get_configured_voice_id

ROOT = Path(__file__).resolve().parents[2]

# Shared body for octopus experiment — factual core held constant
OCTOPUS_BODY = (
    "An octopus has three hearts. Two push blood through the gills. "
    "The third pumps blood to the rest of the body. "
    "When it swims, the systemic heart nearly stops — which is why octopuses prefer crawling. "
    "Blue copper blood and distributed intelligence make this animal even stranger. "
    "Follow for the next underwater myth we'll unpack."
)

HOOKS = {
    "A": {
        "style": "curiosity_gap",
        "hook": "You've seen an octopus move — but almost nobody asks why its blood system is built like this.",
        "title": "Why Octopuses Have Three Hearts",
    },
    "B": {
        "style": "counterintuitive_fact",
        "hook": "Stop. An octopus has three hearts — and one of them basically shuts down when it swims.",
        "title": "An Octopus Has Three Hearts — Here's Why",
    },
    "C": {
        "style": "immediate_visual_payoff",
        "hook": "Watch this: three hearts, blue blood, and a body that thinks with its arms.",
        "title": "Three Hearts. Blue Blood. One Octopus.",
    },
}


def build_controlled_hook_scripts() -> list[dict[str, Any]]:
    """Return A/B/C scripts differing only in hook structure/wording."""
    rows = []
    for label, meta in HOOKS.items():
        script = f"{meta['hook']} {OCTOPUS_BODY}".strip()
        rows.append(
            {
                "label": label,
                "hook_style": meta["style"],
                "hook": meta["hook"],
                "title": meta["title"],
                "script": script,
                "body_constant": OCTOPUS_BODY,
                "cta": "Follow for the next underwater myth we'll unpack.",
            }
        )
    return rows


def produce_variant_package(
    experiment_id: str,
    variant: dict[str, Any],
    *,
    platform: str = "youtube_shorts",
    duration_target_sec: float = 45.0,
    narrator: str = "professor",
    voice_id: str = "",
) -> dict[str, Any]:
    """Build one complete package: script, narration, captions, thumbnail, MP4, reports."""
    label = str(variant.get("label") or "A")
    out_dir = experiment_path(experiment_id).parent / f"variant_{label}"
    out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    vid = (voice_id or get_configured_voice_id(narrator) or "").strip()
    synth = synthesize_voice(
        str(variant.get("script") or ""),
        profile={
            "provider_voice_id": vid,
            "voice_id": vid,
            "narrator_profile": narrator,
            "profile_id": f"cpl_{experiment_id}_{label}",
        },
        settings={"preferred_provider": "elevenlabs"},
        narrator=narrator,
        preferred_provider="elevenlabs",
        allow_fallback=False,
    )
    narr_src = Path(str(synth.get("path") or ""))
    narr_path = out_dir / "narration.mp3"
    if narr_src.exists():
        shutil.copy2(narr_src, narr_path)

    qa = validate_narration_audio(narr_path, timing=(synth.get("voice_package") or {}).get("timing"))
    dur = float(synth.get("duration_sec") or qa.get("duration_sec") or duration_target_sec)

    script_path = out_dir / "SCRIPT.md"
    script_path.write_text(
        "\n".join(
            [
                f"# {variant.get('title')}",
                "",
                f"**Variant:** {label}",
                f"**Hook style:** {variant.get('hook_style')}",
                f"**Hook:** {variant.get('hook')}",
                "",
                "## Full script",
                "",
                str(variant.get("script") or ""),
                "",
            ]
        ),
        encoding="utf-8",
    )

    srt_path = out_dir / "captions.srt"
    _write_srt(srt_path, str(variant.get("script") or ""), dur)

    thumb_path = out_dir / "thumbnail.png"
    _write_thumbnail(thumb_path, str(variant.get("title") or ""), label)

    mp4_path = out_dir / "Final.mp4"
    mux = _mux_short(mp4_path, narr_path, dur, srt_path)
    render_sec = round(time.time() - t0, 2)

    candidate = {
        "topic": "Why Octopuses Have Three Hearts",
        "title": variant.get("title"),
        "hook": variant.get("hook"),
        "platform": platform,
        "duration_sec": int(round(dur)),
        "niche": "biology",
    }
    axes = {
        "hook": variant.get("hook"),
        "hook_style": variant.get("hook_style"),
        "narration": "professor",
        "title": variant.get("title"),
        "caption_style": "minimal_clean",
        "music": "soft_pulse",
        "thumbnail": "centered_subject_bold_title",
    }
    scores = _score_hook_variant(axes, str(variant.get("hook") or ""))
    scored_variant = {
        "label": label,
        "variant_id": f"{experiment_id}_{label}",
        "axes": axes,
        "scores": scores,
        "overall_score": int(scores.get("overall") or 0),
    }
    prediction = _predict_variant(candidate, scored_variant)
    prediction["_label"] = "PREDICTION — not real audience results"

    quality = {
        "production_quality": {
            "audio_qa": qa,
            "elevenlabs_provider": synth.get("provider"),
            "placeholder": synth.get("placeholder"),
            "audible_narration": bool(qa.get("ok") and qa.get("not_silent", True)),
        },
        "creative_quality": scored_variant.get("scores") or {},
        "hook_score": (scored_variant.get("scores") or {}).get("hook_quality"),
        "completion_prediction_pct": prediction.get("completion_rate_pct"),
        "shareability_prediction": prediction.get("share_probability"),
        "visual_score": (scored_variant.get("scores") or {}).get("visual_quality"),
        "narration_score": (scored_variant.get("scores") or {}).get("narration"),
        "audio_score": 100 if qa.get("ok") else 0,
        "thumbnail_score": 75,
        "prediction": prediction,
    }
    (out_dir / "QUALITY_REPORT.json").write_text(json.dumps(quality, indent=2) + "\n", encoding="utf-8")
    (out_dir / "VARIANT_META.json").write_text(
        json.dumps(
            {
                "label": label,
                "hook_style": variant.get("hook_style"),
                "variables_changed": ["hook_structure", "hook_wording"],
                "variables_held_constant": [
                    "core_factual_content",
                    "narrator_voice",
                    "music_style",
                    "caption_style",
                    "overall_visual_identity",
                    "call_to_action",
                    "export_settings",
                ],
                "body_fingerprint": hash(OCTOPUS_BODY) % 10**10,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return {
        "label": label,
        "variant_id": f"{experiment_id}_{label}",
        "production_id": f"{experiment_id}_{label}",
        "hook_style": variant.get("hook_style"),
        "hook": variant.get("hook"),
        "title": variant.get("title"),
        "script_path": str(script_path),
        "narration_path": str(narr_path),
        "captions_path": str(srt_path),
        "thumbnail_path": str(thumb_path),
        "mp4_path": str(mp4_path) if mux.get("ok") else "",
        "duration_sec": dur,
        "provider": synth.get("provider"),
        "placeholder": synth.get("placeholder"),
        "audio_qa_ok": qa.get("ok"),
        "mux_ok": mux.get("ok"),
        "render_time_sec": render_sec,
        "scores": scored_variant.get("scores"),
        "overall_score": scored_variant.get("overall_score"),
        "prediction": prediction,
        "quality_report_path": str(out_dir / "QUALITY_REPORT.json"),
        "package_dir": str(out_dir),
        "publishing": "disabled",
    }


def produce_experiment_variants(experiment: dict[str, Any], *, voice_id: str = "") -> dict[str, Any]:
    eid = str(experiment["experiment_id"])
    scripts = build_controlled_hook_scripts()
    packages = []
    for row in scripts[: int(experiment.get("number_of_variants") or 3)]:
        packages.append(
            produce_variant_package(
                experiment_id=eid,
                variant=row,
                platform=str(experiment.get("platform") or "youtube_shorts"),
                duration_target_sec=float(experiment.get("video_length_sec") or 45),
                narrator="professor",
                voice_id=voice_id,
            )
        )
    return {"variants": packages, "scripts": scripts}


def _write_srt(path: Path, text: str, duration: float) -> None:
    sentences = [s.strip() for s in text.replace(". ", ".|").split("|") if s.strip()]
    chunk = max(duration, 1.0) / max(1, len(sentences))

    def ts(x: float) -> str:
        h = int(x // 3600)
        m = int((x % 3600) // 60)
        s = int(x % 60)
        ms = int((x - int(x)) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    lines = []
    for i, sent in enumerate(sentences):
        start = i * chunk
        end = min(duration, (i + 1) * chunk)
        lines += [str(i + 1), f"{ts(start)} --> {ts(end)}", sent, ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_thumbnail(path: Path, title: str, label: str) -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont

        img = Image.new("RGB", (1080, 1920), (12, 28, 48))
        draw = ImageDraw.Draw(img)
        draw.rectangle((0, 0, 1080, 220), fill=(20, 90, 140))
        draw.text((48, 80), f"VARIANT {label}", fill=(255, 255, 255))
        # wrap title
        words = (title or "Octopus").split()
        line = ""
        y = 720
        for w in words:
            trial = (line + " " + w).strip()
            if len(trial) > 18:
                draw.text((64, y), line, fill=(240, 248, 255))
                y += 70
                line = w
            else:
                line = trial
        if line:
            draw.text((64, y), line, fill=(240, 248, 255))
        img.save(path)
    except Exception:  # noqa: BLE001
        path.write_bytes(b"")  # placeholder empty → recreate minimal ppm-like skip
        # fallback tiny PNG via ffmpeg color
        ff = shutil.which("ffmpeg")
        if ff:
            subprocess.run(
                [ff, "-y", "-f", "lavfi", "-i", "color=c=0x0c1c30:s=1080x1920", "-frames:v", "1", str(path)],
                capture_output=True,
                timeout=30,
            )


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _score_hook_variant(axes: dict[str, Any], hook: str) -> dict[str, Any]:
    """Lightweight internal scores (predictions) — avoids optimization_lab import cycles."""
    hook_quality = 55.0
    if "?" in hook:
        hook_quality += 8
    if "—" in hook or ":" in hook:
        hook_quality += 5
    words = len(hook.split())
    if 8 <= words <= 24:
        hook_quality += 12
    style = str(axes.get("hook_style") or "")
    if style == "curiosity_gap":
        hook_quality += 10
    elif style == "counterintuitive_fact":
        hook_quality += 12
    elif style == "immediate_visual_payoff":
        hook_quality += 9
    if any(w in hook.lower() for w in ("stop", "nobody", "watch", "three hearts", "shuts down")):
        hook_quality += 6
    hook_quality = _clamp(hook_quality, 0, 100)
    educational = 78.0
    retention = _clamp(62 + (hook_quality - 70) * 0.35, 40, 95)
    narration = 82.0
    visual = 70.0
    entertainment = _clamp(60 + (8 if style == "counterintuitive_fact" else 4), 40, 95)
    psychology = _clamp(65 + (hook_quality - 60) * 0.4, 40, 95)
    scores = {
        "hook_quality": int(round(hook_quality)),
        "psychology": int(round(psychology)),
        "retention": int(round(retention)),
        "educational_value": int(round(educational)),
        "entertainment": int(round(entertainment)),
        "seo": 72,
        "visual_quality": int(round(visual)),
        "narration": int(round(narration)),
        "professional_appearance": 75,
        "platform_readiness": 80,
    }
    scores["overall"] = int(round(sum(scores.values()) / len(scores)))
    return scores


def _predict_variant(candidate: dict[str, Any], winner: dict[str, Any]) -> dict[str, Any]:
    scores = winner.get("scores") or {}
    hook_q = float(scores.get("hook_quality") or 70)
    retention = float(scores.get("retention") or 70)
    entertainment = float(scores.get("entertainment") or 70)
    try:
        from services.learning.predictions import predict_performance

        base = predict_performance(
            topic=str(candidate.get("title") or candidate.get("topic") or ""),
            niche=str(candidate.get("niche") or ""),
            platform=str(candidate.get("platform") or "youtube_shorts"),
            runtime_sec=int(candidate.get("duration_sec") or 45),
            psychology_score=float(scores.get("psychology") or 0),
            seo_score=float(scores.get("seo") or 0),
            qa_score=float(scores.get("overall") or 0),
        )
    except Exception:  # noqa: BLE001
        base = {"expected_ctr": 4.5, "expected_avg_view_duration_sec": 28, "confidence": 0.4}
    ctr = _clamp(float(base.get("expected_ctr") or 4.5) + (hook_q - 70) * 0.08, 1.0, 22.0)
    completion = _clamp(retention * 0.82 + entertainment * 0.1, 10.0, 95.0)
    share = _clamp((entertainment * 0.4 + hook_q * 0.35 + retention * 0.25) / 100.0, 0.05, 0.9)
    return {
        "ctr_pct": round(ctr, 2),
        "average_view_duration_sec": round(float(base.get("expected_avg_view_duration_sec") or 28), 1),
        "completion_rate_pct": round(completion, 1),
        "share_probability": round(share, 3),
        "confidence": round(float(base.get("confidence") or 0.4), 3),
        "reasons": [
            "PREDICTION from internal heuristic scores — not real audience results",
            f"Hook style {(winner.get('axes') or {}).get('hook_style')} influences predicted retention",
        ],
    }


def _mux_short(mp4: Path, narr: Path, duration: float, srt: Path) -> dict[str, Any]:
    ff = shutil.which("ffmpeg")
    if not ff or not narr.exists():
        return {"ok": False, "error": "ffmpeg or narration missing"}
    cmd = [
        ff,
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c=0x0c1c30:s=1080x1920:d={max(1.0, duration)}",
        "-i",
        str(narr),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-shortest",
        "-movflags",
        "+faststart",
        str(mp4),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    ok = proc.returncode == 0 and mp4.exists() and mp4.stat().st_size > 1000
    # softburn captions optional — keep soft SRT alongside for sync validation
    return {"ok": ok, "error": "" if ok else (proc.stderr or "")[-300:], "captions_sidecar": str(srt)}
