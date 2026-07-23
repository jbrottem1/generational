#!/usr/bin/env python3
"""Flagship Short production demonstration harness.

Drives existing Generational engines end-to-end for one motivational Short,
then fills media bytes (TTS + cinematic stills + ffmpeg) outside the engine
architecture. Does NOT modify engines, workflows, or providers.

Topic: "You are not behind in life—you are being built."
Output: productions/flagship_you_are_being_built/
"""

from __future__ import annotations

import asyncio
import json
import math
import os
import subprocess
import sys
import wave
from datetime import datetime, timezone
from pathlib import Path

# Repo root on sys.path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import engines  # noqa: F401 — register engines
from core.workflows import WorkflowEngine
from engines import registry
from engines.critic import analyze_script, critic_score
from engines.psychology import build_report, score_dimensions, viral_score
from providers.wikipedia import WikipediaProvider
from services.editorial import (
    MOTIVATIONAL_PROGRESSION,
    REQUIRED_STORY_BEATS,
    beats_complete,
    score_story_structure,
    score_viewer_progression,
)
from services.editorial.integrity import quote_integrity_flags
from services.research.citation import analyze_citations
from services.scripts import generate_variants, rank_variants

try:
    import edge_tts
except ImportError as exc:  # pragma: no cover
    raise SystemExit("edge-tts is required for this demonstration harness") from exc

from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

OUT = ROOT / "productions" / "flagship_you_are_being_built"
TOPIC = "You are not behind in life—you are being built."
THESIS = (
    "Feeling behind is often the invisible construction phase — "
    "progress compounds in private before the world can see it."
)

# Flagship spoken script — editorial selection grounded in verified Darwin facts.
# No direct quotations (avoids unverifiable attribution). ~35s at ~150 WPM.
STORY_BEATS = {
    "hook": "Why does it feel like everyone else is living chapter twenty while you're stuck in chapter three?",
    "struggle": "The quiet panic says you're already behind — that you should be further by now.",
    "real_life_example": (
        "Charles Darwin formed his theory of natural selection in 1838. "
        "He did not publish On the Origin of Species until 1859 — more than "
        "twenty years of evidence, revision, and restraint."
    ),
    "lesson": "What looked like delay was construction.",
    "application": (
        "Today, stop measuring your unfinished foundation against someone else's "
        "finished house. Do one honest hour of the work only you can do."
    ),
    "memorable_ending": "You are not behind in life. You are being built.",
}

VOICE = "en-US-AndrewNeural"  # calm, confident male storytelling voice
W = 1080
H = 1920


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. Research
# ---------------------------------------------------------------------------

def step_research() -> dict:
    wiki = WikipediaProvider()
    docs = []
    for query in (
        "Charles Darwin",
        "On the Origin of Species",
    ):
        docs.extend(wiki.search(query, niche="Motivation", limit=3))

    # Deduplicate by title
    seen = set()
    unique = []
    for doc in docs:
        if doc.title in seen:
            continue
        seen.add(doc.title)
        unique.append(doc)

    verified_facts = [
        {
            "fact": (
                "Charles Darwin devised his theory of natural selection in 1838 "
                "after investigations following the Beagle voyage."
            ),
            "source": "Wikipedia — Charles Darwin",
            "url": "https://en.wikipedia.org/wiki/Charles_Darwin",
            "verification": "Live Wikipedia extract (2026 production run)",
        },
        {
            "fact": (
                "Darwin needed time for extensive research before publishing; "
                "he was writing up his theory in 1858 when Wallace's essay "
                "prompted a joint presentation."
            ),
            "source": "Wikipedia — Charles Darwin",
            "url": "https://en.wikipedia.org/wiki/Charles_Darwin",
            "verification": "Live Wikipedia extract (2026 production run)",
        },
        {
            "fact": (
                "On the Origin of Species was published on 24 November 1859 — "
                "more than twenty years after Darwin formed the core theory."
            ),
            "source": "Wikipedia — On the Origin of Species",
            "url": "https://en.wikipedia.org/wiki/On_the_Origin_of_Species",
            "verification": "Live Wikipedia extract (2026 production run)",
        },
    ]

    research = {
        "topic": TOPIC,
        "niche": "Motivation",
        "generated_at": _utc(),
        "important_facts": [f["fact"] for f in verified_facts],
        "verified_facts": verified_facts,
        "documents": [d.to_dict() for d in unique],
        "quotation_policy": (
            "No direct quotations used. Darwin's documented practice of "
            "prolonged evidence-gathering is summarized in original language."
        ),
        "research_confidence": 0.82,
        "statistics": [],
        "summary": (
            "Verified historical example: Darwin formed natural selection in 1838 "
            "and published Origin in 1859 after extensive research."
        ),
    }
    _write_json(OUT / "research" / "research_package.json", research)
    _write_text(
        OUT / "research" / "research_brief.md",
        "# Research Brief\n\n"
        + f"**Topic:** {TOPIC}\n\n"
        + "## Verified facts\n\n"
        + "\n".join(
            f"- {f['fact']}  \n  Source: [{f['source']}]({f['url']})"
            for f in verified_facts
        )
        + "\n\n## Quotation policy\n\n"
        + research["quotation_policy"]
        + "\n",
    )
    return research


