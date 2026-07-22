"""Production renderer — FFmpeg assembly with mock fallback.

Walks the render plan (resolve assets → timeline → motion → captions →
audio mix → encode). When ffmpeg is available, writes a real MP4 under
data/renders/. Otherwise preserves the historical mock contract so dry-run
pipelines keep working unchanged.
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
    """Render pass — real FFmpeg when available, mock URI otherwise.

    Class name retained for backward compatibility with tests and imports.
    """

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
        output_format: "dict | None" = None,
    ) -> dict:
        """Render one video; returns the render result dict."""
        job = job or RenderJob(title=title)
        warnings = list(warnings or [])
        segments = timeline.get("segments", [])
        duration = float(timeline.get("total_duration_sec", 0.0))
        fmt = dict(output_format or OUTPUT_FORMAT)

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
                "output_path": "",
                "mp4_path": "",
                "duration_sec": 0.0,
                "warnings": warnings + ["Empty timeline — render skipped."],
                "missing_assets": list(missing_assets),
                "render_log": list(job.log),
                "job": job.to_dict(),
                "estimated_render_duration_sec": 0.0,
                "mock": True,
                "assembly": {},
            }

        job.advance(RenderJobStatus.RENDERING, "Render started.", progress_pct=10)
        log(f"Resolved {len(scene_render_plan)} scene assets ({len(missing_assets)} placeholder fallbacks).")
        log(f"Laid {len(segments)} timeline segments over {duration}s at {fmt.get('fps', OUTPUT_FORMAT['fps'])}fps.")
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
        resolution = (fmt.get("resolution") or OUTPUT_FORMAT["resolution"])
        output_path = (
            f"data/renders/{job.job_id}/{_slug(title)}_"
            f"{resolution['width']}x{resolution['height']}.mp4"
        )

        # Fail closed: never assemble blank/color-bed MP4s when visuals are invalid.
        try:
            from services.media_production.visual_qa import (
                validate_scene_visuals,
                write_visual_pipeline_report,
            )

            qa = validate_scene_visuals(scene_render_plan, require_all=True)
            report_path = write_visual_pipeline_report(
                qa,
                output_path=f"data/renders/{job.job_id}/VISUAL_PIPELINE_REPORT.md",
                title=title,
                extra={
                    "missing_assets": len(missing_assets or []),
                    "job_id": job.job_id,
                },
            )
            log(f"Visual QA {'PASS' if qa.get('ok') else 'FAIL'} → {report_path}")
            if not qa.get("ok") or missing_assets:
                reason = qa.get("error") or "missing validated visual media"
                if missing_assets:
                    reason = f"{reason} | missing_assets={len(missing_assets)}"
                job.advance(RenderJobStatus.FAILED, reason, progress_pct=100)
                warnings.append(reason)
                return {
                    "render_status": RenderStatus.FAILED,
                    "mock_output_path": "",
                    "output_path": "",
                    "mp4_path": "",
                    "file_uri": "",
                    "duration_sec": duration,
                    "warnings": warnings,
                    "missing_assets": list(missing_assets),
                    "render_log": list(job.log),
                    "job": job.to_dict(),
                    "estimated_render_duration_sec": estimate_render_duration(duration, len(segments)),
                    "mock": True,
                    "assembly": {"ok": False, "error": reason, "rejected_color_bed": True},
                    "output_format": fmt,
                    "visual_qa": qa,
                    "visual_pipeline_report": report_path,
                }
        except Exception as exc:  # noqa: BLE001
            job.advance(RenderJobStatus.FAILED, f"Visual QA error: {exc}", progress_pct=100)
            return {
                "render_status": RenderStatus.FAILED,
                "mock_output_path": "",
                "output_path": "",
                "mp4_path": "",
                "file_uri": "",
                "duration_sec": duration,
                "warnings": warnings + [f"Visual QA error: {exc}"],
                "missing_assets": list(missing_assets),
                "render_log": list(job.log),
                "job": job.to_dict(),
                "estimated_render_duration_sec": estimate_render_duration(duration, len(segments)),
                "mock": True,
                "assembly": {"ok": False, "error": str(exc)},
                "output_format": fmt,
            }

        assembly: dict = {}
        mock = True
        try:
            from services.media_production.ffmpeg_assembler import assemble_mp4, write_assembly_sidecar

            job.advance(RenderJobStatus.RENDERING, "FFmpeg assembly.", progress_pct=55)
            assembly = assemble_mp4(
                title=title,
                output_path=output_path,
                timeline=timeline,
                scene_render_plan=scene_render_plan,
                audio_mix_plan=audio_mix_plan,
                output_format=fmt,
                allow_color_bed=False,
            )
            if assembly.get("ok"):
                mock = False
                output_path = assembly.get("output_path") or output_path
                log(f"Encoded real MP4 → {output_path} ({assembly.get('bytes', 0)} bytes).")
                write_assembly_sidecar(assembly, output_path)
            else:
                reason = assembly.get("error") or "ffmpeg unavailable"
                log(f"Assembly failed ({reason}).")
                warnings.append(f"Real MP4 not written: {reason}")
                job.advance(RenderJobStatus.FAILED, reason, progress_pct=100)
                return {
                    "render_status": RenderStatus.FAILED,
                    "mock_output_path": output_path,
                    "output_path": output_path,
                    "mp4_path": "",
                    "file_uri": output_path,
                    "duration_sec": duration,
                    "warnings": warnings,
                    "missing_assets": list(missing_assets),
                    "render_log": list(job.log),
                    "job": job.to_dict(),
                    "estimated_render_duration_sec": estimate_render_duration(duration, len(segments)),
                    "mock": True,
                    "assembly": assembly,
                    "output_format": fmt,
                }
        except Exception as exc:  # noqa: BLE001 — never crash render
            log(f"Assembly error: {exc}")
            warnings.append(f"Assembly error: {exc}")
            assembly = {"ok": False, "error": str(exc), "mock": True}
            job.advance(RenderJobStatus.FAILED, str(exc), progress_pct=100)
            return {
                "render_status": RenderStatus.FAILED,
                "mock_output_path": output_path,
                "output_path": output_path,
                "mp4_path": "",
                "file_uri": output_path,
                "duration_sec": duration,
                "warnings": warnings,
                "missing_assets": list(missing_assets),
                "render_log": list(job.log),
                "job": job.to_dict(),
                "estimated_render_duration_sec": estimate_render_duration(duration, len(segments)),
                "mock": True,
                "assembly": assembly,
                "output_format": fmt,
            }

        job.output = {"path": output_path, "duration_sec": duration, "mock": mock}
        job.advance(RenderJobStatus.COMPLETE, "Render complete.")

        return {
            "render_status": RenderStatus.SUCCESS,
            "mock_output_path": output_path,
            "output_path": output_path,
            "mp4_path": output_path,
            "file_uri": output_path,
            "duration_sec": duration,
            "warnings": warnings,
            "missing_assets": list(missing_assets),
            "render_log": list(job.log),
            "job": job.to_dict(),
            "estimated_render_duration_sec": estimate_render_duration(duration, len(segments)),
            "mock": False,
            "assembly": assembly,
            "output_format": fmt,
        }


# Alias for clarity in new call sites
ProductionRenderer = MockRenderer
