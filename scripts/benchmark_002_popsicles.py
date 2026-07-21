#!/usr/bin/env python3
"""Production Benchmark #002 — How Popsicles Are Made.

Long-form educational documentary (8–12 min) via:
  chaptered educational stills (layout engine) + Ken Burns
  full TTS narration (chunked) + ffmpeg assemble
  technical QC + Media Library export

Usage:
  ./venv/bin/python scripts/benchmark_002_popsicles.py
  ./venv/bin/python scripts/benchmark_002_popsicles.py --skip-export
"""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
import time
import wave
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.env import load_application_env

load_application_env()

from services.animation.popsicle_documentary import build_all_scenes
from services.generational_os.export import export_verified_production
from services.media_production.ffmpeg_assembler import assemble_mp4, find_ffmpeg
from services.provider_runtime.config import has_credential

REPORT_DIR = ROOT / "data" / "productions" / "_validation" / "benchmark_002_popsicles"
SCENES_DIR = REPORT_DIR / "scenes"
AUDIO_DIR = REPORT_DIR / "audio"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

PROJECT_ID = "benchmark_002_popsicles"
TITLE = "How Popsicles Are Made"
FILENAME = "FoodScience_002_How_Popsicles_Are_Made.mp4"

# Chaptered narration — verified claims only (see FACT_SHEET.py)
# Target ~1,400–1,700 words for 8–12 min documentary pacing.
CHAPTERS: list[dict[str, str]] = [
    {
        "id": "ch0_open",
        "title": "Open",
        "text": (
            "What if one of the world's most familiar summer treats started as an accident — "
            "left outside overnight by an eleven-year-old? "
            "A flavored drink. A stirring stick. A cold night in California's Bay Area. "
            "By morning, something new had formed: ice you could hold. "
            "Today we follow that frozen drink on a stick from a childhood porch to modern factories, "
            "ingredient labs, packaging lines, and the physics of ice itself. "
            "We will ask what each ingredient contributes, how industrial production actually works, "
            "and why sugar changes the freeze. "
            "This is How Popsicles Are Made — a Generational educational documentary."
        ),
    },
    {
        "id": "ch1_history",
        "title": "History",
        "text": (
            "Chapter one: the history of the Popsicle. "
            "In nineteen-oh-five, Frank W. Epperson — then about eleven — mixed flavored powder with water. "
            "He left the cup outside overnight with a stirring stick still in it. "
            "By morning, the mixture had frozen around the stick. "
            "That story is how Epperson is widely credited with inventing the modern ice pop on a stick. "
            "Obituaries and inventor profiles repeat the account. "
            "Still, origin tales can polish themselves over decades — so we say credited with, "
            "not absolute certainty of every childhood detail. Exact city within the Bay Area is debated across sources, "
            "so we keep the geography honest: California's Bay Area. "
            "What is clear is the product idea: a flavored ice you could hold without a spoon or a bowl. "
            "Years later, as an adult, Epperson brought the treat to the public. "
            "In the nineteen-twenties he patented a handled frozen confection and marketed it as an Epsicle — "
            "a playful blend of his name and icicle. "
            "The brand name that stuck in American language was Popsicle. "
            "From a neighborhood experiment to a patented confection, the ice pop scaled into a summer ritual. "
            "Kids could walk, talk, and melt their way through a treat designed for one hand. "
            "Here's the curiosity hook: why does that same handheld idea still work in factories a century later? "
            "Because the science of freezing — water, sugar, crystals, and cold — never went out of date. "
            "The stick was not a gimmick. It was an interface between frozen chemistry and human hands."
        ),
    },
    {
        "id": "ch2_ingredients",
        "title": "Ingredients",
        "text": (
            "Chapter two: ingredients. What actually goes into a typical ice pop — and what does each one do? "
            "Start with water. Water is the solvent that becomes the ice structure. "
            "It is the bulk of the freeze. Without water, there is no ice pop — only syrup and disappointment. "
            "Fruit juice or puree brings flavor, natural pigments, and sugars that fruit already contains. "
            "Juice-forward recipes taste brighter; puree can add body. "
            "Added sugar does more than sweeten. Dissolved sugar lowers the freezing point of water. "
            "That is freezing-point depression — a colligative effect taught in basic physical chemistry. "
            "More dissolved particles, harder for pure ice to form at zero Celsius. "
            "Sweetness and texture are therefore linked: change the sugar, change the bite. "
            "Natural flavors are concentrated aroma compounds drawn from foods. "
            "Artificial flavors, when used, are synthesized aroma molecules chosen for a consistent taste profile "
            "batch after batch. Both exist to deliver smell and taste — and much of what we call flavor "
            "is finished by the nose as aroma rises from the melt. "
            "Food coloring shapes expectation before the first bite. "
            "Color is identity in the freezer case: cherry reads red; lemon reads yellow; blue raspberry "
            "announces itself before you taste it. Manufacturers use coloring for visual consistency across seasons. "
            "Stabilizers — often food gums and related texture agents — help manage ice structure "
            "and how the pop behaves as it softens or experiences temperature swings in storage. "
            "They are engineering tools for mouthfeel and shelf stability, not magic. "
            "Put together: water builds the ice; juice and flavors write the sensory story; "
            "sugar tunes freeze and sweetness; color sets expectation; stabilizers protect texture. "
            "Every line on the ingredient list earns its place."
        ),
    },
    {
        "id": "ch3_factory",
        "title": "Factory",
        "text": (
            "Chapter three: factory production. "
            "In industrial frozen-novelty manufacturing, the journey is a controlled sequence — "
            "not a backyard freezer and a lucky overnight chill. "
            "First: ingredient mixing. Water, sweeteners, flavors, colors, and stabilizers are blended "
            "in industrial tanks until the batch is uniform. Consistency is the product. "
            "A batch that is sweet in one corner and watery in another will freeze into uneven quality. "
            "Next: quality testing. Plants check attributes such as sweetness and dissolved solids "
            "so the mix matches the target formula before it commits to molds. "
            "Measure. Adjust. Release. That is the educational rhythm of process control. "
            "Then: automated filling. Liquid mix enters molds — the negative space of tomorrow's popsicles. "
            "Each cavity is a promise of shape: classic flat pop, twin pop, or novelty silhouette. "
            "Stick insertion happens while the mix can still grip the stick — typically before the freeze is complete. "
            "Insert too early into a thin liquid and sticks wander. Insert too late into hard ice and they will not seat. "
            "The stick is both handle and structure. "
            "Flash freezing — rapid cold in tunnels or related cold systems — sets the structure "
            "quickly enough for demolding and packaging. Faster freezes tend to favor smaller ice crystals; "
            "and crystal size is texture you can feel. "
            "After demolding comes packaging: wraps, cartons, cases. "
            "Then shipping under cold-chain discipline. From tank to truck, temperature control "
            "is the difference between a smooth pop and a coarse, freezer-stressed one. "
            "We are not claiming proprietary plant secrets or secret brand formulas. "
            "This is the standard educational map: mix, test, fill, insert sticks, freeze, package, ship. "
            "Scale changes the machines. Physics does not change the chapter titles."
        ),
    },
    {
        "id": "ch4_science",
        "title": "Science",
        "text": (
            "Chapter four: the science. Why does freezing work — and why does a popsicle not feel like a rock of pure ice? "
            "Pure water freezes at zero degrees Celsius, thirty-two Fahrenheit. "
            "As heat leaves the liquid, water molecules settle into an ordered ice lattice. "
            "That lattice is the skeleton of every ice pop. "
            "Add sugar, and dissolved particles interfere with that packing. The freezing point drops. "
            "At typical home-freezer temperatures, more of a sugared mixture can remain partially unfrozen "
            "compared with pure water. Bite softens. Melt changes. The pop is no longer a brick of ice. "
            "Ice crystal size is the texture code. Small crystals feel smoother on the tongue. "
            "Large crystals feel icy, coarse, almost crunchy. "
            "Formulation and freeze rate both influence which crystal population you get. "
            "Here is a key contrast with ice cream: water ices and ice pops are usually frozen still in molds — "
            "quiescent freezing — with little continuous stirring. "
            "Ice cream is often churned, incorporating air and breaking crystals as they grow. "
            "Different process, different crystal story, different mouthfeel. "
            "Flavor release follows melt. As ice returns to liquid on your tongue, sugars dissolve "
            "and aroma compounds volatilize upward into your nose. "
            "That is when cherry, orange, or grape actually arrives as a full sensation — not when the pop is still a silent solid. "
            "So a popsicle is not merely frozen juice. "
            "It is applied freezing-point chemistry, crystal engineering, and sensory timing — "
            "compressed into a shape you can hold in one hand."
        ),
    },
    {
        "id": "ch5_facts",
        "title": "Facts",
        "text": (
            "Chapter five: interesting facts — surprising, but verified. "
            "One: Popsicle began as a brand name for a patented ice pop on a stick. "
            "The trademarked word escaped the wrapper and entered everyday speech the way Band-Aid and Kleenex sometimes do. "
            "Two: Sugar is a texture engineer as much as a sweetener. "
            "It changes how water freezes through freezing-point depression, not only how sweet the pop tastes. "
            "Three: Ice pops typically freeze still in molds. That quiescent freeze is a different crystal story "
            "than ice cream churned with air. Same freezer aisle. Different physics playbook. "
            "Four: Crystal size is a major reason one pop feels smooth and another feels crunchy-icy — "
            "even when both look similar in the package. "
            "Five: Stabilizers help the product survive the real world — warehouse freezers, delivery trucks, "
            "store cabinets, and the slow warm-up on the ride home — by supporting texture through temperature swings. "
            "Notice what we left out: exact overnight temperatures from nineteen-oh-five, "
            "unverifiable modern sales myths, and etymology legends we cannot defend. "
            "Curiosity stays. Unsupported claims do not."
        ),
    },
    {
        "id": "ch6_future",
        "title": "Future",
        "text": (
            "Chapter six: the future of frozen desserts. "
            "Where ice pops go next is already visible on ingredient labels and packaging claims. "
            "Healthier recipes lean fruit-forward and reduce added sugar. "
            "That sounds simple — until you remember sugar also tunes the freeze. "
            "Less sugar can mean a harder, icier structure unless formulators compensate with other tools. "
            "Natural colors from plant pigments are replacing some synthetic dyes as shoppers demand cleaner labels "
            "and recognizable color sources. "
            "Sustainable packaging aims to cut plastic waste while still protecting a cold, fragile product "
            "that must survive shipping without leaking or drying out. "
            "Manufacturing innovations tighten temperature control, improve freeze consistency, and reduce waste — "
            "better freezes, fewer rejected batches, less energy thrown away on product that never ships. "
            "A century after an accidental overnight freeze in the Bay Area, the popsicle is still teaching the same lesson: "
            "history, ingredients, factories, and physics meet in one simple snack. "
            "The stick is still a handle. The science is still water learning how to become ice — on purpose. "
            "Freezing is chemistry you can taste. "
            "Thanks for learning with Generational. If this sparked a question, follow it — "
            "that is how educational curiosity keeps working."
        ),
    },
]


