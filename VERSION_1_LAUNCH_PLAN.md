# Generational Version 1 Launch Plan

**Status:** First real-world deployment  
**Architecture:** Frozen  
**Objective:** Publish real content safely and collect high-quality data for Version 2  
**Not the objective:** Improving internal scores or building new engines

Related:
- Live checklist: `LAUNCH_CHECKLIST.md` (`python scripts/run_v1_launch_checklist.py`)
- Ops runbook: `VERSION_1_OPERATIONS_MANUAL.md`
- Intelligence: `PUBLISHING_INTELLIGENCE.md`
- Local export: `LOCAL_EXECUTION.md`
- Prior audit: `LAUNCH_READINESS_AUDIT.md` (91.6 — prediction accuracy needs real publish data)

---

## PHASE 1 — Launch checklist

Run verification:

```bash
python scripts/run_v1_launch_checklist.py
```

| Area | What “ready” means | Where it lives |
|------|--------------------|----------------|
| Production pipeline | Ops + pipeline orchestrators run end-to-end | `services/production_operations`, `services/production_pipeline` |
| Export pipeline | ffmpeg present; local render → Desktop media library | `LOCAL_EXECUTION.md`, `scripts/run_local_render_job.py` |
| Publishing packages | MP4, thumbnail plan, SEO title/desc, tags, keywords, hashtags, category, publish time, audience, upload checklist | `services/publishing_intelligence/pipeline.py` |
| Thumbnail generation | Thumbnail concepts / plans generated | `services/visual/thumbnails.py` + SEO package |
| SEO generation | Titles, descriptions, keywords, hashtags | `services.seo.package.optimize_content` |
| Analytics recording | Predicted + actual metrics persist | `data/analytics/intelligence_records.json` |
| Error recovery | Stage retry / repair / fallback / continue | `services/production_operations/resilience.py` |
| Logging | Structured `log_event` | `core/log.py` |
| Configuration | `.env` from example; local-only execution | `.env.example`, `LOCAL_EXECUTION.md` |
| API keys | `OPENAI_API_KEY` required to leave Demo Mode | project-root `.env` |
| Publish credentials | YouTube API / OAuth for Shorts upload | `YOUTUBE_*` in `.env` |

### Credentials required to publish (Shorts-first)

| Priority | Variable | Purpose |
|----------|----------|---------|
| Required | `OPENAI_API_KEY` | Exit Demo Mode; script/narration path |
| Required for YouTube upload | `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN` (and/or access token) | Upload + channel binding |
| Helpful | `YOUTUBE_API_KEY` | Analytics / catalog reads |
| Optional | `ELEVENLABS_API_KEY` | Higher-end voice |
| Deferred | TikTok / Instagram / Facebook / X tokens | Week 3+ only if Shorts loop is stable |

Never commit `.env`. Restart Streamlit after credential changes (`streamlit run app.py`).

### Publish package contents (every finished video)

Final MP4 · Thumbnail plan · SEO title · SEO description · Platform tags · Keywords · Hashtags · Category · Suggested publish time · Suggested audience · Upload checklist — for YouTube Shorts (primary), with packages also generated for TikTok, Instagram Reels, Facebook Reels, X, and long-form YouTube (deferred upload).

---

## PHASE 2 — First publishing campaign (intentionally small)

### Initial platforms

| Order | Platform | Role |
|-------|----------|------|
| 1 | **YouTube Shorts only** | Sole public surface for Days 1–14 |
| 2 | TikTok (optional, Week 3) | Only after ≥10 Shorts uploaded with analytics |
| — | Instagram / Facebook / X / long-form | **Deferred** — packages stay ready; do not upload yet |

Rationale: one analytics source, one credential set, one retention curve to calibrate.

### Initial content categories (2 channels worth of topics, 1 brand voice)

Pick **two** niches max for month one (proven in validation suite):

1. **Nature / biology** — documentary-curious audience  
2. **Psychology / everyday science** — short explainers  

Do **not** launch AI, finance, or medicine in week 1 (higher claim / compliance / novelty risk).

### Volume & frequency

| Setting | Value |
|---------|-------|
| Videos per day | **1** max |
| Videos per week | **3–5** |
| Length | Shorts 35–55s |
| Concurrent WIP | ≤2 productions in-flight |

### Best publishing times (US local; from SEO window tables)

| Platform | Prefer |
|----------|--------|
| YouTube Shorts | Friday 17–20 · Saturday 15–18 · Sunday 14–17 · Wednesday 16–19 |
| (Later) TikTok | Tuesday 18–21 · Thursday 19–22 |

Always prefer the `suggested_publish_time` from the publishing package when present.

### Risk management

1. **Kill switch:** Stop uploads after 2 consecutive export/upload failures; run ops diagnostics before resuming.  
2. **Content risk:** No medical advice, financial advice, or unverifiable claims in V1.  
3. **Credential risk:** Rotate tokens if upload auth fails twice; never paste secrets into tickets.  
4. **Quality gate:** Do not publish if validation overall &lt; 85 or upload checklist fails critical items (MP4, title, description).  
5. **Scope risk:** Do not add platforms mid-week because a single Short performed well.  
6. **Data integrity:** After every upload, record actuals into intelligence cycle within 48h when available (even partial: views, CTR).  
7. **Brand risk:** One consistent channel name, thumbnail layout family, and voice for first 30 days.

