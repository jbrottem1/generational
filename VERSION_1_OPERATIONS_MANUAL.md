# Generational Version 1 — Operations Manual

Operational runbook for the first public deployment. Architecture is frozen. Prefer existing CLIs and Studio surfaces.

Companion: `VERSION_1_LAUNCH_PLAN.md`

---

## Daily workflow

**Goal:** Ship at most one high-quality Short and record state.

1. **Health (5 min)**  
   - Confirm ffmpeg available  
   - `python scripts/run_v1_launch_checklist.py` if credentials or env changed  
   - Glance Studio / ops dashboard for failed jobs  

2. **Produce (30–90 min)**  
   - Choose topic inside the two V1 niches (nature/biology or psychology/everyday science)  
   - Run existing Studio Ops / production path (do not invent new pipelines)  
   - Export final MP4 to local media library (`LOCAL_EXECUTION.md`)  

3. **Package (5–10 min)**  
   ```bash
   python scripts/run_publishing_intelligence.py \
     --topic "Exact topic" \
     --mp4 "/path/to/final.mp4"
   ```  
   - Open the cycle JSON under `data/analytics/intelligence_cycles/`  
   - Use **youtube_shorts** package only  
   - Walk `upload_checklist` item by item  

4. **Publish (5–10 min)**  
   - Upload at package `suggested_publish_time` (or next YouTube window)  
   - Confirm job recorded in publishing queue/history when using in-app publish  

5. **Log (2 min)**  
   - Note production_id, publish time, package path in ops notes or ticket  
   - Do **not** change creative system mid-day  

6. **Stop rule**  
   - Two consecutive failures → stop publishing; run recovery (below)

---

## Weekly workflow

**Cadence:** 3–5 Shorts / week (Week 1–2). 1/day only if Week 2 gates pass.

| Day | Focus |
|-----|--------|
| Mon | Queue topics for the week (≤5). Confirm credentials. |
| Tue–Fri | Produce + publish within daily cap. |
| Fri PM | Pull mid-week metrics for anything &gt;48h old into intelligence. |
| Sun | Apply **one** improvement only from intelligence recommendation. Freeze all other knobs. |

Weekly checklist:

- [ ] Upload success rate reviewed  
- [ ] Every public video has an intelligence record  
- [ ] Actual metrics backfilled where available  
- [ ] Calibration report regenerated  
- [ ] Creative library updated (`run_intelligence_cycle` does this)  
- [ ] Highest-impact improvement noted for next week  
- [ ] No platform expansion unless planned in launch plan  

Commands:

```bash
python scripts/run_publishing_intelligence.py --seed-demo-actuals  # NEVER for real review
python scripts/run_publishing_intelligence.py --topic "…"         # real cycle
python scripts/run_launch_readiness_audit.py
```

---

## Monthly review process

At end of each 30-day block (first one = Week 4 of launch plan):

1. Export calibration: `data/analytics/prediction_calibration.json`  
2. Export creative library winners: `data/analytics/creative_knowledge_library.json`  
3. Studio intelligence board: `data/analytics/STUDIO_INTELLIGENCE_DASHBOARD.json`  
4. Compare Phase 3 metrics vs targets in `VERSION_1_LAUNCH_PLAN.md`  
5. Decide hold / continue / expand platform  
6. Write `data/productions/_validation/launch_plan/MONTHLY_REVIEW_YYYYMM.md` with:  
   - Videos published  
   - Upload success rate  
   - Top / bottom performers  
   - Prediction accuracy  
   - Single priority for next month  

Do not start V2 features in the monthly review. Capture learning requests as a prioritized list only.

---

## Backup procedures

| What | Location | Suggested backup |
|------|----------|------------------|
| Credentials | `.env` (never in git) | Secure password manager / encrypted disk copy |
| Productions | `data/generational_os/productions/`, `data/productions/` | Weekly zip of manifests + validation reports |
| Analytics | `data/analytics/` | Daily copy while launching (intelligence_records, calibration, priors, creative library) |
| Exports | `~/Desktop/AI Start-Up/Videos/` | Time Machine / external drive |
| Publish audit | `data/publishing_queue/` | Include in weekly analytics backup |

