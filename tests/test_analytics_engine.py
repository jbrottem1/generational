"""Tests for the Analytics Engine (Agent 9, key: analytics).

Proves: the engine satisfies the shared contract, every published piece of
content generates one structured analytics record per platform, records
carry full attribution back to upstream decisions, metrics come through
the AnalyticsProvider interface deterministically, the store is
append-only and deduplicated, the publish listener measures out-of-band
publishes, and the orchestrator stage runs safely with and without input.
"""

from __future__ import annotations

import pytest

import engines  # noqa: F401 - importing registers all engines
from engines import registry
from engines.contracts import ContractEngine
from providers.analytics import MockAnalyticsProvider, get_analytics_provider
from services.analytics import (
    ANALYTICS_METRIC_FIELDS,
    ANALYTICS_PACKAGE_FIELDS,
    ANALYTICS_RECORD_FIELDS,
    AnalyticsStore,
    MetricsStatus,
    attach_experiment,
    performance_score,
)
from services.analytics.integration import AnalyticsPublishListener
from services.orchestrator import Orchestrator, StageStatus


@pytest.fixture
def analytics_dir(tmp_path, monkeypatch):
    """Function-scoped isolation of the whole Agent 9 persistence layer."""
    import services.analytics.store as analytics_store

    directory = str(tmp_path / "analytics")
    monkeypatch.setattr(analytics_store, "_DEFAULT_DIR", directory)
    return directory


def make_item(project_id="proj1", platform="youtube_shorts", published=True, hook=""):
    """One canonical ContentPackage-style dict with a publish job."""
    status = "published" if published else "scheduled"
    return {
        "project_id": project_id,
        "title": "Ocean Mystery",
        "hook": hook or "What if the ocean disappeared tomorrow?",
        "topic": "deep sea creatures",
        "niche": "science",
        "keywords": ["ocean", "science"],
        "psychology_score": 82,
        "virality_score": 74,
        "attention_score": 68,
        "quality_score": 80,
        "publish_ready": True,
        "psychology": {"triggers": ["curiosity", "awe"]},
        "script_package": {"script": "Imagine the ocean gone...", "script_score": 78},
        "audio_package": {"voice_style": {"name": "narrator"}, "pacing": {"wpm": 150}},
        "seo_package": {"title": "Ocean Mystery", "recommended_title": "The Ocean Mystery Nobody Talks About"},
        "render_package": {"render_package_version": "2.0", "duration_sec": 42.0},
        "publishing_package": {
            "engine_version": "1.0.0",
            "status": status,
            "jobs": [
                {
                    "job_id": f"pub_{project_id}",
                    "platform": platform,
                    "provider": "base",
                    "status": status,
                    "scheduled_time": "2026-07-08T17:00:00+00:00",
                    "timezone": "UTC-05:00",
                    "post_id": f"post_{project_id}" if published else "",
                    "post_url": f"mock://posts/{platform}/post_{project_id}" if published else "",
                    "published_at": "2026-07-08T17:00:01+00:00" if published else "",
                    "analytics_ref": f"an_pub_{project_id}_{platform}",
                }
            ],
        },
    }


# ----------------------------------------------------------------- contract


def test_analytics_engine_is_a_live_contract_engine():
    engine = registry.get_engine("analytics")
    assert isinstance(engine, ContractEngine)
    assert engine.is_ready() is True
    diag = engine.diagnostics()
    assert diag["engine_id"] == "analytics"
    assert diag["version"] == "1.0.0"
    assert "unified_packages" in diag["input_contract"]
    assert "analytics_summary" in diag["output_contract"]
    assert "publishing" in diag["dependencies"]


# ------------------------------------------------------------------ records


def test_every_published_item_generates_a_full_analytics_record(analytics_dir):
    context = {"unified_packages": [make_item("p1"), make_item("p2", platform="tiktok")]}
    updates = registry.get_engine("analytics").run(context)

    records = updates["analytics_records"]
    assert len(records) == 2
    for record in records:
        for field in ANALYTICS_RECORD_FIELDS:
            assert field in record, field
        for metric in ANALYTICS_METRIC_FIELDS:
            assert metric in record["metrics"], metric
        assert record["metrics_status"] == MetricsStatus.COLLECTED
        assert record["metrics_source"] == "mock"
        assert record["analytics_ref"].startswith("an_pub_")


