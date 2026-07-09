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
`production_packages`, `pipeline_steps`.

Future engines declare which keys they consume/produce via
`input_contract` / `output_contract` on `ContractEngine`.

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

## 6. Change protocol

1. Appending a ContentPackage field: add to the dataclass **and**
   `PRODUCTION_PACKAGE_FIELDS`, with a default; get Agent 1 review.
2. New context keys: prefix with your domain if collision is possible
   (e.g. `seo_optimization_report`).
3. Never write to another agent's package slot.
4. Anything in this file changes only with Agent 1 review.
