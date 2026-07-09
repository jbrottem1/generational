"""Tests for the Optimization Laboratory (Agent 13, key: optimization_lab).

Proves: variant generation produces unique, versioned, attributed
variants for every experiment type; the configurable scoring engine
blends fourteen weighted inputs; ranking is deterministic and history-
aware; experiments create/schedule/run/conclude with statistical
confidence under concurrency limits; recommendations are structured,
conflict-free, and low-confidence-flagged; the learning loop feeds
historical winners back into future rankings; the pipeline integration
runs orchestrator-only; and every failure mode degrades gracefully.
"""

from __future__ import annotations

import pytest

import engines  # noqa: F401 - importing registers all engines
from engines import registry
from engines.contracts import ContractEngine
from services.optimization import (
    EXPERIMENT_MODES,
    EXPERIMENT_TYPES,
    LAB_EXPERIMENT_FIELDS,
    OPTIMIZATION_PACKAGE_FIELDS,
    OPTIMIZATION_RECOMMENDATION_FIELDS,
    OPTIMIZATION_REPORT_FIELDS,
    SCORING_INPUTS,
    VARIANT_FIELDS,
    ExperimentHistory,
    ExperimentManager,
    ExperimentStatus,
    MockExperimentProvider,
    OptimizationConfig,
    all_experiment_types,
    best_content_package,
    build_recommendation,
    configure,
    dedupe_variants,
    experiment_winner_priors,
    find_duplicates,
    generate_variants,
    get_experiment_provider,
    get_optimization_config,
    get_optimization_lab,
    get_prediction_model,
    make_variant,
    rank_variants,
    register_prediction_model,
    render_report_text,
    reset_optimization_config,
    resolve_conflicts,
    run_optimization,
    score_variant,
    validate_variant_group,
)
from services.optimization.predictions import PredictionModel
from services.orchestrator import StageStatus, get_orchestrator
from services.orchestrator.stages import STAGE_GROUPS


@pytest.fixture(autouse=True)
def fresh_config():
    """Every test starts from default configuration."""
    reset_optimization_config()
    yield
    reset_optimization_config()


@pytest.fixture
def lab_dir(tmp_path, monkeypatch):
    """Function-scoped isolation of the laboratory's experiment store."""
    import services.optimization.experiments as lab_experiments

    directory = str(tmp_path / "optimization")
    monkeypatch.setattr(lab_experiments, "_DEFAULT_DIR", directory)
    return directory


def sample_item(**overrides):
    item = {
        "hook": "the deep ocean is stranger than space",
        "title": "Ocean secrets scientists can't explain",
        "topic": "oceans",
        "niche": "science",
        "keywords": ["ocean", "deep sea"],
        "psychology_score": 80,
        "virality_score": 74,
        "seo_score": 68,
        "trend_score": 62,
        "attention_score": 71,
        "target_platforms": ["youtube_shorts"],
        "project_id": "proj_1",
    }
    item.update(overrides)
    return item


# ----------------------------------------------------------------- contract


def test_optimization_lab_is_a_live_contract_engine():
    engine = registry.get_engine("optimization_lab")
    assert isinstance(engine, ContractEngine)
    assert engine.is_ready()
    assert engine.version == "1.0.0"
    assert "optimization_report" in engine.output_contract
    assert "optimization_recommendations" in engine.output_contract
    assert "quality" in engine.dependencies


def test_optimization_stage_is_registered():
    assert STAGE_GROUPS.get("optimization") == ["optimization_lab"]


# --------------------------------------------------------- variant generation


def test_variants_carry_id_version_metadata_source_confidence():
    group = generate_variants("hook", base_content="black holes bend time")
    for variant in group["variants"]:
        for field in VARIANT_FIELDS:
            assert field in variant, field
        assert variant["variant_id"].startswith("var_")
        assert variant["version"] == "1.0"
        assert variant["generation_source"] in ("control", "heuristic", "upstream")
        assert 0 <= variant["confidence"] <= 100
    ids = [v["variant_id"] for v in group["variants"]]
    assert len(ids) == len(set(ids)), "variant ids must be unique"


