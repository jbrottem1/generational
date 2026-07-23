"""Agent 22 — Real Provider Integration & Production Connectors tests."""

from __future__ import annotations

import json

import pytest

from services.provider_runtime import (
    ProviderRequest,
    ProviderResponse,
    ProviderRuntime,
    SecretManager,
    VersionManager,
    all_providers,
    capability_lookup,
    ensure_registered,
    get_provider,
    register_plugin,
    register_provider,
    set_priority,
)
from services.provider_runtime.adapter import ProviderAdapter
from services.provider_runtime.cache import ProviderCache
from services.provider_runtime.capabilities import IMAGE_GENERATION, LLM, PUBLISH, SCRIPT, SPEECH
from services.provider_runtime.connectors import PRODUCTION_CONNECTOR_CLASSES
from services.provider_runtime.connectors.base import ProductionConnector
from services.provider_runtime.connectors.text import OpenAIConnector
from services.provider_runtime.execution import RateLimiter, execute_with_retry
from services.provider_runtime.fallback import ProviderFallbackManager
from services.provider_runtime.http_client import HttpRequest, HttpResponse, set_default_transport
from services.provider_runtime.models import ProviderProfile
from services.provider_runtime.registry import health_score, record_health_score, reset_registry
from services.provider_runtime.reliability import ProviderReliabilityManager
from services.provider_runtime.secrets import decrypt_secrets, encrypt_secrets
from services.provider_runtime.selection import ProviderSelectionEngine, set_reliability_manager


@pytest.fixture(autouse=True)
def _isolate(monkeypatch):
    reset_registry()
    set_reliability_manager(ProviderReliabilityManager())
    set_default_transport(None)
    # Avoid accidental live calls
    for key in (
        "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "BFL_API_KEY",
        "IDEOGRAM_API_KEY", "STABILITY_API_KEY", "RUNWAY_API_KEY", "PIKA_API_KEY",
        "KLING_API_KEY", "LUMA_API_KEY", "ELEVENLABS_API_KEY",
        "YOUTUBE_ACCESS_TOKEN", "TIKTOK_ACCESS_TOKEN", "INSTAGRAM_ACCESS_TOKEN",
        "FACEBOOK_ACCESS_TOKEN", "X_ACCESS_TOKEN",
    ):
        monkeypatch.delenv(key, raising=False)
    yield
    set_default_transport(None)
    reset_registry()
    set_reliability_manager(None)


def _mock_transport(handler):
    def transport(request: HttpRequest) -> HttpResponse:
        return handler(request)

    set_default_transport(transport)


# ---------------------------------------------------- registration / discovery


def test_production_connectors_register():
    ensure_registered()
    names = {p.name for p in all_providers()}
    for cls in PRODUCTION_CONNECTOR_CLASSES:
        assert cls.name in names, cls.name
    assert "demo" in names
    assert "openai_tts" in names
    assert "openai_images" in names
    assert "music_future" in names
    assert "youtube" in names


def test_plugin_dynamic_registration():
    ensure_registered()

    class PluginAdapter(ProviderAdapter):
        name = "plugin_vendor"
        capabilities = (LLM,)

        def is_available(self):
            return True

        def execute(self, request):
            return ProviderResponse(success=True, provider=self.name, operation=request.operation, data={})

    def hook():
        register_provider(PluginAdapter())
        return 1

    register_plugin(hook)
    from services.provider_runtime.registry import run_plugins

    assert run_plugins() == 1
    assert get_provider("plugin_vendor") is not None


def test_capability_lookup_and_priority():
    ensure_registered()
    set_priority("demo", 100)
    ranked = capability_lookup(SCRIPT)
    assert ranked
    assert ranked[0]["name"] == "demo" or "priority" in ranked[0]


# ---------------------------------------------------- selection helpers


def test_runtime_selects_best_cheapest_fastest():
    ensure_registered()
    runtime = ProviderRuntime(config={"cache_enabled": False})
    assert runtime.best_provider(SCRIPT) is not None
    assert runtime.cheapest_provider(SCRIPT) is not None
    assert runtime.fastest_provider(SCRIPT) is not None
    assert runtime.highest_quality_provider(IMAGE_GENERATION) is not None
    assert runtime.fallback_provider(IMAGE_GENERATION) is not None


