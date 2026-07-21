"""Voice engine — AI voiceover generation from scripts via production voice service."""

from __future__ import annotations

from core.log import get_logger, log_event
from core.production_models import VoiceSettings
from engines.base import Engine
from services.media_production.voice import synthesize_voice
from services.voice_profiles import get_default_profile, get_voice_profile_manager

logger = get_logger(__name__)


class VoiceEngine(Engine):
    key = "voice"
    label = "Voice"
    icon = "🎙️"
    description = "Generate AI voiceovers from scripts with provider fallback and timing metadata."
    version = "1.0.0"

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        niche = context.get("niche", "")
        profile_id = context.get("voice_profile_id", "")
        manager = get_voice_profile_manager()
        if profile_id:
            profile = manager.get_profile(profile_id) or get_default_profile(niche)
        else:
            profile = get_default_profile(niche)
        settings = profile.get("settings", VoiceSettings().to_dict())

        ideas = context.get("ideas") or context.get("selected_ideas") or []
        packages = context.get("production_packages") or []
        candidates = context.get("candidates") or []
        voice_packages = []

        # Prefer candidates (ops/pipeline) then packages then ideas — same objects the video engine renders.
        targets = candidates or packages or ideas
        for item in targets:
            existing = item.get("voice_package") if isinstance(item.get("voice_package"), dict) else {}
            script = (
                item.get("script")
                or (item.get("structured_script") or {}).get("full_script")
                or (item.get("video_script") or {}).get("full_voiceover")
                or existing.get("text")
                or existing.get("plain_text")
                or ""
            )
            if not script:
                # Fall back to concatenated scene narration
                scenes = item.get("scenes") or (item.get("visual_package") or {}).get("scenes") or []
                script = " ".join(str(s.get("narration") or "") for s in scenes if isinstance(s, dict)).strip()
            # Keep upstream audio only when it covers the full script (narration stage may leave short clips).
            if existing.get("path") and not existing.get("placeholder"):
                words = len(str(script).split())
                est_sec = words / 2.4 if words else 0.0  # ~144 wpm
                dur = float(existing.get("duration_sec") or existing.get("duration") or 0)
                if not script or dur >= max(20.0, est_sec * 0.7):
                    voice_packages.append(existing)
                    continue
            result = synthesize_voice(
                script,
                profile={
                    **profile,
                    **(context.get("voice_profile_hint") or {}),
                },
                settings=settings,
                mode=str(context.get("voice_mode") or "ai"),
                preferred_provider=str(
                    context.get("preferred_voice_provider")
                    or (context.get("studio_brief") or {}).get("preferred_voice_provider")
                    or ""
                ),
                narrator=str(
                    context.get("narration_style")
                    or context.get("narrator")
                    or (context.get("studio_brief") or {}).get("narrator")
                    or profile.get("style")
                    or "founder"
                ),
            )
            voice_pkg = result.get("voice_package") or {}
            # Prefer prior real audio if this attempt fell back to placeholder.
            if (not voice_pkg.get("path") or voice_pkg.get("placeholder")) and existing.get("path"):
                voice_pkg = existing
            item["voice_package"] = voice_pkg
            if voice_pkg.get("path"):
                item.setdefault("audio_package", {})
                if isinstance(item.get("audio_package"), dict):
                    item["audio_package"] = {**item["audio_package"], "path": voice_pkg["path"]}
            voice_packages.append(voice_pkg)

        log_event(logger, "voice.completed", items=len(voice_packages), profile=profile.get("profile_id", ""))
        updates: dict = {"voice_profile": profile, "voice_packages": voice_packages}
        if candidates:
            updates["candidates"] = candidates
        if packages:
            updates["production_packages"] = packages
        if ideas:
            updates["ideas"] = ideas
        # Mirror onto candidates when voice ran against ideas/packages only
        if voice_packages and candidates and not any(
            isinstance(c, dict) and (c.get("voice_package") or {}).get("path") for c in candidates
        ):
            for c, vp in zip(candidates, voice_packages):
                if isinstance(c, dict) and isinstance(vp, dict) and vp.get("path"):
                    c["voice_package"] = vp
                    c["audio_package"] = {**(c.get("audio_package") or {}), "path": vp["path"]}
            updates["candidates"] = candidates
        return updates
