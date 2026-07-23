# Audience Intelligence System

**Status:** Production  
**Service:** `services/audience_intelligence/`  
**CLI:** `scripts/audience_intelligence.py`

Reusable intelligence layer that learns what keeps viewers watching. It advises existing production systems — it does **not** create engines, redesign the pipeline, or replace Psychology, Research, Publishing Intelligence, or Creative Performance Lab.

---

## What it does

1. **Topic enrichment** (existing) — Human Attention Score, psych drivers, engagement estimates, creative directives before Script Generation.
2. **Creative Brief** (pre-production) — hook, pacing, visual density, camera, narration, captions, thumbnail strategy, expectations, weak points.
3. **Creative memory** — searchable lessons with **evidence + confidence**.
4. **Post-production review** — evaluates craft signals, records **exactly one** highest-impact lesson.
5. **Analytics interfaces** — stub contracts for YouTube / TikTok / Instagram / A/B results (no live integrations required yet).

---

## Architecture (frozen boundaries)

```
Discovery / Psychology / Research
        │
        ▼
Audience Intelligence  ← enrich + brief + memory + post-review
        │  (guides)
        ▼
Script · Scene · World · Cinematic · Voice · Publishing · Creative Excellence / CPL
```

Soft ops hook: after Creative Excellence, `run_studio_ops` calls `review_production_audience` and stores the lesson path on the production report. Failure never blocks ops.

---

## Knowledge base

Store: `data/audience_intelligence/CREATIVE_MEMORY.json`  
Mirror: `data/audience_intelligence/PRODUCTION_LESSONS.json`

Categories: hook patterns · curiosity gaps · emotional triggers · visual pacing · camera movement · narration · thumbnails · captions · scene density · transitions · subject best practices · platform recommendations.

Every lesson includes `evidence[]` and `confidence` (0–1). Near-duplicate statements corroborate (confidence ↑) instead of duplicating rows.

Related (composed, not duplicated):

- Creative Performance Lab → `data/creative_performance_lab/creative_performance_knowledge.json`
- Publishing Intelligence → `data/analytics/creative_knowledge_library.json`

---

## Creative Brief (pre-production)

```bash
python scripts/audience_intelligence.py brief \
  --topic "Why Octopuses Have Three Hearts" \
  --niche biology \
  --platform youtube_shorts \
  --narrator professor
```

Output fields: `recommended_opening_hook`, `ideal_pacing`, `recommended_visual_density`, `suggested_camera_style`, `narration_recommendations`, `caption_recommendations`, `thumbnail_strategy`, `predicted_viewer_expectations`, `potential_weak_points`, `supporting_lessons`.

Attach (additive only):

```python
from services.audience_intelligence import build_creative_brief, attach_brief_to_candidate

brief = build_creative_brief(topic="...", niche="biology")
candidate = attach_brief_to_candidate(candidate, brief)
```

---

## Post-production review

```bash
python scripts/audience_intelligence.py review \
  --topic "Why Octopuses Have Three Hearts" \
  --niche biology \
  --production-id octopus_three_hearts_... \
  --ce-json path/to/CREATIVE_EXCELLENCE.json
```

Evaluates: hook · visual engagement · story clarity · audio · educational value · emotional impact · retention prediction · shareability.

Writes one lesson into creative memory and emits `AUDIENCE_INTELLIGENCE` summary JSON + Markdown under `data/audience_intelligence/reviews/`.

---

## Creative memory search

```bash
python scripts/audience_intelligence.py search "ocean biology hooks"
python scripts/audience_intelligence.py lessons
python scripts/audience_intelligence.py seed
python scripts/audience_intelligence.py interfaces
```

---

## Future analytics (interfaces only)

| Interface | Status |
|-----------|--------|
| YouTube Analytics | Stub; wraps existing provider if credentials present |
| TikTok Analytics | Stub |
| Instagram Insights | Stub |
| A/B test results | Local CPL learnings surface only |

Contract: `AudienceAnalyticsProvider` with `fetch_video_metrics` / `fetch_retention_curve`. Wire live platforms later without changing this architecture.

---

## Inputs consumed

Existing Generational productions · ops / production reports · Creative Excellence reviews · hook / retention / completion predictions · thumbnail evaluations · publishing reports · (future) platform analytics via interfaces.

---

## Docs

| Doc | Role |
|-----|------|
| `AUDIENCE_INTELLIGENCE.md` | This system guide |
| `CREATIVE_KNOWLEDGE_BASE.md` | Memory store + CPL bridge |
| `PRODUCTION_LESSONS.md` | Human-readable lesson log |

---

## Files

| Path | Role |
|------|------|
| `builder.py` / `scoring.py` / `models.py` / `adapters.py` | Topic enrichment (Agent 3 feed) |
| `memory.py` | Creative memory CRUD + search |
| `brief.py` | Pre-production Creative Brief |
| `post_review.py` | Post-production review + one lesson |
| `analytics_interfaces.py` | Future provider contracts |
| `engines/audience_intelligence.py` | Pipeline adapter (unchanged role) |
| `scripts/audience_intelligence.py` | CLI |

```bash
./venv/bin/python -m pytest tests/test_audience_intelligence.py -q
```
