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

## 5. Change protocol

1. Appending a ContentPackage field: add to the dataclass **and**
   `PRODUCTION_PACKAGE_FIELDS`, with a default; get Agent 1 review.
2. New context keys: prefix with your domain if collision is possible
   (e.g. `seo_optimization_report`).
3. Never write to another agent's package slot.
4. Anything in this file changes only with Agent 1 review.
