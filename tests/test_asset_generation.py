"""Tests for the Universal Asset Generation Engine (Agent 14).

Proves: provider selection, prompt compilation, asset registry, caching,
versioning, quality validation, failure handling, pipeline integration,
provider fallback, and the engine contract.
"""

from __future__ import annotations

import engines  # noqa: F401 - importing registers all engines
from engines import registry
from engines.contracts import ContractEngine
from providers.asset_generation import (
    MockGenerationProvider,
    get_generation_provider,
    register_generation_provider,
    unregister_generation_provider,
)
from providers.generation_provider import GenerationProvider
from services.asset_generation import (
    ASSET_FIELDS,
    ASSET_PACKAGE_FIELDS,
    ASSET_SUMMARY_FIELDS,
    compile_prompt,
    compute_fingerprint,
    configure,
    optimize_for_provider,
    reset_asset_generation_config,
    select_providers,
)
from services.asset_generation.catalog import asset_type_ids, resolve_asset_type
from services.asset_generation.models import AssetStatus, JobStatus, PackageReadiness
from services.asset_generation.package import build_asset_package
from services.asset_generation.registry import AssetRegistry
from services.orchestrator import ContentPackage, Orchestrator, StageStatus


def make_item(project_id="proj1"):
    """One ContentPackage-style dict with scene breakdown for generation."""
    return {
        "project_id": project_id,
        "topic": "deep sea creatures",
        "niche": "science",
        "title": "The Ocean Mystery",
        "hook": "What if the ocean disappeared tomorrow?",
        "script": (
            "The ocean vanishes overnight. Cities panic as the tides stop. "
            "Scientists trace the cause to a rift. The rift is growing. "
            "Humanity must act before dawn."
        ),
        "keywords": ["ocean", "science"],
        "quality_score": 80,
        "publish_ready": True,
        "script_package": {"script": "The ocean vanishes overnight...", "script_score": 78},
        "visual_package": {"scenes": []},
        "audio_package": {"voice_style": {"name": "narrator"}},
        "render_package": {"render_package_version": "2.0"},
        "scene_breakdown": [
            {"visual": "Bioluminescent jellyfish drift through the midnight zone."},
            {"visual": "Scientists in a submarine discover a glowing rift."},
            {"visual": "Coastal cities watch the tide retreat in panic."},
        ],
    }


def make_item_with_creative_package(project_id="proj_creative"):
    """Item with a minimal creative_package for requirement-based generation."""
    item = make_item(project_id)
    item["creative_package"] = {
        "creative_blueprint": {"visual_style": "cinematic", "aspect_ratio": "9:16", "tone": "awe"},
        "storyboard": [
            {
                "scene_id": "scene_01",
                "emotion": "wonder",
                "lighting": "deep blue bioluminescence",
                "color_palette": "navy and cyan",
                "camera_angle": "wide",
                "characters": ["char_narrator"],
                "estimated_duration_sec": 5,
            }
        ],
        "character_plan": {
            "cast": [
                {
                    "character_id": "char_narrator",
                    "name": "Dr. Marin",
                    "visual_signature": "silver-haired marine biologist, weathered face",
                    "wardrobe": "navy expedition jacket",
                    "color_anchor": "teal",
                }
            ]
        },
        "asset_requirements": [
            {
                "asset_id": "scene_01_visual",
                "scene_id": "scene_01",
                "asset_type": "ai_image",
                "description": "Bioluminescent jellyfish in the deep ocean",
                "prompt": "bioluminescent jellyfish drifting through midnight ocean",
                "style": "cinematic",
                "priority": "required",
                "reusable": False,
                "character_ids": ["char_narrator"],
            }
        ],
        "thumbnail_concepts": [
            {
                "concept_id": "thumb_01",
                "direction": "Glowing jellyfish against black ocean",
                "style": "cinematic",
                "color_strategy": "electric cyan accents",
            }
        ],
    }
    return item


