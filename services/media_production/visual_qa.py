"""Hard visual QA — fail closed before render when scenes lack real media.

Never treats mock://, runtime://, zero-byte files, or missing paths as success.
Writes VISUAL_PIPELINE_REPORT.md for forensic review.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.log import get_logger
from services.media_production.persistence import absolute_media_path

logger = get_logger(__name__)

ROOT = Path(__file__).resolve().parents[2]
_STILL_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
_VIDEO_EXTS = {".mp4", ".mov", ".webm"}
_MIN_BYTES = 1024


def _resolve_file(asset: dict[str, Any] | None, scene: dict[str, Any] | None = None) -> Path | None:
    asset = asset or {}
    scene = scene or {}
    if asset.get("placeholder") and not asset.get("approved_fallback_visual"):
        return None
    for key in ("path", "uri", "local_path", "image_path", "video_path"):
        raw = str(asset.get(key) or scene.get(key) or "")
        if not raw or raw.startswith(("mock://", "runtime://", "http://", "https://")):
            continue
        path = absolute_media_path(raw)
        if path is None:
            candidate = Path(raw)
            if not candidate.is_absolute():
                candidate = ROOT / raw
            path = candidate if candidate.exists() else None
        if path and path.exists() and path.stat().st_size >= _MIN_BYTES:
            if path.suffix.lower() in (_STILL_EXTS | _VIDEO_EXTS):
                return path
    return None


def inspect_scene(scene: dict[str, Any], index: int = 0) -> dict[str, Any]:
    asset = (
        scene.get("resolved_asset")
        or scene.get("asset")
        or scene.get("visual")
        or {}
    )
    if not isinstance(asset, dict):
        asset = {}
    path = _resolve_file(asset, scene)
    prompt = (
        asset.get("prompt")
        or scene.get("image_prompt")
        or scene.get("ai_image_prompt")
        or scene.get("visual_description")
        or ""
    )
    provider = str(asset.get("provider") or asset.get("source") or "")
    ok = path is not None
    reason = ""
    if not ok:
        if asset.get("placeholder") and not asset.get("approved_fallback_visual"):
            reason = "placeholder_or_demo_asset"
        elif not asset:
            reason = "no_resolved_asset"
        elif str(asset.get("path") or "").startswith(("mock://", "runtime://")):
            reason = "fake_uri_not_persisted"
        else:
            reason = "missing_or_invalid_file"
    return {
        "scene_number": scene.get("scene_number") or scene.get("scene_id") or index + 1,
        "narration": scene.get("narration") or "",
        "expected_visual": scene.get("visual_description") or scene.get("ai_image_prompt") or prompt,
        "actual_visual": str(path) if path else "",
        "provider": provider,
        "generation_prompt": prompt,
        "storage_path": str(path) if path else str(asset.get("path") or ""),
        "resolution": f"{asset.get('width', '')}x{asset.get('height', '')}".strip("x") or "",
        "file_size": int(path.stat().st_size) if path else 0,
        "timeline_reference": bool(scene.get("scene_number") or scene.get("scene_id")),
        "renderer_reference": bool(path),
        "approved_fallback_visual": bool(asset.get("approved_fallback_visual")),
        "placeholder": bool(asset.get("placeholder")),
        "validation_result": "PASS" if ok else "FAIL",
        "failure_reason": reason,
    }


def validate_scene_visuals(
    scene_render_plan: list,
    *,
    require_all: bool = True,
) -> dict[str, Any]:
    rows = [inspect_scene(scene if isinstance(scene, dict) else {}, i) for i, scene in enumerate(scene_render_plan or [])]
    passed = [r for r in rows if r["validation_result"] == "PASS"]
    failed = [r for r in rows if r["validation_result"] == "FAIL"]
    ok = bool(rows) and (not failed if require_all else bool(passed))
    return {
        "ok": ok,
        "total_scenes": len(rows),
        "passed": len(passed),
        "failed": len(failed),
        "scenes": rows,
        "error": ""
        if ok
        else (
            f"Visual QA failed: {len(failed)}/{len(rows)} scenes lack validated media. "
            "Production stopped — refusing blank/color-bed render."
        ),
    }


def write_visual_pipeline_report(
    qa: dict[str, Any],
    *,
    output_path: "str | Path" = "VISUAL_PIPELINE_REPORT.md",
    title: str = "",
    extra: "dict[str, Any] | None" = None,
) -> str:
    path = Path(output_path)
    if not path.is_absolute():
        path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    extra = extra or {}
    lines = [
        "# VISUAL PIPELINE REPORT",
        "",
        f"- Generated: {datetime.now(timezone.utc).isoformat()}",
        f"- Title: {title or extra.get('title') or '(untitled)'}",
        f"- Overall: {'PASS' if qa.get('ok') else 'FAIL'}",
        f"- Scenes passed: {qa.get('passed', 0)} / {qa.get('total_scenes', 0)}",
        "",
        "## Root-cause note",
        "",
        "Blank colored MP4s historically came from demo/mock image URIs",
        "(`runtime://image/demo`) that never persisted files. The assembler then",
        "substituted `lavfi color=c=0x101820`. This QA blocks that path.",
        "",
        "## Scene audit",
        "",
        "| Scene | Narration | Expected Visual | Actual Visual | Provider | Prompt | Storage Path | Resolution | File Size | Timeline Ref | Renderer Ref | Result |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in qa.get("scenes") or []:
        narr = str(row.get("narration") or "").replace("|", "/")[:80]
        expected = str(row.get("expected_visual") or "").replace("|", "/")[:80]
        prompt = str(row.get("generation_prompt") or "").replace("|", "/")[:80]
        lines.append(
            "| {scene} | {narr} | {expected} | {actual} | {provider} | {prompt} | {storage} | {res} | {size} | {tref} | {rref} | {result} |".format(
                scene=row.get("scene_number"),
                narr=narr,
                expected=expected,
                actual=str(row.get("actual_visual") or "")[:80],
                provider=str(row.get("provider") or ""),
                prompt=prompt,
                storage=str(row.get("storage_path") or "")[:80],
                res=row.get("resolution") or "",
                size=row.get("file_size") or 0,
                tref="yes" if row.get("timeline_reference") else "no",
                rref="yes" if row.get("renderer_reference") else "no",
                result=row.get("validation_result"),
            )
        )
        if row.get("failure_reason"):
            lines.append(f"| | **FAIL reason:** `{row['failure_reason']}` | | | | | | | | | | |")

    lines.extend(["", "## Failures", ""])
    fails = [r for r in (qa.get("scenes") or []) if r.get("validation_result") == "FAIL"]
    if not fails:
        lines.append("- none")
    else:
        for row in fails:
            lines.append(
                f"- Scene {row.get('scene_number')}: {row.get('failure_reason')} "
                f"(path={row.get('storage_path')!r})"
            )

    if extra:
        lines.extend(["", "## Extra diagnostics", ""])
        for key, value in extra.items():
            lines.append(f"- **{key}**: {value}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("visual_qa.report_written | path=%s ok=%s", path, qa.get("ok"))
    return str(path)
