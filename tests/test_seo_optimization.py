"""Tests for the Global Content Optimization Engine (Agent 8).

Covers title generation, keyword generation, hashtag generation,
localization interfaces, posting-window recommendations, optimization
scoring, publishing-package generation, and the engine's registration +
pipeline integration. Everything runs deterministically with zero API keys.
"""

import engines  # noqa: F401 - importing registers all engines
from engines import registry
from engines.contracts import ContractEngine
from providers.seo_sources import get_seo_provider_registry
from providers.seo_sources.base import SeoSourceProvider
from services.orchestrator import ContentPackage, Orchestrator, StageStatus
from services.seo.hashtags import build_hashtag_package
from services.seo.keywords import build_keyword_package, classify_intent, collect_keyword_signals
from services.seo.localization import (
    LOCALIZATION_TARGETS,
    HeuristicLocalizationAdapter,
    LocalizationAdapter,
    build_localization_package,
)
from services.seo.models import (
    HASHTAG_PLATFORMS,
    KEYWORD_CLASSES,
    LOCALIZATION_TARGET_FIELDS,
    OPTIMIZATION_REPORT_FIELDS,
    PUBLISH_WINDOW_FIELDS,
    PUBLISHING_PACKAGE_FIELDS,
    THUMBNAIL_EVAL_KEYS,
    TITLE_ARCHETYPES,
    TITLE_CANDIDATE_FIELDS,
)
from services.seo.package import optimize_content
from services.seo.report import build_optimization_report
from services.seo.thumbnails import rank_thumbnail_concepts
from services.seo.titles import generate_title_candidates
from services.seo.windows import recommend_publish_windows


def make_idea(**overrides) -> dict:
    idea = {
        "title": "Octopus Intelligence — The Truth",
        "hook": "This creature rewrites everything we know about intelligence.",
        "script": "Octopuses have nine brains and can solve puzzles faster than expected.",
        "description": "A short breakdown of octopus intelligence.",
        "keywords": ["octopus", "intelligence", "marine biology", "animal cognition"],
        "hashtags": ["#Octopus", "#Science"],
        "seo_score": 72,
        "thumbnail_concept": "Bold 3-word text beside a close-up octopus eye.",
        "thumbnail_concepts": [
            {
                "concept_id": "thumb_1",
                "archetype": "shock_face",
                "label": "Shock Face",
                "description": "High-contrast close-up reaction face, secret reveal energy.",
                "emotion": "shocked",
                "title_overlay": "NINE BRAINS?!",
                "focal_subject": "octopus eye",
                "scores": {"curiosity": 82, "contrast": 74, "facial_focus": 88, "object_focus": 60, "color": 70},
                "contrast_score": 74,
                "click_probability_pct": 7.4,
            },
            {
                "concept_id": "thumb_2",
                "archetype": "mystery_object",
                "label": "Mystery Object",
                "description": "Blurred object with a question mark overlay.",
                "emotion": "",
                "title_overlay": "WHAT IS THIS DEEP SEA CREATURE HIDING FROM US",
                "scores": {"curiosity": 76, "contrast": 55, "facial_focus": 30, "object_focus": 80, "color": 58},
                "contrast_score": 55,
                "click_probability_pct": 5.1,
            },
        ],
        "psychology_score": 78,
        "publishable": True,
        "scores": {"publish": 84, "virality": 76},
    }
    idea.update(overrides)
    return idea


# ------------------------------------------------------------------ titles


def test_title_generation_covers_all_archetypes_and_ranking_fields():
    titles = generate_title_candidates("octopus intelligence", base_title="Octopus Facts",
                                       keywords=["octopus", "intelligence"], base_psychology=75)
    archetypes = {t["archetype"] for t in titles}
    assert set(TITLE_ARCHETYPES).issubset(archetypes)
    for candidate in titles:
        for field in TITLE_CANDIDATE_FIELDS:
            assert field in candidate, field
        assert 0 <= candidate["ctr_prediction"] <= 100
        assert 0 <= candidate["seo_score"] <= 100
        assert 0 <= candidate["psychology_score"] <= 100
        assert 0 <= candidate["confidence"] <= 100
        assert len(candidate["title"]) <= 60


def test_title_generation_is_ranked_and_deterministic():
    first = generate_title_candidates("black holes", keywords=["black holes"])
    second = generate_title_candidates("black holes", keywords=["black holes"])
    assert first == second
    assert [t["rank"] for t in first] == list(range(1, len(first) + 1))
    overalls = [t["overall"] for t in first]
    assert overalls == sorted(overalls, reverse=True)


# ---------------------------------------------------------------- keywords


