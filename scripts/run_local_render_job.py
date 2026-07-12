#!/usr/bin/env python3
"""Execute LOCAL_RENDER_JOB.json on the user's Mac (local mode only)."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.env import load_application_env

load_application_env()

from services.animation.communicator_delivery import build_paused_narration
from services.animation.foundation_gate import evaluate_foundation_export
from services.animation.foundation_v2 import STUDIO_BLUE_TOP, V2_STICK_SPEC
from services.animation.performer import render_lip_sync_performance
from services.animation.stick_figure import StickFigureSpec
from services.education.director_review import review_lesson
from services.media_production.execution_mode import get_execution_context
from services.media_production.local_cache import copy_catalog_image_to_cache
from services.generational_os.export import export_verified_production
from services.media_production.ffmpeg_assembler import find_ffmpeg
from services.provider_runtime.config import has_credential
from services.reality.qc import collect_demo_image_ids, evaluate_reality_export
from services.reality.smoke_narration import build_smoke_narration


def _warm_image_cache(image_ids: list[str]) -> list[str]:
    warmed = []
    for iid in image_ids:
        path = copy_catalog_image_to_cache(iid)
        if path:
            warmed.append(iid)
    return warmed


def _load_job(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if int(data.get("schema_version") or 0) >= 3:
        return data
    return load_render_job(path)


def execute_job(job_path: Path, *, smoke: bool = False) -> dict:
    ctx = get_execution_context()
    if not ctx.can_render_media:
        return {
            "ok": False,
            "status": "awaiting_local_render",
            "error": "This machine is in CLOUD mode. Run on your Mac locally.",
            "mode": ctx.mode.value,
        }

    job = _load_job(job_path)
    project_id = str(job.get("project_id") or job.get("job_id") or "job")
    script = job.get("script") or {}
    beats = script.get("beats") or job.get("timing", {}).get("beats") or []
    demo_id = (job.get("animations") or {}).get("demo_id") or ""
    export = job.get("export") or {}
    filename = str(export.get("filename") or "output.mp4")

    work = ROOT / "data" / "productions" / "_validation" / "local_jobs" / project_id
    work.mkdir(parents=True, exist_ok=True)
    voice = work / "narration.mp3"
    episode = work / "episode.mp4"

    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        return {"ok": False, "error": "ffmpeg missing"}

    image_ids = [a.get("image_id") for a in (job.get("assets") or {}).get("images") or [] if a.get("image_id")]
    _warm_image_cache(image_ids)

    if smoke or not has_credential("OPENAI_API_KEY"):
        if not smoke:
            print("WARNING: OPENAI_API_KEY missing — using smoke narration", file=sys.stderr)
        build_smoke_narration(beats, voice, ffmpeg=ffmpeg)
    else:
        narr = job.get("narration") or {}
        build_paused_narration(
            beats,
            voice,
            ffmpeg=ffmpeg,
            voice=str(narr.get("voice") or "nova"),
            model=str(narr.get("model") or "tts-1-hd"),
        )

    spec = StickFigureSpec(
        character_id=V2_STICK_SPEC.get("character_id", "CHAR-PROFESSOR-V2-001"),
        name=V2_STICK_SPEC.get("name", "Professor Gen"),
        attire=V2_STICK_SPEC.get("attire", "lab_coat"),
        head_ratio=float(V2_STICK_SPEC.get("head_ratio", 0.38)),
    )
    t0 = time.time()
    result = render_lip_sync_performance(
        audio_path=voice,
        output_path=episode,
        fps=int((job.get("timing") or {}).get("fps") or 24),
        bg_color=STUDIO_BLUE_TOP,
        demo_id=demo_id,
        educator_mode=True,
        max_duration_sec=60.0,
        spec=spec,
    )
    if not result.get("ok") or not episode.is_file():
        return {"ok": False, "error": "render failed", "result": result}

    export_result = export_verified_production(
        episode,
        project_id=project_id,
        filename=filename,
        domain=str(job.get("domain") or export.get("domain_folder") or ""),
        subject=str(job.get("title") or ""),
        demo_id=demo_id,
        render_duration_sec=result.get("duration_sec"),
    )
    if not export_result.get("ok"):
        return {"ok": False, **export_result, "render": result}

    export_path = Path(str(export_result["export_path"]))

    edu = review_lesson(
        hook=str(script.get("hook") or ""),
        script=" ".join(str(b.get("text") or "") for b in beats),
        takeaway=str(script.get("takeaway") or ""),
        main_concept=str(script.get("main_concept") or ""),
        beats=beats,
        has_visual_demo=True,
        sources=list(script.get("sources") or []),
    )
    production = {
        "title": job.get("title"),
        "demo_id": demo_id,
        "export_path": str(export_path),
        "duration_sec": result.get("duration_sec"),
        "educational_review": edu.to_dict(),
    }
    gate = evaluate_foundation_export(production, script=script, educational=edu.to_dict())
    reality_qc = evaluate_reality_export(image_ids=collect_demo_image_ids(demo_id), demo_id=demo_id)

    return {
        "ok": True,
        "status": "export_verified",
        "message": "Video exported and verified on local Desktop.",
        "export_path": str(export_path),
        "verification": export_result.get("verification"),
        "duration_sec": result.get("duration_sec"),
        "render_sec": round(time.time() - t0, 2),
        "foundation_gate": gate.to_dict(),
        "reality_qc": reality_qc.to_dict(),
        "mode": ctx.mode.value,
        "os_version": job.get("os_version") or "2.5",
        "domain_folder": export_result.get("domain_folder"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute LOCAL_RENDER_JOB.json")
    parser.add_argument("--job", default="LOCAL_RENDER_JOB.json", help="Path to render job JSON")
    parser.add_argument("--smoke", action="store_true", help="Use smoke narration when TTS unavailable")
    args = parser.parse_args()
    payload = execute_job(Path(args.job), smoke=args.smoke)
    print(json.dumps(payload, indent=2))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
