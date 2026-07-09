"""MockRenderer — simulates the render pass so the whole pipeline runs today.

Walks the render plan exactly like a real renderer would (resolve assets →
lay the timeline → apply motion → burn captions → mix audio → encode) and
produces the same shaped result a real renderer will return: status,
output path, duration, warnings, missing assets, and a step-by-step render
log. No MP4 is written — the mock output path is a URI reserved for the
real renderer. Swapping in a real backend means implementing this class's
`render()` signature against ffmpeg or a cloud renderer; nothing upstream
or downstream changes.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

from engines.render.models import (
    OUTPUT_FORMAT,
    RenderJob,
    RenderJobStatus,
    RenderStatus,
)

# Rough simulation of real render cost: fixed pipeline overhead plus
# per-second encode time and per-scene asset generation time (seconds).
BASE_OVERHEAD_SEC = 15.0
PER_CONTENT_SECOND = 2.0
PER_SCENE_SEC = 4.0


def estimate_render_duration(total_duration_sec: float, scene_count: int) -> float:
    """Estimated wall-clock seconds a real render of this plan would take."""
    return round(
        BASE_OVERHEAD_SEC + total_duration_sec * PER_CONTENT_SECOND + scene_count * PER_SCENE_SEC,
        1,
    )


def _slug(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (title or "untitled").lower()).strip("-")
    return slug[:60] or "untitled"


class MockRenderer:
    """Simulated render pass — same contract a real renderer will honor."""

    def render(
        self,
        *,
        title: str,
        timeline: dict,
        scene_render_plan: list,
        caption_render_plan: dict,
        audio_mix_plan: dict,
        missing_assets: list,
        warnings: "list | None" = None,
        job: "RenderJob | None" = None,
    ) -> dict:
        """Simulate rendering one video; returns the render result dict."""
        job = job or RenderJob(title=title)
        warnings = list(warnings or [])
        segments = timeline.get("segments", [])
        duration = float(timeline.get("total_duration_sec", 0.0))

        def log(message: str) -> None:
            job.log.append(
                {
                    "at": datetime.now(timezone.utc).isoformat(),
                    "status": job.status,
                    "message": message,
                }
            )

        job.advance(RenderJobStatus.PLANNING, "Render plan received.", progress_pct=5)

        if not segments:
            job.advance(RenderJobStatus.FAILED, "Nothing to render — empty timeline.")
            return {
                "render_status": RenderStatus.SKIPPED,
                "mock_output_path": "",
                "duration_sec": 0.0,
                "warnings": warnings + ["Empty timeline — render skipped."],
                "missing_assets": list(missing_assets),
                "render_log": list(job.log),
                "job": job.to_dict(),
                "estimated_render_duration_sec": 0.0,
                "mock": True,
            }

        job.advance(RenderJobStatus.RENDERING, "Simulated render started.", progress_pct=10)
        log(f"Resolved {len(scene_render_plan)} scene assets ({len(missing_assets)} placeholder fallbacks).")
        log(f"Laid {len(segments)} timeline segments over {duration}s at {OUTPUT_FORMAT['fps']}fps.")
        log(f"Applied motion + transitions to {len(segments)} segments.")
        log(f"Burned {len(caption_render_plan.get('segments', []))} caption segments (safe-area verified).")
        tracks = audio_mix_plan.get("tracks", {})
        log(
            "Mixed audio: "
            f"{len(tracks.get('narration', {}).get('segments', []))} narration segments, "
            f"{len(tracks.get('sfx', {}).get('cues', []))} SFX cues, "
            f"{len(tracks.get('transitions', {}).get('cues', []))} transition sounds, "
            f"music ducking {'on' if tracks.get('music', {}).get('ducking', {}).get('enabled') else 'off'}."
        )
        resolution = OUTPUT_FORMAT["resolution"]
        output_path = (
            f"data/renders/{job.job_id}/{_slug(title)}_"
            f"{resolution['width']}x{resolution['height']}.mp4"
        )
        log(f"Encoded mock output → {output_path} (no file written — mock render).")

        if missing_assets:
            warnings.append(
                f"{len(missing_assets)} asset(s) rendered with placeholders — "
                "replace before real rendering."
            )

        job.output = {"path": output_path, "duration_sec": duration}
        job.advance(RenderJobStatus.COMPLETE, "Simulated render complete.")

        return {
            "render_status": RenderStatus.WARNING if missing_assets else RenderStatus.SUCCESS,
            "mock_output_path": output_path,
            "duration_sec": duration,
            "warnings": warnings,
            "missing_assets": list(missing_assets),
            "render_log": list(job.log),
            "job": job.to_dict(),
            "estimated_render_duration_sec": estimate_render_duration(duration, len(segments)),
            "mock": True,
        }