def test_keyword_package_has_all_classes_and_intent_classification():
    package = build_keyword_package(
        "octopus intelligence",
        hook="This creature rewrites everything we know.",
        script="Octopuses have nine brains.",
        base_keywords=["octopus", "marine biology"],
        niche="Science",
        signals=collect_keyword_signals("octopus intelligence"),
    )
    for cls in KEYWORD_CLASSES:
        assert package.get(cls), cls
    intents = package["search_intent"]
    assert intents["dominant"] in ("informational", "navigational", "commercial", "transactional")
    assert set(intents["by_intent"]) == {"informational", "navigational", "commercial", "transactional"}
    assert package["signal_sources"]  # placeholder providers feed the package


def test_intent_classifier_covers_the_taxonomy():
    assert classify_intent("what is a black hole") == "informational"
    assert classify_intent("best telescope review") == "commercial"
    assert classify_intent("buy telescope discount") == "transactional"
    assert classify_intent("NASA") == "navigational"


def test_seo_provider_registry_discovers_future_provider_interfaces():
    providers = get_seo_provider_registry()
    for key in ("google_search", "google_trends", "youtube_search", "tiktok_search",
                "reddit", "news_api", "keyword_api"):
        assert key in providers, key
        assert isinstance(providers[key], SeoSourceProvider)
    signals = providers["google_search"].keyword_signals("octopus", limit=3)
    assert len(signals) == 3
    for signal in signals:
        assert signal["kind"] in ("semantic", "long_tail", "question", "entity")
        assert 0 <= signal["competition"] <= 1
        assert signal["source"] == "google_search"


# ---------------------------------------------------------------- hashtags


def test_hashtag_package_is_platform_specific_and_ranked():
    package = build_hashtag_package("octopus intelligence", niche="Science",
                                    keywords=["octopus", "marine biology"])
    for platform in HASHTAG_PLATFORMS:
        assert platform in package, platform
        tags = package[platform]
        assert tags, platform
        assert [t["rank"] for t in tags] == list(range(1, len(tags) + 1))
        usefulness = [t["usefulness"] for t in tags]
        assert usefulness == sorted(usefulness, reverse=True)
        for tag in tags:
            assert tag["tag"].startswith("#")
            assert 0 <= tag["usefulness"] <= 100
    assert len(package["x"]) <= 3        # platform limits respected
    assert len(package["instagram"]) <= 8


# ------------------------------------------------------------ localization


def test_localization_interfaces_and_package_structure():
    assert issubclass(HeuristicLocalizationAdapter, LocalizationAdapter)
    package = build_localization_package(
        "US", "en",
        keywords=["octopus", "intelligence"],
        hashtags=["#Octopus"],
        platform="youtube",
    )
    assert package["base_locale"] == "en-US"
    assert package["translation_performed"] is False
    assert len(package["targets"]) == len(LOCALIZATION_TARGETS)
    for plan in package["targets"]:
        for field in LOCALIZATION_TARGET_FIELDS:
            assert field in plan, field
    base = next(p for p in package["targets"] if p["locale"] == "en-US")
    assert base["status"] == "ready" and base["readiness"] == 100
    foreign = next(p for p in package["targets"] if p["language"] != "en")
    assert foreign["translation_pending"] is True
    assert all(slot["status"] == "pending_translation" for slot in foreign["keyword_replacements"])
    assert foreign["regional_posting"]["peak_hours_local"]


# ----------------------------------------------------------------- windows


def test_publish_windows_are_ranked_with_full_contract():
    windows = recommend_publish_windows(
        platforms=["youtube", "tiktok"], country="US", language="en",
        audience_score=70, competition_score=60, trend_velocity=0.8,
    )
    assert windows
    assert [w["rank"] for w in windows] == list(range(1, len(windows) + 1))
    scores = [w["score"] for w in windows]
    assert scores == sorted(scores, reverse=True)
    for window in windows:
        for field in PUBLISH_WINDOW_FIELDS:
            assert field in window, field
        assert window["platform"] in ("youtube", "tiktok")
        assert 0 <= window["confidence"] <= 100


def test_publish_windows_ignore_unknown_platforms_gracefully():
    windows = recommend_publish_windows(platforms=["myspace"])
    assert windows and all(w["platform"] == "youtube" for w in windows)  # sane fallback


# -------------------------------------------------------------- thumbnails


def test_thumbnail_recommendations_are_evaluated_and_ranked():
    ranked = rank_thumbnail_concepts(make_idea()["thumbnail_concepts"])
    assert [t["rank"] for t in ranked] == [1, 2]
    assert ranked[0]["concept_id"] == "thumb_1"  # higher click probability wins
    for item in ranked:
        for key in THUMBNAIL_EVAL_KEYS:
            assert key in item["evaluation"], key
            assert 0 <= item["evaluation"][key] <= 100
        assert item["click_probability_pct"] > 0
        assert item["recommendation"]


