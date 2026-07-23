"""Production media integrations — voice, assembly, QC gates, reports.

Enhances existing ProviderRuntime + RenderEngine seams without replacing them.
"""

from __future__ import annotations

from services.media_production.bootstrap import bootstrap_media_production
from services.media_production.ffmpeg_assembler import assemble_mp4, ffmpeg_available, find_ffmpeg
from services.media_production.formats import (
    DURATION_PRESETS,
    RESOLUTION_PRESETS,
    duration_band,
    resolve_output_format,
)
from services.media_production.readiness import media_production_readiness
from services.media_production.reports import write_full_report_bundle
from services.media_production.voice import VoiceProviderStatus, synthesize_voice

bootstrap_media_production()

__all__ = [
    "DURATION_PRESETS",
    "RESOLUTION_PRESETS",
    "VoiceProviderStatus",
    "assemble_mp4",
    "bootstrap_media_production",
    "duration_band",
    "ffmpeg_available",
    "find_ffmpeg",
    "media_production_readiness",
    "resolve_output_format",
    "synthesize_voice",
    "write_full_report_bundle",
]