def test_variant_counts_follow_configuration():
    group = generate_variants("hook", base_content="topic", count=20)
    assert len(group["variants"]) == 20
    configure(variant_counts={"title": 15})
    assert len(generate_variants("title", base_content="topic")["variants"]) == 15
    # Caps apply even to absurd requests.
    configure(max_variants_per_type=10)
    assert len(generate_variants("hook", base_content="topic", count=500)["variants"]) <= 10


def test_every_experiment_type_generates_a_usable_group():
    for experiment_type in EXPERIMENT_TYPES:
        group = generate_variants(experiment_type, base_content="sleep science")
        assert len(group["variants"]) >= 2, experiment_type
        assert group["experiment_type"] == experiment_type


def test_upstream_variants_join_the_pool():
    upstream = [{"content": "Scientists hate this ocean fact", "label": "script_variant", "confidence": 77}]
    group = generate_variants("hook", base_content="ocean", upstream_variants=upstream)
    sources = {v["generation_source"] for v in group["variants"]}
    assert "upstream" in sources and "control" in sources


def test_unknown_experiment_type_rejected_until_registered():
    with pytest.raises(ValueError):
        generate_variants("hologram_style", base_content="x")
    configure(extra_experiment_types=["hologram_style"])
    assert "hologram_style" in all_experiment_types()
    group = generate_variants("hologram_style", base_content="")
    assert len(group["variants"]) >= 2  # future types still produce a testable pair


def test_duplicate_detection_and_dedupe():
    a = make_variant("hook", "the ocean is deeply strange")
    b = make_variant("hook", "the ocean is deeply strange")
    c = make_variant("hook", "volcanoes under the ice")
    assert find_duplicates([a, b, c], threshold=0.9) == [(a["variant_id"], b["variant_id"])]
    assert [v["variant_id"] for v in dedupe_variants([a, b, c], threshold=0.9)] == [
        a["variant_id"], c["variant_id"],
    ]


def test_validation_flags_duplicates_empty_and_undersized_groups():
    group = {"variants": [make_variant("hook", "same text"), make_variant("hook", "same text"),
                          make_variant("hook", "")]}
    problems = validate_variant_group(group)
    assert any("near-duplicate" in p for p in problems)
    assert any("empty content" in p for p in problems)
    assert validate_variant_group({"variants": [make_variant("hook", "only one")]})


# ------------------------------------------------------------------ scoring


def test_scoring_produces_full_breakdown_and_composite():
    variant = make_variant("hook", "Why nobody talks about the deep ocean?")
    scored = score_variant(variant, item=sample_item())
    assert 0 <= scored["score"] <= 100
    for dimension in SCORING_INPUTS:
        assert dimension in scored["score_breakdown"], dimension
        assert 0 <= scored["score_breakdown"][dimension] <= 100


def test_scoring_is_deterministic():
    item = sample_item()
    first = score_variant(make_variant("hook", "The secret behind sleep"), item=item)
    second = dict(first)
    second["score"] = 0
    assert score_variant(second, item=item)["score"] == first["score"]


def test_scoring_weights_are_configurable():
    item = sample_item()
    curiosity = make_variant("hook", "The secret nobody tells you about oceans?")
    plain = make_variant("hook", "some ordinary words about water and things and stuff")
    # All weight on CTR prediction: the curiosity hook must win big.
    ctr_only = {key: 0.0 for key in SCORING_INPUTS}
    ctr_only["ctr_prediction"] = 1.0
    configure(scoring_weights=ctr_only)
    assert score_variant(curiosity, item=item)["score"] > score_variant(plain, item=item)["score"]
    # All weight on generation confidence: the higher-confidence variant wins.
    conf_only = {key: 0.0 for key in SCORING_INPUTS}
    conf_only["confidence"] = 1.0
    configure(scoring_weights=conf_only)
    low = make_variant("hook", "identical words here", confidence=10)
    high = make_variant("hook", "different words there", confidence=95)
    assert score_variant(high, item=item)["score"] > score_variant(low, item=item)["score"]


