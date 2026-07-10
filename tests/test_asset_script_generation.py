"""Tests for Phase 1 asset video script generation and production pipeline UI."""

from __future__ import annotations

import json

import pytest

from core.models import normalize_idea_asset
from core.script_models import (
    ScriptSegment,
    VideoScript,
    apply_script_to_asset,
    asset_has_video_script,
    build_pipeline_stages,
    estimated_duration_from_segments,
    load_video_script,
    pipeline_progress_percent,
    validate_script_payload,
)
from core.storage.json_store import JsonProjectStore
from services.script_generator import generate_video_script

VALID_SCRIPT = {
    "title": "The Hidden Signal",
    "target_duration_seconds": 60,
    "tone": "mysterious",
    "primary_emotion": "curiosity",
    "script_summary": "A tight short on a hidden signal most people miss.",
    "segments": [
        {
            "segment_number": 1,
            "start_time": 0,
            "end_time": 2,
            "segment_type": "hook",
            "voiceover": "This signal changes everything about black holes.",
            "emotion": "curiosity",
            "delivery": "quiet and suspenseful",
            "retention_device": "open loop",
        },
        {
            "segment_number": 2,
            "start_time": 2,
            "end_time": 10,
            "segment_type": "context",
            "voiceover": "Most explanations stop at the surface, which is why the pattern keeps repeating.",
            "emotion": "intrigue",
            "delivery": "steady and clear",
            "retention_device": "pattern interrupt",
        },
        {
            "segment_number": 3,
            "start_time": 10,
            "end_time": 18,
            "segment_type": "retention_hook",
            "voiceover": "And the next detail is the one people replay.",
            "emotion": "tension",
            "delivery": "lean in",
            "retention_device": "direct address",
        },
        {
            "segment_number": 4,
            "start_time": 18,
            "end_time": 35,
            "segment_type": "escalation",
            "voiceover": "Once the mechanism clicks, the effect compounds faster than most models predict.",
            "emotion": "surprise",
            "delivery": "building pace",
            "retention_device": "visual switch",
        },
        {
            "segment_number": 5,
            "start_time": 35,
            "end_time": 48,
            "segment_type": "payoff",
            "voiceover": "That is why this signal matters right now.",
            "emotion": "revelation",
            "delivery": "peak energy then pause",
            "retention_device": "emotional peak",
        },
        {
            "segment_number": 6,
            "start_time": 48,
            "end_time": 60,
            "segment_type": "cta",
            "voiceover": "Follow for the next breakdown.",
            "emotion": "resolve",
            "delivery": "warm and direct",
            "retention_device": "clear ask",
        },
    ],
    "call_to_action": "Follow for the next breakdown.",
}
VALID_SCRIPT["full_voiceover"] = " ".join(s["voiceover"] for s in VALID_SCRIPT["segments"])
VALID_SCRIPT["estimated_word_count"] = len(VALID_SCRIPT["full_voiceover"].split())

SAMPLE_ASSET = {
    "asset_id": "asset_1",
    "title": "Black Hole Signal",
    "hook": "Nobody explains this part of black holes.",
    "description": "A fast explainer on the hidden signal.",
    "cta": "Follow for more.",
    "keywords": ["black holes", "space"],
    "hashtags": ["#space", "#science"],
    "thumbnail_concept": "Glowing accretion disk with bold text",
}


def test_valid_script_response_parsing():
    script, errors = validate_script_payload(VALID_SCRIPT)
    assert errors == []
    assert script is not None
    assert script.title == "The Hidden Signal"
    assert len(script.segments) == 6
    assert script.segments[0].segment_type == "hook"


def test_invalid_json_missing_segments():
    script, errors = validate_script_payload({"title": "X"})
    assert script is None
    assert any("segments" in err for err in errors)


def test_invalid_json_rejects_banned_phrase():
    bad = dict(VALID_SCRIPT)
    bad["full_voiceover"] = "Welcome back to the channel. " + bad["full_voiceover"]
    script, errors = validate_script_payload(bad)
    assert script is None
    assert any("banned" in err.lower() for err in errors)


