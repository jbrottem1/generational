"""Pre-publish integrity gate — blocks live publish when production checks fail."""

from __future__ import annotations

from pathlib import Path

from services.publishing.extensions import PrePublishGate, register_pre_publish_gate
from services.provider_runtime.config import has_credential

ROOT = Path(__file__).resolve().parents[2]

_PLATFORM_OAUTH = {
    "youtube": "YOUTUBE_ACCESS_TOKEN",
    "youtube_shorts": "YOUTUBE_ACCESS_TOKEN",
    "tiktok": "TIKTOK_ACCESS_TOKEN",
    "instagram": "INSTAGRAM_ACCESS_TOKEN",
    "instagram_reels": "INSTAGRAM_ACCESS_TOKEN",
    "facebook": "FACEBOOK_ACCESS_TOKEN",
    "facebook_reels": "FACEBOOK_ACCESS_TOKEN",
    "x": "X_ACCESS_TOKEN",
    "linkedin": "LINKEDIN_ACCESS_TOKEN",
}


def _render_of(job: dict) -> dict:
    package = job.get("package") or {}
    return (
        package.get("render_package")
        or package.get("video")
        or (package.get("content") or {}).get("render_package")
        or {}
    )


def _path_exists(path: str) -> bool:
    if not path or str(path).startswith(("mock://", "runtime://")):
        return False
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = ROOT / path
    return candidate.exists() and candidate.stat().st_size > 100


def _live_oauth_configured(platform: str) -> bool:
    env = _PLATFORM_OAUTH.get(str(platform or "").lower())
    return bool(env and has_credential(env))


class ProductionIntegrityGate(PrePublishGate):
    """Reject live OAuth publishing when the finished MP4 / media package is incomplete.

    Dry-run and mock-adapter publishes (no platform OAuth) are allowed so the
    existing pipeline and tests keep working. Once OAuth tokens exist for the
    target platform, real media is required.
    """

    key = "production_integrity"

    def review(self, job: dict) -> list[str]:
        dry_run = (
            job.get("publish_mode") == "dry_run"
            or job.get("mode") == "dry_run"
            or bool((job.get("package") or {}).get("dry_run"))
        )
        if dry_run:
            return []

        platform = str(job.get("platform") or "")
        if not _live_oauth_configured(platform) and not job.get("enforce_production_qc"):
            # No live credentials — adapters will mock; do not cancel the job.
            return []

        problems: list[str] = []
        package = job.get("package") or {}
        render = _render_of(job)

        mp4 = (
            render.get("mp4_path")
            or render.get("output_path")
            or render.get("file_uri")
            or render.get("mock_output_path")
            or ""
        )
        if render.get("mock"):
            problems.append("Final MP4 is still a mock render — real assembly required before live publish")
        if not _path_exists(str(mp4)):
            problems.append("Final MP4 missing or unreadable")

        voice = package.get("voice_package") or package.get("audio_package") or {}
        narration = package.get("narration_tracks") or []
        has_voice = bool(
            (isinstance(voice, dict) and (voice.get("path") or voice.get("audio_b64")))
            or any(isinstance(t, dict) and (t.get("path") or not t.get("placeholder", True)) for t in narration)
        )
        if not has_voice:
            problems.append("Voice track missing")

        captions = (
            render.get("caption_render_plan")
            or package.get("captions")
            or (package.get("structured_script") or {}).get("caption_plan")
        )
        if not captions:
            problems.append("Captions missing")

        if not (package.get("seo_package") or package.get("metadata") or package.get("title")):
            problems.append("Metadata / SEO package missing")

        thumb = package.get("thumbnail") or package.get("thumbnail_plan") or render.get("thumbnail")
        if not thumb:
            problems.append("Thumbnail missing")

        timeline = render.get("timeline") or {}
        if not (timeline.get("segments") or render.get("scene_render_plan")):
            problems.append("Scene timing / timeline missing")

        return problems


_REGISTERED = False


def ensure_production_gate_registered() -> None:
    global _REGISTERED
    if _REGISTERED:
        return
    register_pre_publish_gate(ProductionIntegrityGate())
    _REGISTERED = True
