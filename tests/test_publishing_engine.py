"""Tests for the Publishing & Distribution Engine (Agent 7).

Covers: provider adapters + registry, publishing package generation, queue
creation and job lifecycle, scheduler (immediate / explicit / optimal
windows, timezone-aware), retry manager (backoff + provider overrides +
safe failure), account placeholders, extension seams, and orchestrator
integration. All tests run in Demo Mode — mock providers, no API keys.
"""

from datetime import datetime, timedelta, timezone

import pytest

import engines  # noqa: F401 - importing registers all engines
from engines import registry
from engines.contracts import ContractEngine
from engines.publishing import PublishingEngine, SchedulerEngine, publish_content
from providers.publishing import (
    MockPublishingProvider,
    get_publishing_provider,
    publishing_provider_keys,
    register_publishing_provider,
    resolve_platform_key,
)
from services.orchestrator import Orchestrator, StageStatus
from services.publishing import (
    DEFAULT_RETRY_POLICY,
    JobStatus,
    PLATFORM_PUBLISH_PACKAGE_FIELDS,
    PUBLISH_ATTEMPT_FIELDS,
    PUBLISH_SCHEDULE_ENTRY_FIELDS,
    PUBLISHING_ACCOUNT_FIELDS,
    PUBLISHING_JOB_FIELDS,
    PUBLISHING_RESULT_FIELDS,
    PublishingHistory,
    PublishingManager,
    PublishingQueue,
    PublishingScheduler,
    RetryManager,
    build_platform_publish_package,
    build_publishing_account,
    build_publishing_job,
    next_window_occurrence,
    register_publish_listener,
    register_pre_publish_gate,
    unregister_publish_listener,
    unregister_pre_publish_gate,
)
from services.publishing.extensions import PrePublishGate, PublishListener

SUPPORTED_PLATFORMS = (
    "youtube_shorts", "instagram_reels", "facebook_reels",
    "tiktok", "x", "linkedin", "pinterest",
)


def make_item(**overrides) -> dict:
    item = {
        "title": "Black Hole Facts",
        "project_id": "proj_test_1",
        "target_platforms": ["youtube_shorts", "tiktok"],
        "seo_package": {
            "title": "Black Hole Facts",
            "description": "Amazing facts about black holes.",
            "keywords": ["black holes", "space"],
            "hashtags": ["#space", "#blackholes"],
            "seo_score": 80,
        },
        "render_package": {
            "file_uri": "mock://renders/out.mp4",
            "mock_output_path": "mock://renders/out.mp4",
            "duration_sec": 42.0,
            "resolution": "1080x1920",
            "aspect_ratio": "9:16",
            "mock": True,
            "production_readiness_score": 88,
            "render_manifest": {"ready_for_publishing": True},
            "caption_render_plan": {"segments": [{"text": "hook", "start_sec": 0}]},
        },
    }
    item.update(overrides)
    return item


def make_optimization(**overrides) -> dict:
    optimization = {
        "package_version": "1.0",
        "project_id": "proj_test_1",
        "title": "The Truth About Black Holes",
        "description": "Everything you need to know.",
        "keywords": ["black holes", "event horizon"],
        "hashtags": {"youtube": [{"tag": "#BlackHoles", "rank": 1}, {"tag": "#Space", "rank": 2}]},
        "thumbnail": {"concept_id": "t1", "archetype": "curiosity"},
        "publish_windows": [
            {"platform": "youtube", "country": "US", "language": "en",
             "day": "friday", "start_hour_local": 17, "end_hour_local": 20,
             "score": 90, "rank": 1},
        ],
        "platforms": ["youtube_shorts", "tiktok"],
        "language": "en",
        "country": "US",
        "status": "optimized",
    }
    optimization.update(overrides)
    return optimization


@pytest.fixture()
def manager(tmp_path):
    """A PublishingManager isolated on a temp queue directory."""
    directory = str(tmp_path / "publishing_queue")
    return PublishingManager(
        queue=PublishingQueue(directory=directory),
        history=PublishingHistory(directory=directory),
    )


# --------------------------------------------------------- provider adapters


def test_all_supported_platforms_have_registered_providers():
    for platform in SUPPORTED_PLATFORMS:
        provider = get_publishing_provider(platform)
        assert provider is not None, platform
        assert provider.key == platform
        assert provider.is_available()