Operator steps (weekly):

```bash
# Example — adjust destination
ts=$(date -u +%Y%m%d)
mkdir -p ~/Backups/generational/$ts
cp -R data/analytics ~/Backups/generational/$ts/
cp -R data/publishing_queue ~/Backups/generational/$ts/
# Copy .env separately via secure channel — do not email plaintext
```

---

## Recovery procedures

### Production / stage failure

1. Open ops status under `data/productions/_ops/`  
2. Ops is designed to **retry → repair → fallback → continue** (`services/production_operations/resilience.py`) — do not kill the whole run unless stuck  
3. Re-run the failed stage via Studio Ops if status shows aborted manually  
4. If export failed: verify ffmpeg (`ffmpeg -version`), disk space, narration MP3 presence  

### Upload / credential failure

1. Confirm tokens present (checklist script; secrets never printed)  
2. Refresh YouTube OAuth tokens; update `.env`; restart app  
3. Do not switch to another platform as a workaround in Week 1–2  
4. Record failed attempt in publishing history for analytics honesty  

### Analytics / intelligence corruption

1. Restore latest `data/analytics/` backup  
2. Re-run cycle for recent topics to regenerate packages (idempotent enough for V1)  
3. If `intelligence_records.json` is truncated JSON, restore backup before appending  

### Kill switch

After 2 consecutive critical failures (export **or** upload):

1. Stop scheduled publishes  
2. Fix root cause  
3. Re-run `run_v1_launch_checklist.py`  
4. Publish **one** unlisted/private test before resuming public cadence  

---

## Monitoring process

| Signal | Where to look | Action if bad |
|--------|---------------|---------------|
| Jobs stuck | Studio executive dashboard / core jobs | Cancel + requeue; check logs |
| Ops health | `data/productions/_ops`, production_operations dashboard | Inspect stage retries |
| Publish queue | `data/publishing_queue/jobs.json` / history | Retry failed jobs manually |
| Export missing | Desktop media library path | Re-run local render job |
| Checklist regression | `LAUNCH_CHECKLIST.md` | Fix blockers before next public upload |
| Log noise | Application logs via `core.log` | Search `ops.`, `publishing.`, `analytics.` events |

Health rhythm:

- **Daily:** jobs + last export path  
- **Per upload:** checklist  
- **Weekly:** calibration + success rate  

---

## Analytics review

### Per video (48h after publish)

Ingest platform numbers into intelligence actuals:

- views, impressions, CTR  
- audience_retention, average_view_duration  
- likes, comments, shares, subscribers, watch_time  

Then run intelligence cycle so calibration + creative library update.

### Weekly analytics review (30–45 min)

1. Open Studio Intelligence Dashboard snapshot  
2. Note best / worst video  
3. Check prediction deltas (CTR, retention, shares)  
4. Accept **one** improvement for next week  
5. Ignore vanity spikes that would force niche change  

### What “good data” looks like for V2

- ≥15 videos with complete actual_metrics  
- Calibration report with per-metric MAE  
- Creative library winners backed by views/CTR not hunches  
- Documented weekly single-change experiments  

---

## Command cheat sheet

```bash
python scripts/run_v1_launch_checklist.py
python scripts/run_publishing_intelligence.py --topic "…" --mp4 "…" --audit
python scripts/run_launch_readiness_audit.py
python scripts/run_local_render_job.py --job RENDER_PACKAGE.json
python scripts/run_content_validation.py   # only if quality regression suspected
```

---

## Roles (minimal)

| Role | Responsibility |
|------|----------------|
| Operator | Daily produce/publish + checklist |
| Reviewer (can be same person) | Weekly metrics + one improvement |
| Owner | Kill switch + credential vault + monthly go/hold |

No new team tooling required for V1.