# ----------------------------------------------------------------- scoring


def test_optimization_report_has_all_ten_metrics_in_range():
    result = optimize_content(make_idea(), {"niche": "Science", "subject": "octopus intelligence"})
    report = result["report"]
    for metric in OPTIMIZATION_REPORT_FIELDS:
        assert metric in report, metric
        assert 0 <= report[metric] <= 100, metric
    assert report["publishing_readiness"] > 80  # every component was produced


def test_optimization_report_handles_missing_components():
    report = build_optimization_report([], {}, {}, {}, [], {}, [])
    for metric in OPTIMIZATION_REPORT_FIELDS:
        assert 0 <= report[metric] <= 100, metric


# ----------------------------------------------- publishing package + engine


def test_publishing_package_generation_is_standardized():
    result = optimize_content(make_idea(), {"niche": "Science", "subject": "octopus intelligence"})
    package = result["publishing_package"]
    for field in PUBLISHING_PACKAGE_FIELDS:
        assert field in package, field
    assert package["package_version"] == "1.0"
    assert package["status"] == "optimized"
    assert package["title"] and len(package["title"]) <= 60
    assert package["titles"] and package["thumbnails"] and package["publish_windows"]
    assert package["localization"]["translation_performed"] is False


def test_enrichment_preserves_refinement_stage_seo_fields():
    package_dict = ContentPackage(
        topic="octopus intelligence",
        keywords=["octopus"],
        seo_package={
            "title": "Original Title",
            "description": "Original description.",
            "hashtags": ["#Original"],
            "keywords": ["octopus"],
            "seo_score": 70,
        },
        thumbnail_plan=[{"source": "seo", "concept": "Bold text beside octopus eye."}],
        publish_ready=True,
    ).to_dict()
    result = optimize_content(package_dict, {})
    enriched = result["seo_package"]
    # Base fields untouched (add-only contract from engines/seo/README.md).
    assert enriched["title"] == "Original Title"
    assert enriched["description"] == "Original description."
    assert enriched["hashtags"] == ["#Original"]
    assert enriched["seo_score"] == 70
    # New optimization layers added.
    assert enriched["optimized_titles"] and enriched["keyword_package"]
    assert enriched["localization"] and enriched["publish_windows"]


def test_engine_registered_live_with_contracts():
    engine = registry.get_engine("seo_optimization")
    assert isinstance(engine, ContractEngine)
    assert engine.is_ready() is True
    diag = engine.diagnostics()
    assert diag["engine_id"] == "seo_optimization"
    assert "seo_optimization_report" in diag["output_contract"]
    assert "publishing_packages" in diag["output_contract"]
    assert diag["dependencies"] == ["seo", "quality"]


def test_engine_run_produces_contract_outputs_from_ideas():
    engine = registry.get_engine("seo_optimization")
    context = {"ideas": [make_idea()], "seo_keywords": ["octopus"], "niche": "Science",
               "subject": "octopus intelligence"}
    updates = engine.run(context)
    assert engine.validate_output(updates) == []
    assert updates["seo_optimization_report"]["items"] == 1
    assert updates["seo_optimization_report"]["status"] == "optimized"
    assert len(updates["publishing_packages"]) == 1
    assert context["ideas"][0]["seo_package"]["optimized_titles"]


def test_engine_prefers_unified_packages_and_respects_publish_gate():
    engine = registry.get_engine("seo_optimization")
    ready = ContentPackage(topic="octopus", publish_ready=True).to_dict()
    held = ContentPackage(topic="octopus", publish_ready=False).to_dict()
    context = {"unified_packages": [ready, held], "ideas": [make_idea()]}
    updates = engine.run(context)
    assert updates["seo_optimization_report"]["source"] == "unified_packages"
    assert updates["seo_optimization_report"]["items"] == 1  # held package excluded
    # Agent 7's slot stays untouched — handover is via publishing_packages.
    assert ready["publishing_package"] == {}


def test_engine_with_empty_context_still_meets_output_contract():
    engine = registry.get_engine("seo_optimization")
    updates = engine.run({})
    assert engine.validate_output(updates) == []
    assert updates["seo_optimization_report"]["items"] == 0
    assert updates["publishing_packages"] == []


def test_orchestrator_seo_stage_now_runs_live():
    orch = Orchestrator()
    context = {"ideas": [make_idea()], "seo_keywords": ["octopus"], "niche": "Science",
               "subject": "octopus intelligence"}
    report = orch.run_seo_stage(context)
    assert report.status == StageStatus.SUCCESS, report.errors
    assert context["seo_optimization_report"]["items"] == 1
    assert context["publishing_packages"]