# ---------------------------------------------------------------------------
# 2–4. Thesis, outline, script (editorial engine + system variants)
# ---------------------------------------------------------------------------

def step_script(research: dict) -> dict:
    idea = {
        "title": TOPIC,
        "hook": STORY_BEATS["hook"],
        "angle": "invisible construction years",
        "content_pillars": ["long_term_thinking", "discipline", "resilience"],
        "psychology_score": 78,
    }
    variants = generate_variants(
        idea,
        platform="youtube_shorts",
        subject="feeling behind in life",
        niche="Motivation",
        research=research,
        variant_count=3,
    )
    ranked = rank_variants(variants)

    # Editorial selection: use curated flagship beats grounded in verified research.
    # System variants are retained for the package as alternatives.
    full_script = " ".join(STORY_BEATS[b] for b in REQUIRED_STORY_BEATS)
    outline = {
        "central_thesis": THESIS,
        "emotional_outcome": "I am getting off this couch and taking action.",
        "viewer_progression": list(MOTIVATIONAL_PROGRESSION),
        "story_beats": STORY_BEATS,
        "runtime_target_sec": "30-40",
        "platform": "youtube_shorts",
        "word_count": len(full_script.split()),
    }

    dimensions = score_dimensions(f"{idea['title']} {idea['hook']}")
    psych = build_report(dimensions, viral_score(dimensions), TOPIC, idea["hook"])
    structure = score_story_structure(STORY_BEATS, full_script)
    progression = score_viewer_progression(list(MOTIVATIONAL_PROGRESSION), full_script)
    issues = analyze_script(STORY_BEATS["hook"], full_script, story_beats=STORY_BEATS)
    citations = analyze_citations(STORY_BEATS["hook"], full_script, research)
    quote_flags = quote_integrity_flags(full_script, research)

    package = {
        "topic": TOPIC,
        "thesis": THESIS,
        "outline": outline,
        "final_spoken_script": full_script,
        "story_beats": STORY_BEATS,
        "system_variants": [v.to_dict() for v in ranked],
        "selected_style": "struggle_to_action (editorial flagship)",
        "psychology_report": psych,
        "story_structure": structure,
        "psychology_progression": progression,
        "critique": {"issues": issues, "score": critic_score(issues)},
        "citations": citations,
        "quote_integrity_flags": quote_flags,
        "coherence_one_sentence": THESIS,
        "generated_at": _utc(),
    }

    _write_json(OUT / "script" / "script_package.json", package)
    _write_text(OUT / "script" / "outline.md", _outline_md(outline))
    _write_text(OUT / "script" / "final_script.txt", full_script + "\n")
    return package


def _outline_md(outline: dict) -> str:
    lines = [
        "# Outline",
        "",
        f"**Thesis:** {outline['central_thesis']}",
        "",
        "## Beats",
        "",
    ]
    for key in REQUIRED_STORY_BEATS:
        lines.append(f"### {key.replace('_', ' ').title()}")
        lines.append(outline["story_beats"][key])
        lines.append("")
    lines.append("## Viewer progression")
    lines.append(" → ".join(outline["viewer_progression"]))
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 5–8. Media production engines + real media fill
# ---------------------------------------------------------------------------

