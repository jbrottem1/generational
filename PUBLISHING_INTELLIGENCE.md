# Continuous Learning & Publishing Intelligence V2.0

Architecture remains **frozen**. This system adds thin orchestration over existing SEO, publishing, analytics, learning, QA, and studio dashboards.

## What it does

Every finished production can feed a learning cycle:

1. **Publishing packages** — Final MP4, thumbnail, SEO title/description, tags, keywords, hashtags, category, publish window, audience, upload checklist for Shorts, TikTok, Reels (IG/FB), X, and long-form YouTube.
2. **Analytics layer** — Attribution + predicted vs actual metrics (`data/analytics/intelligence_records.json`).
3. **Prediction calibration** — Accuracy reports + soft priors (`prediction_calibration.json`, `prediction_priors.json`).
4. **Creative Knowledge Library** — Winning creative combinations (`creative_knowledge_library.json`).
5. **One improvement** — Highest-impact next fix only (never optimize everything).
6. **Studio Intelligence Dashboard** — Executive board (`STUDIO_INTELLIGENCE_DASHBOARD.json`), also surfaced on the Studio executive dashboard.
7. **Business Intelligence** — Cost/speed/revenue **projections** until monetization actuals exist.

## Commands

```bash
# Full intelligence cycle (+ optional demo actuals + launch audit)
python scripts/run_publishing_intelligence.py --seed-demo-actuals --audit

# Launch Readiness Audit only
python scripts/run_launch_readiness_audit.py
```

## Python API

```python
from services.publishing_intelligence import (
    run_intelligence_cycle,
    build_complete_publish_packages,
    build_studio_intelligence_dashboard,
)
from services.launch_readiness import run_launch_readiness_audit

result = run_intelligence_cycle(
    {"topic": "Why bees dance", "platform": "youtube_shorts"},
    seed_demo_actuals=True,  # offline smoke only
)
audit = run_launch_readiness_audit()
```

## Rules

- No new engines; reuse existing providers and stores.
- Recommendations must improve quality, retention, speed, publishing efficiency, or prediction accuracy.
- Real analytics should replace `seed_demo_actuals` once videos are published.

## Artifacts

| Artifact | Path |
|----------|------|
| Intelligence records | `data/analytics/intelligence_records.json` |
| Calibration report | `data/analytics/prediction_calibration.json` |
| Prediction priors | `data/analytics/prediction_priors.json` |
| Creative library | `data/analytics/creative_knowledge_library.json` |
| Studio board | `data/analytics/STUDIO_INTELLIGENCE_DASHBOARD.json` |
| Cycle dumps | `data/analytics/intelligence_cycles/` |
| Launch audit | `LAUNCH_READINESS_AUDIT.md` |