---

## PHASE 3 — Success metrics

### Track every published video

| Metric | Source |
|--------|--------|
| Upload success rate | Publishing queue / history (`data/publishing_queue/`) |
| Views | Platform analytics → intelligence `actual_metrics.views` |
| Average view duration | `actual_metrics.average_view_duration` |
| Audience retention | `actual_metrics.audience_retention` |
| CTR | `actual_metrics.ctr` |
| Likes / shares / comments | matching actual fields |
| Subscribers gained | `actual_metrics.subscribers` |

### Predicted vs actual (mandatory)

After analytics land, run:

```bash
python scripts/run_publishing_intelligence.py --topic "…"
# or paste actuals into the cycle API
```

Compare at minimum:

| Predicted | Actual |
|-----------|--------|
| Hook / retention expectation | Audience retention |
| Expected CTR | Actual CTR |
| Expected completion | Retention / AVD |
| Shareability score | Shares |

Store calibration in `data/analytics/prediction_calibration.json`.  
V1 success is **data quality**, not hitting vanity view targets.

### V1 success thresholds (30 days)

| Metric | Target |
|--------|--------|
| Upload success rate | ≥95% |
| Videos with analytics ingested | ≥80% of published |
| Intelligence records with actuals | ≥15 |
| Average prediction accuracy | ≥75% on CTR **or** completion |
| Critical pipeline failures | 0 unresolved week-over-week |
| Platforms used | 1 (YouTube Shorts) unless explicitly expanded |

Vanity (not gates): absolute views may vary; do not chase viral outliers by changing niches mid-campaign.

---

## PHASE 4 — Operations Manual

See **[VERSION_1_OPERATIONS_MANUAL.md](VERSION_1_OPERATIONS_MANUAL.md)** for:

- Daily / weekly / monthly workflows  
- Backup & recovery  
- Monitoring & analytics review  

---

## PHASE 5 — 30-day launch roadmap

### Week 1 — Controlled testing

| Day focus | Actions |
|-----------|---------|
| Day 1 | Pass `run_v1_launch_checklist.py`; confirm `.env` YouTube + OpenAI |
| Day 2–3 | Produce 2 Shorts; export locally; complete upload checklist; **do not** set public yet (or publish unlisted) |
| Day 4 | Publish **1** Short publicly at recommended window |
| Day 5–7 | Publish up to 2 more; fill intelligence records (even if views are low); freeze creative template |

**Exit Week 1:** ≥1 public upload + checklist 100% pass on published item + zero crash loops.

### Week 2 — Optimization

- Keep volume at 3–5 / week  
- Apply **one** highest-impact improvement from intelligence (`recommend_highest_impact_improvement`) per week — never stack changes  
- Tighten thumbnail + hook only if CTR or retention is the weak element  
- Confirm analytics collection for every upload  

**Exit Week 2:** ≥6 published Shorts · at least 3 with actual metrics · prediction calibration report exists.

### Week 3 — Scaling (careful)

- Raise to **1/day** only if Week 2 upload success ≥95% and ops recovery unused for ≥5 days  
- Still Shorts-only unless operator explicitly enables TikTok  
- Add second niche topic only if first niche has ≥8 published pieces  
- Keep WIP ≤2  

**Exit Week 3:** Steady cadence · creative library has early winners · no new infrastructure.

### Week 4 — Performance review

- Full calibration report + creative library snapshot  
- Compare predicted vs actual across all metrics in Phase 3  
- Decide: continue Shorts-only, add TikTok, or hold and deepen niches  
- Write short retrospective into `data/productions/_validation/launch_plan/WEEK4_REVIEW.md` (operator)  
- Re-run Launch Readiness Audit; expectation: prediction_accuracy blocker clears once real actuals accumulate  

**Exit Week 4:** Clear go / hold for V1.1 cadence and V2 learning priorities.

---

## Operator quick-start (safe first publish)

```bash
# 1. Verify launch surface
python scripts/run_v1_launch_checklist.py

# 2. Produce locally (existing ops / studio path)
#    — finish MP4 under media library (LOCAL_EXECUTION.md)

# 3. Build packages + intelligence cycle
python scripts/run_publishing_intelligence.py --topic "Your topic" --mp4 /path/to/final.mp4 --audit

# 4. Follow upload_checklist for youtube_shorts only
# 5. After 24–48h, ingest actual metrics into intelligence cycle
```

---

## Mission success definition

Generational V1 is successfully launched when:

1. Real content publishes on a controlled channel cadence  
2. Exports and uploads are reliable (≥95% success)  
3. Every publish feeds analytics + prediction calibration  
4. Operators follow one improvement at a time  
5. The system is collecting trustworthy data for Version 2  

Architecture stays frozen. Features stay deferred. Outcomes stay measurable.