# ----------------------------------------------------------------- contract


def test_asset_generation_is_a_live_contract_engine():
    engine = registry.get_engine("asset_generation")
    assert isinstance(engine, ContractEngine)
    assert engine.is_ready() is True
    diag = engine.diagnostics()
    assert diag["engine_id"] == "asset_generation"
    assert diag["version"] == "1.1.0"
    assert "unified_packages" in diag["input_contract"]
    assert "asset_generation_summary" in diag["output_contract"]
    assert "asset_packages" in diag["output_contract"]
    assert engine.health_check()["healthy"] is True


# ----------------------------------------------------------- catalog/types


def test_catalog_covers_all_supported_asset_types():
    ids = asset_type_ids()
    assert "scene_image" in ids
    assert "thumbnail" in ids
    assert "video_clip" in ids
    assert "object_3d" in ids
    assert len(ids) >= 40


def test_resolve_asset_type_normalizes_creative_studio_vocabulary():
    entry = resolve_asset_type("ai_image")
    assert entry["type_id"] == "scene_image"
    assert entry["asset_class"] == "image"


# -------------------------------------------------------- prompt compiler


def test_prompt_compiler_builds_canonical_spec():
    request = {
        "prompt": "bioluminescent jellyfish",
        "style": "cinematic",
        "lighting": "deep blue rim light",
        "aspect_ratio": "9:16",
        "resolution": "1080x1920",
    }
    spec = compile_prompt(request, {})
    assert "bioluminescent jellyfish" in spec["prompt"]
    assert spec["style"] == "cinematic"
    assert spec["negative_prompt"]
    assert spec["aspect_ratio"] == "9:16"


def test_optimize_for_provider_rewrites_dialect():
    spec = compile_prompt({"prompt": "sunset over mountains", "aspect_ratio": "16:9"}, {})
    provider = MockGenerationProvider()
    optimized = optimize_for_provider(spec, provider)
    assert optimized["provider"] == "mock_generation"
    assert optimized["prompt"]


def test_prompt_compiler_embeds_character_references():
    item = make_item_with_creative_package()
    request = dict(item["creative_package"]["asset_requirements"][0])
    request["character_ids"] = ["char_narrator"]
    spec = compile_prompt(request, item)
    assert "Dr. Marin" in spec["prompt"] or "marine biologist" in spec["prompt"]
    assert spec["character_references"]


def test_fingerprint_is_deterministic():
    request = {"prompt": "test", "asset_type": "scene_image", "style": "minimal"}
    spec = compile_prompt(request, {})
    first = compute_fingerprint(request, spec)
    second = compute_fingerprint(request, spec)
    assert first == second
    assert len(first) == 64


# ---------------------------------------------------- provider selection


def test_provider_selection_returns_primary_and_fallbacks():
    plan = select_providers({"asset_class": "image", "asset_type": "scene_image"})
    assert plan["primary"] == "mock_generation"
    assert plan["primary"] in [entry["provider"] for entry in plan["candidates"]]
    # With no API keys configured, the offline mock is the sole candidate.
    assert plan["candidates"]


def test_quality_strategy_prefers_higher_quality_providers():
    configure(selection_strategy="quality")
    try:
        plan = select_providers({"asset_class": "image"})
        scores = {entry["provider"]: entry["score"] for entry in plan["candidates"]}
        assert scores[plan["primary"]] == max(scores.values())
    finally:
        reset_asset_generation_config()


# ----------------------------------------------------------- generation


def test_build_asset_package_produces_full_contract():
    item = make_item()
    package = build_asset_package(item)
    for field in ASSET_PACKAGE_FIELDS:
        assert field in package, field
    assert package["assets"]
    for asset in package["assets"]:
        for field in ASSET_FIELDS:
            assert field in asset, field
    assert package["readiness"]["status"] in PackageReadiness.ALL