def test_retry_behavior_uses_second_valid_response(monkeypatch):
    calls = {"n": 0}

    class FakeProvider:
        name = "fake"

        def is_available(self):
            return True

        def generate_json(self, system, user, model):
            calls["n"] += 1
            if calls["n"] == 1:
                return {"title": "broken"}, 10
            return VALID_SCRIPT, 25

    monkeypatch.setattr("services.script_generator.is_demo_mode", lambda: False)
    monkeypatch.setattr("services.script_generator.get_provider", lambda: FakeProvider())

    result = generate_video_script(SAMPLE_ASSET, {"model": "gpt-4o-mini"})
    assert result.ok
    assert result.script is not None
    assert result.attempts == 2
    assert result.tokens_used == 35


def test_invalid_json_falls_back_to_heuristic_after_retry(monkeypatch):
    class BadProvider:
        name = "bad"

        def is_available(self):
            return True

        def generate_json(self, system, user, model):
            return None, 0

    monkeypatch.setattr("services.script_generator.is_demo_mode", lambda: False)
    monkeypatch.setattr("services.script_generator.get_provider", lambda: BadProvider())

    result = generate_video_script(SAMPLE_ASSET, {"model": "gpt-4o-mini"})
    assert result.ok
    assert result.script is not None
    assert result.attempts == 2
    assert result.demo_mode is True


def test_script_duration_calculation():
    segments = [ScriptSegment.from_dict(item) for item in VALID_SCRIPT["segments"]]
    assert estimated_duration_from_segments(segments) == 60


def test_pipeline_status_marks_idea_and_script_correctly():
    asset = dict(SAMPLE_ASSET)
    stages = build_pipeline_stages(asset)
    by_key = {stage["key"]: stage["status"] for stage in stages}
    assert by_key["idea"] == "complete"
    assert by_key["script"] == "not_started"
    assert by_key["scenes"] == "not_started"
    assert by_key["render"] == "not_started"

    updated = apply_script_to_asset(asset, VideoScript.from_dict(VALID_SCRIPT))
    stages = build_pipeline_stages(updated)
    by_key = {stage["key"]: stage["status"] for stage in stages}
    assert by_key["idea"] == "complete"
    assert by_key["script"] == "complete"
    assert by_key["visuals"] == "not_started"
    assert pipeline_progress_percent(stages) == 20


def test_pipeline_in_progress_during_generation():
    asset = dict(SAMPLE_ASSET)
    stages = build_pipeline_stages(asset, script_generating=True)
    assert next(s for s in stages if s["key"] == "script")["status"] == "in_progress"


def test_legacy_asset_without_script_data():
    legacy = normalize_idea_asset({"title": "Old", "hook": "Old hook", "script": "Legacy line."}, index=0)
    assert legacy["script"] == "Legacy line."
    assert not asset_has_video_script(legacy)
    assert load_video_script(legacy) is None
    stages = build_pipeline_stages(legacy)
    assert next(s for s in stages if s["key"] == "script")["status"] == "not_started"


def test_normalize_idea_reads_video_script_voiceover():
    asset = normalize_idea_asset(
        {"title": "T", "video_script": VALID_SCRIPT},
        index=0,
    )
    assert asset["script"] == VALID_SCRIPT["full_voiceover"]
    assert asset_has_video_script(asset)


def test_save_and_reload_generated_script(tmp_path):
    store = JsonProjectStore(directory=str(tmp_path / "projects"))
    project = {
        "name": "Script Test Project",
        "command": "test",
        "ideas": [SAMPLE_ASSET],
        "model": "gpt-4o-mini",
        "demo_mode": True,
    }
    result = generate_video_script(SAMPLE_ASSET, project, force_heuristic=True)
    assert result.ok and result.script

    project["ideas"][0] = apply_script_to_asset(SAMPLE_ASSET, result.script)
    path = store.save_project(project)

    with open(path, encoding="utf-8") as handle:
        reloaded = json.load(handle)
    idea = reloaded["ideas"][0]
    assert asset_has_video_script(idea)
    assert idea["script"]
    assert idea["production_pipeline"]["progress_percent"] == 20
    script = load_video_script(idea)
    assert script is not None
    assert len(script.segments) >= 6


def test_heuristic_generation_in_demo_mode(monkeypatch):
    monkeypatch.setattr("services.script_generator.is_demo_mode", lambda: True)
    result = generate_video_script(SAMPLE_ASSET, {"model": "gpt-4o-mini"})
    assert result.ok
    assert result.demo_mode
    assert result.script.target_duration_seconds == 60
    assert result.script.segments[0].segment_type == "hook"
