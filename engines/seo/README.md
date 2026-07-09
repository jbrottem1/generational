# Global Content Optimization Engine — Agent 8 (LANDED)

The post-render, pre-publish optimization stage of the AI Content
Operating System. It does NOT generate scripts or videos — it maximizes
discoverability, search performance, click-through rate, localization
readiness, and long-term audience growth, then hands a standardized
PublishingPackage to the Publishing Engine.

```
Render Engine (Agent 6)
   ↓
Global Content Optimization Engine (this engine — key: seo_optimization)
   ↓
Publishing Engine (Agent 7)
```

## Where the code lives

| Piece | Path |
|---|---|
| Engine (thin `ContractEngine`) | `engines/seo_optimization.py` |
| Business logic | `services/seo/` |
| SEO signal providers (auto-discovered registry) | `providers/seo_sources/` |
| Tests | `tests/test_seo_optimization.py` |

Note: the engine module is `engines/seo_optimization.py` rather than a
module inside this folder because `engines/seo.py` (the live
refinement-stage engine, different owner) already claims the `engines.seo`
import name — a Python file/package collision. This folder holds the
engine's documentation.

## What one optimization pass produces

`services/seo/package.py::optimize_content(item, context)` accepts a
pipeline idea dict OR a canonical ContentPackage dict and returns:

1. **Enriched `seo_package`** (additive — the refinement-stage `title`,
   `description`, `hashtags`, `keywords`, `seo_score` are never touched):
   - `optimized_titles` — ten archetypes (curiosity, authority,
     educational, question, shock, list, contrarian, story, breaking_news,
     scientific) + the base title, each ranked with CTR prediction, SEO
     score, psychology score, confidence, and overall.
   - `description_package` — long/short/platform descriptions, CTA,
     first-comment and pinned-comment suggestions.
   - `keyword_package` — primary, secondary, semantic, long-tail, entity,
     and question keywords + search-intent classification.
   - `hashtag_package` — per-platform (YouTube, TikTok, Instagram,
     Facebook, X, LinkedIn, Pinterest) ranked hashtags with estimated
     usefulness.
   - `thumbnail_recommendations` — Visual Intelligence concepts
     re-evaluated on curiosity, contrast, text density, facial emotion,
     object emphasis, and color psychology; ranked by click probability.
   - `localization` — per-locale plans (10 default country/language
     targets): keyword-replacement slots, regional hashtags, regional
     posting strategy, readiness. **No translation is performed yet** —
     a `LocalizationAdapter` (services/seo/localization.py) fills the
     pending slots later with zero contract changes.
   - `publish_windows` — ranked posting windows per platform/country
     scored on engagement tables, audience, competition, trend velocity.
   - `optimization_report` — SEO score, CTR prediction, retention
     prediction, competition score, trend strength, evergreen score,
     localization readiness, publishing readiness, confidence, overall
     optimization score.
2. **PublishingPackage v1.0** (`PUBLISHING_PACKAGE_FIELDS`,
   `services/seo/models.py`) — the standardized handover for Agent 7.
3. **Per-item Optimization Report** (also aggregated engine-wide).

## Engine contract

- Key `seo_optimization` · subclasses `engines.contracts.ContractEngine` ·
  `is_ready() == True` (graduated from the `engines/future_stubs.py` stub).
- Input: `unified_packages` (preferred; only `publish_ready` items) or
  `ideas` / `selected_ideas` (only `publishable` items), plus trend context
  (`top_opportunity`), `niche`, `subject`.
- Output: `seo_optimization_report` + `publishing_packages` context keys;
  each item's `seo_package` enriched in place.
- Ownership: never rewrites `engines/seo.py` output; never writes the
  ContentPackage `publishing_package` slot (Agent 7's); never modifies the
  Render or Publishing engines.
- Run it via `get_orchestrator().run_seo_stage(context)` — with nothing to
  optimize it reports zero items, never a failure.

## Future providers — nothing hardcoded

`providers/seo_sources/` mirrors `providers/trend_sources/`: drop a module
containing a `SeoSourceProvider` subclass and the registry auto-discovers
it. Placeholder (deterministic) providers ship for Google Search, Google
Trends, YouTube Search, TikTok Search, Reddit, News APIs, and Keyword
APIs; live API wiring is a per-file swap, and proprietary providers are
new modules. Providers return normalized `KEYWORD_SIGNAL_FIELDS` dicts —
the Keyword Engine works fully with zero providers available.

## Scoring

Everything is deterministic (Demo Mode, no API key): word-bank +
structure heuristics from `engines/heuristics.py`, blended via
`weighted_blend`, jittered stably per text so results are reproducible and
testable. Provider-backed (LLM/search-data) scoring can replace any module
without changing the field contracts in `services/seo/models.py`.