def test_platform_aliases_resolve_to_canonical_providers():
    assert resolve_platform_key("youtube") == "youtube_shorts"
    assert resolve_platform_key("instagram") == "instagram_reels"
    assert resolve_platform_key("facebook") == "facebook_reels"
    assert resolve_platform_key("twitter") == "x"
    assert get_publishing_provider("youtube").key == "youtube_shorts"


def test_provider_constraints_and_mock_publish():
    for platform in SUPPORTED_PLATFORMS:
        provider = get_publishing_provider(platform)
        limits = provider.constraints()
        for key in ("max_title_chars", "max_description_chars", "max_hashtags", "max_duration_sec"):
            assert limits[key] > 0, (platform, key)
        result = provider.publish({"title": "T"})
        assert result["status"] == "published"
        assert result["post_id"] and result["post_url"]
        assert result["mock"] is True


def test_provider_formats_metadata_to_platform_limits():
    provider = get_publishing_provider("x")  # tightest description limit
    formatted = provider.format_metadata({
        "title": "T" * 500,
        "description": "D" * 500,
        "hashtags": [f"#tag{i}" for i in range(50)],
    })
    limits = provider.constraints()
    assert len(formatted["title"]) <= limits["max_title_chars"]
    assert len(formatted["description"]) <= limits["max_description_chars"]
    assert len(formatted["hashtags"]) == limits["max_hashtags"]
    assert len(formatted["format_warnings"]) == 3


def test_future_provider_registers_without_engine_changes():
    class MastodonProvider(MockPublishingProvider):
        key = "mastodon"
        label = "Mastodon"

    register_publishing_provider(MastodonProvider())
    assert "mastodon" in publishing_provider_keys()
    assert get_publishing_provider("mastodon").label == "Mastodon"


# --------------------------------------------- publishing package generation


def test_publishing_package_generation_is_standardized():
    provider = get_publishing_provider("youtube_shorts")
    scheduler = PublishingScheduler()
    optimization = make_optimization()
    schedule = scheduler.schedule(optimization, "youtube_shorts", mode="scheduled")
    package = build_platform_publish_package(make_item(), optimization, provider, schedule)

    for field in PLATFORM_PUBLISH_PACKAGE_FIELDS:
        assert field in package, field
    assert package["package_version"] == "1.0"
    assert package["video"]["file_uri"] == "mock://renders/out.mp4"
    assert package["title"] == "The Truth About Black Holes"
    assert package["hashtags"] == ["#BlackHoles", "#Space"]
    assert package["platform"] == "youtube_shorts"
    assert package["publish_time"] == schedule["publish_time"]
    assert package["timezone"] == "UTC-05:00"
    assert package["playlist"]["placeholder"] is True
    assert package["category"]["placeholder"] is True
    assert package["status"] == "prepared"
    assert package["diagnostics"]["ready_for_publishing"] is True


def test_package_degrades_gracefully_without_optimization():
    provider = get_publishing_provider("tiktok")
    schedule = PublishingScheduler().schedule({}, "tiktok", mode="immediate")
    package = build_platform_publish_package(make_item(), {}, provider, schedule)
    # Falls back to the base seo_package metadata.
    assert package["title"] == "Black Hole Facts"
    assert package["hashtags"] == ["#space", "#blackholes"]
    assert package["diagnostics"]["optimization_status"] == "missing"


def test_provider_validation_blocks_bad_packages():
    provider = get_publishing_provider("youtube_shorts")
    schedule = PublishingScheduler().schedule({}, "youtube_shorts", mode="immediate")
    item = make_item()
    item["render_package"]["duration_sec"] = 999.0
    item["seo_package"]["title"] = ""
    item["title"] = ""
    package = build_platform_publish_package(item, {}, provider, schedule)
    assert package["status"] == "blocked"
    assert "missing title" in package["diagnostics"]["provider_problems"]
    assert any("exceeds" in p for p in package["diagnostics"]["provider_problems"])


# ------------------------------------------------------------------ scheduler


def test_scheduler_immediate_mode_publishes_now():
    now = datetime(2026, 7, 8, 12, 0, tzinfo=timezone.utc)
    entry = PublishingScheduler(now=now).schedule(make_optimization(), "youtube_shorts", mode="immediate")
    for field in PUBLISH_SCHEDULE_ENTRY_FIELDS:
        assert field in entry, field
    assert entry["mode"] == "immediate"
    assert entry["publish_time"] == now.isoformat()


