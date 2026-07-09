# Generational — Data Contracts (v8.1)

The shared data shapes every agent must honor. **All contracts are
additive-only:** append fields/keys freely (coordinate with Agent 1), never
remove, rename, or repurpose existing ones.

---

## 1. ContentPackage (canonical) — `services/orchestrator/models.py`

`ContentPackage` is the OS-level name; `ProductionPackage` is the same class
(alias). One package = one publishable content unit. The canonical field
list is `CONTENT_PACKAGE_FIELDS`.

| Field | Type | Written by |
|---|---|---|
| `project_id` | str | packager |
| `brand` / `brand_id` / `channel_id` | str | packager / **Agent 10** |
| `platforms` / `target_platforms` | list | packager |
| `target_country` / `language` / `target_language` | str | packager |
| `topic` / `keywords` | str / list | trend + script stages |
| `trend_score` / `opportunity_score` / `competition_score` | int/float | trend stage |
| `psychology_score` / `virality_score` / `attention_score` | int | psychology + attention stages |
| `hook` / `script` / `script_package` | str / dict | script stage |
| `scene_breakdown` / `visual_assets` / `visual_package` / `thumbnail_plan` | list/dict | visual stage |
| `voice_assets` / `music_assets` / `audio_package` / `captions` | dict/list | audio + production stages |
| `seo_package` | dict | refinement `seo`; enriched by **Agent 8** |
| `quality_score` / `publish_ready` | int / bool | quality gate |
| `render_package` | dict | **Agent 6** |
| `publishing_package` | dict | **Agent 7** |
| `analytics_placeholder` / `analytics_package` | dict | **Agent 9** |
| `learning_metadata` | dict | **Agent 9** |
| `status` | str | pipeline (`planned → approved/held → rendered → scheduled → published`) |
| `diagnostics` | dict | any stage (append keys) |
| `created_at` / `extras` | str / dict | packager / forward-compat overflow |

Serialization: `to_dict()` / `from_dict()`. Unknown fields survive
round-trips inside `extras` — old code never crashes on new fields.

---

## 2. Shared context dict (intelligence pipeline)

Never rename or remove these keys; add new ones instead:
`command`, `provider`, `subject`, `trends`, `trend_opportunities`,
`trend_keywords`, `research`, `research_references`, `candidates`,
`selected_ideas`, `ideas`, `psychology_report`, `attention_report`,
`visual_intelligence_package`, `voice_audio_package`, `quality_summary`,
`production_packages`, `pipeline_steps`, `publish_mode`,
`production_report` (v9.0 — the unified Production Report written by the
orchestrator at the end of every full run; see
`services/orchestrator/report.py`),
`trend_forecasts`, `trend_classifications`, `opportunity_recommendations`,
`trend_intelligence_report` (v9.1 — **Agent 11**, written by the
`trend_forecasting` engine after opportunity ranking; see §2.2 and
`TREND_INTELLIGENCE.md`).

Future engines declare which keys they consume/produce via
`input_contract` / `output_contract` on `ContractEngine`.

---

## 2.1 Shared analysis library — `engines/analysis.py`

Pure deterministic functions needed by more than one engine (the
18-dimension psychology scorer, the script critique). Per Architecture
Directive #1, shared logic moves here instead of creating engine-to-engine
imports. Any engine may import it freely; it imports no engines, touches no
context, and has no side effects. The Psychology and Critic engines
re-export its functions for backward compatibility.

---

## 2.2 Trend intelligence contracts (Agent 11) — `services/trend_intelligence/models.py`

The `trend_forecasting` engine (runs inside the trend stage, after
`opportunity_ranking`) emits three list keys plus one report, all
additive; the field tuples in `services/trend_intelligence/models.py`
are the testable contract:

| Context key | Shape | Contract |
|---|---|---|
| `trend_forecasts` | list of TrendForecast dicts | `FORECAST_FIELDS`: days_to_peak, expected_lifespan_days, trajectory, saturation_risk, publishing_window, recommended_posts_per_week, future_opportunity_score, forecast_confidence |
| `trend_classifications` | list of classification dicts | `CLASSIFICATION_FIELDS`: lifecycle (breaking/exploding/emerging/growing/peak/declining), content_type (evergreen/seasonal/recurring/topical), market_reach (niche/mid_market/mass_market), labels |
| `opportunity_recommendations` | list of OpportunityRecommendation dicts, sorted by priority | `RECOMMENDATION_FIELDS`: recommended_platform, hook_direction, psychology_strategy, recommended_duration_sec, recommended_format, thumbnail_direction, title_direction, seo_recommendations, publishing_window, estimated_roi, confidence_score, risk_score, priority_score |
| `trend_intelligence_report` | dict | QC results (kept/dropped/conflicts), classification histograms, historical_performance factor, top_recommendation, average_priority |

