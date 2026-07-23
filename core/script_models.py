"""Video script schema, validation, and production-pipeline status helpers.

Phase 1 of the asset workspace: structured 30–90 second short-form scripts
with timed segments, retention devices, and an honest 10-stage pipeline view.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

# --- Production pipeline (asset workspace) -----------------------------------

PIPELINE_STAGE_KEYS = (
    "idea",
    "script",
    "scenes",
    "visual_prompts",
    "images",
    "video_clips",
    "voice",
    "music",
    "sfx",
    "captions",
    "timeline",
    "render",
    "quality",
    "export",
    "publish",
)

PIPELINE_STAGE_LABELS = {
    "idea": "Idea",
    "script": "Script",
    "scenes": "Scenes",
    "visual_prompts": "Visual Prompts",
    "images": "Images",
    "video_clips": "Video Clips",
    "voice": "Voice",
    "music": "Music",
    "sfx": "SFX",
    "captions": "Captions",
    "timeline": "Timeline",
    "render": "FFmpeg Render",
    "quality": "Quality",
    "export": "Export MP4",
    "publish": "Publish Prep",
}

# Canonical execution statuses for live production runs
PIPELINE_STATUSES = frozenset(
    {
        "not_started",
        "started",
        "running",
        "in_progress",  # alias used by script generation UI
        "completed",
        "complete",  # alias for completed
        "failed",
        "skipped",
        "needs_review",
    }
)

STATUS_ICONS = {
    "not_started": "○",
    "started": "◔",
    "running": "◐",
    "in_progress": "◐",
    "completed": "●",
    "complete": "●",
    "failed": "✕",
    "skipped": "◌",
    "needs_review": "◑",
}

STATUS_LABELS = {
    "not_started": "Not started",
    "started": "Started",
    "running": "Running",
    "in_progress": "Running",
    "completed": "Completed",
    "complete": "Completed",
    "failed": "Failed",
    "skipped": "Skipped",
    "needs_review": "Needs review",
}

_COMPLETE_STATUSES = frozenset({"complete", "completed", "skipped"})
_RUNNING_STATUSES = frozenset({"started", "running", "in_progress"})


# --- Script schema -----------------------------------------------------------

VALID_SEGMENT_TYPES = frozenset(
    {
        "hook",
        "context",
        "escalation",
        "evidence",
        "payoff",
        "cta",
        "pattern_interrupt",
        "retention_hook",
        "story_beat",
    }
)

BANNED_PHRASES = (
    "welcome back",
    "hey guys",
    "what's up everyone",
    "in today's video",
    "don't forget to like and subscribe",
)

MIN_TARGET_DURATION = 30
MAX_TARGET_DURATION = 90


@dataclass
class ScriptSegment:
    segment_number: int
    start_time: float
    end_time: float
    segment_type: str
    voiceover: str
    emotion: str
    delivery: str
    retention_device: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScriptSegment":
        return cls(
            segment_number=int(data["segment_number"]),
            start_time=float(data["start_time"]),
            end_time=float(data["end_time"]),
            segment_type=str(data["segment_type"]),
            voiceover=str(data["voiceover"]).strip(),
            emotion=str(data.get("emotion") or "curiosity"),
            delivery=str(data.get("delivery") or "conversational"),
            retention_device=str(data.get("retention_device") or "open loop"),
        )


@dataclass
class VideoScript:
    title: str
    target_duration_seconds: int
    tone: str
    primary_emotion: str
    script_summary: str
    segments: list[ScriptSegment]
    full_voiceover: str
    call_to_action: str
    estimated_word_count: int
    generated_at: str = ""
    source: str = "ai"  # "ai" | "heuristic" | "edited"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["segments"] = [segment.to_dict() for segment in self.segments]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VideoScript":
        segments = [ScriptSegment.from_dict(item) for item in (data.get("segments") or [])]
        return cls(
            title=str(data.get("title") or ""),
            target_duration_seconds=int(data.get("target_duration_seconds") or 60),
            tone=str(data.get("tone") or "engaging"),
            primary_emotion=str(data.get("primary_emotion") or "curiosity"),
            script_summary=str(data.get("script_summary") or ""),
            segments=segments,
            full_voiceover=str(data.get("full_voiceover") or "").strip(),
            call_to_action=str(data.get("call_to_action") or "").strip(),
            estimated_word_count=int(data.get("estimated_word_count") or 0),
            generated_at=str(data.get("generated_at") or ""),
            source=str(data.get("source") or "ai"),
        )


@dataclass
class ScriptGenerationResult:
    ok: bool
    script: VideoScript | None = None
    error: str = ""
    tokens_used: int = 0
    attempts: int = 0
    demo_mode: bool = False


# --- Validation --------------------------------------------------------------

def _word_count(text: str) -> int:
    return len(text.split()) if text else 0


def estimated_duration_from_segments(segments: list[ScriptSegment]) -> float:
    if not segments:
        return 0.0
    return max(segment.end_time for segment in segments)


def validate_script_payload(data: dict[str, Any] | None) -> tuple[VideoScript | None, list[str]]:
    """Validate and normalize a raw script dict. Returns (script, errors)."""
    errors: list[str] = []
    if not isinstance(data, dict):
        return None, ["Response is not a JSON object"]

    required_top = (
        "title",
        "target_duration_seconds",
        "tone",
        "primary_emotion",
        "script_summary",
        "segments",
        "full_voiceover",
        "call_to_action",
        "estimated_word_count",
    )
    for key in required_top:
        if key not in data or data[key] in (None, ""):
            if key != "estimated_word_count":
                errors.append(f"Missing required field: {key}")

    segments_raw = data.get("segments")
    if not isinstance(segments_raw, list) or not segments_raw:
        errors.append("segments must be a non-empty list")
        return None, errors

    segments: list[ScriptSegment] = []
    for index, raw in enumerate(segments_raw):
        if not isinstance(raw, dict):
            errors.append(f"Segment {index + 1} is not an object")
            continue
        for field_name in (
            "segment_number",
            "start_time",
            "end_time",
            "segment_type",
            "voiceover",
            "emotion",
            "delivery",
            "retention_device",
        ):
            if field_name not in raw or raw[field_name] in (None, ""):
                errors.append(f"Segment {index + 1} missing {field_name}")
        try:
            segment = ScriptSegment.from_dict(raw)
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"Segment {index + 1} invalid: {exc}")
            continue
        if segment.end_time <= segment.start_time:
            errors.append(f"Segment {segment.segment_number} has invalid timing")
        if segment.segment_type not in VALID_SEGMENT_TYPES:
            errors.append(f"Segment {segment.segment_number} has unknown segment_type")
        segments.append(segment)

    if errors:
        return None, errors

    target = int(data["target_duration_seconds"])
    if not MIN_TARGET_DURATION <= target <= MAX_TARGET_DURATION:
        errors.append(f"target_duration_seconds must be {MIN_TARGET_DURATION}–{MAX_TARGET_DURATION}")

    full_voiceover = str(data["full_voiceover"]).strip()
    lower_voice = full_voiceover.lower()
    for phrase in BANNED_PHRASES:
        if phrase in lower_voice:
            errors.append(f"Script contains banned filler phrase: {phrase!r}")

    if segments[0].segment_type != "hook":
        errors.append("First segment must be segment_type 'hook'")
    if segments[0].start_time != 0:
        errors.append("Hook must start at 0 seconds")
    if segments[0].end_time > 3:
        errors.append("Opening hook should land within the first 1–2 seconds (end_time ≤ 3)")

    for prev, cur in zip(segments, segments[1:]):
        if abs(cur.start_time - prev.end_time) > 0.5:
            errors.append(
                f"Gap between segment {prev.segment_number} and {cur.segment_number}"
            )

    estimated = estimated_duration_from_segments(segments)
    if estimated < MIN_TARGET_DURATION - 5 or estimated > MAX_TARGET_DURATION + 10:
        errors.append(
            f"Segment timeline spans {estimated:.0f}s; expected ~{MIN_TARGET_DURATION}–{MAX_TARGET_DURATION}s"
        )

    word_count = int(data.get("estimated_word_count") or _word_count(full_voiceover))
    if word_count < 40:
        errors.append("Script is too short — likely filler or incomplete")

    if errors:
        return None, errors

    script = VideoScript(
        title=str(data["title"]).strip(),
        target_duration_seconds=target,
        tone=str(data["tone"]).strip(),
        primary_emotion=str(data["primary_emotion"]).strip(),
        script_summary=str(data["script_summary"]).strip(),
        segments=segments,
        full_voiceover=full_voiceover,
        call_to_action=str(data["call_to_action"]).strip(),
        estimated_word_count=word_count,
        generated_at=str(data.get("generated_at") or ""),
        source=str(data.get("source") or "ai"),
    )
    return script, []


def apply_script_to_asset(asset: dict[str, Any], script: VideoScript) -> dict[str, Any]:
    """Merge a validated script onto an asset dict (backward compatible)."""
    payload = script.to_dict()
    if not payload.get("generated_at"):
        payload["generated_at"] = datetime.now(timezone.utc).isoformat()
    updated = dict(asset)
    updated["video_script"] = payload
    updated["script"] = script.full_voiceover
    updated["cta"] = script.call_to_action or updated.get("cta") or ""
    updated["estimated_runtime_sec"] = int(round(estimated_duration_from_segments(script.segments)))
    updated["workspace_status"] = "scripted"
    updated["production_pipeline"] = build_pipeline_snapshot(updated)
    return updated


def asset_has_video_script(asset: dict[str, Any] | None) -> bool:
    if not isinstance(asset, dict):
        return False
    vs = asset.get("video_script")
    return isinstance(vs, dict) and bool(vs.get("segments"))


def load_video_script(asset: dict[str, Any] | None) -> VideoScript | None:
    if not asset_has_video_script(asset):
        return None
    script, errors = validate_script_payload(asset.get("video_script"))
    if script is None:
        return None
    return script


# --- Pipeline status ---------------------------------------------------------

def _normalize_status(status: str) -> str:
    value = str(status or "not_started").lower()
    if value == "complete":
        return "completed"
    if value == "in_progress":
        return "running"
    return value if value in PIPELINE_STATUSES else "not_started"


def _stage_status(asset: dict[str, Any], stage_key: str, *, script_generating: bool = False) -> str:
    stored = asset.get("production_pipeline") or {}
    stages = stored.get("stages") if isinstance(stored, dict) else None
    if isinstance(stages, dict) and stage_key in stages:
        raw = stages[stage_key]
        if isinstance(raw, dict):
            status = _normalize_status(raw.get("status") or "not_started")
        else:
            status = _normalize_status(raw)
        if status in PIPELINE_STATUSES:
            return status

    if stage_key == "idea":
        return "completed" if asset.get("title") or asset.get("hook") else "not_started"

    if stage_key == "script":
        if script_generating:
            return "running"
        return "completed" if asset_has_video_script(asset) else "not_started"

    if stage_key == "scenes":
        scenes = (asset.get("scene_breakdown") or (asset.get("visual_package") or {}).get("scenes") or [])
        return "completed" if scenes else "not_started"

    if stage_key == "visual_prompts":
        return "completed" if asset.get("visual_prompts") or (asset.get("visual_package") or {}).get("image_prompts") else "not_started"

    if stage_key == "images":
        arts = (asset.get("production_artifacts") or {}).get("images") or asset.get("generated_images") or []
        return "completed" if arts else "not_started"

    if stage_key == "video_clips":
        arts = (asset.get("production_artifacts") or {}).get("video_clips") or asset.get("generated_videos") or []
        if arts:
            return "completed"
        if (asset.get("production_pipeline") or {}).get("stages", {}).get("video_clips"):
            return _normalize_status(
                ((asset.get("production_pipeline") or {}).get("stages") or {}).get("video_clips")
            )
        return "not_started"

    if stage_key == "voice":
        voice = asset.get("voice_package") or {}
        return "completed" if isinstance(voice, dict) and (voice.get("path") or not voice.get("placeholder", True)) else "not_started"

    if stage_key == "music":
        return "completed" if (asset.get("production_artifacts") or {}).get("music") or (asset.get("audio_package") or {}).get("music_path") else "not_started"

    if stage_key == "sfx":
        return "completed" if (asset.get("production_artifacts") or {}).get("sfx") else "not_started"

    if stage_key == "captions":
        return "completed" if (asset.get("production_artifacts") or {}).get("captions") or asset.get("captions_srt") else "not_started"

    if stage_key == "timeline":
        render = asset.get("render_package") or {}
        return "completed" if (render.get("timeline") or {}).get("segments") else "not_started"

    if stage_key == "render":
        render = asset.get("render_package") or {}
        if render.get("mp4_path") and not render.get("mock"):
            return "completed"
        if render.get("mock_output_path") or render.get("file_uri"):
            return "completed" if not render.get("mock") else "needs_review"
        return "not_started"

    if stage_key == "quality":
        qc = asset.get("production_qc") or {}
        if qc.get("passed") is True:
            return "completed"
        if qc.get("passed") is False:
            return "failed"
        return "not_started"

    if stage_key == "export":
        return "completed" if (asset.get("production_artifacts") or {}).get("render") or (
            (asset.get("render_package") or {}).get("mp4_path") and not (asset.get("render_package") or {}).get("mock")
        ) else "not_started"

    if stage_key == "publish":
        prep = asset.get("publish_package") or {}
        if prep.get("ready") or prep.get("status") == "prepared":
            return "completed"
        if prep.get("status") == "awaiting_oauth":
            return "skipped"
        return "not_started"

    return "not_started"


def build_pipeline_stages(asset: dict[str, Any] | None, *, script_generating: bool = False) -> list[dict[str, Any]]:
    asset = asset or {}
    stored = (asset.get("production_pipeline") or {}).get("stages") or {}
    rows = []
    for key in PIPELINE_STAGE_KEYS:
        detail = stored.get(key) if isinstance(stored, dict) else None
        if isinstance(detail, dict):
            status = _normalize_status(detail.get("status") or _stage_status(asset, key, script_generating=script_generating))
            row = {
                "key": key,
                "label": PIPELINE_STAGE_LABELS[key],
                "status": status,
                "retry_count": int(detail.get("retry_count") or 0),
                "execution_time_sec": float(detail.get("execution_time_sec") or 0),
                "error": str(detail.get("error") or ""),
                "artifacts": list(detail.get("artifacts") or []),
                "started_at": str(detail.get("started_at") or ""),
                "completed_at": str(detail.get("completed_at") or ""),
            }
        else:
            status = _stage_status(asset, key, script_generating=script_generating)
            row = {
                "key": key,
                "label": PIPELINE_STAGE_LABELS[key],
                "status": status,
                "retry_count": 0,
                "execution_time_sec": 0.0,
                "error": "",
                "artifacts": [],
                "started_at": "",
                "completed_at": "",
            }
        rows.append(row)
    return rows


def pipeline_progress_percent(stages: list[dict[str, Any]]) -> int:
    if not stages:
        return 0
    complete = sum(1 for stage in stages if stage.get("status") in _COMPLETE_STATUSES)
    return int(round(complete / len(stages) * 100))


def build_pipeline_snapshot(asset: dict[str, Any], *, script_generating: bool = False) -> dict[str, Any]:
    stages = build_pipeline_stages(asset, script_generating=script_generating)
    return {
        "stages": {
            stage["key"]: {
                "status": stage["status"],
                "retry_count": stage.get("retry_count", 0),
                "execution_time_sec": stage.get("execution_time_sec", 0),
                "error": stage.get("error", ""),
                "artifacts": stage.get("artifacts") or [],
                "started_at": stage.get("started_at", ""),
                "completed_at": stage.get("completed_at", ""),
            }
            for stage in stages
        },
        "progress_percent": pipeline_progress_percent(stages),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


ProgressCallback = Callable[[str], None]