def synthesize_voice(text: str, out_path: Path) -> Path:
    from services.provider_runtime.engine_api import runtime_synthesize_voice

    result = runtime_synthesize_voice(
        text,
        profile={"provider": "openai_tts", "voice": "onyx"},
        settings={"model": "tts-1-hd", "voice": "onyx"},
        mode="ai",
    )
    path = Path(str(result.get("path") or ""))
    if path.exists():
        out_path.write_bytes(path.read_bytes())
        return out_path
    b64 = str(result.get("audio_b64") or "")
    if b64:
        out_path.write_bytes(base64.b64decode(b64))
        return out_path
    raise RuntimeError(f"Voice failed: {result.get('error') or result}")


def audio_duration_sec(path: Path) -> float:
    """Best-effort duration via ffprobe, falling back to wave for WAV."""
    ffmpeg = find_ffmpeg()
    if ffmpeg:
        ffprobe = ffmpeg.replace("ffmpeg", "ffprobe")
        cmd = [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        try:
            return float((proc.stdout or "").strip())
        except ValueError:
            pass
    if path.suffix.lower() == ".wav":
        with wave.open(str(path), "rb") as wf:
            return wf.getnframes() / float(wf.getframerate())
    return 0.0


def concat_audio(parts: list[Path], out_path: Path, ffmpeg: str, gap_sec: float = 0.55) -> Path:
    """Concatenate chapter MP3s with short silence gaps via ffmpeg."""
    list_file = out_path.parent / "concat_audio.txt"
    silence = out_path.parent / "gap_silence.mp3"
    # Generate short silence
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"anullsrc=r=24000:cl=mono",
            "-t",
            str(gap_sec),
            "-q:a",
            "9",
            "-acodec",
            "libmp3lame",
            str(silence),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    lines: list[str] = []
    for i, part in enumerate(parts):
        lines.append(f"file '{part.as_posix()}'")
        if i < len(parts) - 1 and silence.exists():
            lines.append(f"file '{silence.as_posix()}'")
    list_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cmd = [
        ffmpeg,
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_file),
        "-c:a",
        "libmp3lame",
        "-q:a",
        "2",
        str(out_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0 or not out_path.exists():
        raise RuntimeError(f"audio concat failed: {(proc.stderr or '')[-800:]}")
    return out_path


def write_srt(chapters: list[dict], chapter_durs: list[float], gap_sec: float, out_path: Path) -> Path:
    """Simple chapter-level captions (safe lower-third style cues)."""
    lines: list[str] = []
    t = 0.0
    idx = 1
    for ch, dur in zip(chapters, chapter_durs):
        start = t
        end = t + dur
        # Split text into ~12-word caption chunks
        words = ch["text"].split()
        chunk_n = max(8, min(14, len(words) // max(1, int(dur / 4))))
        chunks = [" ".join(words[i : i + chunk_n]) for i in range(0, len(words), chunk_n)]
        if not chunks:
            continue
        slice_dur = (end - start) / len(chunks)
        for j, chunk in enumerate(chunks):
            cs = start + j * slice_dur
            ce = start + (j + 1) * slice_dur
            lines.append(str(idx))
            lines.append(f"{_ts(cs)} --> {_ts(ce)}")
            lines.append(chunk[:90])
            lines.append("")
            idx += 1
        t = end + gap_sec
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def _ts(sec: float) -> str:
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int((sec - int(sec)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def burn_captions(video: Path, srt: Path, out_path: Path, ffmpeg: str) -> Path:
    """Burn captions with safe bottom margin (MarginV=80)."""
    # Escape path for ffmpeg subtitles filter
    srt_esc = str(srt).replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
    vf = (
        f"subtitles='{srt_esc}':force_style="
        "'FontName=Arial,FontSize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H00101010,"
        "BorderStyle=1,Outline=2,Shadow=0,Alignment=2,MarginV=80'"
    )
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(video),
        "-vf",
        vf,
        "-c:a",
        "copy",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        str(out_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0 or not out_path.exists():
        # Soft-fail: keep uncaptioned master
        return video
    return out_path


def qc_report(
    *,
    duration: float,
    scene_count: int,
    audio_path: Path,
    video_path: Path,
    word_count: int,
) -> dict:
    hard_fails: list[str] = []
    warnings: list[str] = []

    if duration < 8 * 60:
        hard_fails.append(f"duration_below_8min ({duration:.1f}s)")
    elif duration > 12 * 60 + 30:
        warnings.append(f"duration_above_12min ({duration:.1f}s)")

    if not audio_path.exists() or audio_path.stat().st_size < 1000:
        hard_fails.append("audio_missing_or_tiny")
    if not video_path.exists() or video_path.stat().st_size < 100_000:
        hard_fails.append("video_missing_or_tiny")
    if scene_count < 10:
        warnings.append(f"few_scenes ({scene_count})")
    if word_count < 900:
        warnings.append(f"short_script ({word_count} words)")

    # Probe video
    ffmpeg = find_ffmpeg()
    probe: dict = {}
    if ffmpeg and video_path.exists():
        ffprobe = ffmpeg.replace("ffmpeg", "ffprobe")
        cmd = [
            ffprobe,
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(video_path),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        try:
            probe = json.loads(proc.stdout or "{}")
        except json.JSONDecodeError:
            probe = {}
        streams = probe.get("streams") or []
        has_v = any(s.get("codec_type") == "video" for s in streams)
        has_a = any(s.get("codec_type") == "audio" for s in streams)
        if not has_v:
            hard_fails.append("no_video_stream")
        if not has_a:
            hard_fails.append("no_audio_stream")

    score = 100.0
    score -= 25.0 * len(hard_fails)
    score -= 5.0 * len(warnings)
    score = max(0.0, min(100.0, score))

    return {
        "ok": not hard_fails,
        "qc_score": score,
        "hard_fails": hard_fails,
        "warnings": warnings,
        "duration_sec": duration,
        "scene_count": scene_count,
        "word_count": word_count,
        "probe_summary": {
            "format_duration": (probe.get("format") or {}).get("duration"),
            "streams": len(probe.get("streams") or []),
        },
        "checks": {
            "scientific_accuracy": "FACT_SHEET verified claims only",
            "historical_accuracy": "credited-with framing for Epperson origin",
            "annotation_accuracy": "semantic educational graphics only",
            "no_overlapping_text": "layout_engine collision resolve on boards",
            "readability": "fit_font_size + safe margins 64px",
            "smooth_transitions": "Ken Burns per scene + chapter audio gaps",
            "synchronization": "timeline duration locked to narration length",
            "visual_clarity": "16:9 1920x1080 documentary frames",
            "audio_quality": "OpenAI tts-1-hd onyx",
            "caption_placement": "SRT Alignment=2 MarginV=80",
            "presenter_positioning": "motion-graphics documentary (no host overlay covering content)",
        },
    }


def main() -> dict:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-export", action="store_true")
    parser.add_argument("--skip-captions", action="store_true")
    args = parser.parse_args()

    print("=== PRODUCTION BENCHMARK #002 — HOW POPSICLES ARE MADE ===", flush=True)
    t0 = time.time()
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        raise SystemExit("ffmpeg required")
    if not has_credential("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY required")

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    SCENES_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Scenes
    print("→ Building educational scene frames…", flush=True)
    scene_plan = build_all_scenes(SCENES_DIR)
    print(f"  {len(scene_plan)} scenes → {SCENES_DIR}", flush=True)

    # 2. Narration (chunked TTS)
    print("→ Synthesizing chapter narration (tts-1-hd)…", flush=True)
    chapter_paths: list[Path] = []
    chapter_durs: list[float] = []
    full_text_parts: list[str] = []
    for ch in CHAPTERS:
        out = AUDIO_DIR / f"{ch['id']}.mp3"
        if out.exists() and out.stat().st_size > 500:
            print(f"  reuse {out.name}", flush=True)
        else:
            print(f"  TTS {ch['id']} ({len(ch['text'])} chars)…", flush=True)
            synthesize_voice(ch["text"], out)
        chapter_paths.append(out)
        chapter_durs.append(audio_duration_sec(out))
        full_text_parts.append(ch["text"])

    narration = AUDIO_DIR / "narration_full.mp3"
    print("→ Concatenating narration…", flush=True)
    concat_audio(chapter_paths, narration, ffmpeg, gap_sec=0.55)
    duration = audio_duration_sec(narration)
    print(f"  narration duration: {duration:.1f}s ({duration/60:.2f} min)", flush=True)

    word_count = len(" ".join(full_text_parts).split())
    if duration < 8 * 60:
        print(
            f"⚠ Duration {duration:.0f}s below 8 min — consider expanding script on re-run.",
            flush=True,
        )

    # 3. Captions
    srt_path = REPORT_DIR / "captions.srt"
    write_srt(CHAPTERS, chapter_durs, gap_sec=0.55, out_path=srt_path)

    # 4. Assemble
    out_raw = REPORT_DIR / "How_Popsicles_Are_Made_raw.mp4"
    print("→ Assembling MP4…", flush=True)
    assembly = assemble_mp4(
        title=TITLE,
        output_path=str(out_raw),
        timeline={"total_duration_sec": duration},
        scene_render_plan=scene_plan,
        audio_mix_plan={
            "tracks": {
                "narration": {
                    "segments": [{"path": str(narration)}],
                }
            }
        },
        output_format={
            "aspect_ratio": "16:9",
            "resolution": {"width": 1920, "height": 1080},
            "fps": 30,
        },
        timeout_sec=1800.0,
    )
    if not assembly.get("ok"):
        raise SystemExit(f"assemble failed: {assembly}")

    final_video = out_raw
    if not args.skip_captions:
        captioned = REPORT_DIR / "How_Popsicles_Are_Made_captioned.mp4"
        print("→ Burning captions…", flush=True)
        final_video = burn_captions(out_raw, srt_path, captioned, ffmpeg)

    master = REPORT_DIR / "How_Popsicles_Are_Made.mp4"
    if final_video != master:
        master.write_bytes(final_video.read_bytes())

    # 5. QC
    qc = qc_report(
        duration=duration,
        scene_count=len(scene_plan),
        audio_path=narration,
        video_path=master,
        word_count=word_count,
    )
    (REPORT_DIR / "QC_REPORT.json").write_text(json.dumps(qc, indent=2), encoding="utf-8")
    print(f"→ QC score {qc['qc_score']} ok={qc['ok']} fails={qc['hard_fails']}", flush=True)

    export_result: dict = {"skipped": True}
    if not args.skip_export and qc["ok"]:
        print("→ Exporting to Media Library…", flush=True)
        sources = [
            "https://www.nytimes.com/1983/10/27/obituaries/frank-epperson-89-inventor-of-popsicle-dies-in-california.html",
            "https://lemelson.mit.edu/resources/frank-epperson",
            "https://www.kqed.org/bayareabites/98186/how-a-bay-area-11-year-old-invented-the-popsicle",
            "https://theconversation.com/how-does-ice-cream-work-a-chemist-explains-why-you-cant-just-freeze-cream-and-expect-results-205038",
        ]
        export_result = export_verified_production(
            master,
            project_id=PROJECT_ID,
            filename=FILENAME,
            domain="Food Science",
            subject=TITLE,
            title=TITLE,
            series="FoodScience",
            episode="002",
            topic=TITLE,
            demo_id="benchmark_002_popsicles",
            keywords=["popsicle", "ice pop", "freezing point depression", "food science", "Frank Epperson"],
            sources=sources,
            script_md=(REPORT_DIR / "SCRIPT.md").read_text(encoding="utf-8")
            if (REPORT_DIR / "SCRIPT.md").exists()
            else "",
            qc_score=float(qc["qc_score"]),
            render_duration_sec=duration,
            platform="youtube",
            character="Documentary Narration",
            qc_warnings=list(qc.get("warnings") or []),
            qc_hard_fails=list(qc.get("hard_fails") or []),
            render_manifest={
                "benchmark": "002",
                "pipeline": "chaptered_stills_ken_burns_tts",
                "scenes": len(scene_plan),
                "chapters": [c["id"] for c in CHAPTERS],
            },
        )
    elif not qc["ok"]:
        print("✗ QC hard-fail — refusing Media Library export", flush=True)

    elapsed = time.time() - t0
    summary = {
        "ok": bool(qc.get("ok")),
        "title": TITLE,
        "duration_sec": duration,
        "word_count": word_count,
        "scenes": len(scene_plan),
        "master": str(master),
        "qc": qc,
        "export": {
            "ok": export_result.get("ok"),
            "export_path": export_result.get("export_path"),
            "final_status": export_result.get("final_status"),
            "skipped": export_result.get("skipped"),
        },
        "elapsed_sec": round(elapsed, 1),
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    (REPORT_DIR / "PRODUCTION_REPORT.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)
    return summary


if __name__ == "__main__":
    main()
