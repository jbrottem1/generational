"""Phase 1 — Launch checklist verifier against frozen architecture."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "data" / "productions" / "_validation" / "launch_plan"

# Launch credentials — presence only (never print secret values)
LAUNCH_CREDENTIAL_KEYS = (
    "OPENAI_API_KEY",  # required to leave Demo Mode / local TTS
    "YOUTUBE_API_KEY",
    "YOUTUBE_ACCESS_TOKEN",
    "YOUTUBE_CLIENT_ID",
    "YOUTUBE_CLIENT_SECRET",
    "YOUTUBE_REFRESH_TOKEN",
    "ELEVENLABS_API_KEY",  # optional voice upgrade
)

REQUIRED_FOR_CONTROLLED_LAUNCH = (
    "OPENAI_API_KEY",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _item(
    key: str,
    label: str,
    ok: bool,
    *,
    required: bool = True,
    detail: str = "",
    how_to: str = "",
) -> dict[str, Any]:
    return {
        "id": key,
        "label": label,
        "ok": ok,
        "required": required,
        "status": "PASS" if ok else ("BLOCKER" if required else "OPTIONAL_MISSING"),
        "detail": detail,
        "how_to": how_to,
    }


def run_launch_checklist() -> dict[str, Any]:
    """Verify everything needed to publish safely under frozen V1."""
    items: list[dict] = []

    # --- Production pipeline ---
    prod_ok = (ROOT / "services" / "production_operations" / "orchestrator.py").exists()
    pipe_ok = (ROOT / "services" / "production_pipeline" / "orchestrator.py").exists()
    items.append(
        _item(
            "production_pipeline",
            "Production pipeline",
            prod_ok and pipe_ok,
            detail="production_operations + production_pipeline present",
            how_to="Studio Ops / run_studio_ops — see LOCAL_EXECUTION.md",
        )
    )

    # --- Export pipeline ---
    ffmpeg = shutil.which("ffmpeg") is not None
    export_docs = (ROOT / "LOCAL_EXECUTION.md").exists()
    local_job = (ROOT / "scripts" / "run_local_render_job.py").exists()
    items.append(
        _item(
            "export_pipeline",
            "Export pipeline",
            bool(ffmpeg and export_docs and local_job),
            detail=f"ffmpeg={'yes' if ffmpeg else 'NO'}; local render job script={'yes' if local_job else 'no'}",
            how_to="brew install ffmpeg; python scripts/run_local_render_job.py",
        )
    )

    # --- Publishing packages ---
    pub_pkg_ok = False
    pub_detail = ""
    try:
        from services.publishing_intelligence.pipeline import build_complete_publish_packages

        pkg = build_complete_publish_packages(
            {
                "topic": "Launch checklist topic",
                "title": "Launch checklist topic",
                "video_path": "/tmp/launch_checklist.mp4",
                "render_package": {
                    "mp4_path": "/tmp/launch_checklist.mp4",
                    "file_uri": "/tmp/launch_checklist.mp4",
                },
            }
        )
        platforms = pkg.get("platforms") or {}
        pub_pkg_ok = len(platforms) >= 5 and bool(pkg.get("seo_title")) and bool(pkg.get("suggested_publish_time"))
        pub_detail = f"platforms={len(platforms)}; title={'yes' if pkg.get('seo_title') else 'no'}"
    except Exception as exc:  # noqa: BLE001
        pub_detail = f"error: {exc}"[:200]
    items.append(
        _item(
            "publishing_packages",
            "Publishing packages",
            pub_pkg_ok,
            detail=pub_detail,
            how_to="python scripts/run_publishing_intelligence.py",
        )
    )

    # --- Thumbnail generation ---
    thumb_mod = (ROOT / "services" / "visual" / "thumbnails.py").exists()
    items.append(
        _item(
            "thumbnail_generation",
            "Thumbnail generation",
            thumb_mod,
            detail="services/visual/thumbnails.py",
            how_to="Included in SEO optimize_content + publishing packages thumbnail_plan",
        )
    )

    # --- SEO generation ---
    seo_ok = False
    seo_detail = ""
    try:
        from services.seo.package import optimize_content

        out = optimize_content({"topic": "Launch SEO check", "title": "Launch SEO check"}, {})
        seo_ok = bool(out.get("seo_package") or out.get("publishing_package"))
        seo_detail = "optimize_content returned package" if seo_ok else "empty SEO package"
    except Exception as exc:  # noqa: BLE001
        seo_detail = f"error: {exc}"[:200]
    items.append(
        _item(
            "seo_generation",
            "SEO generation",
            seo_ok,
            detail=seo_detail,
            how_to="services.seo.package.optimize_content",
        )
    )

    # --- Analytics recording ---
    analytics_ok = False
    analytics_detail = ""
    try:
        from services.publishing_intelligence.analytics_layer import (
            build_intelligence_analytics_record,
            list_intelligence_records,
        )

        rec = build_intelligence_analytics_record(
            candidate={"topic": "analytics check", "platform": "youtube_shorts"},
            platform="youtube_shorts",
            predicted={"ctr": 4.0},
            actual={"views": 1},
        )
        analytics_ok = bool(rec.get("record_id") and "actual_metrics" in rec)
        n = len(list_intelligence_records(limit=5))
        analytics_detail = f"schema_ok; stored_records≈{n}"
    except Exception as exc:  # noqa: BLE001
        analytics_detail = f"error: {exc}"[:200]
    items.append(
        _item(
            "analytics_recording",
            "Analytics recording",
            analytics_ok,
            detail=analytics_detail,
            how_to="data/analytics/intelligence_records.json via run_intelligence_cycle",
        )
    )

    # --- Error recovery ---
    recovery = (ROOT / "services" / "production_operations" / "resilience.py").exists()
    items.append(
        _item(
            "error_recovery",
            "Error recovery",
            recovery,
            detail="ops resilience: retry / repair / fallback / continue",
            how_to="services.production_operations.resilience.run_stage_engines",
        )
    )

    # --- Logging ---
    log_ok = (ROOT / "core" / "log.py").exists()
    items.append(
        _item(
            "logging",
            "Logging",
            log_ok,
            detail="core.log.get_logger / log_event",
            how_to="Structured log_event calls across ops, publishing, analytics",
        )
    )

    # --- Configuration ---
    env_example = (ROOT / ".env.example").exists()
    exec_mode = (ROOT / "EXECUTION_MODE.md").exists() or (ROOT / "LOCAL_EXECUTION.md").exists()
    items.append(
        _item(
            "configuration",
            "Configuration",
            env_example and exec_mode,
            detail=f".env.example={'yes' if env_example else 'no'}; local execution docs={'yes' if exec_mode else 'no'}",
            how_to="Copy .env.example → .env; ExecutionMode.LOCAL only",
        )
    )

    # --- API keys / credentials ---
    from core.env import credential_status, load_application_env

    load_application_env(create_if_missing=False)
    cred_rows = {k: credential_status(k) for k in LAUNCH_CREDENTIAL_KEYS}
    openai_ok = bool(cred_rows["OPENAI_API_KEY"]["present"])
    youtube_publish = any(
        cred_rows[k]["present"]
        for k in ("YOUTUBE_ACCESS_TOKEN", "YOUTUBE_REFRESH_TOKEN", "YOUTUBE_CLIENT_ID")
    )
    items.append(
        _item(
            "required_api_keys",
            "Required API keys",
            openai_ok,
            detail="OPENAI_API_KEY "
            + ("present" if openai_ok else "MISSING — Demo Mode / limited production"),
            how_to="Set OPENAI_API_KEY in project-root .env (never commit)",
        )
    )
    items.append(
        _item(
            "required_credentials",
            "YouTube publish credentials (API/OAuth)",
            youtube_publish or bool(cred_rows["YOUTUBE_API_KEY"]["present"]),
            required=False,
            detail=(
                "Present — automated or API-assisted upload available"
                if (youtube_publish or cred_rows["YOUTUBE_API_KEY"]["present"])
                else "Missing — Week 1 OK with manual YouTube Studio upload from package checklist"
            ),
            how_to="Set YOUTUBE_* in .env for automated upload; or upload MP4 manually using package metadata",
        )
    )

    # Optional voice
    items.append(
        _item(
            "optional_elevenlabs",
            "Optional ElevenLabs voice",
            bool(cred_rows["ELEVENLABS_API_KEY"]["present"]),
            required=False,
            detail="upgrade path when OpenAI TTS is insufficient",
            how_to="ELEVENLABS_API_KEY in .env",
        )
    )

    # Disk smoke: intelligence cycle CLI
    items.append(
        _item(
            "publishing_intelligence_cli",
            "Publishing intelligence CLI",
            (ROOT / "scripts" / "run_publishing_intelligence.py").exists(),
            detail="scripts/run_publishing_intelligence.py",
            how_to="python scripts/run_publishing_intelligence.py --audit",
        )
    )

    blockers = [i for i in items if i["required"] and not i["ok"]]
    optional_gaps = [i for i in items if not i["required"] and not i["ok"]]
    passed = sum(1 for i in items if i["ok"])
    report = {
        "generated_at": _now(),
        "version": "1.0.0",
        "mission": "Version 1 Launch Plan — Phase 1 Checklist",
        "ready_to_publish": len(blockers) == 0,
        "passed": passed,
        "total": len(items),
        "blockers": blockers,
        "optional_gaps": optional_gaps,
        "items": items,
        "credential_presence": {
            k: {"present": v["present"], "source": v["source"]} for k, v in cred_rows.items()
        },
        "documentation": {
            "launch_plan": "VERSION_1_LAUNCH_PLAN.md",
            "operations_manual": "VERSION_1_OPERATIONS_MANUAL.md",
            "publishing_intelligence": "PUBLISHING_INTELLIGENCE.md",
            "local_execution": "LOCAL_EXECUTION.md",
            "env_example": ".env.example",
        },
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "LAUNCH_CHECKLIST.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (OUT_DIR / "LAUNCH_CHECKLIST.md").write_text(_checklist_md(report), encoding="utf-8")
    (ROOT / "LAUNCH_CHECKLIST.md").write_text(_checklist_md(report), encoding="utf-8")
    return report


def _checklist_md(report: dict) -> str:
    lines = [
        "# Version 1 Launch Checklist",
        "",
        f"Generated: {report.get('generated_at')}",
        f"Ready to publish: **{'YES' if report.get('ready_to_publish') else 'NO'}**",
        f"Passed: {report.get('passed')}/{report.get('total')}",
        "",
        "## Verification results",
        "",
    ]
    for i in report.get("items") or []:
        mark = "x" if i["ok"] else " "
        lines.append(f"- [{mark}] **{i['label']}** — `{i['status']}` — {i.get('detail') or ''}")
        if i.get("how_to") and not i["ok"]:
            lines.append(f"  - How: {i['how_to']}")
    if report.get("blockers"):
        lines.extend(["", "## Blockers (must resolve before public publish)", ""])
        for b in report["blockers"]:
            lines.append(f"1. **{b['label']}** — {b.get('detail')} → {b.get('how_to')}")
    lines.extend(
        [
            "",
            "## Docs",
            "",
            "- VERSION_1_LAUNCH_PLAN.md",
            "- VERSION_1_OPERATIONS_MANUAL.md",
            "- PUBLISHING_INTELLIGENCE.md",
            "- LOCAL_EXECUTION.md",
            "- .env.example",
            "",
        ]
    )
    return "\n".join(lines)
