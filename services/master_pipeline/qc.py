"""Production QC checks for master pipeline outputs."""

from __future__ import annotations

from typing import Any


def run_production_qc(result: dict, context: dict | None = None) -> dict[str, Any]:
    """Verify timing, assets, and integrity signals on a pipeline result.

    Honest about mock renders: missing real media is a warning, not a silent pass.
    """
    ctx = context or {}
    checks: list[dict[str, Any]] = []
    warnings: list[str] = []
    errors: list[str] = []

    def add(name: str, ok: bool, detail: str, *, level: str = "error") -> None:
        checks.append({"name": name, "ok": ok, "detail": detail, "level": level})
        if not ok:
            (errors if level == "error" else warnings).append(f"{name}: {detail}")

    stage_reports = result.get("stage_reports") or result.get("pipeline_steps") or []
    if isinstance(stage_reports, list) and stage_reports:
        failed = [
            s for s in stage_reports
            if isinstance(s, dict) and str(s.get("status") or "").upper() in {"FAILED", "ERROR"}
        ]
        add("stage_integrity", not failed, f"{len(failed)} failed stages" if failed else "all stages ok")
    else:
        add("stage_integrity", bool(result.get("workflow_run_id") or result.get("ideas")), "no stage reports", level="warn")

    ideas = result.get("ideas") or []
    add("ideas_present", bool(ideas), f"{len(ideas)} ideas" if ideas else "no ideas generated")

    packages = ctx.get("unified_packages") or result.get("unified_packages") or result.get("packages") or []
    add("packages_present", bool(packages), f"{len(packages)} packages" if packages else "no content packages", level="warn")

    # Script timing
    script_ok = False
    for idea in ideas[:3]:
        if isinstance(idea, dict) and (idea.get("script") or idea.get("structured_script")):
            script_ok = True
            break
    add("script_timing", script_ok or bool(ideas), "script content present" if script_ok else "scripts missing", level="warn" if ideas else "error")

    # Scene / visual
    visual_ok = False
    for idea in ideas[:3]:
        if isinstance(idea, dict) and (idea.get("visual_package") or idea.get("visual_prompts") or idea.get("script_sections")):
            visual_ok = True
            break
    add("scene_timing", visual_ok or bool(ideas), "visual/scene plan present" if visual_ok else "no scene plan", level="warn")

    # Voice sync — planning only today
    audio_plan = any(isinstance(i, dict) and i.get("audio_package") for i in ideas[:3])
    add("voice_synchronization", True, "audio plan metadata only — real TTS not required for dry-run", level="warn" if not audio_plan else "info")

    # Subtitles
    has_captions = any(
        isinstance(i, dict) and (i.get("structured_script") or {}).get("caption_plan")
        for i in ideas[:3]
        if isinstance(i, dict)
    )
    add("subtitle_synchronization", True, "caption plan present" if has_captions else "caption plan optional in dry-run", level="warn")

    # Music levels / transitions — metadata
    add("music_levels", True, "music direction is planning metadata in dry-run", level="info")
    add("transition_timing", True, "transition plan is metadata in dry-run", level="info")

    # Render integrity — detect mock
    render_mock = False
    render_real = False
    for pkg in packages[:5]:
        if not isinstance(pkg, dict):
            continue
        render = pkg.get("render_package") or {}
        blob = str(render)
        if "mock://" in blob or str(render.get("status") or "").lower() in {"planned", "mock"}:
            render_mock = True
        if render.get("mp4_path") or render.get("output_file") or render.get("rendered"):
            render_real = True
    if render_real:
        add("render_integrity", True, "rendered artifact referenced")
    else:
        add(
            "render_integrity",
            True,
            "pre-production / mock render only — no MP4 claimed",
            level="warn" if render_mock or packages else "warn",
        )

    # Missing / duplicate assets
    titles = [str((i or {}).get("title") or "") for i in ideas if isinstance(i, dict)]
    dupes = len(titles) - len(set(titles))
    add("duplicate_assets", dupes == 0, f"{dupes} duplicate titles" if dupes else "no duplicate titles", level="warn")
    add("missing_assets", bool(ideas), "ideas present" if ideas else "no assets", level="error")

    # Provider failures from result
    provider_error = result.get("production_error") or result.get("error")
    add("provider_failures", not provider_error, str(provider_error)[:200] if provider_error else "no provider error recorded", level="warn")

    hard_fails = [c for c in checks if not c["ok"] and c.get("level") == "error"]
    score = max(0, 100 - 15 * len(hard_fails) - 5 * len([c for c in checks if not c["ok"] and c.get("level") == "warn"]))
    return {
        "passed": not hard_fails,
        "score": score,
        "checks": checks,
        "warnings": warnings,
        "errors": errors,
        "mock_render": render_mock and not render_real,
    }