def test_scheduler_uses_optimal_window_timezone_aware():
    now = datetime(2026, 7, 8, 12, 0, tzinfo=timezone.utc)  # a Wednesday
    entry = PublishingScheduler(now=now).schedule(make_optimization(), "youtube_shorts")
    assert entry["mode"] == "scheduled"
    assert entry["window"]["day"] == "friday"
    assert entry["timezone"] == "UTC-05:00"
    slot = datetime.fromisoformat(entry["publish_time"])
    assert slot > now
    # Friday 17:00 local (UTC-5) == 22:00 UTC.
    assert slot.hour == 22
    local = datetime.fromisoformat(entry["local_time"])
    assert local.hour == 17


def test_scheduler_explicit_publish_time_is_honored():
    explicit = "2026-12-01T09:30:00+00:00"
    entry = PublishingScheduler().schedule(make_optimization(), "tiktok", publish_time=explicit)
    assert entry["publish_time"] == explicit


def test_scheduler_supports_multiple_countries():
    now = datetime(2026, 7, 8, 12, 0, tzinfo=timezone.utc)
    scheduler = PublishingScheduler(now=now)
    japan = scheduler.schedule(make_optimization(country="JP", publish_windows=[]), "tiktok")
    brazil = scheduler.schedule(make_optimization(country="BR", publish_windows=[]), "tiktok")
    assert japan["timezone"] == "UTC+09:00"
    assert brazil["timezone"] == "UTC-03:00"
    assert japan["publish_time"] != brazil["publish_time"]


def test_next_window_occurrence_lands_inside_window():
    window = {"platform": "youtube", "country": "GB", "day": "monday",
              "start_hour_local": 17, "end_hour_local": 20}
    now = datetime(2026, 7, 8, 12, 0, tzinfo=timezone.utc)
    slot = next_window_occurrence(window, now=now)
    assert slot > now
    assert slot.weekday() == 0        # Monday
    assert slot.hour == 17            # GB is UTC+0


def test_scheduler_engine_emits_publish_schedule():
    engine = registry.get_engine("scheduler")
    assert isinstance(engine, ContractEngine)
    assert isinstance(engine, SchedulerEngine)
    assert engine.is_ready() is True
    assert engine.output_contract == ["publish_schedule"]

    context = {
        "ideas": [make_item()],
        "publishing_packages": [make_optimization()],
    }
    updates = engine.run(context)
    schedule = updates["publish_schedule"]
    assert len(schedule) == 2  # youtube_shorts + tiktok
    for entry in schedule:
        for field in PUBLISH_SCHEDULE_ENTRY_FIELDS:
            assert field in entry, field


# -------------------------------------------------------------- retry manager


def test_retry_manager_exponential_backoff():
    retry = RetryManager()
    policy = dict(DEFAULT_RETRY_POLICY)
    assert retry.delay_sec(1, policy) == policy["base_delay_sec"]
    assert retry.delay_sec(2, policy) == policy["base_delay_sec"] * 2
    assert retry.delay_sec(3, policy) == policy["base_delay_sec"] * 4
    assert retry.delay_sec(99, policy) == policy["max_delay_sec"]


def test_retry_manager_provider_specific_policy():
    retry = RetryManager()
    tiktok_policy = retry.policy_for(get_publishing_provider("tiktok"))
    assert tiktok_policy["max_retries"] == 4
    assert tiktok_policy["base_delay_sec"] == 120
    default_policy = retry.policy_for(get_publishing_provider("pinterest"))
    assert default_policy == DEFAULT_RETRY_POLICY


def test_retry_manager_requeues_then_fails_safely():
    retry = RetryManager(policy={"max_retries": 2, "base_delay_sec": 1})
    job = build_publishing_job(
        {"project_id": "p"}, platform="x", provider="mock",
        scheduled_time="2026-01-01T00:00:00+00:00", max_retries=2,
    )
    job = retry.record_failure(job, "rate limited")
    assert job["status"] == JobStatus.QUEUED
    assert job["attempts"] == 1
    assert job["next_retry_at"]

    job = retry.record_failure(job, "rate limited again")
    assert job["status"] == JobStatus.FAILED       # retries exhausted — safe failure
    assert job["attempts"] == 2
    assert job["last_error"] == "rate limited again"
    assert job["next_retry_at"] == ""


