"""Provider interface tests."""

from providers import get_voice_provider
from providers.voice.base import VoiceMode
from providers.voice.demo_ai import DemoAIVoiceProvider
from services.voice_profiles import get_default_profile, get_voice_profile_manager


def test_demo_ai_voice_synthesizes():
    provider = DemoAIVoiceProvider()
    result = provider.synthesize("Hello world this is a test narration.", get_default_profile("Science"), {})
    assert result.asset_id
    assert result.duration_sec > 0
    assert result.mode == VoiceMode.AI
    assert result.placeholder is True


def test_voice_provider_factory():
    assert get_voice_provider(VoiceMode.AI).name == "demo_ai"


def test_voice_profile_manager_create_and_list():
    manager = get_voice_profile_manager()
    import tempfile
    manager.directory = tempfile.mkdtemp()
    profile = manager.create_profile("Test Narrator", "science", mode="ai")
    assert profile["profile_id"]
    assert len(manager.list_profiles()) == 1