Recommendations are strategy only — never scripts or content. The same
enriched shapes are served on demand by the `OpportunityFeed`
(`services/trend_intelligence/feed.py`): `top_opportunity` / `top(n)` /
`emerging` / `evergreen` / `for_platform` / `highest_roi` /
`highest_confidence`. See `TREND_INTELLIGENCE.md`.

---

## 3. Engine contract — `engines/contracts.py`

Future engines subclass `ContractEngine` (which extends `Engine`) and
declare: `engine_id` (the registry `key`), `name` (`label`), `version`,
`input_contract`, `output_contract`, `dependencies`, `capabilities`, and
implement `run()`. Provided: `validate_input()`, `validate_output()`
(return problem lists — never raise), `health_check()`, `diagnostics()`.
`FutureEngine` is the not-yet-implemented variant (reports not-ready,
returns `NOT_IMPLEMENTED`).

---

## 4. StageReport / PipelineResult — `services/orchestrator/models.py`

Every stage run yields a `StageReport`: `stage`, `status`
(SUCCESS/WARNING/FAILED/SKIPPED), `started_at`, `finished_at`,
`duration_ms`, `confidence`, `warnings`, `errors`, `diagnostics`.
A full run yields a `PipelineResult`: `status`, `packages`,
`stage_reports`, `context`, `error`.

---

## 5. render_package (Agent 6) — `engines/render/`

Written into `ContentPackage.render_package` by the Render Engine.
Contract version `render_package_version: "2.0"` (the planning-layer
package inside `visual_package["render_package"]` remains `"1.0"`).
Additive over the media-production seed — `render_package_id`,
`queue_status`, etc. survive.

| Field | Type | Meaning |
|---|---|---|
| `output_format` | dict | 9:16 · 1080x1920 · MP4 · h264/aac · 30fps |
| `platforms` | list | youtube_shorts, tiktok, instagram_reels, facebook_reels |
| `resolution` / `aspect_ratio` / `duration_sec` | str/str/float | final output spec |
| `timeline` | dict | contiguous segments (`TIMELINE_SEGMENT_FIELDS`): scene_id, start/end/duration, narration/visual/caption/audio references, transitions, motion_effect, overlay_text, render_status |
| `scene_render_plan` | list | per scene (`SCENE_RENDER_PLAN_FIELDS`): asset type, image/video prompts, stock query, user/avatar/reaction footage slots, camera movement, zoom/pan/ken-burns effect, text overlays, caption placement, sound cues |
| `caption_render_plan` | dict | word-by-word or sentence mode, per-word timing map, emphasis words, safe area, platform layouts, style presets |
| `audio_mix_plan` | dict | narration/music/sfx/transition tracks, ducking, silence drops, volume levels, platform-safe loudness placeholder (-14 LUFS) |
| `transition_plan` / `motion_plan` | dict/list | normalized transition + motion instructions |
| `asset_requirements` / `missing_assets` | list | what the render needs / what only has placeholders |
| `render_warnings` | list | everything a human should know before real rendering |
| `estimated_render_duration_sec` | float | predicted wall-clock render time |
| `production_readiness_score` | int | 0-100 — the number Publishing gates on |
| `validation` | dict | SUCCESS/WARNING/FAILED/SKIPPED + per-check diagnostics |
| `render_status` / `mock` | str/bool | mock render outcome (`mock: true` until real backends land) |
| `mock_output_path` / `file_uri` | str | reserved output URI (no file written yet) |
| `render_log` / `render_job` | list/dict | simulated render log + job lifecycle |
| `render_manifest` | dict | counts + `ready_for_publishing` — Agent 7's gate |

Consumption (Agent 7): read `render_manifest.ready_for_publishing`,
`file_uri`, `duration_sec`, `platforms`, and `production_readiness_score`;
never mutate render fields.

---

## 6. seo_package enrichment + PublishingPackage (Agent 8) — `services/seo/`

