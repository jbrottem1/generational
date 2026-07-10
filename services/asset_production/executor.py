"""End-to-end asset production executor.

Runs Idea → … → Export MP4 → Publish Prep automatically for one workspace
asset. Reuses ProviderRuntime, visual package builders, voice service, and
FFmpeg assembler — no architecture redesign.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Callable

from core.log import get_logger, log_event
from core.script_models import (
    PIPELINE_STAGE_KEYS,
    PIPELINE_STAGE_LABELS,
    apply_script_to_asset,
    asset_has_video_script,
    build_pipeline_snapshot,
)
from services.asset_production import artifacts as art

logger = get_logger(__name__)

ProgressFn = Callable[[dict[str, Any]], None]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_pipeline(asset: dict) -> dict:
    pipeline = dict(asset.get("production_pipeline") or {})
    stages = dict(pipeline.get("stages") or {})
    for key in PIPELINE_STAGE_KEYS:
        if key not in stages or not isinstance(stages.get(key), dict):
            prev = stages.get(key)
            stages[key] = {
                "status": prev if isinstance(prev, str) else "not_started",
                "retry_count": 0,
                "execution_time_sec": 0.0,
                "error": "",
                "artifacts": [],
                "started_at": "",
                "completed_at": "",
            }
    pipeline["stages"] = stages
    asset["production_pipeline"] = pipeline
    return pipeline


def _set_stage(
    asset: dict,
    key: str,
    *,
    status: str,
    error: str = "",
    artifacts: list | None = None,
    retry_count: int | None = None,
    started_at: str = "",
    completed_at: str = "",
    execution_time_sec: float | None = None,
) -> None:
    pipeline = _ensure_pipeline(asset)
    stage = dict(pipeline["stages"].get(key) or {})
    stage["status"] = status
    if error:
        stage["error"] = error
    elif status in {"completed", "skipped"}:
        stage["error"] = ""
    if artifacts is not None:
        stage["artifacts"] = list(artifacts)
    if retry_count is not None:
        stage["retry_count"] = int(retry_count)
    if started_at:
        stage["started_at"] = started_at
    if completed_at:
        stage["completed_at"] = completed_at
    if execution_time_sec is not None:
        stage["execution_time_sec"] = round(float(execution_time_sec), 3)
    pipeline["stages"][key] = stage
    pipeline["progress_percent"] = build_pipeline_snapshot(asset).get("progress_percent", 0)
    pipeline["updated_at"] = _now()
    pipeline["current_stage"] = key
    asset["production_pipeline"] = pipeline


def _emit(on_progress: ProgressFn | None, asset: dict, key: str, message: str) -> None:
    if not on_progress:
        return
    stage = ((asset.get("production_pipeline") or {}).get("stages") or {}).get(key) or {}
    on_progress(
        {
            "stage": key,
            "label": PIPELINE_STAGE_LABELS.get(key, key),
            "status": stage.get("status"),
            "message": message,
            "retry_count": stage.get("retry_count", 0),
            "execution_time_sec": stage.get("execution_time_sec", 0),
            "progress_percent": (asset.get("production_pipeline") or {}).get("progress_percent", 0),
            "asset": asset,
        }
    )


def _run_stage(
    asset: dict,
    key: str,
    fn: Callable[[], tuple[dict, list[str]]],
    *,
    on_progress: ProgressFn | None,
    max_retries: int = 1,
) -> bool:
    """Execute one stage with retries. Returns False on hard failure."""
    started = _now()
    t0 = time.perf_counter()
    _set_stage(asset, key, status="started", started_at=started)
    _emit(on_progress, asset, key, f"{PIPELINE_STAGE_LABELS.get(key, key)} started")
    _set_stage(asset, key, status="running", started_at=started)
    _emit(on_progress, asset, key, f"{PIPELINE_STAGE_LABELS.get(key, key)} running")

    last_error = ""
    for attempt in range(max_retries + 1):
        try:
            updates, artifact_paths = fn()
            if updates:
                asset.update(updates)
            elapsed = time.perf_counter() - t0
            status = "skipped" if updates.get("_stage_skipped") else "completed"
            _set_stage(
                asset,
                key,
                status=status,
                artifacts=artifact_paths,
                retry_count=attempt,
                started_at=started,
                completed_at=_now(),
                execution_time_sec=elapsed,
            )
            # Drop internal flag
            asset.pop("_stage_skipped", None)
            _emit(on_progress, asset, key, f"{PIPELINE_STAGE_LABELS.get(key, key)} {status}")
            return True
        except Exception as exc:  # noqa: BLE001
            last_error = str(exc)[:400]
            _set_stage(asset, key, status="running", retry_count=attempt + 1, error=last_error, started_at=started)
            _emit(on_progress, asset, key, f"Retry {attempt + 1}: {last_error}")
            log_event(logger, "asset_production.stage_retry", level=30, stage=key, attempt=attempt + 1, error=last_error)
            if attempt >= max_retries:
                break
            time.sleep(0.4)

    elapsed = time.perf_counter() - t0
    _set_stage(
        asset,
        key,
        status="failed",
        error=last_error,
        retry_count=max_retries + 1,
        started_at=started,
        completed_at=_now(),
        execution_time_sec=elapsed,
    )
    _emit(on_progress, asset, key, f"{PIPELINE_STAGE_LABELS.get(key, key)} failed: {last_error}")
    return False


def _scenes_from_script(asset: dict) -> list[dict]:
    """Build Director-compatible scenes from video_script segments."""
    vs = asset.get("video_script") if isinstance(asset.get("video_script"), dict) else {}
    segments = vs.get("segments") or []
    scenes = []
    for index, seg in enumerate(segments):
        if not isinstance(seg, dict):
            continue
        start = float(seg.get("start_time") or 0)
        end = float(seg.get("end_time") or start)
        duration = max(0.5, end - start)
        purpose = str(seg.get("segment_type") or "story_beat")
        narration = str(seg.get("voiceover") or "")
        visual = (
            f"{purpose.replace('_', ' ').title()} visual: {narration[:120]}"
            if narration
            else f"Scene {index + 1} visual for {asset.get('title') or 'video'}"
        )
        scenes.append(
            {
                "scene_number": index + 1,
                "purpose": purpose if purpose != "cta" else "cta",
                "emotion": seg.get("emotion") or "",
                "length_sec": duration,
                "narration": narration,
                "visual_description": visual,
                "camera_motion": "subtle push" if index == 0 else "static",
                "zoom": "punch-in" if index == 0 else "",
                "motion_intensity": 70 if index == 0 else 45,
                "transition_in": "none" if index == 0 else "cut",
                "transition_out": "hard cut",
                "asset_type": "ai_image",
                "ai_image_prompt": visual,
                "ai_video_prompt": f"Cinematic motion: {visual}",
                "stock_footage_query": "",
                "text_overlay": narration.split()[:4] and " ".join(narration.split()[:4]) or "",
                "overlay": "",
                "caption_placement": "bottom third, safe zone",
                "caption_timing": {"start_sec": start, "end_sec": end},
                "caption_emphasis": [],
                "sound_effect": "whoosh" if index > 0 else "bass hit",
                "sfx_timing": {"cue": "whoosh" if index > 0 else "bass hit", "at_sec": start},
            }
        )
    return scenes


def _build_srt(scenes: list, voice_timing: dict | None = None) -> str:
    lines = []
    index = 1
    sentences = (voice_timing or {}).get("sentence_timestamps") or []
    if sentences:
        for item in sentences:
            start = float(item.get("start") or 0)
            end = float(item.get("end") or start + 1)
            text = str(item.get("text") or "").strip()
            if not text:
                continue
            lines.append(str(index))
            lines.append(f"{_ts(start)} --> {_ts(end)}")
            lines.append(text)
            lines.append("")
            index += 1
        return "\n".join(lines)
    for scene in scenes:
        timing = scene.get("caption_timing") or {}
        start = float(timing.get("start_sec") or 0)
        end = float(timing.get("end_sec") or start + float(scene.get("length_sec") or 1))
        text = str(scene.get("narration") or "").strip()
        if not text:
            continue
        lines.append(str(index))
        lines.append(f"{_ts(start)} --> {_ts(end)}")
        lines.append(text)
        lines.append("")
        index += 1
    return "\n".join(lines)


def _ts(seconds: float) -> str:
    ms = int(round(max(0.0, seconds) * 1000))
    h, rem = divmod(ms, 3600_000)
    m, rem = divmod(rem, 60_000)
    s, milli = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{milli:03d}"


def run_asset_production(
    asset: dict,
    project: dict,
    *,
    on_progress: ProgressFn | None = None,
    skip_publish_if_no_oauth: bool = True,
    max_images: int = 8,
    resume_from: str = "",
) -> dict[str, Any]:
    """Execute the full production chain for one asset. Mutates and returns asset.

    ``resume_from`` skips stages before the named key (inclusive start), so a
    failed run can continue without regenerating earlier artifacts.
    """
    asset = dict(asset)
    asset_id = str(asset.get("asset_id") or f"asset_{abs(hash(asset.get('title') or 'x')) % 10**8}")
    asset["asset_id"] = asset_id
    _ensure_pipeline(asset)
    artifact_index: dict[str, Any] = dict(asset.get("production_artifacts") or {})

    stage_order = list(PIPELINE_STAGE_KEYS)
    resume_idx = stage_order.index(resume_from) if resume_from in stage_order else 0

    def _should_run(key: str) -> bool:
        return stage_order.index(key) >= resume_idx

    # ---- idea ----
    def stage_idea():
        if not (asset.get("title") or asset.get("hook")):
            raise RuntimeError("Asset is missing title/hook")
        path = art.write_json(asset_id, "idea.json", {
            "title": asset.get("title"),
            "hook": asset.get("hook"),
            "description": asset.get("description"),
        })
        return {}, [path]

    if _should_run("idea"):
        if not _run_stage(asset, "idea", stage_idea, on_progress=on_progress):
            return _finalize(asset, project, ok=False, error="idea stage failed")
    else:
        _emit(on_progress, asset, "idea", "Idea skipped (resume)")

    # ---- script ----
    def stage_script():
        if asset_has_video_script(asset):
            path = art.write_json(asset_id, "script.json", asset.get("video_script"))
            return {}, [path]
        from services.script_generator import generate_video_script

        result = generate_video_script(
            asset,
            project,
            model=str(project.get("model") or ""),
            on_progress=lambda msg: _emit(on_progress, asset, "script", msg),
        )
        if not result.ok or not result.script:
            raise RuntimeError(result.error or "Script generation failed")
        updated = apply_script_to_asset(asset, result.script)
        asset.update(updated)
        path = art.write_json(asset_id, "script.json", asset.get("video_script"))
        return {"video_script": asset.get("video_script"), "script": asset.get("script")}, [path]

    if _should_run("script"):
        if not _run_stage(asset, "script", stage_script, on_progress=on_progress, max_retries=1):
            return _finalize(asset, project, ok=False, error="script stage failed")
    else:
        script_path = art.production_dir(asset_id) / "script.json"
        if script_path.exists() and not asset_has_video_script(asset):
            import json as _json

            asset["video_script"] = _json.loads(script_path.read_text(encoding="utf-8"))
            asset["script"] = (asset.get("video_script") or {}).get("full_voiceover") or asset.get("script")

    # ---- scenes ----
    def stage_scenes():
        scenes = _scenes_from_script(asset)
        if not scenes:
            # Fall back to visual planner
            from services.visual.scenes import plan_scenes

            planned = plan_scenes(asset) or []
            scenes = []
            for item in planned:
                if hasattr(item, "to_dict"):
                    scenes.append(item.to_dict())
                elif isinstance(item, dict):
                    scenes.append(item)
        if not scenes:
            raise RuntimeError("No scenes could be built from script")
        visual_package = dict(asset.get("visual_package") or {})
        visual_package["scenes"] = scenes
        path = art.write_json(asset_id, "scenes.json", scenes)
        return {
            "scene_breakdown": scenes,
            "visual_package": visual_package,
        }, [path]

    if _should_run("scenes"):
        if not _run_stage(asset, "scenes", stage_scenes, on_progress=on_progress):
            return _finalize(asset, project, ok=False, error="scenes stage failed")
    else:
        scenes_path = art.production_dir(asset_id) / "scenes.json"
        if scenes_path.exists() and not asset.get("scene_breakdown"):
            import json as _json

            loaded = _json.loads(scenes_path.read_text(encoding="utf-8"))
            asset["scene_breakdown"] = loaded
            visual_package = dict(asset.get("visual_package") or {})
            visual_package["scenes"] = loaded
            asset["visual_package"] = visual_package

    scenes = list(asset.get("scene_breakdown") or (asset.get("visual_package") or {}).get("scenes") or [])
    if not scenes:
        scenes = _scenes_from_script(asset)

    # ---- visual prompts ----
    def stage_visual_prompts():
        image_prompts = []
        video_prompts = []
        for scene in scenes:
            prompt = str(scene.get("ai_image_prompt") or scene.get("visual_description") or asset.get("title") or "cinematic still")
            image_prompts.append(
                {
                    "scene_number": scene.get("scene_number"),
                    "prompt": prompt,
                    "aspect_ratio": "9:16",
                }
            )
            video_prompts.append(
                {
                    "scene_number": scene.get("scene_number"),
                    "prompt": str(scene.get("ai_video_prompt") or f"Cinematic motion: {prompt}"),
                    "duration_sec": scene.get("length_sec"),
                }
            )
        flat = [item["prompt"] for item in image_prompts]
        payload = {"image_prompts": image_prompts, "video_prompts": video_prompts}
        path = art.write_json(asset_id, "visual_prompts.json", payload)
        visual_package = dict(asset.get("visual_package") or {})
        visual_package["image_prompts"] = image_prompts
        visual_package["video_prompts"] = video_prompts
        return {
            "visual_prompts": flat,
            "visual_package": visual_package,
        }, [path]

    if _should_run("visual_prompts"):
        if not _run_stage(asset, "visual_prompts", stage_visual_prompts, on_progress=on_progress):
            return _finalize(asset, project, ok=False, error="visual_prompts stage failed")

    # ---- images ----
    def stage_images():
        from services.provider_runtime.engine_api import runtime_generate_image

        generated = []
        prompts = (asset.get("visual_package") or {}).get("image_prompts") or []
        targets = scenes[:max_images]
        for index, scene in enumerate(targets):
            prompt = ""
            if index < len(prompts):
                item = prompts[index]
                prompt = item.get("prompt") if isinstance(item, dict) else str(item)
            prompt = prompt or scene.get("ai_image_prompt") or scene.get("visual_description") or asset.get("title") or "cinematic still"
            result = runtime_generate_image(prompt, {"width": 1080, "height": 1920})
            if result.get("path") and not str(result.get("path")).startswith(("mock://", "runtime://")):
                copied = art.copy_into(asset_id, str(result["path"]), f"image_{index + 1:02d}.png")
                if copied:
                    result = {**result, "path": copied, "local_path": copied}
            generated.append({**result, "scene_number": scene.get("scene_number", index + 1), "prompt": prompt})
            scene["resolved_asset"] = generated[-1]
        # Attach resolved assets onto visual package scenes
        for scene in scenes:
            for g in generated:
                if g.get("scene_number") == scene.get("scene_number"):
                    scene["resolved_asset"] = g
        path = art.write_json(asset_id, "images.json", generated)
        real = [g for g in generated if g.get("path") and not g.get("placeholder")]
        if not real and generated:
            # Still mark completed with placeholders — FFmpeg can use color bed
            pass
        visual_package = dict(asset.get("visual_package") or {})
        visual_package["scenes"] = scenes
        return {
            "generated_images": generated,
            "render_assets": {"assets": generated, "missing_assets": [], "warnings": [], "requests": []},
            "visual_package": visual_package,
            "scene_breakdown": scenes,
        }, [path] + [g["path"] for g in generated if g.get("path") and not str(g["path"]).startswith(("mock://", "runtime://"))]

    if _should_run("images"):
        if not _run_stage(asset, "images", stage_images, on_progress=on_progress, max_retries=1):
            return _finalize(asset, project, ok=False, error="images stage failed")
    else:
        images_path = art.production_dir(asset_id) / "images.json"
        if images_path.exists() and not asset.get("generated_images"):
            import json as _json

            asset["generated_images"] = _json.loads(images_path.read_text(encoding="utf-8"))

    # ---- video clips (optional failover to stills) ----
    def stage_video_clips():
        from services.provider_runtime.config import has_credential
        from services.provider_runtime.engine_api import runtime_generate_video

        video_keys = ("RUNWAY_API_KEY", "FAL_KEY", "REPLICATE_API_TOKEN", "PIKA_API_KEY", "LUMA_API_KEY")
        if not any(has_credential(k) for k in video_keys):
            path = art.write_json(asset_id, "video_clips.json", {"skipped": True, "reason": "no video provider configured — using stills"})
            return {"_stage_skipped": True, "generated_videos": []}, [path]

        clips = []
        # Generate at most 2 clips to control cost/latency
        for index, scene in enumerate(scenes[:2]):
            prompt = scene.get("ai_video_prompt") or scene.get("visual_description") or ""
            result = runtime_generate_video(prompt, float(scene.get("length_sec") or 3), {"width": 1080, "height": 1920})
            if result.get("path") and not str(result.get("path")).startswith(("mock://", "runtime://")):
                copied = art.copy_into(asset_id, str(result["path"]), f"clip_{index + 1:02d}.mp4")
                if copied:
                    result = {**result, "path": copied}
            clips.append({**result, "scene_number": scene.get("scene_number", index + 1)})
        path = art.write_json(asset_id, "video_clips.json", clips)
        return {"generated_videos": clips}, [path]

    if _should_run("video_clips"):
        if not _run_stage(asset, "video_clips", stage_video_clips, on_progress=on_progress, max_retries=1):
            # Soft-fail: continue with stills
            _set_stage(asset, "video_clips", status="skipped", error="video clips unavailable — continuing with stills")
            _emit(on_progress, asset, "video_clips", "Video clips skipped — continuing with stills")

    # ---- voice ----
    def stage_voice():
        from services.media_production.voice import synthesize_voice
        from services.voice_profiles import get_default_profile

        text = str(asset.get("script") or (asset.get("video_script") or {}).get("full_voiceover") or "")
        if not text.strip():
            text = " ".join(str(s.get("narration") or "") for s in scenes)
        profile = get_default_profile(str(project.get("niche") or ""))
        result = synthesize_voice(text, profile=profile, settings=profile.get("settings") or {})
        voice_pkg = result.get("voice_package") or {}
        local = ""
        if voice_pkg.get("path"):
            local = art.copy_into(asset_id, str(voice_pkg["path"]), "voice.mp3") or str(voice_pkg["path"])
            voice_pkg = {**voice_pkg, "path": local}
        path = art.write_json(asset_id, "voice.json", voice_pkg)
        arts = [path]
        if local:
            arts.append(local)
        if voice_pkg.get("placeholder"):
            raise RuntimeError(voice_pkg.get("error") or "Voice synthesis returned placeholder — check TTS credentials")
        return {"voice_package": voice_pkg, "audio_package": {**(asset.get("audio_package") or {}), "path": local, "voice_package": voice_pkg}}, arts

    if _should_run("voice"):
        if not _run_stage(asset, "voice", stage_voice, on_progress=on_progress, max_retries=2):
            return _finalize(asset, project, ok=False, error="voice stage failed")

    # ---- music ----
    def stage_music():
        from services.provider_runtime.config import has_credential
        from services.provider_runtime.runtime import get_provider_runtime

        mood = str(asset.get("music_style") or (asset.get("audio_package") or {}).get("music_mood") or "uplifting ambient")
        music_direction = {"style": mood, "bpm_range": [90, 120], "energy_curve": ["rise", "sustain", "resolve"]}
        music_meta = {"prompt": mood, "mood": mood, "duration_sec": float(asset.get("estimated_runtime_sec") or 60)}
        if has_credential("ELEVENLABS_API_KEY"):
            resp = get_provider_runtime().generate_music(music_meta, allow_fallback=True)
            data = dict(resp.data or {})
            path = art.write_json(asset_id, "music.json", {"provider": resp.provider, **data, "mood": mood})
            return {
                "audio_package": {
                    **(asset.get("audio_package") or {}),
                    "music_direction": music_direction,
                    "music_mood": mood,
                    "music": data,
                }
            }, [path]
        path = art.write_json(asset_id, "music.json", {"planned": True, "mood": mood, "note": "No music provider — plan only"})
        return {
            "_stage_skipped": True,
            "audio_package": {
                **(asset.get("audio_package") or {}),
                "music_direction": music_direction,
                "music_mood": mood,
            },
        }, [path]

    if _should_run("music"):
        _run_stage(asset, "music", stage_music, on_progress=on_progress, max_retries=1)

    # ---- sfx ----
    def stage_sfx():
        from services.provider_runtime.config import has_credential
        from services.provider_runtime.runtime import get_provider_runtime

        cues = []
        for scene in scenes:
            cue = (scene.get("sfx_timing") or {}).get("cue") or scene.get("sound_effect") or ""
            if cue:
                cues.append({"scene_number": scene.get("scene_number"), "cue": cue})
        if has_credential("ELEVENLABS_API_KEY") and cues:
            resp = get_provider_runtime().generate_sound_effects(
                {"prompt": cues[0]["cue"], "duration_sec": 1.5},
                allow_fallback=True,
            )
            data = dict(resp.data or {})
            path = art.write_json(asset_id, "sfx.json", {"cues": cues, "sample": data, "provider": resp.provider})
            return {"sfx_cues": cues}, [path]
        path = art.write_json(asset_id, "sfx.json", {"cues": cues, "planned": True})
        return {"_stage_skipped": True, "sfx_cues": cues}, [path]

    if _should_run("sfx"):
        _run_stage(asset, "sfx", stage_sfx, on_progress=on_progress, max_retries=1)

    # ---- captions ----
    def stage_captions():
        timing = ((asset.get("voice_package") or {}).get("timing") or {})
        srt = _build_srt(scenes, timing)
        srt_path = art.write_text(asset_id, "captions.srt", srt)
        meta_path = art.write_json(asset_id, "captions.json", {"srt": srt_path, "scene_count": len(scenes)})
        return {"captions_srt": srt, "caption_file": srt_path}, [srt_path, meta_path]

    if _should_run("captions"):
        if not _run_stage(asset, "captions", stage_captions, on_progress=on_progress):
            return _finalize(asset, project, ok=False, error="captions stage failed")

    # ---- timeline + render (FFmpeg) ----
    def stage_timeline():
        from engines.render.timeline import TimelineBuilder

        timeline = TimelineBuilder().build(scenes)
        path = art.write_json(asset_id, "timeline.json", timeline)
        return {"_timeline": timeline}, [path]

    if _should_run("timeline"):
        if not _run_stage(asset, "timeline", stage_timeline, on_progress=on_progress):
            return _finalize(asset, project, ok=False, error="timeline stage failed")
    else:
        timeline_path = art.production_dir(asset_id) / "timeline.json"
        if timeline_path.exists() and not asset.get("_timeline"):
            import json as _json

            asset["_timeline"] = _json.loads(timeline_path.read_text(encoding="utf-8"))

    def stage_render():
        from engines.render.audio_mix import AudioMixer
        from engines.render.captions import CaptionRenderer
        from engines.render.motion import MotionPlanner
        from engines.render.packaging import OutputPackager
        from engines.render.scene_plans import SceneRenderer
        from engines.render.timeline import TimelineBuilder
        from engines.render.transitions import TransitionPlanner
        from engines.render.validator import RenderValidator
        from services.media_production.ffmpeg_assembler import assemble_mp4, write_assembly_sidecar
        from services.media_production.formats import resolve_output_format

        timeline = asset.get("_timeline") or TimelineBuilder().build(scenes)
        transition_plan = TransitionPlanner().plan(scenes)
        motion_plan = MotionPlanner().plan(scenes)
        voice_path = (asset.get("voice_package") or {}).get("path") or ""
        audio_package = {
            **(asset.get("audio_package") or {}),
            "path": voice_path,
        }
        caption_render_plan = CaptionRenderer().build(scenes, timeline)
        audio_mix_plan = AudioMixer().build(
            scenes, audio_package, timeline, transition_plan["transitions"]
        )
        # Ensure narration segments point at the real voice file
        for seg in ((audio_mix_plan.get("tracks") or {}).get("narration") or {}).get("segments") or []:
            if voice_path:
                seg["path"] = voice_path
        if voice_path and not ((audio_mix_plan.get("tracks") or {}).get("narration") or {}).get("segments"):
            audio_mix_plan.setdefault("tracks", {}).setdefault("narration", {})["segments"] = [
                {
                    "scene_id": 1,
                    "path": voice_path,
                    "start_sec": 0,
                    "end_sec": float(timeline.get("total_duration_sec") or asset.get("estimated_runtime_sec") or 30),
                }
            ]

        generated = [g for g in (asset.get("generated_images") or []) if isinstance(g, dict)]
        scene_render_plan = SceneRenderer().build(scenes, generated, audio_package.get("scene_cues", []) if isinstance(audio_package.get("scene_cues"), list) else [])
        for plan in scene_render_plan:
            if not isinstance(plan, dict):
                continue
            for scene in scenes:
                if not isinstance(scene, dict):
                    continue
                if scene.get("scene_number") == plan.get("scene_id") and isinstance(scene.get("resolved_asset"), dict):
                    plan["resolved_asset"] = scene["resolved_asset"]

        validation = RenderValidator().validate(
            scenes=scenes,
            timeline=timeline,
            scene_render_plan=scene_render_plan,
            caption_render_plan=caption_render_plan,
            audio_mix_plan=audio_mix_plan,
            missing_assets=[],
        )

        fmt = resolve_output_format(aspect="vertical")
        resolution = fmt["resolution"]
        out_rel = f"data/productions/{asset_id}/render.mp4"
        assembly = assemble_mp4(
            title=str(asset.get("title") or "Untitled"),
            output_path=out_rel,
            timeline=timeline,
            scene_render_plan=scene_render_plan,
            audio_mix_plan=audio_mix_plan,
            output_format=fmt,
        )
        if not assembly.get("ok"):
            raise RuntimeError(assembly.get("error") or "FFmpeg assembly failed")

        mp4_path = assembly.get("output_path") or out_rel
        write_assembly_sidecar(assembly, mp4_path)
        render_result = {
            "render_status": "SUCCESS",
            "mock_output_path": mp4_path,
            "output_path": mp4_path,
            "mp4_path": mp4_path,
            "file_uri": mp4_path,
            "duration_sec": float(timeline.get("total_duration_sec") or 0),
            "warnings": [],
            "missing_assets": [],
            "render_log": assembly.get("log") or [],
            "job": {},
            "estimated_render_duration_sec": float(timeline.get("total_duration_sec") or 0),
            "mock": False,
            "assembly": assembly,
            "output_format": fmt,
        }
        render_package = OutputPackager().package(
            title=str(asset.get("title") or "Untitled"),
            timeline=timeline,
            scene_render_plan=scene_render_plan,
            caption_render_plan=caption_render_plan,
            audio_mix_plan=audio_mix_plan,
            transition_plan=transition_plan,
            motion_plan=motion_plan,
            asset_requirements=[],
            missing_assets=[],
            render_warnings=[],
            validation=validation,
            render_result=render_result,
        )
        arts = [art.write_json(asset_id, "render_package.json", render_package), mp4_path]
        return {"render_package": render_package, "mp4_path": mp4_path}, arts

    if _should_run("render"):
        if not _run_stage(asset, "render", stage_render, on_progress=on_progress, max_retries=1):
            return _finalize(asset, project, ok=False, error="render stage failed")

    # ---- quality ----
    def stage_quality():
        from services.master_pipeline.qc import run_production_qc

        qc = run_production_qc(
            {"ideas": [asset], "workflow_run_id": f"asset_{asset_id}"},
            {"unified_packages": [asset]},
        )
        render = asset.get("render_package") or {}
        checks = list(qc.get("checks") or [])
        if render.get("mock"):
            checks.append({"name": "real_mp4", "ok": False, "detail": "mock render", "level": "error"})
            qc["passed"] = False
        elif not render.get("mp4_path"):
            checks.append({"name": "real_mp4", "ok": False, "detail": "missing mp4", "level": "error"})
            qc["passed"] = False
        else:
            checks.append({"name": "real_mp4", "ok": True, "detail": render.get("mp4_path"), "level": "info"})
        voice = asset.get("voice_package") or {}
        checks.append({
            "name": "voice_file",
            "ok": bool(voice.get("path") and not voice.get("placeholder")),
            "detail": voice.get("path") or "missing",
            "level": "error" if voice.get("placeholder") else "info",
        })
        qc["checks"] = checks
        if any(c.get("level") == "error" and not c.get("ok") for c in checks):
            qc["passed"] = False
        path = art.write_json(asset_id, "production_report.json", qc)
        if not qc.get("passed"):
            raise RuntimeError("Quality control failed: " + "; ".join(qc.get("errors") or ["see production_report.json"]))
        return {"production_qc": qc}, [path]

    if _should_run("quality"):
        if not _run_stage(asset, "quality", stage_quality, on_progress=on_progress):
            return _finalize(asset, project, ok=False, error="quality stage failed")

    # ---- export ----
    def stage_export():
        render = asset.get("render_package") or {}
        mp4 = render.get("mp4_path") or ""
        metadata = {
            "title": asset.get("title"),
            "description": asset.get("description") or asset.get("hook"),
            "hashtags": asset.get("hashtags") or [],
            "cta": asset.get("cta"),
            "duration_sec": render.get("duration_sec") or asset.get("estimated_runtime_sec"),
            "mp4_path": mp4,
            "platform": project.get("platform") or "youtube_shorts",
            "generated_at": _now(),
        }
        # Thumbnail: first generated image or concept
        thumb_path = ""
        images = asset.get("generated_images") or []
        if images and images[0].get("path"):
            thumb_path = art.copy_into(asset_id, str(images[0]["path"]), "thumbnail.png") or ""
        meta_path = art.write_json(asset_id, "metadata.json", metadata)
        arts = [meta_path]
        if thumb_path:
            arts.append(thumb_path)
        if mp4:
            arts.append(mp4)
        manifest = art.write_json(asset_id, "export_manifest.json", {"artifacts": art.list_artifacts(asset_id), "metadata": metadata})
        arts.append(manifest)
        return {
            "export_package": metadata,
            "thumbnail_path": thumb_path,
            "workspace_status": "rendered",
        }, arts

    if _should_run("export"):
        if not _run_stage(asset, "export", stage_export, on_progress=on_progress):
            return _finalize(asset, project, ok=False, error="export stage failed")

    # ---- publish prep (stop if no OAuth) ----
    def stage_publish():
        from services.provider_runtime.config import has_credential

        oauth = any(
            has_credential(env)
            for env in (
                "YOUTUBE_ACCESS_TOKEN",
                "TIKTOK_ACCESS_TOKEN",
                "INSTAGRAM_ACCESS_TOKEN",
                "FACEBOOK_ACCESS_TOKEN",
                "X_ACCESS_TOKEN",
            )
        )
        render = asset.get("render_package") or {}
        package = {
            "title": asset.get("title"),
            "description": (asset.get("export_package") or {}).get("description"),
            "hashtags": asset.get("hashtags") or [],
            "mp4_path": render.get("mp4_path"),
            "thumbnail": asset.get("thumbnail_path"),
            "platform": project.get("platform") or "youtube_shorts",
            "ready": bool(oauth and render.get("mp4_path") and not render.get("mock")),
            "status": "prepared" if oauth else "awaiting_oauth",
            "note": "" if oauth else "Publishing credentials unavailable — stopped after MP4 export",
        }
        path = art.write_json(asset_id, "publish_package.json", package)
        if skip_publish_if_no_oauth and not oauth:
            return {"_stage_skipped": True, "publish_package": package}, [path]
        return {"publish_package": package}, [path]

    if _should_run("publish"):
        _run_stage(asset, "publish", stage_publish, on_progress=on_progress)

    artifact_index = {
        "root": str(art.rel(art.production_dir(asset_id))),
        "files": art.list_artifacts(asset_id),
        "images": asset.get("generated_images") or [],
        "music": (asset.get("audio_package") or {}).get("music"),
        "sfx": asset.get("sfx_cues"),
        "captions": asset.get("caption_file"),
        "render": (asset.get("render_package") or {}).get("mp4_path"),
    }
    asset["production_artifacts"] = artifact_index
    asset["production_pipeline"] = build_pipeline_snapshot(asset)
    return _finalize(asset, project, ok=True)


def _finalize(asset: dict, project: dict, *, ok: bool, error: str = "") -> dict:
    asset["production_pipeline"] = build_pipeline_snapshot(asset)
    asset["production_ok"] = ok
    if error:
        asset["production_error"] = error
    elif ok:
        asset.pop("production_error", None)
    log_event(
        logger,
        "asset_production.complete",
        ok=ok,
        asset_id=asset.get("asset_id"),
        progress=(asset.get("production_pipeline") or {}).get("progress_percent"),
        error=error[:120] if error else "",
    )
    return asset