def test_revenue_prediction_is_a_neutral_placeholder():
    scored = score_variant(make_variant("hook", "anything"), item=sample_item())
    assert scored["score_breakdown"]["revenue_prediction"] == 50


# ------------------------------------------------------------------ ranking


def test_ranking_orders_best_first_with_ranks():
    group = generate_variants("hook", base_content="the ocean", count=10)
    ranked = rank_variants(group["variants"], item=sample_item())
    scores = [v["score"] for v in ranked]
    assert scores == sorted(scores, reverse=True)
    assert [v["rank"] for v in ranked] == list(range(1, len(ranked) + 1))


def test_historical_priors_influence_ranking():
    item = sample_item()
    variants = [make_variant("hook", f"neutral filler statement number {i}", label=f"v{i}")
                for i in range(4)]
    baseline = rank_variants([dict(v) for v in variants], item=item)
    loser_label = baseline[-1]["label"]
    boosted = rank_variants(
        [dict(v) for v in variants], item=item,
        historical_priors={loser_label: 100},
    )
    baseline_rank = next(v["rank"] for v in baseline if v["label"] == loser_label)
    boosted_rank = next(v["rank"] for v in boosted if v["label"] == loser_label)
    assert boosted_rank < baseline_rank, "a strong historical prior must lift the variant"
    # With ranking history disabled AND the historical scoring weight
    # zeroed, priors stop mattering entirely.
    no_history_weights = dict(get_optimization_config().scoring_weights)
    no_history_weights["historical_performance"] = 0.0
    configure(ranking_strategy="score", history_influence=0.0,
              scoring_weights=no_history_weights)
    with_prior = rank_variants([dict(v) for v in variants], item=item,
                               historical_priors={loser_label: 100})
    without_prior = rank_variants([dict(v) for v in variants], item=item)
    assert [v["label"] for v in with_prior] == [v["label"] for v in without_prior]


# -------------------------------------------------------------- experiments


def test_experiment_lifecycle_create_run_conclude(lab_dir):
    manager = ExperimentManager()
    group = generate_variants("hook", base_content="the deep ocean", count=8)
    experiment = manager.create_experiment("hook", group, hypothesis="curiosity wins")
    for field in LAB_EXPERIMENT_FIELDS:
        assert field in experiment, field
    assert experiment["status"] == ExperimentStatus.DRAFT
    assert experiment["mode"] in EXPERIMENT_MODES

    concluded = manager.run_experiment(experiment["experiment_id"], item=sample_item())
    assert concluded["status"] in (ExperimentStatus.COMPLETED, ExperimentStatus.LOW_CONFIDENCE)
    assert concluded["runs"], "a run must be recorded"
    result = concluded["result"]
    assert result["winner"]["rank"] == 1
    assert result["method"] == "predicted"
    assert len(result["ranked"]) == len(result["losers"]) + 1
    assert 0 <= result["confidence"] <= 100


def test_experiment_rejects_invalid_inputs(lab_dir):
    manager = ExperimentManager()
    group = generate_variants("hook", base_content="x", count=4)
    with pytest.raises(ValueError):
        manager.create_experiment("not_a_type", group)
    with pytest.raises(ValueError):
        manager.create_experiment("hook", group, mode="quantum")
    with pytest.raises(ValueError):
        manager.create_experiment("hook", {"variants": [make_variant("hook", "only one")]})
    with pytest.raises(ValueError):
        manager.run_experiment("lab_does_not_exist")


