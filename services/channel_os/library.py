"""Channel Content Library — organize productions under Videos/{Channel}/Category/Topic/."""

from __future__ import annotations

import json
import shutil
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from core.storage.json_collection import slugify

SUBFOLDERS: tuple[str, ...] = (
    "Project",
    "Assets",
    "Audio",
    "Captions",
    "Thumbnail",
    "Export",
    "Reports",
    "Analytics",
)


def resolve_videos_root() -> Path:
    """Shared Desktop Videos root (same resolver as GenOS / execution_mode)."""
    from services.media_production.execution_mode import canonical_export_dir

    return canonical_export_dir(create=True)


def channel_project_root(
    brand_name: str,
    category: str,
    topic: str,
    *,
    create: bool = True,
) -> Path:
    root = (
        resolve_videos_root()
        / brand_name.strip()
        / _title(category)
        / _title(topic)
    )
    if create:
        ensure_channel_tree(root)
    return root


def ensure_channel_tree(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    for sub in SUBFOLDERS:
        (root / sub).mkdir(parents=True, exist_ok=True)
    return root


def _title(text: str) -> str:
    text = (text or "General").strip()
    # Keep readable folder names
    return " ".join(w.capitalize() if w.islower() else w for w in text.replace("_", " ").split()) or "General"


def _copy_if(src: Any, dest: Path) -> str | None:
    if not src:
        return None
    path = Path(str(src))
    if not path.is_file():
        return None
    dest.parent.mkdir(parents=True, exist_ok=True)
    if path.resolve() != dest.resolve():
        shutil.copy2(path, dest)
    return str(dest)


def package_channel_production(
    ops_result: dict[str, Any],
    *,
    profile: dict[str, Any],
    category: str = "",
) -> dict[str, Any]:
    """Copy ops artifacts into the Channel Content Library tree + write reports."""
    report = ops_result.get("report") or {}
    status = ops_result.get("status") or {}
    brief = ops_result.get("brief") or {}
    topic = str(brief.get("topic") or report.get("topic") or "Untitled")
    cat = category or str(
        (profile.get("topic_categories") or ["General"])[0]
        if profile.get("topic_categories")
        else brief.get("domain") or "General"
    )
    brand = str(profile.get("brand_name") or profile.get("name") or "Channel")
    root = channel_project_root(brand, cat, topic, create=True)

    # Locate common artifact locations from ops status / context
    arts = _discover_artifacts(ops_result)
    stamp = date.today().isoformat()
    base = f"{stamp}_{slugify(topic)[:40]}"

    paths: dict[str, Any] = {
        "project_root": str(root),
        "channel_id": profile.get("channel_id"),
        "brand_name": brand,
        "category": cat,
        "topic": topic,
    }

    if arts.get("mp4"):
        paths["export_mp4"] = _copy_if(arts["mp4"], root / "Export" / f"{base}.mp4")
    if arts.get("audio"):
        paths["audio"] = _copy_if(arts["audio"], root / "Audio" / f"{base}_narration.mp3")
    if arts.get("captions"):
        paths["captions"] = _copy_if(arts["captions"], root / "Captions" / f"{base}.srt")
    if arts.get("thumbnail"):
        paths["thumbnail"] = _copy_if(arts["thumbnail"], root / "Thumbnail" / f"{base}.jpg")

    for img in arts.get("images") or []:
        name = Path(str(img)).name
        _copy_if(img, root / "Assets" / name)

    # Branding / production reports
    branding = {
        "channel_id": profile.get("channel_id"),
        "brand_name": brand,
        "narrator_profile": profile.get("narrator_profile"),
        "voice_profile": profile.get("voice_profile"),
        "visual_style": profile.get("visual_style"),
        "world_preferences": profile.get("world_preferences"),
        "thumbnail_style": profile.get("thumbnail_style"),
        "tone": profile.get("tone"),
        "platforms": profile.get("platforms"),
        "production_id": ops_result.get("production_id") or status.get("production_id"),
        "topic": topic,
        "category": cat,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ops_style": brief.get("style"),
        "ops_narrator": brief.get("narrator"),
        "ops_voice": brief.get("voice") or brief.get("voice_preference"),
    }
    brand_path = root / "Reports" / "CHANNEL_BRANDING.json"
    brand_path.write_text(json.dumps(branding, indent=2) + "\n", encoding="utf-8")
    paths["branding_report"] = str(brand_path)

    prod_report = {
        "production_id": branding["production_id"],
        "success": bool(status.get("success") or ops_result.get("success")),
        "topic": topic,
        "channel_id": profile.get("channel_id"),
        "brand_name": brand,
        "report": report,
        "elapsed_ms": status.get("elapsed_ms") or ops_result.get("elapsed_ms"),
        "pipeline_health": status.get("pipeline_health"),
        "packaged_at": datetime.now(timezone.utc).isoformat(),
        "artifact_paths": {k: v for k, v in paths.items() if k != "project_root"},
    }
    report_path = root / "Reports" / "PRODUCTION_REPORT.json"
    report_path.write_text(json.dumps(prod_report, indent=2, default=str) + "\n", encoding="utf-8")
    paths["production_report"] = str(report_path)

    (root / "Reports" / "CHANNEL_PRODUCTION.md").write_text(
        _md_report(branding, prod_report, paths),
        encoding="utf-8",
    )
    (root / "Project" / "CHANNEL_PROFILE.json").write_text(
        json.dumps(
            {
                "channel_id": profile.get("channel_id"),
                "brand_name": brand,
                "narrator_profile": profile.get("narrator_profile"),
                "voice_profile": profile.get("voice_profile"),
                "visual_style": profile.get("visual_style"),
                "world_preferences": profile.get("world_preferences"),
                "thumbnail_style": profile.get("thumbnail_style"),
                "hashtag_strategy": profile.get("hashtag_strategy"),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "Analytics" / "PLACEHOLDER.json").write_text(
        json.dumps(
            {
                "note": "Analytics providers soft-wired; history lives on channel profile",
                "channel_id": profile.get("channel_id"),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return paths


def _discover_artifacts(ops_result: dict[str, Any]) -> dict[str, Any]:
    status = ops_result.get("status") or {}
    report = ops_result.get("report") or {}
    export = status.get("export") or report.get("export") or {}
    outs: dict[str, Any] = {"images": []}

    for key in ("video_path", "mp4_path", "final_video", "episode_path"):
        if export.get(key):
            outs["mp4"] = export[key]
            break
    if not outs.get("mp4"):
        for key in ("video_path", "mp4_path", "output_path"):
            if report.get(key):
                outs["mp4"] = report[key]
                break

    for key in ("narration_path", "audio_path", "voice_path"):
        if report.get(key) or export.get(key):
            outs["audio"] = report.get(key) or export.get(key)
            break

    for key in ("captions_path", "srt_path"):
        if report.get(key) or export.get(key):
            outs["captions"] = report.get(key) or export.get(key)
            break

    for key in ("thumbnail_path", "thumb_path"):
        if report.get(key) or export.get(key):
            outs["thumbnail"] = report.get(key) or export.get(key)
            break

    # Executive export / ops context paths
    ctx = ops_result.get("context") if isinstance(ops_result.get("context"), dict) else {}
    exec_exp = ctx.get("executive_export") if isinstance(ctx.get("executive_export"), dict) else {}
    paths = exec_exp.get("paths") if isinstance(exec_exp.get("paths"), dict) else {}
    if paths.get("mp4") and not outs.get("mp4"):
        outs["mp4"] = paths["mp4"]
    if paths.get("audio") and not outs.get("audio"):
        outs["audio"] = paths["audio"]
    if (paths.get("captions_srt") or paths.get("captions")) and not outs.get("captions"):
        outs["captions"] = paths.get("captions_srt") or paths.get("captions")
    if paths.get("thumbnail") and not outs.get("thumbnail"):
        outs["thumbnail"] = paths["thumbnail"]

    # Candidate render package
    for cand in ctx.get("candidates") or ops_result.get("candidates") or []:
        if not isinstance(cand, dict):
            continue
        rp = cand.get("render_package") if isinstance(cand.get("render_package"), dict) else {}
        if not outs.get("mp4"):
            outs["mp4"] = rp.get("mp4_path") or rp.get("output_path")
        audio = cand.get("audio_package") if isinstance(cand.get("audio_package"), dict) else {}
        if not outs.get("audio"):
            outs["audio"] = audio.get("path")
        break

    # Scan ops directory
    prod_id = ops_result.get("production_id") or status.get("production_id")
    if prod_id:
        try:
            from services.production_operations.status import ops_dir

            root = ops_dir(str(prod_id))
            if root.is_dir():
                for pattern, field in (
                    ("*.mp4", "mp4"),
                    ("*.mp3", "audio"),
                    ("*.srt", "captions"),
                    ("*thumb*.jpg", "thumbnail"),
                    ("*thumb*.png", "thumbnail"),
                ):
                    if outs.get(field):
                        continue
                    found = sorted(root.rglob(pattern))
                    if found:
                        outs[field] = str(found[0])
                images = list(root.rglob("*.jpg")) + list(root.rglob("*.png"))
                outs["images"] = [str(p) for p in images[:24]]
        except Exception:  # noqa: BLE001
            pass

    # Scan executive export folder
    if paths.get("manifest"):
        man_parent = Path(str(paths["manifest"])).parent
        if man_parent.is_dir():
            if not outs.get("mp4"):
                mp4s = sorted(man_parent.glob("*.mp4"))
                if mp4s:
                    outs["mp4"] = str(mp4s[0])
            if not outs.get("audio"):
                auds = sorted(man_parent.glob("narration.*"))
                if auds:
                    outs["audio"] = str(auds[0])
            if not outs.get("captions"):
                srts = sorted(man_parent.glob("*.srt"))
                if srts:
                    outs["captions"] = str(srts[0])
            if not outs.get("thumbnail"):
                thumbs = sorted(man_parent.glob("thumbnail.*"))
                if thumbs:
                    outs["thumbnail"] = str(thumbs[0])
    return outs


def _md_report(branding: dict[str, Any], prod: dict[str, Any], paths: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# {branding.get('brand_name')} — Channel Production Report",
            "",
            f"**Topic:** {branding.get('topic')}",
            f"**Category:** {branding.get('category')}",
            f"**Production ID:** {branding.get('production_id')}",
            f"**Success:** {prod.get('success')}",
            "",
            "## Branding applied",
            "",
            f"- Narrator: `{branding.get('narrator_profile')}`",
            f"- Voice: `{branding.get('voice_profile')}`",
            f"- Visual style: {branding.get('visual_style')}",
            f"- World: {branding.get('world_preferences')}",
            f"- Thumbnail style: {branding.get('thumbnail_style')}",
            "",
            f"**Project root:** `{paths.get('project_root')}`",
            "",
        ]
    )