The Global Content Optimization Engine (`seo_optimization`) ENRICHES
`ContentPackage.seo_package` additively. The base refinement-stage fields
(`title`, `description`, `hashtags`, `keywords`, `seo_score`) are never
overwritten; these fields are added on top (field tuples in
`services/seo/models.py` are the testable contract):

| Field | Type | Meaning |
|---|---|---|
| `optimized_titles` | list | ten archetype titles + the base title, each with `TITLE_CANDIDATE_FIELDS` (ctr_prediction, seo_score, psychology_score, confidence, overall, rank) |
| `recommended_title` | str | the top-ranked candidate |
| `description_package` | dict | long/short/platform descriptions, CTA, first + pinned comment (`DESCRIPTION_PACKAGE_FIELDS`) |
| `keyword_package` | dict | primary/secondary/semantic/long_tail/entity/question classes + `search_intent` classification (`KEYWORD_CLASSES`, `SEARCH_INTENTS`) |
| `hashtag_package` | dict | per-platform ranked hashtags with estimated usefulness (`HASHTAG_PLATFORMS`) |
| `thumbnail_recommendations` | list | Visual Intelligence concepts re-evaluated on the six click dimensions (`THUMBNAIL_EVAL_KEYS`), ranked with click probability |
| `localization` | dict | per-locale plans (`LOCALIZATION_TARGET_FIELDS`): keyword-replacement slots, regional hashtags/posting, readiness — translation intentionally pending (`LocalizationAdapter` fills later) |
| `publish_windows` | list | ranked posting windows (`PUBLISH_WINDOW_FIELDS`) per platform/country with confidence |
| `optimization_report` | dict | the ten metrics (`OPTIMIZATION_REPORT_FIELDS`), incl. `overall_optimization_score` |

**PublishingPackage v1.0** (`PUBLISHING_PACKAGE_FIELDS`) is the
standardized handover to the Publishing Engine, emitted on the
`publishing_packages` context key (one per optimized item) alongside the
aggregate `seo_optimization_report`. Additive-only from v1.0 on. Agent 8
never writes the ContentPackage `publishing_package` slot — that stays
Agent 7's. SEO signal providers implement `SeoSourceProvider`
(`providers/seo_sources/base.py`, normalized `KEYWORD_SIGNAL_FIELDS`
dicts) and auto-discover from `providers/seo_sources/`.

---

## 7. publishing_package + PublishingResult (Agent 7) — `services/publishing/`

The Publishing & Distribution Engine (`publishing` + `scheduler`) consumes
the RenderPackage (§5), the optimization PublishingPackage (§6), and
channel/brand configuration, and writes the ContentPackage
`publishing_package` slot (status → `scheduled` / `published`). Field
tuples in `services/publishing/models.py` are the testable contract; all
output is JSON-safe dicts.

**Platform publish package** (`PLATFORM_PUBLISH_PACKAGE_FIELDS`, v1.0) —
one per item × platform, fitted to the platform's constraints by its
provider adapter:

| Field | Type | Meaning |
|---|---|---|
| `video` | dict | file_uri, duration_sec, resolution, aspect_ratio, mock flag (from the render package) |
| `thumbnail` / `title` / `description` / `hashtags` / `keywords` | dict/str/list | optimization metadata, truncated to platform limits with warnings |
| `captions` | dict | the render caption plan |
| `language` / `country` / `platform` / `provider` | str | routing |
| `account` | dict | placeholder PublishingAccount reference (no credentials) |
| `publish_time` / `timezone` | str | ISO-8601 UTC + audience UTC offset |
| `visibility` | str | public / unlisted / private |
| `playlist` / `category` | dict | explicit placeholders for future routing |
| `status` / `diagnostics` | str/dict | prepared / blocked / published + format warnings, provider problems, readiness gates |

**PublishingJob** (`PUBLISHING_JOB_FIELDS`) — the queued unit
(`data/publishing_queue/jobs.json`): package, provider, `JobStatus`
(queued / scheduled / publishing / published / failed / cancelled),
attempts, retry schedule, full attempt history (`PUBLISH_ATTEMPT_FIELDS`),
and an `analytics_ref` the Analytics Engine (Agent 9) correlates against
(history log: `data/publishing_queue/history.json`).

