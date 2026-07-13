"""RenderValidator — is this package actually renderable?

Runs the pre-flight checklist over a render plan: every scene has a
visual and narration, captions and an audio plan exist, total runtime sits
inside the short-form window, the output format is supported, and missing
assets are surfaced. Returns SUCCESS / WARNING / FAILED / SKIPPED with
per-check diagnostics plus a 0-100 production readiness score — the number
Publishing (Agent 7) gates on.
"""

from __future__ import annotations

from engines.render.models import (
    MAX_RUNTIME_SEC,
    MIN_RUNTIME_SEC,
    OUTPUT_FORMAT,
    RenderStatus,
)

# Readiness weight per check — blockers weigh more than polish. Sum == 1.0.
CHECK_WEIGHTS = {
    "scenes_present": 0.15,
    "scenes_have_visuals": 0.20,
    "scenes_have_narration": 0.20,
    "captions_exist": 0.10,
    "audio_plan_exists": 0.10,
    "runtime_reasonable": 0.10,
    "output_format_supported": 0.05,
    "assets_resolved": 0.10,
}

# Checks that FAIL the package outright (nothing to render without them).
_BLOCKING_CHECKS = ("scenes_present",)


class RenderValidator:
    """Pre-flight validation for one render package."""

    def validate(
        self,
        *,
        scenes: list,
        timeline: dict,
        scene_render_plan: list,
        caption_render_plan: dict,
        audio_mix_plan: dict,
        missing_assets: list,
        output_format: "dict | None" = None,
    ) -> dict:
        """{status, checks, problems, production_readiness_score}."""
        if not scenes and not timeline.get("segments"):
            return {
                "status": RenderStatus.SKIPPED,
                "checks": [],
                "problems": ["Nothing to validate — no scenes were provided."],
                "production_readiness_score": 0,
            }

        output_format = output_format or OUTPUT_FORMAT
        checks = []
        problems = []

        def record(name: str, passed: bool, detail: str) -> None:
            checks.append({"check": name, "passed": passed, "detail": detail})
            if not passed:
                problems.append(f"{name}: {detail}")

        record(
            "scenes_present",
            bool(scenes),
            f"{len(scenes)} scenes in the plan." if scenes else "No scenes to render.",
        )

        without_visuals = [
            plan["scene_id"]
            for plan in scene_render_plan
            if not (
                plan.get("resolved_asset")
                or plan.get("image_prompt")
                or plan.get("video_prompt")
                or plan.get("stock_footage_query")
            )
        ]
        record(
            "scenes_have_visuals",
            not without_visuals,
            "Every scene has a visual asset or prompt."
            if not without_visuals
            else f"Scenes without any visual source: {without_visuals}.",
        )

        without_narration = [
            plan["scene_id"] for plan in scene_render_plan if not plan.get("narration", "").strip()
        ]
        record(
            "scenes_have_narration",
            not without_narration,
            "Every scene has narration."
            if not without_narration
            else f"Scenes without narration: {without_narration}.",
        )

        caption_segments = caption_render_plan.get("segments", [])
        record(
            "captions_exist",
            bool(caption_segments),
            f"{len(caption_segments)} caption segments planned."
            if caption_segments
            else "No caption plan was produced.",
        )

        has_audio = bool(audio_mix_plan.get("tracks", {}).get("narration", {}).get("segments"))
        record(
            "audio_plan_exists",
            has_audio,
            "Audio mix plan covers narration/music/SFX tracks."
            if has_audio
            else "No audio mix plan was produced.",
        )

        runtime = float(timeline.get("total_duration_sec", 0.0))
        runtime_ok = MIN_RUNTIME_SEC <= runtime <= MAX_RUNTIME_SEC
        record(
            "runtime_reasonable",
            runtime_ok,
            f"Total runtime {runtime}s is inside the {MIN_RUNTIME_SEC}-{MAX_RUNTIME_SEC}s short-form window."
            if runtime_ok
            else f"Total runtime {runtime}s is outside the {MIN_RUNTIME_SEC}-{MAX_RUNTIME_SEC}s short-form window.",
        )

        format_ok = (
            output_format.get("aspect_ratio") == OUTPUT_FORMAT["aspect_ratio"]
            and output_format.get("container") == OUTPUT_FORMAT["container"]
            and output_format.get("resolution") == OUTPUT_FORMAT["resolution"]
        )
        record(
            "output_format_supported",
            format_ok,
            "9:16 1080x1920 MP4 — supported."
            if format_ok
            else f"Unsupported output format: {output_format}.",
        )

        record(
            "assets_resolved",
            not missing_assets,
            "All asset requests were fulfilled."
            if not missing_assets
            else f"{len(missing_assets)} asset(s) missing (placeholders in use): "
            + ", ".join(
                f"scene {item.get('scene_number', 0)} ({item.get('source', '?')})"
                for item in missing_assets
            )
            + ".",
        )

        failed_names = {check["check"] for check in checks if not check["passed"]}
        if failed_names & set(_BLOCKING_CHECKS):
            status = RenderStatus.FAILED
        elif failed_names:
            status = RenderStatus.WARNING
        else:
            status = RenderStatus.SUCCESS

        score = round(
            sum(
                CHECK_WEIGHTS.get(check["check"], 0.0)
                for check in checks
                if check["passed"]
            )
            * 100
        )

        return {
            "status": status,
            "checks": checks,
            "problems": problems,
            "production_readiness_score": int(score),
        }
