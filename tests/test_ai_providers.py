from core.ai import GenerationRequest, get_provider
from core.ai.demo_provider import DemoProvider


def _request(count=3):
    return GenerationRequest(
        command="Create shorts about focus", niche="Psychology", subject="focus", count=count, model="gpt-4o-mini"
    )


def test_demo_provider_generates_requested_count():
    result = DemoProvider().generate_ideas(_request(count=4))
    assert len(result.ideas) == 4
    assert result.demo_mode is True
    assert result.tokens_used == 0


def test_demo_ideas_have_full_content_package():
    idea = DemoProvider().generate_ideas(_request(count=1)).ideas[0]
    for key in ("title", "hook", "script", "cta", "hashtags", "thumbnail_concept"):
        assert idea.get(key)


def test_get_provider_returns_demo_without_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert get_provider().name == "demo"
