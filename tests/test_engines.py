import engines  # noqa: F401 - importing registers all engines
from engines import registry
from engines.base import PlannedEngine

EXPECTED_KEYS = {
    "ideation",
    "research",
    "seo",
    "script",
    "voice",
    "image",
    "video",
    "publishing",
    "analytics",
    "learning",
}


def test_all_engines_registered():
    assert EXPECTED_KEYS.issubset(set(registry.engine_keys()))


def test_ideation_is_ready_and_planned_engines_are_not():
    assert registry.get_engine("ideation").is_ready() is True
    for key in EXPECTED_KEYS - {"ideation"}:
        assert registry.get_engine(key).is_ready() is False


def test_planned_engines_return_not_implemented():
    result = registry.get_engine("research").run({})
    assert result == {"research_status": "not_implemented"}


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