def test_cache_reuses_identical_requests():
    registry_store = AssetRegistry(directory="/tmp/test_asset_gen_cache")
    item = make_item("cache1")
    first = build_asset_package(item, registry=registry_store)
    second = build_asset_package(item, registry=registry_store)
    hits = sum(1 for job in second["generation_jobs"] if job["status"] == JobStatus.CACHE_HIT)
    assert hits >= 1
    assert first["assets"][0]["uri"] == second["assets"][0]["uri"]


def test_safety_rules_block_generation():
    configure(safety_rules=["forbidden_term_xyz"])
    try:
        item = make_item_with_creative_package("blocked1")
        for requirement in item["creative_package"]["asset_requirements"]:
            requirement["prompt"] = "forbidden_term_xyz in scene"
        package = build_asset_package(item)
        blocked = [asset for asset in package["assets"] if asset["status"] == AssetStatus.BLOCKED]
        assert blocked
    finally:
        reset_asset_generation_config()


def test_provider_fallback_reaches_mock_when_primary_fails():
    class FailingProvider(GenerationProvider):
        name = "failing_test_provider"
        label = "Always Fails"
        asset_classes = ("image",)
        profile = {"quality": 99, "cost_per_asset": 0.01, "speed": 99, "consistency": 99}

        def is_available(self):
            return True

        def generate(self, prompt_spec, request):
            return {"error": "simulated failure", "provider": self.name}

    register_generation_provider(FailingProvider())
    configure(provider_priority={"image": ["failing_test_provider"]})
    try:
        item = make_item("fallback1")
        package = build_asset_package(item)
        produced = [asset for asset in package["assets"] if asset.get("uri")]
        assert produced
        assert any(asset.get("provider") == "mock_generation" for asset in produced)
    finally:
        unregister_generation_provider("failing_test_provider")
        reset_asset_generation_config()


def test_mock_provider_is_deterministic():
    provider = MockGenerationProvider()
    request = {"asset_class": "image", "asset_type": "scene_image"}
    spec = compile_prompt({"prompt": "ocean wave"}, {})
    first = provider.generate(spec, request)
    second = provider.generate(spec, request)
    assert first == second
    assert first["placeholder"] is True
    assert first["uri"].startswith("mock://assets/generated/")


# -------------------------------------------------------- slot ownership


def test_engine_writes_only_asset_package_slot():
    item = make_item()
    before = {
        key: repr(item[key])
        for key in ("script_package", "visual_package", "audio_package", "render_package")
        if key in item
    }
    registry.get_engine("asset_generation").run({"unified_packages": [item]})
    for key, snapshot in before.items():
        assert repr(item[key]) == snapshot, f"{key} was mutated"
    assert item["asset_package"]["assets"]


def test_empty_context_reports_no_items_never_fails():
    updates = registry.get_engine("asset_generation").run({"command": "probe"})
    assert updates["asset_generation_summary"]["status"] == "no_items"
    assert updates["asset_generation_summary"]["items"] == 0
    assert updates["asset_packages"] == []


def test_summary_carries_the_full_contract():
    updates = registry.get_engine("asset_generation").run({"unified_packages": [make_item()]})
    summary = updates["asset_generation_summary"]
    for field in ASSET_SUMMARY_FIELDS:
        assert field in summary, field
    assert summary["status"] == "generated"
    assert summary["assets_generated"] >= 1


# ------------------------------------------------------------ registry


def test_asset_registry_versions_regenerations():
    store = AssetRegistry(directory="/tmp/test_asset_gen_versions")
    asset = {
        "asset_id": "asset_v1",
        "fingerprint": "fp_a",
        "uri": "mock://a",
        "provider": "mock_generation",
        "status": "generated",
        "version": 1,
        "created_at": "2026-01-01T00:00:00+00:00",
    }
    store.register_asset(asset)
    store.register_asset({**asset, "fingerprint": "fp_b", "uri": "mock://b", "version": 2})
    stored = store.get_asset("asset_v1")
    assert stored["version"] == 2
    assert len(stored["versions"]) == 2