def test_duplicate_variants_are_dropped_at_creation(lab_dir):
    manager = ExperimentManager()
    group = {
        "experiment_type": "hook",
        "variants": [
            make_variant("hook", "the exact same hook text"),
            make_variant("hook", "the exact same hook text"),
            make_variant("hook", "a genuinely different angle"),
        ],
    }
    experiment = manager.create_experiment("hook", group)
    assert len(experiment["variant_group"]["variants"]) == 2


def test_scheduler_enforces_concurrency_and_releases_due(lab_dir):
    configure(max_concurrent_experiments=2)
    manager = ExperimentManager()
    experiments = [
        manager.create_experiment("hook", generate_variants("hook", base_content=f"topic {i}", count=3))
        for i in range(3)
    ]
    manager.schedule_experiment(experiments[0]["experiment_id"], scheduled_for="2000-01-01T00:00:00+00:00")
    manager.schedule_experiment(experiments[1]["experiment_id"], scheduled_for="2000-01-01T00:00:00+00:00")
    manager.schedule_experiment(experiments[2]["experiment_id"], scheduled_for="2999-01-01T00:00:00+00:00")

    due = manager.scheduler.due()
    assert [e["experiment_id"] for e in due] == [
        experiments[0]["experiment_id"], experiments[1]["experiment_id"],
    ], "future-scheduled experiments must not release early"

    results = manager.run_due_experiments(item=sample_item())
    assert len(results) == 2
    assert all(r["status"] in ExperimentStatus.CONCLUDED for r in results)


def test_concurrent_experiments_run_independently(lab_dir):
    manager = ExperimentManager()
    first = manager.create_experiment("hook", generate_variants("hook", base_content="a", count=4))
    second = manager.create_experiment("title", generate_variants("title", base_content="b", count=4))
    manager.run_experiment(first["experiment_id"], item=sample_item())
    manager.run_experiment(second["experiment_id"], item=sample_item())
    assert manager.history.count() == 2
    assert {e["experiment_type"] for e in manager.history.concluded()} == {"hook", "title"}


def test_observed_scores_conclude_with_statistical_confidence(lab_dir):
    manager = ExperimentManager()
    group = generate_variants("thumbnail", count=2)
    experiment = manager.create_experiment("thumbnail", group, mode="ab")
    winner_id = group["variants"][0]["variant_id"]
    loser_id = group["variants"][1]["variant_id"]
    for _ in range(3):
        manager.record_observed_scores(
            experiment["experiment_id"], {winner_id: 90, loser_id: 30}
        )
    concluded = manager.history.get(experiment["experiment_id"])
    assert concluded["status"] == ExperimentStatus.COMPLETED
    assert concluded["result"]["method"] == "observed"
    assert concluded["result"]["winner"]["variant_id"] == winner_id
    assert concluded["result"]["confidence"] >= 90


def test_cancelled_experiments_stay_concluded(lab_dir):
    manager = ExperimentManager()
    experiment = manager.create_experiment("hook", generate_variants("hook", base_content="x", count=3))
    manager.cancel_experiment(experiment["experiment_id"])
    after = manager.run_experiment(experiment["experiment_id"], item=sample_item())
    assert after["status"] == ExperimentStatus.CANCELLED
    assert not after["runs"]


# ---------------------------------------------------------------- providers


def test_provider_interface_and_mock_placeholder(lab_dir):
    provider = get_experiment_provider("youtube_shorts", mode="ab")
    assert provider is not None and provider.key == "mock"
    assert provider.supports("tiktok", "multivariate")
    manager = ExperimentManager()
    experiment = manager.create_experiment(
        "thumbnail", generate_variants("thumbnail", count=3), provider=provider.key
    )
    result = provider.start_experiment(experiment)
    assert result["status"] == "completed"
    assert set(result["scores"]) == {
        v["variant_id"] for v in experiment["variant_group"]["variants"]
    }
    # Provider outcomes flow back through the observed-score path.
    concluded = manager.record_observed_scores(experiment["experiment_id"], result["scores"])
    assert concluded["status"] in ExperimentStatus.CONCLUDED