def test_records_carry_attribution_back_to_upstream_decisions(analytics_dir):
    context = {"unified_packages": [make_item("p1")]}
    record = registry.get_engine("analytics").run(context)["analytics_records"][0]

    assert record["hook"] == "What if the ocean disappeared tomorrow?"
    assert record["title"] == "The Ocean Mystery Nobody Talks About"
    assert record["topic"] == "deep sea creatures"
    assert record["psychology_strategy"] == ["curiosity", "awe"]
    assert record["psychology_score"] == 82
    assert record["script_version"]          # stable fingerprints, non-empty
    assert record["voice_version"]
    assert record["render_version"] == "2.0"
    assert record["video_length_sec"] == 42.0
    assert record["posting_time"] == "2026-07-08T17:00:00+00:00"
    assert record["platform"] == "youtube_shorts"


def test_analytics_package_slot_is_written_per_item(analytics_dir):
    item = make_item("p1")
    registry.get_engine("analytics").run({"unified_packages": [item]})

    package = item["analytics_package"]
    for field in ANALYTICS_PACKAGE_FIELDS:
        assert field in package, field
    assert package["status"] == "collected"
    assert package["performance_score"] > 0
    assert package["metrics"]["views"] > 0


def test_scheduled_but_unpublished_content_yields_pending_records(analytics_dir):
    item = make_item("p1", published=False)
    updates = registry.get_engine("analytics").run({"unified_packages": [item]})

    record = updates["analytics_records"][0]
    assert record["metrics_status"] == MetricsStatus.PENDING
    assert record["metrics"]["views"] == 0
    assert item["analytics_package"]["status"] == "pending"
    # Pending records are not persisted — the store holds real outcomes only.
    assert updates["analytics_summary"]["persisted"] == 0


def test_empty_context_reports_no_items_never_fails(analytics_dir):
    updates = registry.get_engine("analytics").run({"command": "probe"})
    assert updates["analytics_summary"]["status"] == "no_items"
    assert updates["analytics_summary"]["items"] == 0
    assert updates["analytics_records"] == []


def test_experiment_linkage_flows_into_records(analytics_dir):
    item = attach_experiment(make_item("p1"), "exp_123", "var_a")
    record = registry.get_engine("analytics").run({"unified_packages": [item]})["analytics_records"][0]
    assert record["experiment_id"] == "exp_123"
    assert record["variant_id"] == "var_a"


# ---------------------------------------------------------------- providers


def test_mock_provider_is_deterministic_per_content_and_platform():
    provider = MockAnalyticsProvider()
    first = provider.fetch_metrics("post_abc", "tiktok")
    second = provider.fetch_metrics("post_abc", "tiktok")
    other = provider.fetch_metrics("post_abc", "youtube_shorts")
    assert first == second
    assert first != other
    assert first["mock"] is True
    assert 35 <= first["audience_retention"] <= 90


def test_provider_registry_swaps_real_adapters_per_platform():
    from providers.analytics import register_analytics_provider
    from providers.analytics_provider import AnalyticsProvider

    class FakeYouTube(AnalyticsProvider):
        name = "youtube_api"

        def is_available(self):
            return True

        def fetch_metrics(self, content_id, platform):
            return {"views": 1}

    register_analytics_provider("youtube_shorts", FakeYouTube())
    try:
        assert get_analytics_provider("youtube_shorts").name == "youtube_api"
        assert get_analytics_provider("tiktok").name == "mock"
    finally:
        from providers.analytics import _providers

        _providers.pop("youtube_shorts", None)


# -------------------------------------------------------------------- store


