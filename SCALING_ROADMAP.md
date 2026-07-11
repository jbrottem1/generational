# Scaling Roadmap

## Current stage: **RC2 — True Motion Active**

The platform produces verified educator Shorts with animation QC, educational review, and multidimensional quality scoring. Full orchestrator pipeline runs in demo/stub modes for several engines. Live publish blocked on YouTube OAuth.

## Hierarchy (implemented)

```
Organization → Brand → Channel → Platform Account → Series → Project → Asset → Publication
```

Models in `services/organization/hierarchy.py`. Existing `ChannelManager` (`services/channels.py`) remains backward compatible.

## Multi-account readiness: **35%**

| Capability | Status |
|------------|--------|
| Per-channel identity | Partial (`ChannelManager`) |
| Credential isolation | **Not production-ready** (local JSON) |
| Brand guidelines per account | Schema only |
| Publish target validation | `validate_isolation()` helper |
| Rate limits / queues | Workflow retry policy only |

## Multi-platform readiness: **45%**

| Platform | Status |
|----------|--------|
| YouTube Shorts | Dry-run + packaging ready |
| Instagram/TikTok/etc. | Registered, mock publish |
| Platform-specific exports | ffmpeg assembler supports Shorts format |
| OAuth | **Blocker** for YouTube |

## Infrastructure requirements (next releases)

### Release 1.0.0 (GA)

- Fix 10 remaining test failures
- YouTube OAuth + one live publish smoke
- Wire QualityReport + EducationalReview into default export gate
- Engine registry alignment for animation/true-motion

### Release 1.1.0 (Scale prep)

- Job queue worker (Redis/SQLite) separate from Streamlit
- Secrets manager for platform credentials
- Repetition Booster on script/voice/image stages
- Storage retention policy for `data/media/`

### Release 2.0.0 (Multi-brand)

- Postgres for org/brand/channel/project
- Per-account budget limits (schema exists on Brand)
- Publishing scheduler with rate-limit backoff
- Analytics feedback into SEO ranking (evidence-based, not fake scores)

## Cost controls (designed, not billing)

- Provider Runtime cost logging per request
- Workflow `budget_usd` in `WorkflowConfig`
- Repetition Booster reuse metrics in `data/repetition_booster/registry.json`
- Benchmark TTS: ~6 segments × $0.015 ≈ $0.09 per 25s video

## Future opportunities

- Series arcs with running questions (schema on `Series`)
- Premium sound identity per brand
- Long-form via Agent 23 autonomous executor
- Human creator handoff mode in Studio UI