def test_disabled_providers_are_skipped():
    configure(disabled_providers=["mock"])
    assert get_experiment_provider("youtube_shorts") is None


# ----------------------------------------------------------- recommendations


def test_recommendation_shape_and_low_confidence_warning(lab_dir):
    manager = ExperimentManager()
    experiment = manager.create_experiment(
        "hook", generate_variants("hook", base_content="the ocean", count=6)
    )
    concluded = manager.run_experiment(experiment["experiment_id"], item=sample_item())
    recommendation = build_recommendation(concluded)
    for field in OPTIMIZATION_RECOMMENDATION_FIELDS:
        assert field in recommendation, field
    assert recommendation["source"] == "optimization_lab"
    assert recommendation["target_slot"] == "hook"
    assert recommendation["content"] == concluded["result"]["winner"]["content"]
    if recommendation["confidence"] < get_optimization_config().low_confidence_threshold:
        assert any("low confidence" in w for w in recommendation["warnings"])


def test_conflicting_recommendations_resolve_to_highest_confidence():
    strong = {"recommendation_id": "a", "target_slot": "hook", "confidence": 90.0,
              "experiment_type": "hook", "warnings": []}
    weak = {"recommendation_id": "b", "target_slot": "hook", "confidence": 40.0,
            "experiment_type": "hook", "warnings": []}
    other = {"recommendation_id": "c", "target_slot": "title", "confidence": 50.0,
             "experiment_type": "title", "warnings": []}
    resolved = resolve_conflicts([weak, strong, other])
    assert [r["recommendation_id"] for r in resolved] == ["a", "c"]
    assert any("conflicting recommendation b" in w for w in strong["warnings"])


def test_pipeline_query_surface_returns_best_of_everything(lab_dir):
    lab = get_optimization_lab()
    lab.optimize({"ideas": [sample_item()]})
    assert lab.best_hook() and lab.best_hook()["experiment_type"] == "hook"
    assert lab.best_title()["target_slot"] == "title"
    assert lab.best_thumbnail() and lab.best_caption() and lab.best_narration_style()
    assert lab.best_cta()["experiment_type"] == "cta_placement"
    assert lab.best_publishing_window()["experiment_type"] == "publishing_time"
    package = lab.best_content_package()
    assert set(package) >= {"hook", "title", "thumbnail", "caption"}
    assert best_content_package(lab.history) .keys() == package.keys()


def test_query_surface_is_empty_without_history(lab_dir):
    lab = get_optimization_lab()
    assert lab.best_hook() is None
    assert lab.best_content_package() == {}


# --------------------------------------------------------------- full cycle


def test_run_optimization_fills_slots_and_reports(lab_dir):
    item = sample_item()
    updates = run_optimization({"ideas": [item]})
    report = updates["optimization_report"]
    for field in OPTIMIZATION_REPORT_FIELDS:
        assert field in report, field
    assert report["status"] == "optimized"
    assert report["items"] == 1
    assert report["experiments_run"] == len(get_optimization_config().active_experiment_types)
    assert report["variants_generated"] > 20
    assert report["winning_variants"] and report["losing_variants"]

    package = item["optimization_package"]
    for field in OPTIMIZATION_PACKAGE_FIELDS:
        assert field in package, field
    assert package["status"] in ("optimized", "partial")
    assert package["best"]["hook"], "the strongest hook must be named"

    routed = updates["optimization_recommendations"]
    assert set(routed) == set(get_optimization_config().active_experiment_types)
    assert render_report_text(report).startswith("Optimization Report")


def test_run_optimization_prefers_unified_packages(lab_dir):
    package_item = sample_item()
    updates = run_optimization({"unified_packages": [package_item], "ideas": [sample_item()]})
    assert updates["optimization_report"]["items"] == 1
    assert "optimization_package" in package_item
    assert "unified_packages" in updates


def test_empty_context_degrades_to_no_items(lab_dir):
    updates = run_optimization({})
    assert updates["optimization_report"]["status"] == "no_items"
    assert updates["optimization_recommendations"] == {}