# --------------------------------------------------- queue and job lifecycle


def test_queue_creation_persists_jobs(tmp_path):
    queue = PublishingQueue(directory=str(tmp_path / "q"))
    job = build_publishing_job(
        {"project_id": "p1"}, platform="tiktok", provider="mock",
        scheduled_time="2026-01-01T00:00:00+00:00",
    )
    queue.enqueue(job)
    for field in PUBLISHING_JOB_FIELDS:
        assert field in job, field
    assert queue.count() == 1
    assert queue.get(job["job_id"])["platform"] == "tiktok"
    # A fresh queue over the same directory sees the persisted job.
    assert PublishingQueue(directory=str(tmp_path / "q")).count() == 1


def test_job_lifecycle_queued_to_published(manager):
    jobs, warnings = manager.prepare_jobs(make_item(), make_optimization(), mode="immediate")
    assert not warnings
    assert len(jobs) == 2
    assert all(job["status"] == JobStatus.QUEUED for job in jobs)

    executed = manager.execute_due_jobs()
    assert len(executed) == 2
    for job in executed:
        assert job["status"] == JobStatus.PUBLISHED
        assert job["attempts"] == 1
        attempt = job["history"][-1]
        for field in PUBLISH_ATTEMPT_FIELDS:
            assert field in attempt, field
        assert attempt["post_id"] and attempt["post_url"]
        assert attempt["duration_ms"] >= 0
        assert attempt["analytics_ref"] == job["analytics_ref"]
    assert len(manager.history.all()) == 2


def test_scheduled_jobs_wait_until_due(manager):
    jobs, _ = manager.prepare_jobs(make_item(), make_optimization(), mode="scheduled")
    assert all(job["status"] == JobStatus.SCHEDULED for job in jobs)
    assert manager.execute_due_jobs() == []       # windows are in the future
    future = (datetime.now(timezone.utc) + timedelta(days=14)).isoformat()
    executed = manager.execute_due_jobs(now=future)
    assert len(executed) == 2
    assert all(job["status"] == JobStatus.PUBLISHED for job in executed)


def test_job_can_be_cancelled(manager):
    jobs, _ = manager.prepare_jobs(make_item(), make_optimization(), mode="scheduled")
    cancelled = manager.queue.cancel(jobs[0]["job_id"])
    assert cancelled["status"] == JobStatus.CANCELLED
    # Terminal jobs cannot be cancelled twice and are never due.
    assert manager.queue.cancel(jobs[0]["job_id"]) is None
    future = (datetime.now(timezone.utc) + timedelta(days=14)).isoformat()
    assert all(j["job_id"] != jobs[0]["job_id"] for j in manager.queue.due_jobs(now=future))


def test_failed_publish_is_retried_and_history_logged(manager):
    class FlakyProvider(MockPublishingProvider):
        key = "flaky_platform"
        label = "Flaky"
        calls = 0

        def publish(self, package):
            type(self).calls += 1
            if type(self).calls == 1:
                return {"status": "failed", "error": "HTTP 503", "post_id": "",
                        "post_url": "", "published_at": ""}
            return super().publish(package)

    register_publishing_provider(FlakyProvider())
    item = make_item(target_platforms=["flaky_platform"])
    jobs, _ = manager.prepare_jobs(item, {}, mode="immediate")
    job = manager.execute_job(jobs[0])
    assert job["status"] == JobStatus.QUEUED      # failure → requeued for retry
    assert job["last_error"] == "HTTP 503"
    assert job["next_retry_at"]

    job["next_retry_at"] = datetime.now(timezone.utc).isoformat()
    manager.queue.update(job)
    job = manager.execute_due_jobs()[0]
    assert job["status"] == JobStatus.PUBLISHED
    history = manager.history.for_job(job["job_id"])
    assert [entry["status"] for entry in history] == ["failed", "published"]


# ---------------------------------------------------- accounts and extensions


def test_publishing_account_is_placeholder_only():
    account = build_publishing_account("brand-1", "chan-1", "youtube_shorts", handle="@demo")
    for field in PUBLISHING_ACCOUNT_FIELDS:
        assert field in account, field
    assert account["credentials"]["placeholder"] is True
    assert account["permissions"]["placeholder"] is True
    assert account["token"]["placeholder"] is True
    assert account["status"] == "unlinked"


