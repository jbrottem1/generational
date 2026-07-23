"""Phase 1 — operational health checks for V1 Launch (compose existing systems)."""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.env import load_application_env, project_root, startup_credential_report

OUT_DIR = project_root() / "data" / "productions" / "_validation" / "v1_launch"
REPORT_JSON = OUT_DIR / "LAUNCH_READINESS_REPORT.json"
REPORT_MD = project_root() / "V1_LAUNCH_READINESS.md"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_launch_health_checks() -> dict[str, Any]:
    """Verify subsystems, APIs, assets, and config — no new engines."""
    load_application_env(create_if_missing=False)
    checks: list[dict[str, Any]] = []

    def add(cid: str, ok: bool, detail: str, *, blocker: bool = False) -> None:
        checks.append({"id": cid, "ok": ok, "detail": detail, "blocker": blocker and not ok})

    # Credentials
    creds = startup_credential_report()
    for key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "ELEVENLABS_API_KEY"):
        st = (creds.get("credentials") or {}).get(key) or {}
        present = bool(st.get("present") or st.get("loaded") or os.environ.get(key))
        add(f"credential_{key}", present, f"{key} present={present}", blocker=key in ("OPENAI_API_KEY", "ELEVENLABS_API_KEY"))

    # Execution / export
    try:
        from services.media_production.execution_mode import canonical_export_dir, get_execution_context

        ctx = get_execution_context()
        export = canonical_export_dir(create=True)
        add("execution_local", ctx.mode.value == "local", f"mode={ctx.mode.value}")
        add("export_root", export.is_dir(), f"path={export}", blocker=True)
        add("can_render", bool(ctx.can_render_media), f"can_render_media={ctx.can_render_media}", blocker=True)
    except Exception as exc:  # noqa: BLE001
        add("execution_local", False, str(exc)[:200], blocker=True)

    # ffmpeg
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    add("ffmpeg", bool(ffmpeg), f"ffmpeg={ffmpeg}", blocker=True)
    add("ffprobe", bool(ffprobe), f"ffprobe={ffprobe}", blocker=True)

    # Engine registry
    try:
        import engines  # noqa: F401
        from engines.registry import get_engine

        required = (
            "research",
            "psychology",
            "ai_director",
            "script_generation",
            "studio_render",
            "voice",
            "optimization_lab",
            "production_qa",
            "production_operations",
        )
        missing = [k for k in required if get_engine(k) is None]
        add("engine_registry", not missing, f"missing={missing or 'none'}", blocker=True)
    except Exception as exc:  # noqa: BLE001
        add("engine_registry", False, str(exc)[:200], blocker=True)

    # Soft composers present
    for label, mod in (
        ("genos", "services.generational_os"),
        ("trend_opportunity", "services.trend_opportunity"),
        ("world_builder", "services.world_builder"),
        ("visual_asset_director", "services.visual_asset_director"),
        ("cinematic_director", "services.cinematic_director"),
        ("voice_studio", "services.voice_studio"),
        ("creative_excellence", "services.creative_excellence"),
        ("audience_intelligence", "services.audience_intelligence"),
        ("publishing_intelligence", "services.publishing_intelligence"),
        ("channel_os", "services.channel_os"),
        ("validation_program", "services.validation_program"),
    ):
        try:
            __import__(mod)
            add(f"package_{label}", True, mod)
        except Exception as exc:  # noqa: BLE001
            add(f"package_{label}", False, f"{mod}: {exc}"[:180], blocker=False)

    # Existing launch readiness audit (analytics/publishing oriented)
    legacy = {}
    try:
        from services.launch_readiness import run_launch_readiness_audit

        legacy = run_launch_readiness_audit()
        add(
            "legacy_launch_audit",
            True,
            f"score={legacy.get('launch_readiness_score')}",
        )
    except Exception as exc:  # noqa: BLE001
        add("legacy_launch_audit", False, str(exc)[:180])

    blockers = [c for c in checks if c.get("blocker")]
    ok_n = sum(1 for c in checks if c.get("ok"))
    report = {
        "generated_at": _now(),
        "program": "Generational V1 Launch Program — Phase 1",
        "checks": checks,
        "passed": ok_n,
        "total": len(checks),
        "pass_rate": round(ok_n / max(1, len(checks)), 3),
        "blockers": blockers,
        "operational": len(blockers) == 0,
        "legacy_launch_readiness_score": legacy.get("launch_readiness_score"),
        "publishing_enabled": False,
        "note": "Architecture frozen. Health only — no new engines.",
    }
    return report


def write_launch_readiness_report(report: dict[str, Any] | None = None) -> dict[str, Path]:
    report = report or run_launch_health_checks()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    lines = [
        "# V1 Launch Readiness Report — Phase 1",
        "",
        f"**Generated:** {report['generated_at']}",
        f"**Operational (no blockers):** {'YES' if report.get('operational') else 'NO'}",
        f"**Checks passed:** {report['passed']} / {report['total']} ({report['pass_rate']})",
        f"**Legacy audit score:** {report.get('legacy_launch_readiness_score')}",
        "",
        "## Blockers",
        "",
    ]
    if report.get("blockers"):
        for b in report["blockers"]:
            lines.append(f"- `{b['id']}` — {b['detail']}")
    else:
        lines.append("- None")
    lines += ["", "## All checks", ""]
    for c in report.get("checks") or []:
        mark = "OK" if c.get("ok") else "FAIL"
        lines.append(f"- [{mark}] `{c['id']}` — {c['detail']}")
    lines += ["", "_Publishing disabled for launch pilot._", ""]
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")
    return {"json": REPORT_JSON, "markdown": REPORT_MD}