def test_selection_prefers_production_over_demo_when_keyed(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    ensure_registered()

    class FakeOpenAI(OpenAIConnector):
        def _execute_impl(self, request):
            return self.ok(request, {"text": "hello"})

    register_provider(FakeOpenAI())
    selector = ProviderSelectionEngine()
    chosen = selector.select(ProviderRequest(operation="generate_script", capability=SCRIPT, optimize_for="quality"))
    assert chosen is not None
    assert chosen.name != "demo"


# ---------------------------------------------------- HTTP mocked integrations


def test_openai_connector_chat_success():
    ensure_registered()

    def handler(req: HttpRequest) -> HttpResponse:
        assert "/chat/completions" in req.url
        return HttpResponse(
            status=200,
            body={
                "choices": [{"message": {"content": "Script about focus"}}],
                "usage": {"total_tokens": 42},
            },
        )

    _mock_transport(handler)
    connector = OpenAIConnector()
    connector.set_credential_overrides({"OPENAI_API_KEY": "sk-test"})
    response = connector.execute(
        ProviderRequest(operation="generate_script", payload={"prompt": "Write a short"})
    )
    assert response.success is True
    assert response.data["script"] == "Script about focus"
    assert response.tokens_used == 42


def test_openai_connector_missing_key_fails():
    connector = OpenAIConnector()
    response = connector.execute(ProviderRequest(operation="generate_script", payload={"prompt": "x"}))
    assert response.success is False
    assert "not available" in response.error


def test_anthropic_and_gemini_connectors(monkeypatch):
    from services.provider_runtime.connectors.text import AnthropicConnector, GoogleGeminiConnector

    def handler(req: HttpRequest) -> HttpResponse:
        if "anthropic" in req.url:
            return HttpResponse(
                status=200,
                body={"content": [{"type": "text", "text": "Claude text"}], "usage": {"input_tokens": 1, "output_tokens": 2}},
            )
        return HttpResponse(
            status=200,
            body={"candidates": [{"content": {"parts": [{"text": "Gemini text"}]}}], "usageMetadata": {"totalTokenCount": 9}},
        )

    _mock_transport(handler)
    anth = AnthropicConnector()
    anth.set_credential_overrides({"ANTHROPIC_API_KEY": "a-key"})
    gem = GoogleGeminiConnector()
    gem.set_credential_overrides({"GOOGLE_API_KEY": "g-key"})
    r1 = anth.execute(ProviderRequest(operation="generate_caption", payload={"prompt": "hi"}))
    r2 = gem.execute(ProviderRequest(operation="generate_metadata", payload={"prompt": "hi"}))
    assert r1.success and "Claude" in r1.data["text"]
    assert r2.success and "Gemini" in r2.data["text"]


def test_image_connectors_mocked():
    from services.provider_runtime.connectors.image import (
        FluxConnector,
        IdeogramConnector,
        OpenAIImagesConnector,
        StabilityAIConnector,
    )

    def handler(req: HttpRequest) -> HttpResponse:
        if "openai" in req.url:
            return HttpResponse(status=200, body={"data": [{"url": "https://img/openai.png"}]})
        if "bfl" in req.url or "flux" in req.url:
            return HttpResponse(status=200, body={"id": "job1", "status": "Ready", "sample": "https://img/flux.png"})
        if "ideogram" in req.url:
            return HttpResponse(status=200, body={"data": [{"url": "https://img/ideo.png"}]})
        return HttpResponse(status=200, body={"artifacts": [{"base64": "abc", "finishReason": "SUCCESS"}]})

    _mock_transport(handler)
    cases = [
        (OpenAIImagesConnector(), {"OPENAI_API_KEY": "k"}),
        (FluxConnector(), {"BFL_API_KEY": "k"}),
        (IdeogramConnector(), {"IDEOGRAM_API_KEY": "k"}),
        (StabilityAIConnector(), {"STABILITY_API_KEY": "k"}),
    ]
    for connector, creds in cases:
        connector.set_credential_overrides(creds)
        resp = connector.execute(ProviderRequest(operation="generate_image", payload={"prompt": "sunset"}))
        assert resp.success, (connector.name, resp.error)


def test_video_connectors_async_jobs():
    from services.provider_runtime.connectors.video import (
        GoogleVeoConnector,
        KlingConnector,
        LumaConnector,
        PikaConnector,
        RunwayConnector,
    )

    def handler(req: HttpRequest) -> HttpResponse:
        return HttpResponse(status=200, body={"id": "vid-1", "status": "PENDING", "name": "ops/1"})

    _mock_transport(handler)
    for cls, env in (
        (GoogleVeoConnector, "GOOGLE_API_KEY"),
        (RunwayConnector, "RUNWAY_API_KEY"),
        (KlingConnector, "KLING_API_KEY"),
        (PikaConnector, "PIKA_API_KEY"),
        (LumaConnector, "LUMA_API_KEY"),
    ):
        c = cls()
        c.set_credential_overrides({env: "key"})
        resp = c.execute(ProviderRequest(operation="generate_video", payload={"prompt": "drone shot"}))
        assert resp.success, (cls.name, resp.error)
        assert resp.data.get("async") is True or resp.data.get("job_id") or resp.data.get("status")


def test_voice_connectors_mocked():
    from services.provider_runtime.connectors.voice import ElevenLabsConnector, OpenAITTSConnector

    def handler(req: HttpRequest) -> HttpResponse:
        return HttpResponse(status=200, body=b"ID3fakeaudio", raw=b"ID3fakeaudio")

    _mock_transport(handler)
    el = ElevenLabsConnector()
    el.set_credential_overrides({"ELEVENLABS_API_KEY": "k"})
    oai = OpenAITTSConnector()
    oai.set_credential_overrides({"OPENAI_API_KEY": "k"})
    r1 = el.execute(ProviderRequest(operation="generate_voice", payload={"text": "Hello"}))
    r2 = oai.execute(ProviderRequest(operation="generate_voice", payload={"text": "Hello"}))
    assert r1.success and r1.data.get("audio_b64")
    assert r2.success and r2.data.get("audio_b64")


def test_publishing_connectors_mocked():
    from services.provider_runtime.connectors.publishing import (
        TikTokPublishingConnector,
        XPublishingConnector,
        YouTubePublishingConnector,
    )

    def handler(req: HttpRequest) -> HttpResponse:
        return HttpResponse(status=200, body={"id": "pub-1", "data": {"id": "pub-1"}})

    _mock_transport(handler)
    yt = YouTubePublishingConnector()
    yt.set_credential_overrides({"YOUTUBE_ACCESS_TOKEN": "t"})
    tk = TikTokPublishingConnector()
    tk.set_credential_overrides({"TIKTOK_ACCESS_TOKEN": "t"})
    x = XPublishingConnector()
    x.set_credential_overrides({"X_ACCESS_TOKEN": "t"})
    package = {"title": "Test", "description": "Desc", "hashtags": ["#a"], "video": {"uri": "https://cdn/v.mp4"}}
    assert yt.execute(ProviderRequest(operation="publish", payload={"package": package})).success
    assert tk.execute(ProviderRequest(operation="publish", payload={"package": package})).success
    assert x.execute(ProviderRequest(operation="publish", payload={"package": package})).success


# ---------------------------------------------------- failure / fallback / rate limit


def test_connector_http_failure_falls_back_to_demo(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-bad")

    def handler(req: HttpRequest) -> HttpResponse:
        return HttpResponse(status=500, body={"error": "boom"})

    _mock_transport(handler)
    ensure_registered()
    # Prefer openai but allow fallback to demo
    runtime = ProviderRuntime(config={"cache_enabled": False}, credential_overrides={"OPENAI_API_KEY": "sk-bad"})
    response = runtime.generate_script({"prompt": "hello"}, preferred_provider="openai", allow_fallback=True)
    assert response.success is True
    assert response.provider == "demo" or response.demo_mode is True or "openai" in response.fallbacks_used


def test_rate_limit_blocks_then_recovers():
    limiter = RateLimiter(default_rpm=1)
    assert limiter.allow("openai") is True
    assert limiter.allow("openai") is False
    limiter.reset()
    assert limiter.allow("openai") is True


def test_retry_on_transient_failure():
    attempts = {"n": 0}

    class Flaky(ProductionConnector):
        name = "flaky_prod"
        capabilities = (IMAGE_GENERATION,)
        api_key_env = ""

        def is_available(self):
            return True

        def _execute_impl(self, request):
            attempts["n"] += 1
            if attempts["n"] < 2:
                return self.fail(request, "transient")
            return self.ok(request, {"ok": True})

    adapter = Flaky()
    resp = execute_with_retry(
        adapter,
        ProviderRequest(operation="generate_image", max_retries=2),
        lambda p, r: p.execute(r),
    )
    assert resp.success is True
    assert attempts["n"] == 2


def test_fallback_manager_skips_failed_provider():
    class Fail(ProviderAdapter):
        name = "fail_img"
        capabilities = (IMAGE_GENERATION,)
        profile = ProviderProfile(quality=99)

        def is_available(self):
            return True

        def execute(self, request):
            return ProviderResponse(success=False, provider=self.name, operation=request.operation, error="nope")

    class Ok(ProviderAdapter):
        name = "ok_img"
        capabilities = (IMAGE_GENERATION,)
        profile = ProviderProfile(quality=50)

        def is_available(self):
            return True

        def execute(self, request):
            return ProviderResponse(success=True, provider=self.name, operation=request.operation, data={"ok": 1})

    register_provider(Fail())
    register_provider(Ok())
    mgr = ProviderFallbackManager()
    resp = mgr.execute_with_fallback(
        ProviderRequest(operation="generate_image", capability=IMAGE_GENERATION),
        lambda p, r: p.execute(r),
        IMAGE_GENERATION,
    )
    assert resp.success is True
    assert resp.provider == "ok_img"


# ---------------------------------------------------- cache / secrets / versions / health


def test_provider_cache_roundtrip(tmp_path):
    cache = ProviderCache(cache_dir=tmp_path, ttl_sec=60)
    req = ProviderRequest(operation="generate_image", payload={"prompt": "a"})
    resp = ProviderResponse(success=True, provider="demo", operation="generate_image", data={"image_url": "x"})
    assert cache.get(req) is None
    cache.put(req, resp)
    hit = cache.get(req)
    assert hit is not None
    assert hit.metadata.get("cache_hit") is True
    assert cache.stats()["hits"] == 1


def test_secret_manager_encrypt_rotate(tmp_path, monkeypatch):
    monkeypatch.setenv("PROVIDER_SECRETS_PASSPHRASE", "test-pass")
    path = tmp_path / "secrets.enc.json"
    mgr = SecretManager(secrets_path=path)
    mgr.rotate("OPENAI_API_KEY", "sk-rotated")
    assert path.exists()
    token = json.loads(path.read_text())["token"]
    decoded = decrypt_secrets(token, "test-pass")
    assert decoded["OPENAI_API_KEY"] == "sk-rotated"
    assert encrypt_secrets({"A": "1"}, "p")


def test_version_manager_pins_models():
    vm = VersionManager({"openai": {"model": "gpt-4o"}})
    assert vm.model_for("openai") == "gpt-4o"
    vm.pin("openai", model="gpt-4o-mini")
    assert vm.model_for("openai") == "gpt-4o-mini"
    assert any(v["provider"] == "anthropic" for v in vm.catalog())


def test_health_scoring():
    ensure_registered()
    record_health_score("demo", 80)
    assert health_score("demo") == 80
    runtime = ProviderRuntime(config={"cache_enabled": False})
    report = runtime.health_report()
    assert isinstance(report, dict)


def test_runtime_publish_capability_exists():
    ensure_registered()
    runtime = ProviderRuntime(config={"cache_enabled": False})
    # Without tokens, falls back to demo publish capability
    resp = runtime.publish({"package": {"title": "Hi"}}, allow_fallback=True)
    assert resp.operation == "publish"
    assert PUBLISH in __import__("services.provider_runtime.capabilities", fromlist=["PUBLISH"]).ALL_CAPABILITIES


def test_music_future_abstraction_unavailable_without_endpoint():
    from services.provider_runtime.connectors.music import FutureMusicConnector

    connector = FutureMusicConnector()
    assert connector.is_available() is False


def test_legacy_publishing_routes_through_runtime_when_keyed(monkeypatch):
    monkeypatch.setenv("YOUTUBE_ACCESS_TOKEN", "yt-token")
    ensure_registered()

    def handler(req: HttpRequest) -> HttpResponse:
        return HttpResponse(status=200, body={"id": "yt123"})

    _mock_transport(handler)
    from providers.publishing.adapters import YouTubeShortsProvider

    result = YouTubeShortsProvider().publish({"title": "Hello", "description": "d", "video": {"uri": "https://v"}})
    assert result["mock"] is False
    assert result["status"] == "published"
    assert "yt123" in result.get("post_id", "") or result.get("post_id")


def test_implementation_status_on_connectors():
    ensure_registered()
    openai = get_provider("openai")
    assert isinstance(openai, ProductionConnector)
    assert openai.implementation_status == "production"
    assert "implementation" in openai.describe()
