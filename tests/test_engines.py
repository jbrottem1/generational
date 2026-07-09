import engines  # noqa: F401 - importing registers all engines
from engines import registry
from engines.base import PlannedEngine

INTELLIGENCE_LIVE = {
    "trend_discovery", "opportunity_ranking",
    "research", "ideation", "psychology", "script_generation",
    "visual_intelligence", "voice_audio", "attention_graph",
    "ranking", "script",
    "critic", "revision", "citation", "seo", "threat_detection", "quality",
}

PRODUCTION_LIVE = {
    "scene_planning", "narration", "visual_planning", "asset_manager",
    "subtitle", "timeline", "render_package", "publishing_queue",
}

LIVE_KEYS = INTELLIGENCE_LIVE | PRODUCTION_LIVE

PLANNED_KEYS = {"voice", "image", "video", "publishing", "analytics", "learning"}

EXPECTED_KEYS = LIVE_KEYS | PLANNED_KEYS


def test_all_engines_registered():
    assert EXPECTED_KEYS.issubset(set(registry.engine_keys()))


def test_intelligence_engines_ready_and_planned_engines_not():
    for key in LIVE_KEYS:
        assert registry.get_engine(key).is_ready() is True, key
    for key in PLANNED_KEYS:
        assert registry.get_engine(key).is_ready() is False, key


def test_planned_engines_return_not_implemented():
    result = registry.get_engine("voice").run({})
    assert result == {"voice_status": "not_implemented"}


def test_new_engine_can_register_and_replace():
    class FakeVoice(PlannedEngine):
        key = "voice"
        label = "Fake Voice"

        def is_ready(self):
            return True

        def run(self, context):
            return {"voice_file": "fake.mp3"}

    original = registry.get_engine("voice")
    try:
        registry.register(FakeVoice())
        assert registry.get_engine("voice").is_ready() is True
        assert registry.get_engine("voice").run({}) == {"voice_file": "fake.mp3"}
    finally:
        registry.register(original)