def test_store_is_append_only_and_deduplicates_on_ref(analytics_dir):
    engine = registry.get_engine("analytics")
    context = {"unified_packages": [make_item("p1")]}

    first = engine.run(dict(context))
    assert first["analytics_summary"]["persisted"] == 1
    assert first["analytics_summary"]["store_size"] == 1

    # Re-measuring the same published content never duplicates history.
    second = engine.run({"unified_packages": [make_item("p1")]})
    assert second["analytics_summary"]["persisted"] == 0
    assert second["analytics_summary"]["store_size"] == 1


def test_store_filters_and_lookup(tmp_path):
    store = AnalyticsStore(directory=str(tmp_path / "a"))
    store.add_record({"record_id": "r1", "analytics_ref": "an_1", "platform": "tiktok",
                      "metrics_status": "collected", "collected_at": "2026-07-01T00:00:00+00:00"})
    store.add_record({"record_id": "r2", "analytics_ref": "an_2", "platform": "youtube_shorts",
                      "metrics_status": "collected", "collected_at": "2026-07-09T00:00:00+00:00"})

    assert store.record_count() == 2
    assert [r["record_id"] for r in store.list_records()] == ["r2", "r1"]  # newest first
    assert [r["record_id"] for r in store.list_records(platform="tiktok")] == ["r1"]
    assert [r["record_id"] for r in store.list_records(since="2026-07-05")] == ["r2"]
    assert store.find_by_ref("an_1")["record_id"] == "r1"
    assert store.find_by_ref("an_missing") is None


def test_performance_metrics_mirror_into_knowledge_base(analytics_dir):
    from services.knowledge import CATEGORY, get_knowledge_base

    before = get_knowledge_base().count(CATEGORY.PERFORMANCE)
    registry.get_engine("analytics").run({"unified_packages": [make_item("kb1")]})
    entries = get_knowledge_base().list_entries(CATEGORY.PERFORMANCE)
    assert len(entries) == before + 1
    assert entries[0]["content"]["topic"] == "deep sea creatures"
    assert entries[0]["metadata"]["source"] == "analytics"


# ---------------------------------------------------------- publish listener


def test_publish_listener_measures_out_of_band_publishes(analytics_dir):
    listener = AnalyticsPublishListener()
    job = {
        "job_id": "pub_x", "analytics_ref": "an_pub_x", "project_id": "px",
        "platform": "tiktok", "scheduled_time": "2026-07-08T12:00:00+00:00",
        "package": {"title": "Queued video", "keywords": ["k"],
                    "video": {"duration_sec": 30}},
    }
    attempt = {"status": "published", "post_id": "post_x", "post_url": "mock://x",
               "published_at": "2026-07-08T12:00:01+00:00"}

    listener.on_publish_attempt(job, attempt)
    store = AnalyticsStore(directory=analytics_dir)
    record = store.find_by_ref("an_pub_x")
    assert record is not None
    assert record["title"] == "Queued video"
    assert record["metrics"]["views"] > 0

    # Duplicate attempts and non-published attempts add nothing.
    listener.on_publish_attempt(job, attempt)
    listener.on_publish_attempt({**job, "analytics_ref": "an_other"}, {"status": "failed"})
    assert store.record_count() == 1


# ------------------------------------------------------------- orchestrator


def test_analytics_stage_runs_through_orchestrator(analytics_dir):
    context = {"command": "probe", "unified_packages": [make_item("p1")]}
    report = Orchestrator().run_analytics_stage(context)
    assert report.status == StageStatus.SUCCESS
    assert not report.errors
    assert context["analytics_summary"]["collected"] == 1
    assert context["unified_packages"][0]["analytics_package"]["status"] == "collected"


def test_performance_score_is_bounded_and_monotonic():
    weak = {"views": 100, "audience_retention": 20, "ctr": 1,
            "likes": 1, "comments": 0, "shares": 0, "saves": 0}
    strong = {"views": 90_000, "audience_retention": 85, "ctr": 12,
              "likes": 5000, "comments": 900, "shares": 1200, "saves": 700}
    assert 0 <= performance_score(weak) < performance_score(strong) <= 100
    assert performance_score({}) == 0