def test_active_experiment_types_are_configurable(lab_dir):
    configure(active_experiment_types=["hook", "title"])
    updates = run_optimization({"ideas": [sample_item()]})
    assert updates["optimization_report"]["experiments_run"] == 2
    assert set(updates["optimization_recommendations"]) == {"hook", "title"}


# ------------------------------------------------------------ learning loop


def test_completed_experiments_grow_long_term_memory(lab_dir, tmp_path, monkeypatch):
    import services.analytics.store as analytics_store

    monkeypatch.setattr(analytics_store, "_DEFAULT_DIR", str(tmp_path / "analytics"))
    from services.learning.memory import MEMORY_CATEGORY, get_memory

    manager = ExperimentManager()
    group = generate_variants("thumbnail", count=2)
    experiment = manager.create_experiment("thumbnail", group, mode="ab")
    winner_id = group["variants"][0]["variant_id"]
    loser_id = group["variants"][1]["variant_id"]
    for _ in range(3):
        manager.record_observed_scores(experiment["experiment_id"], {winner_id: 92, loser_id: 25})

    outcomes = get_memory().recall(MEMORY_CATEGORY.EXPERIMENT_OUTCOMES)
    assert any(o["content"]["experiment_id"] == experiment["experiment_id"] for o in outcomes)


def test_historical_winners_influence_future_rankings(lab_dir):
    manager = ExperimentManager()
    group = generate_variants("hook", base_content="the ocean", count=5)
    experiment = manager.create_experiment("hook", group)
    scores = {v["variant_id"]: 20 for v in group["variants"]}
    champion_label = group["variants"][3]["label"]
    scores[group["variants"][3]["variant_id"]] = 95
    for _ in range(3):
        manager.record_observed_scores(experiment["experiment_id"], scores)

    priors = experiment_winner_priors(manager.history, "hook")
    assert priors.get(champion_label, 0) > 50, "the proven winner must carry a positive prior"

    fresh = generate_variants("hook", base_content="the ocean", count=5)["variants"]
    ranked = rank_variants(fresh, item=sample_item(), historical_priors=priors)
    champion_rank = next((v["rank"] for v in ranked if v["label"] == champion_label), None)
    assert champion_rank is not None and champion_rank <= 2


def test_report_surfaces_historical_trends(lab_dir, tmp_path, monkeypatch):
    import services.analytics.store as analytics_store
    from services.analytics.store import get_analytics_store

    monkeypatch.setattr(analytics_store, "_DEFAULT_DIR", str(tmp_path / "analytics"))
    winner_metrics = {"views": 80_000, "audience_retention": 85, "ctr": 12,
                      "likes": 1600, "comments": 160, "shares": 260, "saves": 200}
    records = [
        {"record_id": f"r{i}", "analytics_ref": f"ref{i}", "platform": "youtube_shorts",
         "topic": "oceans", "niche": "science", "title": "T", "hook": "WIN hook",
         "keywords": ["ocean"], "psychology_strategy": ["curiosity"],
         "video_length_sec": 45.0, "posting_time": "2026-07-08T17:00:00+00:00",
         "published_at": "2026-07-08T17:00:00+00:00", "experiment_id": "", "variant_id": "",
         "metrics": winner_metrics, "metrics_status": "collected",
         "metrics_source": "mock", "collected_at": "2026-07-08T18:00:00+00:00"}
        for i in range(4)
    ]
    get_analytics_store().add_records(records)
    updates = run_optimization({"ideas": [sample_item()]})
    assert updates["optimization_report"]["historical_trends"], (
        "collected history must surface as historical trends"
    )


# -------------------------------------------------------- pipeline integration


def test_orchestrator_runs_the_optimization_stage(lab_dir):
    context = {"command": "optimize", "ideas": [sample_item()]}
    report = get_orchestrator().run_stage("optimization", context)
    assert report.status == StageStatus.SUCCESS, report.errors
    assert context["optimization_report"]["status"] == "optimized"
    assert context["optimization_recommendations"]


