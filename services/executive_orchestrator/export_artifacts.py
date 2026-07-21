"""Export artifact packaging for Executive Orchestrator."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
EXPORT_ROOT = ROOT / "data" / "productions" / "executive_exports"


def _safe_slug(text: str) -> str:
    cleaned = "".join(c if c.isalnum() or c in "-_" else "_" for c in (text or "production"))
    return cleaned.strip("_")[:64] or "production"


def _resolve_media(path: str | Path | None) -> Path | None:
    raw = str(path or "").strip()
    if not raw or raw.startswith(("mock://", "runtime://")):
        return None
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = ROOT / raw
    try:
        if candidate.is_file() and candidate.stat().st_size > 0:
            return candidate.resolve()
    except OSError:
        return None
    return None


def _write_srt(out_path: Path, caption_segments: list) -> bool:
    lines: list[str] = []
    idx = 1
    for seg in caption_segments or []:
        if not isinstance(seg, dict):
            continue
        text = str(seg.get("text") or seg.get("caption") or "").strip()
        if not text:
            continue
        start = float(seg.get("start_sec") or seg.get("start") or 0.0)
        end = float(seg.get("end_sec") or seg.get("end") or (start + 2.0))

        def ts(sec: float) -> str:
            ms = int(round(max(0.0, sec) * 1000))
            h, rem = divmod(ms, 3_600_000)
            m, rem = divmod(rem, 60_000)
            s, milli = divmod(rem, 1000)
            return f"{h:02d}:{m:02d}:{s:02d},{milli:03d}"

        lines.extend([str(idx), f"{ts(start)} --> {ts(end)}", text, ""])
        idx += 1
    if not lines:
        return False
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return True


def package_export_artifacts(
    context: dict,
    *,
    run_id: str,
    topic: str,
    export_dir: Path | None = None,
) -> dict[str, Any]:
    """Collect / write MP4, thumbnail, captions, description, SEO metadata.

    Uses existing render/seo packages when present; always writes a metadata
    bundle so the studio has durable artifacts even in plan/smoke modes.
    """
    out_dir = Path(export_dir or (EXPORT_ROOT / f"{_safe_slug(topic)}_{run_id}"))
    out_dir.mkdir(parents=True, exist_ok=True)

    items = (
        context.get("selected_ideas")
        or context.get("ideas")
        or context.get("candidates")
        or []
    )
    item = items[0] if items and isinstance(items[0], dict) else {}
    render: dict = {}
    if isinstance(item.get("render_package"), dict):
        render = item["render_package"]
    elif isinstance(context.get("render_package"), dict):
        render = context["render_package"]
    else:
        packages = context.get("production_packages") or []
        if packages and isinstance(packages[0], dict) and isinstance(packages[0].get("render_package"), dict):
            render = packages[0]["render_package"]

    seo = item.get("seo_package") or context.get("seo_package") or {}
    captions = (
        item.get("captions")
        or item.get("subtitle_package")
        or (render.get("caption_render_plan") or {}).get("segments")
        or (item.get("structured_script") or {}).get("caption_plan")
        or []
    )
    thumb = (
        item.get("thumbnail")
        or item.get("thumbnail_concepts")
        or item.get("thumbnail_candidate")
        or item.get("preferred_thumbnail_path")
        or {}
    )

    mp4_raw = (
        render.get("mp4_path")
        or ("" if render.get("mock") else (render.get("output_path") or render.get("file_uri")))
        or ""
    )
    # Prefer verified real MP4; fall back to any existing output file on disk
    mp4_file = _resolve_media(mp4_raw) or _resolve_media(render.get("output_path")) or _resolve_media(
        render.get("file_uri")
    )
    paths: dict[str, str] = {}
    size = 0

    if mp4_file:
        dest = out_dir / "episode.mp4"
        try:
            if mp4_file.resolve() != dest.resolve():
                shutil.copy2(mp4_file, dest)
            paths["mp4"] = str(dest.resolve())
            size = dest.stat().st_size
        except OSError:
            paths["mp4"] = str(mp4_file)
            size = mp4_file.stat().st_size
    elif mp4_raw:
        paths["mp4"] = str(mp4_raw)

    caption_path = out_dir / "captions.json"
    caption_path.write_text(json.dumps(captions, indent=2, default=str), encoding="utf-8")
    paths["captions"] = str(caption_path)
    srt_path = out_dir / "captions.srt"
    seg_list = captions if isinstance(captions, list) else (
        (captions.get("segments") or captions.get("cues") or []) if isinstance(captions, dict) else []
    )
    if _write_srt(srt_path, seg_list):
        paths["captions_srt"] = str(srt_path)

    # Audio sidecar when narration exists
    audio = item.get("audio_package") if isinstance(item.get("audio_package"), dict) else {}
    audio_file = _resolve_media(audio.get("path"))
    if not audio_file:
        narr = ((render.get("audio_mix_plan") or {}).get("tracks") or {}).get("narration") or {}
        segs = narr.get("segments") if isinstance(narr, dict) else None
        if isinstance(segs, list):
            for seg in segs:
                if isinstance(seg, dict):
                    audio_file = _resolve_media(seg.get("path") or seg.get("uri"))
                    if audio_file:
                        break
        if not audio_file and isinstance(narr, dict):
            audio_file = _resolve_media(narr.get("path"))
    if audio_file:
        audio_dest = out_dir / f"narration{audio_file.suffix or '.mp3'}"
        try:
            shutil.copy2(audio_file, audio_dest)
            paths["audio"] = str(audio_dest.resolve())
        except OSError:
            paths["audio"] = str(audio_file)

    description = str(
        seo.get("description")
        or item.get("description")
        or f"Educational video: {topic}"
    )
    desc_path = out_dir / "description.txt"
    desc_path.write_text(description, encoding="utf-8")
    paths["description"] = str(desc_path)

    meta = {
        "title": seo.get("title") or item.get("title") or topic,
        "description": description,
        "keywords": seo.get("keywords") or item.get("keywords") or [],
        "hashtags": seo.get("hashtags") or item.get("hashtags") or [],
        "platforms": context.get("platforms") or [context.get("target_platform")],
        "runtime_sec": context.get("target_runtime_sec") or item.get("estimated_runtime_hint_sec"),
        "pqa_decision": item.get("pqa_decision"),
        "pqa_score": item.get("pqa_score"),
        "seo_package": seo,
        "thumbnail": thumb if isinstance(thumb, dict) else {"path": thumb},
        "render_mock": bool(render.get("mock")),
        "mp4_materialized": bool(mp4_file),
    }
    meta_path = out_dir / "seo_metadata.json"
    meta_path.write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")
    paths["seo_metadata"] = str(meta_path)

    thumb_file = None
    if isinstance(thumb, dict):
        thumb_file = _resolve_media(thumb.get("path"))
    elif isinstance(thumb, str):
        thumb_file = _resolve_media(thumb)
    if not thumb_file:
        # First real scene still from the render plan
        for plan in render.get("scene_render_plan") or []:
            if not isinstance(plan, dict):
                continue
            asset = plan.get("resolved_asset") if isinstance(plan.get("resolved_asset"), dict) else {}
            thumb_file = _resolve_media(asset.get("path") or asset.get("local_path"))
            if thumb_file:
                break
    if thumb_file:
        thumb_dest = out_dir / f"thumbnail{thumb_file.suffix or '.png'}"
        try:
            shutil.copy2(thumb_file, thumb_dest)
            paths["thumbnail"] = str(thumb_dest.resolve())
        except OSError:
            paths["thumbnail"] = str(thumb_file)
    else:
        thumb_path = out_dir / "thumbnail_plan.json"
        thumb_path.write_text(json.dumps(thumb or {"status": "pending"}, indent=2), encoding="utf-8")
        paths["thumbnail"] = str(thumb_path)

    manifest = {
        "run_id": run_id,
        "topic": topic,
        "paths": paths,
        "export_size_bytes": size,
        "qa_decision": item.get("pqa_decision"),
        "qa_score": item.get("pqa_score"),
        "mp4_materialized": bool(mp4_file),
    }
    man_path = out_dir / "EXPORT_MANIFEST.json"
    man_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    paths["manifest"] = str(man_path)

    context["executive_export"] = manifest
    return manifest