# ------------------------------------------------------------ orchestrator


def test_asset_generation_stage_runs_through_orchestrator():
    context = {"command": "probe", "unified_packages": [make_item("p1")]}
    report = Orchestrator().run_asset_generation_stage(context)
    assert report.status == StageStatus.SUCCESS
    assert not report.errors
    assert context["asset_generation_summary"]["status"] == "generated"
    assert context["unified_packages"][0]["asset_package"]["assets"]


def test_content_package_carries_asset_slot_through_roundtrips():
    package = ContentPackage(asset_package={"asset_package_version": "1.1"})
    data = package.to_dict()
    assert data["asset_package"] == {"asset_package_version": "1.1"}
    restored = ContentPackage.from_dict(data)
    assert restored.asset_package == {"asset_package_version": "1.1"}


def test_fallback_requests_when_no_creative_package():
    item = {
        "project_id": "fallback_only",
        "title": "Quick Topic",
        "hook": "Something surprising happened",
        "scene_breakdown": [{"visual": "A dramatic opening shot of the city skyline."}],
    }
    package = build_asset_package(item)
    assert package["assets"]
    assert package["assets"][0]["status"] in (AssetStatus.GENERATED, AssetStatus.PLACEHOLDER, AssetStatus.CACHED)


# ============================================================ Phase 2


def test_provider_catalog_lists_all_adapters():
    from providers.asset_generation import ensure_providers_registered, provider_catalog
    from providers.generation_provider import GENERATION_ASSET_CLASSES

    ensure_providers_registered()
    catalog = provider_catalog()
    names = {entry["name"] for entry in catalog}
    for required in (
        "mock_generation", "openai_images", "runway", "flux", "kling",
        "pika", "luma", "google_veo", "stable_diffusion", "midjourney",
    ):
        assert required in names, required
    for entry in catalog:
        assert "latency_ms" in entry
        assert "available" in entry
    for media_class in ("animation", "audio", "motion_graphics"):
        assert media_class in GENERATION_ASSET_CLASSES


def test_selection_includes_latency_signal():
    plan = select_providers({"asset_class": "image", "asset_type": "scene_image"})
    assert plan["candidates"]
    assert "latency_ms" in plan["candidates"][0]


def test_latency_strategy_is_registered():
    from services.asset_generation.config import SELECTION_STRATEGIES

    assert "latency" in SELECTION_STRATEGIES
    configure(selection_strategy="latency")
    try:
        plan = select_providers({"asset_class": "image"})
        assert plan["strategy"] == "latency"
        assert plan["primary"]
    finally:
        reset_asset_generation_config()


def test_asset_metadata_attached_to_generated_assets():
    from services.asset_generation.models import ASSET_METADATA_FIELDS

    package = build_asset_package(make_item("meta1"))
    for asset in package["assets"]:
        assert "metadata" in asset
        for field in ASSET_METADATA_FIELDS:
            assert field in asset["metadata"], field


def test_package_includes_usage_report_and_new_asset_buckets():
    package = build_asset_package(make_item("usage1"))
    assert "usage_report" in package
    assert "events" in package["usage_report"]
    assert "audio_assets" in package
    assert "animation_assets" in package


def test_batch_generate_produces_batch_result():
    from services.asset_generation import BATCH_RESULT_FIELDS, batch_generate

    requests = [
        {
            "asset_id": f"batch_{i}",
            "project_id": "batch_proj",
            "asset_type": "scene_image",
            "asset_class": "image",
            "prompt": f"scene {i}",
            "style": "cinematic",
            "priority": "required",
            "aspect_ratio": "9:16",
            "resolution": "1080x1920",
        }
        for i in range(3)
    ]
    result = batch_generate(requests, {"project_id": "batch_proj"})
    for field in BATCH_RESULT_FIELDS:
        assert field in result, field
    assert result["requested"] == 3
    assert result["status"] in ("completed", "partial")
    assert len(result["assets"]) == 3