def test_optimization_stage_schedules_into_the_full_pipeline(lab_dir):
    from services.optimization.integration import (
        disable_optimization_stage,
        enable_optimization_stage,
    )
    from services.orchestrator.stages import build_pipeline_plan

    try:
        enable_optimization_stage()
        enable_optimization_stage()  # idempotent
        plan = build_pipeline_plan()
        names = [name for name, _ in plan]
        assert names.count("optimization") == 1
        assert names.index("optimization") == names.index("quality") + 1
    finally:
        disable_optimization_stage()
    assert "optimization" not in [name for name, _ in build_pipeline_plan()]
    assert STAGE_GROUPS.get("optimization") == ["optimization_lab"], (
        "manual stage group must survive disabling the scheduled stage"
    )


def test_stage_degrades_gracefully_with_nothing_to_optimize(lab_dir):
    context = {"command": "probe"}
    report = get_orchestrator().run_stage("optimization", context)
    assert report.status in (StageStatus.SUCCESS, StageStatus.WARNING)
    assert context["optimization_report"]["status"] == "no_items"


# ----------------------------------------------------------- failure handling


def test_invalid_experiment_types_degrade_to_warnings(lab_dir):
    configure(active_experiment_types=["hook", "definitely_not_real"])
    item = sample_item()
    updates = run_optimization({"ideas": [item]})
    report = updates["optimization_report"]
    assert any("definitely_not_real" in w for w in report["warnings"])
    assert "hook" in updates["optimization_recommendations"], (
        "one bad experiment type must not block the others"
    )
    assert item["optimization_package"]["status"] == "partial"


def test_prediction_model_failure_degrades_not_crashes(lab_dir):
    class ExplodingModel(PredictionModel):
        key = "exploding"

        def predict(self, variant, item=None, context=None):
            raise RuntimeError("model backend unavailable")

    register_prediction_model(ExplodingModel())
    configure(prediction_model="exploding")
    updates = run_optimization({"ideas": [sample_item()]})
    report = updates["optimization_report"]
    assert report["status"] in ("partial", "no_items")
    assert report["warnings"], "failures must surface as warnings"


def test_unknown_prediction_model_falls_back_to_heuristic():
    configure(prediction_model="does_not_exist")
    assert get_prediction_model().key == "heuristic"


# -------------------------------------------------------------- configuration


def test_configure_overrides_and_rejects_unknown_keys():
    config = configure(min_winner_confidence=80, history_influence=0.5)
    assert config.min_winner_confidence == 80
    assert get_optimization_config().history_influence == 0.5
    with pytest.raises(ValueError):
        configure(not_a_real_knob=1)
    reset_optimization_config()
    assert get_optimization_config().min_winner_confidence != 80


def test_config_round_trips_and_ignores_unknown_fields():
    config = OptimizationConfig.from_dict(
        {"default_variant_count": 9, "unknown_future_field": True}
    )
    assert config.default_variant_count == 9
    assert "scoring_weights" in config.to_dict()


def test_scoring_weight_changes_change_outcomes(lab_dir):
    item = sample_item()
    variant = make_variant("hook", "Why nobody talks about the deep ocean?")
    baseline_score = score_variant(dict(variant), item=item)["score"]
    # Concentrate ALL weight on a single input: the composite must now
    # equal that input exactly — proof the weights drive the outcome.
    for single_input in ("psychology", "ctr_prediction", "localization_suitability"):
        weights = {key: 0.0 for key in SCORING_INPUTS}
        weights[single_input] = 1.0
        configure(scoring_weights=weights)
        scored = score_variant(dict(variant), item=item)
        assert scored["score"] == scored["score_breakdown"][single_input], single_input
    reset_optimization_config()
    assert score_variant(dict(variant), item=item)["score"] == baseline_score