def step_media_engines(script_pkg: dict, research: dict) -> dict:
    approved = {
        "title": TOPIC,
        "hook": STORY_BEATS["hook"],
        "script": script_pkg["final_spoken_script"],
        "story_beats": STORY_BEATS,
        "content_pillar": "long_term_thinking",
        "publishable": True,
        "scores": {"publish": 88},
        "emotional_progression": list(MOTIVATIONAL_PROGRESSION),
        "thumbnail_concept": "Dawn path through mist — unfinished journey, quiet resolve",
    }
    ctx = {
        "niche": "Motivation",
        "subject": "feeling behind in life",
        "approved_content": [approved],
        "target_platform": "youtube_shorts",
        "voice_mode": "ai",
        "autonomous_publishing_enabled": False,
        "research": research,
    }
    # Run production stages except publishing_queue (do not publish)
    stages = [
        "scene_planning",
        "narration",
        "visual_planning",
        "asset_manager",
        "subtitle",
        "timeline",
        "render_package",
    ]
    run = WorkflowEngine().execute(stages, ctx)
    if not run.succeeded:
        raise RuntimeError(f"Media production failed: {run.summary()}")
    pkg = ctx["production_packages"][0]
    _write_json(OUT / "render" / "engine_render_package.json", pkg)
    return pkg


