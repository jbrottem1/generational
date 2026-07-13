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
        voice_packages = []

        targets = packages or ideas
        for item in targets:
            script = (
                item.get("script")
                or (item.get("structured_script") or {}).get("full_script")
                or (item.get("video_script") or {}).get("full_voiceover")
                or ""
            )
            if not script:
                # Fall back to concatenated scene narration
                scenes = item.get("scenes") or (item.get("visual_package") or {}).get("scenes") or []
                script = " ".join(str(s.get("narration") or "") for s in scenes if isinstance(s, dict)).strip()
            result = synthesize_voice(script, profile=profile, settings=settings, mode=str(context.get("voice_mode") or "ai"))
            voice_pkg = result.get("voice_package") or {}
            item["voice_package"] = voice_pkg
            voice_packages.append(voice_pkg)

        log_event(logger, "voice.completed", items=len(voice_packages), profile=profile.get("profile_id", ""))
        updates: dict = {"voice_profile": profile, "voice_packages": voice_packages}
        if packages:
            updates["production_packages"] = packages
        if ideas:
            updates["ideas"] = ideas
        return updates