**PublishingResult** (`PUBLISHING_RESULT_FIELDS`) — the standardized
object returned to the orchestrator on the `publishing_result` context
key: status, item/job counts by outcome, platforms, queue size, warnings,
errors, per-job summaries. The `scheduler` engine separately emits
`publish_schedule` (`PUBLISH_SCHEDULE_ENTRY_FIELDS`, timezone-aware).

Platform adapters implement `PublishingProvider`
(`providers/publishing_provider.py`) and register in
`providers/publishing/` — constraints, metadata formatting, validation,
provider-specific retry rules, publish. Agent 7 never mutates
`render_package` (Agent 6) or the `publishing_packages` handover key
(Agent 8). Accounts are placeholder-only (`PUBLISHING_ACCOUNT_FIELDS`) —
no real credentials are stored.

---

## 8. analytics_package + learning_metadata (Agent 9) — `services/analytics/`, `services/learning/`

The Analytics & Continuous Learning Engine (`analytics` + `learning`)
closes the loop after publishing. Field tuples in
`services/analytics/models.py` and `services/learning/models.py` are the
testable contract; all output is JSON-safe dicts, additive-only from 1.0.

**AnalyticsRecord** (`ANALYTICS_RECORD_FIELDS`, v1.0) — one structured
record per published item × platform, persisted append-only in
`data/analytics/records.json`, deduplicated on the `analytics_ref` issued
by Agent 7's PublishingJob:

| Field group | Fields |
|---|---|
| identity | `record_id`, `record_version`, `analytics_ref`, `project_id`, `brand_id`, `channel_id`, `platform`, `post_id`, `post_url` |
| attribution | `topic`, `niche`, `title`, `hook`, `keywords`, `psychology_strategy`, `psychology_score`, `virality_score`, `attention_score`, `quality_score`, `script_version`, `thumbnail_version`, `voice_version`, `render_version`, `video_length_sec`, `posting_time`, `published_at` |
| experimentation | `experiment_id`, `variant_id` |
| outcome | `metrics` (`ANALYTICS_METRIC_FIELDS`: views, watch_time_sec, average_view_duration_sec, audience_retention, ctr, likes, comments, shares, saves, subscriber_growth, followers_gained, rpm/cpm placeholders), `metrics_status`, `metrics_source`, `collected_at` |

**ContentPackage `analytics_package` slot** (`ANALYTICS_PACKAGE_FIELDS`):
`engine_version`, `status` (collected | pending | skipped), `records`,
aggregate `metrics`, `performance_score` (0-100 composite), `collected_at`.

**ContentPackage `learning_metadata` slot** (`LEARNING_METADATA_FIELDS`):
`engine_version`, `status`, `signals` (insights touching this item),
`recommendations`, `knowledge_size`, `confidence`, `generated_at`.

**Context keys** (additive): `analytics_summary` + `analytics_records`
(analytics stage output), `learning_report` + `learning_recommendations`
(learning stage output — recommendations routed per `TARGET_ENGINES`:
psychology, script_generation, visual_intelligence, voice_audio,
seo_optimization, publishing, trend_discovery).

**Insights & recommendations** (`INSIGHT_FIELDS` /
`RECOMMENDATION_FIELDS`) each carry `confidence` (0-100 from sample size ×
consistency) and `evidence` (samples, average vs baseline score, lift).
Long-term memory entries (`MEMORY_ENTRY_FIELDS`,
`data/analytics/memory.json`) and experiments (`EXPERIMENT_FIELDS`,
`data/analytics/experiments.json`) are append-only — historical knowledge
is never overwritten. Performance reports use
`PERFORMANCE_REPORT_FIELDS` (daily | weekly | monthly).

Platform metric backends implement `AnalyticsProvider`
(`providers/analytics_provider.py`) and register per platform in
`providers/analytics/` (deterministic mock serves every platform today).
Agent 9 writes ONLY the `analytics_package` / `learning_metadata` slots and
its own context keys; render/seo/publishing slots are read, never mutated.
Feedback reaches upstream engines through `OrchestratorHook` (kinds
`analytics` / `learning`) and the guidance adapters — never engine-to-engine
calls.

---

## 9. Change protocol

1. Appending a ContentPackage field: add to the dataclass **and**
   `PRODUCTION_PACKAGE_FIELDS`, with a default; get Agent 1 review.
2. New context keys: prefix with your domain if collision is possible
   (e.g. `seo_optimization_report`).
3. Never write to another agent's package slot.
4. Anything in this file changes only with Agent 1 review.
