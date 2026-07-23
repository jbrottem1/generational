# TOP 10 REMAINING FAILURES

Generated: `2026-07-14T12:45:03.547904+00:00`

## Observed in this validation batch

No publication-blocking failures in the validation batch.

## Systemic backlog (monitor)

1. **animation_engine_not_ready** — Animation registry ready=False — soft skip every run
2. **provider_image_tunnel_or_key** — OpenAI image / ElevenLabs often fail → fallbacks engaged
3. **ops_resume_full_rerun** — Resume flag still re-runs all stages
4. **timeline_render_package_ops_mismatch** — timeline/render_package still keyed off production_packages
5. **vad_approved_zero_when_providers_fail** — Visual Asset Director approved_count can be 0
6. **caption_burn_not_required** — Captions sidecars written; burn-in not mandated
7. **demo_voice_when_tts_fails** — Narration may be local demo bed if keys/network fail
8. **channel_publish_disabled** — Publishing intentionally off for reliability runs
9. **stage_skip_resume** — No durable stage checkpoint skip yet
10. **quality_score_vs_deliverable** — High creative scores can coexist with prior export gaps