def test_batch_generate_empty_is_safe():
    from services.asset_generation import batch_generate

    result = batch_generate([])
    assert result["status"] == "empty"
    assert result["requested"] == 0


def test_job_queue_submit_and_run_generate():
    from services.asset_generation import run_generate

    request = {
        "asset_id": "queue_asset_1",
        "project_id": "queue_proj",
        "asset_type": "thumbnail",
        "asset_class": "image",
        "prompt": "bold thumbnail of a glowing rift",
        "style": "cinematic",
        "priority": "required",
        "aspect_ratio": "16:9",
        "resolution": "1280x720",
    }
    result = run_generate(request, {"project_id": "queue_proj"})
    assert result["asset"].get("uri")
    assert result["job"].get("status") in (
        JobStatus.SUCCEEDED, JobStatus.CACHE_HIT, "succeeded", "cache_hit",
    )


def test_usage_tracker_records_events(tmp_path):
    from services.asset_generation.usage import UsageTracker

    tracker = UsageTracker(directory=str(tmp_path))
    job = {
        "job_id": "j1",
        "asset_id": "a1",
        "asset_type": "scene_image",
        "asset_class": "image",
        "provider": "mock_generation",
        "status": "succeeded",
        "cache_hit": False,
        "cost_estimate": 0.0,
        "latency_ms": 12,
        "created_at": "2026-01-01T00:00:00+00:00",
    }
    event = tracker.record(job, project_id="p1")
    assert event["event_id"]
    summary = tracker.summary(project_id="p1")
    assert summary["events"] == 1
    assert summary["by_provider"]["mock_generation"] == 1


def test_catalog_covers_phase2_media_types():
    ids = asset_type_ids()
    assert "sound_effect" in ids
    assert "music_bed" in ids
    assert "voice_clip" in ids
    assert "motion_graphic" in ids
    assert "character_animation" in ids
    assert resolve_asset_type("sound_effect")["asset_class"] == "audio"


def test_retry_increments_attempts_on_provider_failure():
    class FlakyThenOk(GenerationProvider):
        name = "flaky_then_ok"
        label = "Flaky"
        asset_classes = ("image",)
        profile = {
            "quality": 99, "cost_per_asset": 0.01, "speed": 99,
            "consistency": 99, "latency_ms": 100,
        }
        calls = 0

        def is_available(self):
            return True

        def generate(self, prompt_spec, request):
            FlakyThenOk.calls += 1
            if FlakyThenOk.calls < 2:
                return {"error": "transient", "provider": self.name}
            return {
                "uri": "mock://flaky/ok.png",
                "provider": self.name,
                "model": "flaky-v1",
                "format": "png",
                "width": 1080,
                "height": 1920,
                "placeholder": False,
            }

    FlakyThenOk.calls = 0
    register_generation_provider(FlakyThenOk())
    configure(
        provider_priority={"image": ["flaky_then_ok"]},
        max_retries=3,
        allow_placeholders=False,
    )
    try:
        from services.asset_generation.generator import generate_asset

        request = {
            "asset_id": "retry_1",
            "project_id": "retry_proj",
            "asset_type": "scene_image",
            "asset_class": "image",
            "prompt": "unique retry prompt xyz",
            "style": "minimal",
            "priority": "required",
            "aspect_ratio": "9:16",
            "resolution": "1080x1920",
        }
        asset, job = generate_asset(request, {})
        assert asset["provider"] == "flaky_then_ok"
        assert job["attempts"] >= 2
        assert job["status"] == JobStatus.SUCCEEDED
    finally:
        unregister_generation_provider("flaky_then_ok")
        reset_asset_generation_config()