def test_pre_publish_gate_blocks_and_listener_receives_attempts(manager):
    class BlockEverything(PrePublishGate):
        key = "block_all"

        def review(self, job):
            return ["human review required"]

    class Recorder(PublishListener):
        key = "recorder"

        def __init__(self):
            self.attempts = []

        def on_publish_attempt(self, job, attempt):
            self.attempts.append(attempt)

    gate, listener = BlockEverything(), Recorder()
    register_pre_publish_gate(gate)
    try:
        jobs, _ = manager.prepare_jobs(make_item(), make_optimization(), mode="immediate")
        job = manager.execute_job(jobs[0])
        assert job["status"] == JobStatus.CANCELLED
        assert "human review required" in job["last_error"]
    finally:
        unregister_pre_publish_gate(gate)

    register_publish_listener(listener)
    try:
        job = manager.execute_job(jobs[1])
        assert job["status"] == JobStatus.PUBLISHED
        assert listener.attempts and listener.attempts[0]["analytics_ref"]
    finally:
        unregister_publish_listener(listener)


# ------------------------------------------------------ engine + orchestrator


def test_publishing_engine_registered_with_contracts():
    engine = registry.get_engine("publishing")
    assert isinstance(engine, ContractEngine)
    assert isinstance(engine, PublishingEngine)
    assert engine.is_ready() is True
    assert engine.input_contract == ["publishing_packages"]
    assert engine.output_contract == ["publishing_result"]
    assert "seo_optimization" in engine.dependencies
    assert engine.validate_output(engine.run({})) == []


def test_publish_content_returns_standardized_publishing_result():
    context = {
        "ideas": [make_item()],
        "publishing_packages": [make_optimization()],
        "publish_mode": "immediate",
    }
    updates = publish_content(context)
    result = updates["publishing_result"]
    for field in PUBLISHING_RESULT_FIELDS:
        assert field in result, field
    assert result["status"] == "SUCCESS"
    assert result["items"] == 1
    assert result["jobs_created"] == 2
    assert result["published"] == 2
    assert result["platforms"] == ["tiktok", "youtube_shorts"]
    # The item's ContentPackage slot is populated and status advanced.
    item = context["ideas"][0]
    assert item["publishing_package"]["status"] == "published"
    assert item["status"] == "published"
    assert item["publishing_package"]["jobs"][0]["post_url"]


def test_publish_content_skips_safely_with_no_items():
    updates = publish_content({})
    assert updates["publishing_result"]["status"] == "SKIPPED"
    assert updates["publishing_result"]["jobs_created"] == 0


def test_unsupported_platform_warns_instead_of_failing():
    context = {
        "ideas": [make_item(target_platforms=["myspace", "youtube_shorts"])],
        "publish_mode": "immediate",
    }
    result = publish_content(context)["publishing_result"]
    assert result["status"] == "WARNING"
    assert result["published"] == 1
    assert any("myspace" in warning for warning in result["warnings"])


def test_orchestrator_publish_stage_runs_scheduler_then_publishing():
    context = {
        "command": "test",
        "ideas": [make_item()],
        "publishing_packages": [make_optimization()],
        "publish_mode": "immediate",
    }
    report = Orchestrator().run_publish_stage(context)
    assert report.status == StageStatus.SUCCESS
    assert not report.errors
    engines_run = [step["engine"] for step in report.diagnostics["steps"]]
    assert engines_run == ["scheduler", "publishing"]
    assert context["publish_schedule"]
    assert context["publishing_result"]["published"] == 2


def test_full_seo_to_publish_handover():
    """Render package + SEO optimization → publish, via real Agent 8 output."""
    context = {
        "command": "test",
        "ideas": [make_item()],
        "seo_keywords": ["black holes"],
        "publish_mode": "immediate",
    }
    orch = Orchestrator()
    assert orch.run_seo_stage(context).status == StageStatus.SUCCESS
    assert context["publishing_packages"]
    report = orch.run_publish_stage(context)
    assert report.status == StageStatus.SUCCESS
    result = context["publishing_result"]
    assert result["published"] == result["jobs_created"] == 2
    assert context["ideas"][0]["publishing_package"]["status"] == "published"
