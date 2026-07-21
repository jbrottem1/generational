# Production Validation Suite

Architecture V1 is feature-complete. This suite **produces real content** through the existing ops pipeline and scores publishing readiness.

## Inputs only

Every production starts with:

- Topic  
- Platform  
- Length  
- Style  
- Audience  
- Voice  

Everything else is automatic via `run_studio_ops`.

## Run

```bash
# Full 10-domain suite
python scripts/run_content_validation.py

# Subset
python scripts/run_content_validation.py --limit 3
python scripts/run_content_validation.py --domains biology physics nature
```

## Outputs

Under `data/productions/_validation/content_validation/`:

| Artifact | Purpose |
|----------|---------|
| `CONTENT_VALIDATION_SUITE.json` | Full evaluations + scores |
| `CONTENT_VALIDATION_REPORT.md` | Human summary |
| `IMPROVEMENT_ROADMAP.md` | Highest-impact content fixes |

Also writes root `IMPROVEMENT_ROADMAP.md`.

## Score dimensions

Hook, retention, visuals, animation, narration, audio mix, captions, educational accuracy, SEO, thumbnail, CTR, completion, shareability, overall.

Weaknesses are ranked by **impact × frequency**. The roadmap lists only the top fixes — no new engines or architecture.
