"""Evidence-based production readiness for real MP4 + publish."""

from __future__ import annotations

from typing import Any

from services.media_production.ffmpeg_assembler import ffmpeg_available
from services.media_production.voice import VoiceProviderStatus
from services.provider_runtime.config import has_credential


def media_production_readiness() -> dict[str, Any]:
    voice_rows = VoiceProviderStatus.snapshot()
    voice_ready = any(
        r["configured"] and r["provider"] in {"elevenlabs", "openai_tts"} for r in voice_rows
    )
    image_ready = any(
        has_credential(env)
        for env in ("OPENAI_API_KEY", "BFL_API_KEY", "IDEOGRAM_API_KEY", "STABILITY_API_KEY", "FAL_KEY", "REPLICATE_API_TOKEN")
    )
    video_ready = any(
        has_credential(env)
        for env in ("RUNWAY_API_KEY", "FAL_KEY", "REPLICATE_API_TOKEN", "LUMA_API_KEY", "PIKA_API_KEY")
    )
    # OpenAI images + TTS + ffmpeg can produce a finished short without Runway
    assembly_ready = ffmpeg_available()
    oauth = {
        "youtube": has_credential("YOUTUBE_ACCESS_TOKEN"),
        "tiktok": has_credential("TIKTOK_ACCESS_TOKEN"),
        "instagram": has_credential("INSTAGRAM_ACCESS_TOKEN"),
        "facebook": has_credential("FACEBOOK_ACCESS_TOKEN"),
        "x": has_credential("X_ACCESS_TOKEN"),
        "linkedin": has_credential("LINKEDIN_ACCESS_TOKEN"),
    }
    oauth_any = any(oauth.values())

    score = 40  # architecture baseline already proven by dry-run
    notes: list[str] = ["Orchestrator + dry-run pipeline operational"]
    if voice_ready:
        score += 15
        notes.append("TTS provider configured (ElevenLabs and/or OpenAI)")
    if image_ready:
        score += 10
        notes.append("Image provider configured")
    if video_ready:
        score += 10
        notes.append("Video generation provider configured")
    elif image_ready and assembly_ready:
        score += 5
        notes.append("Stills + FFmpeg can assemble shorts without video API")
    if assembly_ready:
        score += 15
        notes.append("FFmpeg available for final MP4 assembly")
    else:
        notes.append("FFmpeg missing — install ffmpeg or pip install imageio-ffmpeg")
    if oauth_any:
        score += 10
        notes.append("At least one publish OAuth token present")
    else:
        score += 3
        notes.append("Publish OAuth not configured — dry-run only")

    score = min(100, score)
    if score >= 90:
        band = "autonomous_ready"
    elif score >= 75:
        band = "assembly_ready"
    elif score >= 60:
        band = "architecture_ready"
    else:
        band = "blocked"

    blockers = []
    if not voice_ready:
        blockers.append("Configure ELEVENLABS_API_KEY or OPENAI_API_KEY for TTS")
    if not image_ready and not video_ready:
        blockers.append("Configure an image or video provider (OpenAI Images / Flux / Fal / Runway / Replicate)")
    if not assembly_ready:
        blockers.append("Install ffmpeg (or imageio-ffmpeg) for real MP4 export")
    if not oauth_any:
        blockers.append("Add platform OAuth tokens for live publish")

    placeholders = []
    if not video_ready:
        placeholders.append("AI video clips (Runway/Fal/Replicate) — stills+Ken Burns used when absent")
    placeholders.append("Local voice clone (interface reserved)")
    placeholders.append("Remotion motion-graphics path (FFmpeg is the active assembler)")

    return {
        "score": score,
        "band": band,
        "notes": notes,
        "blockers": blockers,
        "placeholders": placeholders,
        "integrated_providers": {
            "voice": [r for r in voice_rows if r.get("configured")],
            "image": image_ready,
            "video": video_ready,
            "assembly": "ffmpeg" if assembly_ready else "unavailable",
            "oauth": {k: v for k, v in oauth.items() if v},
        },
        "remaining_apis": [
            name
            for name, ok in {
                "ELEVENLABS_API_KEY": has_credential("ELEVENLABS_API_KEY"),
                "RUNWAY_API_KEY": has_credential("RUNWAY_API_KEY"),
                "BFL_API_KEY": has_credential("BFL_API_KEY"),
                "FAL_KEY": has_credential("FAL_KEY"),
                "REPLICATE_API_TOKEN": has_credential("REPLICATE_API_TOKEN"),
                "YOUTUBE_ACCESS_TOKEN": has_credential("YOUTUBE_ACCESS_TOKEN"),
            }.items()
            if not ok
        ],
        "oauth_status": oauth,
        "ffmpeg_available": assembly_ready,
        "estimated_time_to_first_autonomous_video": (
            "minutes after ffmpeg + OpenAI (stills+TTS+assemble)"
            if voice_ready and image_ready and assembly_ready
            else "same day after installing ffmpeg and confirming media keys"
            if voice_ready and image_ready
            else "1–2 days after media keys + ffmpeg"
        ),
        "first_autonomous_checklist": [
            "OPENAI_API_KEY present (script + TTS + images)",
            "ffmpeg or imageio-ffmpeg installed",
            "Run Studio production with publish_mode=dry_run",
            "Confirm render_package.mock is False and mp4_path exists",
            "Pass ProductionIntegrityGate checks",
            "Add YouTube OAuth for first live publish",
        ],
        "recommended_next_milestone": (
            "First real MP4 via OpenAI TTS + OpenAI Images + FFmpeg assembly"
            if not assembly_ready or not (voice_ready and image_ready)
            else "First live YouTube publish of an assembled short"
        ),
    }