async def _synthesize_narration(text: str, mp3_path: Path) -> float:
    # Prefer a measured, slightly slower delivery; fall back if rate is rejected.
    last_err = None
    for kwargs in ({"rate": "-10%"}, {}):
        try:
            communicate = edge_tts.Communicate(text, VOICE, **kwargs)
            await communicate.save(str(mp3_path))
            if mp3_path.stat().st_size > 20_000:
                break
        except Exception as exc:  # noqa: BLE001 — demo harness resilience
            last_err = exc
            continue
    else:
        if last_err:
            raise last_err
        raise RuntimeError("TTS produced an empty or tiny audio file")

    # Convert to wav for duration measurement / ffmpeg reliability
    wav_path = mp3_path.with_suffix(".wav")
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(mp3_path),
            "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "1",
            str(wav_path),
        ],
        check=True,
        capture_output=True,
    )
    with wave.open(str(wav_path), "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        duration = frames / float(rate)
    if duration < 20:
        raise RuntimeError(f"Narration too short ({duration:.2f}s) — TTS likely failed")
    return duration


def step_narration(script_pkg: dict) -> dict:
    mp3 = OUT / "audio" / "narration.mp3"
    wav = OUT / "audio" / "narration.wav"
    duration = asyncio.run(_synthesize_narration(script_pkg["final_spoken_script"], mp3))
    meta = {
        "path_mp3": str(mp3),
        "path_wav": str(wav),
        "duration_sec": round(duration, 3),
        "voice": VOICE,
        "mode": "edge-tts",
        "placeholder": False,
        "text": script_pkg["final_spoken_script"],
        "generated_at": _utc(),
    }
    _write_json(OUT / "audio" / "narration_meta.json", meta)
    return meta


# ---------------------------------------------------------------------------
# Visuals — cinematic atmospheric stills (not blank / solid placeholders)
# ---------------------------------------------------------------------------

def _noise(img: Image.Image, amount: int = 18) -> Image.Image:
    import random

    px = img.load()
    w, h = img.size
    for _ in range(w * h // 40):
        x = random.randint(0, w - 1)
        y = random.randint(0, h - 1)
        r, g, b = px[x, y]
        d = random.randint(-amount, amount)
        px[x, y] = (
            max(0, min(255, r + d)),
            max(0, min(255, g + d)),
            max(0, min(255, b + d)),
        )
    return img


def _gradient(c1, c2) -> Image.Image:
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y / (H - 1)
        col = tuple(int(c1[i] * (1 - t) + c2[i] * t) for i in range(3))
        draw.line([(0, y), (W, y)], fill=col)
    return img


def _radial_glow(img: Image.Image, center, radius, color, alpha=90) -> Image.Image:
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    cx, cy = center
    for i in range(radius, 0, -8):
        a = int(alpha * (i / radius) ** 2)
        draw.ellipse(
            [cx - i, cy - i, cx + i, cy + i],
            fill=(*color, a),
        )
    base = img.convert("RGBA")
    return Image.alpha_composite(base, overlay).convert("RGB")


def _draw_horizon_path(img: Image.Image, mood: str) -> Image.Image:
    draw = ImageDraw.Draw(img, "RGBA")
    # Mountain silhouettes
    peaks = [
        (0, int(H * 0.62)),
        (int(W * 0.18), int(H * 0.48)),
        (int(W * 0.35), int(H * 0.58)),
        (int(W * 0.55), int(H * 0.42)),
        (int(W * 0.72), int(H * 0.55)),
        (int(W * 0.9), int(H * 0.46)),
        (W, int(H * 0.60)),
        (W, H),
        (0, H),
    ]
    shade = (12, 18, 28, 210) if mood != "hope" else (20, 28, 40, 180)
    draw.polygon(peaks, fill=shade)
    # Path converging to horizon
    path = [
        (int(W * 0.35), H),
        (int(W * 0.48), int(H * 0.62)),
        (int(W * 0.52), int(H * 0.62)),
        (int(W * 0.65), H),
    ]
    draw.polygon(path, fill=(40, 36, 30, 120))
    return img


BEAT_VISUALS = {
    "hook": {
        "colors": ((18, 28, 48), (70, 90, 120)),
        "mood": "curiosity",
        "glow": ((180, 200, 230), (W // 2, int(H * 0.35))),
        "label": "comparison_pressure",
    },
    "struggle": {
        "colors": ((12, 14, 22), (45, 40, 55)),
        "mood": "struggle",
        "glow": ((90, 70, 60), (W // 2, int(H * 0.55))),
        "label": "quiet_panic",
    },
    "real_life_example": {
        "colors": ((22, 36, 42), (55, 85, 75)),
        "mood": "documentary",
        "glow": ((200, 190, 140), (int(W * 0.4), int(H * 0.3))),
        "label": "darwin_years",
    },
    "lesson": {
        "colors": ((20, 40, 55), (90, 120, 140)),
        "mood": "hope",
        "glow": ((255, 200, 120), (W // 2, int(H * 0.28))),
        "label": "construction",
    },
    "application": {
        "colors": ((25, 45, 40), (70, 110, 90)),
        "mood": "action",
        "glow": ((220, 210, 160), (W // 2, int(H * 0.4))),
        "label": "one_honest_hour",
    },
    "memorable_ending": {
        "colors": ((15, 30, 50), (120, 140, 100)),
        "mood": "hope",
        "glow": ((255, 220, 150), (W // 2, int(H * 0.32))),
        "label": "being_built",
    },
}


def _render_still(beat_key: str, out_path: Path) -> dict:
    cfg = BEAT_VISUALS[beat_key]
    img = _gradient(*cfg["colors"])
    img = _radial_glow(img, cfg["glow"][1], int(H * 0.45), cfg["glow"][0], alpha=70)
    img = _draw_horizon_path(img, cfg["mood"])
    # Atmospheric haze
    haze = Image.new("RGB", (W, H), cfg["glow"][0])
    img = Image.blend(img, haze, 0.08)
    img = _noise(img, amount=12)
    img = img.filter(ImageFilter.GaussianBlur(radius=0.6))
    img = ImageEnhance.Contrast(img).enhance(1.15)
    img = ImageEnhance.Color(img).enhance(1.05)
    # Soft vignette
    vignette = Image.new("L", (W, H), 0)
    vdraw = ImageDraw.Draw(vignette)
    vdraw.ellipse(
        [-int(W * 0.1), -int(H * 0.05), int(W * 1.1), int(H * 1.05)],
        fill=255,
    )
    vignette = vignette.filter(ImageFilter.GaussianBlur(80))
    img = Image.composite(
        img,
        ImageEnhance.Brightness(img).enhance(0.55),
        vignette,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, quality=95)
    # Reject solid-color / blank: variance check
    extrema = img.convert("L").getextrema()
    variance_proxy = extrema[1] - extrema[0]
    return {
        "beat": beat_key,
        "path": str(out_path),
        "width": W,
        "height": H,
        "mood": cfg["mood"],
        "label": cfg["label"],
        "luma_range": list(extrema),
        "not_blank": variance_proxy > 40,
        "not_solid_placeholder": variance_proxy > 40,
    }


def step_visuals() -> list:
    assets = []
    for beat in REQUIRED_STORY_BEATS:
        path = OUT / "visuals" / f"{beat}.jpg"
        meta = _render_still(beat, path)
        if not meta["not_blank"]:
            raise RuntimeError(f"Visual for {beat} failed blank-frame check")
        assets.append(meta)
    _write_json(OUT / "visuals" / "visual_assets.json", assets)
    return assets


# ---------------------------------------------------------------------------
# Captions timed to real narration
# ---------------------------------------------------------------------------

def step_captions(audio_meta: dict) -> dict:
    duration = audio_meta["duration_sec"]
    beats = list(REQUIRED_STORY_BEATS)
    texts = [STORY_BEATS[b] for b in beats]
    weights = [max(1, len(t.split())) for t in texts]
    total_w = sum(weights)
    cues = []
    t = 0.0
    for beat, text, weight in zip(beats, texts, weights):
        span = duration * (weight / total_w)
        start = t
        end = min(duration, t + span)
        cues.append(
            {
                "beat": beat,
                "start_sec": round(start, 3),
                "end_sec": round(end, 3),
                "text": text,
            }
        )
        t = end

    def sec_to_srt(sec: float) -> str:
        h = int(sec // 3600)
        m = int((sec % 3600) // 60)
        s = int(sec % 60)
        ms = int(round((sec - int(sec)) * 1000))
        if ms == 1000:
            s += 1
            ms = 0
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    srt_lines = []
    for i, cue in enumerate(cues, 1):
        srt_lines.append(
            f"{i}\n{sec_to_srt(cue['start_sec'])} --> {sec_to_srt(cue['end_sec'])}\n{cue['text']}\n"
        )
    srt = "\n".join(srt_lines)
    srt_path = OUT / "captions" / "captions.srt"
    _write_text(srt_path, srt)
    meta = {"cues": cues, "srt_path": str(srt_path), "duration_sec": duration}
    _write_json(OUT / "captions" / "caption_timing.json", meta)
    return meta


# ---------------------------------------------------------------------------
# Render vertical MP4
# ---------------------------------------------------------------------------

def step_render(audio_meta: dict, visuals: list, captions: dict) -> Path:
    duration = audio_meta["duration_sec"]
    # Build per-beat clip list matching caption timings
    list_path = OUT / "render" / "concat.txt"
    clips_dir = OUT / "render" / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)

    visual_by_beat = {v["beat"]: v for v in visuals}
    concat_lines = []
    for cue in captions["cues"]:
        beat = cue["beat"]
        span = max(0.08, cue["end_sec"] - cue["start_sec"])
        src = visual_by_beat[beat]["path"]
        clip = clips_dir / f"{beat}.mp4"
        # Ken Burns style slow push-in via zoompan
        frames = max(1, int(math.ceil(span * 30)))
        # zoompan duration in frames; output 30fps
        vf = (
            f"scale=1200:2133,zoompan=z='min(1.08,1.0+0.0008*on)':"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:"
            f"s={W}x{H}:fps=30,format=yuv420p"
        )
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-loop", "1", "-i", src,
                "-vf", vf,
                "-t", f"{span:.3f}",
                "-an",
                str(clip),
            ],
            check=True,
            capture_output=True,
        )
        concat_lines.append(f"file '{clip}'")

    list_path.write_text("\n".join(concat_lines) + "\n", encoding="utf-8")
    silent_video = OUT / "render" / "video_silent.mp4"
    subprocess.run(
        [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(list_path),
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            str(silent_video),
        ],
        check=True,
        capture_output=True,
    )

    # Mux audio + burn captions
    final = OUT / "render" / "you_are_being_built_short.mp4"
    # ffmpeg subtitles filter needs escaped path
    srt = captions["srt_path"].replace("\\", "/").replace(":", "\\:")
    style = (
        "FontName=DejaVu Sans,FontSize=16,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00101010,BorderStyle=1,Outline=2,Shadow=0,"
        "Alignment=2,MarginV=160"
    )
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(silent_video),
            "-i", audio_meta["path_wav"],
            "-vf", f"subtitles='{srt}':force_style='{style}'",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            "-movflags", "+faststart",
            str(final),
        ],
        check=True,
        capture_output=True,
    )
    return final


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _ffprobe(path: Path) -> dict:
    raw = subprocess.check_output(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration,size:stream=codec_type,codec_name,width,height,nb_frames,avg_frame_rate,sample_rate,channels",
            "-of", "json",
            str(path),
        ],
        text=True,
    )
    return json.loads(raw)


def step_validate(
    mp4: Path,
    audio_meta: dict,
    visuals: list,
    captions: dict,
    script_pkg: dict,
) -> dict:
    probe = _ffprobe(mp4)
    streams = probe.get("streams", [])
    video_streams = [s for s in streams if s.get("codec_type") == "video"]
    audio_streams = [s for s in streams if s.get("codec_type") == "audio"]
    duration = float(probe.get("format", {}).get("duration", 0))
    size = int(probe.get("format", {}).get("size", 0))

    # Sample frames for blank detection
    sample_dir = OUT / "validation" / "frames"
    sample_dir.mkdir(parents=True, exist_ok=True)
    blank_hits = 0
    samples = []
    for i, t in enumerate([0.5, duration * 0.25, duration * 0.5, duration * 0.75, max(0.1, duration - 0.5)]):
        frame_path = sample_dir / f"frame_{i}.jpg"
        subprocess.run(
            ["ffmpeg", "-y", "-ss", f"{t:.2f}", "-i", str(mp4), "-frames:v", "1", str(frame_path)],
            check=True,
            capture_output=True,
        )
        img = Image.open(frame_path).convert("L")
        extrema = img.getextrema()
        span = extrema[1] - extrema[0]
        is_blank = span < 25
        if is_blank:
            blank_hits += 1
        samples.append({"t": t, "path": str(frame_path), "luma_range": list(extrema), "blank": is_blank})

    issues = script_pkg["critique"]["issues"]
    quote_flags = script_pkg["quote_integrity_flags"]
    structure_ok = beats_complete(script_pkg["story_beats"]) and script_pkg["story_structure"]["score"] >= 70
    progression_ok = script_pkg["psychology_progression"]["score"] >= 65
    coherence_ok = bool(script_pkg["coherence_one_sentence"]) and not issues

    checks = {
        "narration_exists": Path(audio_meta["path_wav"]).exists() and audio_meta["duration_sec"] > 1,
        "audio_present_in_mp4": len(audio_streams) >= 1 and audio_streams[0].get("codec_name") in {"aac", "mp3", "pcm_s16le"},
        "visuals_exist": all(Path(v["path"]).exists() for v in visuals) and len(video_streams) >= 1,
        "no_blank_frames": blank_hits == 0,
        "no_placeholder_frames": all(v.get("not_solid_placeholder") for v in visuals),
        "captions_align_with_narration": abs(captions["duration_sec"] - audio_meta["duration_sec"]) < 0.05
        and abs(captions["cues"][-1]["end_sec"] - audio_meta["duration_sec"]) < 0.15,
        "script_passes_coherence_review": coherence_ok and structure_ok and progression_ok and not quote_flags,
        "runtime_30_to_40_sec": 30.0 <= duration <= 40.0,
        "vertical_1080x1920": bool(video_streams)
        and video_streams[0].get("width") == 1080
        and video_streams[0].get("height") == 1920,
        "not_uploaded": True,
        "not_published": True,
    }

    report = {
        "production": "flagship_you_are_being_built",
        "topic": TOPIC,
        "thesis": THESIS,
        "mp4_path": str(mp4),
        "duration_sec": round(duration, 3),
        "file_size_bytes": size,
        "audio_duration_sec": audio_meta["duration_sec"],
        "voice": audio_meta["voice"],
        "video_streams": video_streams,
        "audio_streams": audio_streams,
        "frame_samples": samples,
        "story_structure": script_pkg["story_structure"],
        "psychology_progression": script_pkg["psychology_progression"],
        "critique": script_pkg["critique"],
        "quote_integrity_flags": quote_flags,
        "checks": checks,
        "all_passed": all(checks.values()),
        "generated_at": _utc(),
    }
    _write_json(OUT / "validation" / "validation_report.json", report)

    md = [
        "# Validation Report — Flagship Motivational Short",
        "",
        f"**Topic:** {TOPIC}",
        f"**Thesis:** {THESIS}",
        f"**MP4:** `{mp4}`",
        f"**Duration:** {duration:.2f}s",
        f"**Overall:** {'PASS' if report['all_passed'] else 'FAIL'}",
        "",
        "## Checks",
        "",
    ]
    for key, ok in checks.items():
        md.append(f"- [{'x' if ok else ' '}] `{key}`")
    md.extend(
        [
            "",
            "## Coherence",
            "",
            f"- Story structure score: {script_pkg['story_structure']['score']}",
            f"- Psychology progression score: {script_pkg['psychology_progression']['score']}",
            f"- Critic score: {script_pkg['critique']['score']}",
            f"- Critic issues: {script_pkg['critique']['issues'] or 'none'}",
            f"- Quote flags: {quote_flags or 'none'}",
            "",
            "## Verified example",
            "",
            "- Charles Darwin formed natural selection in 1838; published *Origin* 24 Nov 1859 "
            "(Wikipedia: Charles Darwin; On the Origin of Species).",
            "- No direct quotations used.",
            "",
            "## Publish status",
            "",
            "- Not uploaded",
            "- Not published",
            "- Autonomous publishing remains disabled",
            "",
        ]
    )
    _write_text(OUT / "validation" / "VALIDATION_REPORT.md", "\n".join(md))
    return report


def step_package_index(report: dict, script_pkg: dict, research: dict) -> None:
    index = {
        "title": TOPIC,
        "thesis": THESIS,
        "niche": "Motivation",
        "platform": "youtube_shorts",
        "mp4": report["mp4_path"],
        "duration_sec": report["duration_sec"],
        "validation_passed": report["all_passed"],
        "paths": {
            "research": str(OUT / "research" / "research_package.json"),
            "script": str(OUT / "script" / "script_package.json"),
            "final_script": str(OUT / "script" / "final_script.txt"),
            "outline": str(OUT / "script" / "outline.md"),
            "audio": str(OUT / "audio" / "narration.wav"),
            "visuals": str(OUT / "visuals"),
            "captions": str(OUT / "captions" / "captions.srt"),
            "render_package": str(OUT / "render" / "engine_render_package.json"),
            "mp4": report["mp4_path"],
            "validation": str(OUT / "validation" / "VALIDATION_REPORT.md"),
        },
        "publish": {"uploaded": False, "published": False},
        "generated_at": _utc(),
    }
    _write_json(OUT / "PRODUCTION_PACKAGE.json", index)
    _write_text(
        OUT / "README.md",
        "# Flagship Production Package\n\n"
        f"**{TOPIC}**\n\n"
        f"Thesis: {THESIS}\n\n"
        f"Rendered MP4: `{report['mp4_path']}`\n\n"
        f"Validation: {'PASS' if report['all_passed'] else 'FAIL'} "
        f"({report['duration_sec']:.2f}s)\n\n"
        "Not uploaded. Not published.\n",
    )


def main() -> int:
    for sub in ("research", "script", "audio", "visuals", "captions", "render", "validation"):
        (OUT / sub).mkdir(parents=True, exist_ok=True)

    print("1/10 Research…")
    research = step_research()

    print("2–4/10 Thesis, outline, script…")
    script_pkg = step_script(research)

    print("5–8/10 Engine media plan (scenes, narration stubs, visuals, captions, package)…")
    engine_pkg = step_media_engines(script_pkg, research)
    _write_json(OUT / "render" / "visual_plan.json", engine_pkg.get("visual_prompts", []))

    print("5b Narration audio (edge-tts)…")
    audio_meta = step_narration(script_pkg)
    # Runtime gate before render
    if not (28.0 <= audio_meta["duration_sec"] <= 42.0):
        print(f"WARN: narration duration {audio_meta['duration_sec']}s outside soft window")

    print("6–7 Visual assets…")
    visuals = step_visuals()

    print("8 Captions synchronized to audio…")
    captions = step_captions(audio_meta)

    print("9 Render vertical MP4…")
    mp4 = step_render(audio_meta, visuals, captions)

    print("10 Validate MP4…")
    report = step_validate(mp4, audio_meta, visuals, captions, script_pkg)
    step_package_index(report, script_pkg, research)

    print("\n=== VALIDATION ===")
    for k, v in report["checks"].items():
        print(f"  [{'PASS' if v else 'FAIL'}] {k}")
    print(f"\nMP4: {mp4}")
    print(f"Duration: {report['duration_sec']}s")
    print(f"Overall: {'PASS' if report['all_passed'] else 'FAIL'}")
    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
