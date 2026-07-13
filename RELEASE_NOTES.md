# Release Notes — System Audit & Scale Prep

**Date:** 2026-07-11  
**Branch:** `release/1.0.0-rc2` (audit changes pending commit)

## Features improved

- **Agent coordination:** `AgentTask` shared contract for delegation and verification
- **Repetition Booster:** Asset fingerprint registry with reuse tracking and downstream invalidation
- **Quality scoring:** 15-dimension `QualityReport` with hard-fail conditions
- **Educational Director:** Pre-production teaching review gate
- **Multi-account models:** Organization hierarchy dataclasses + isolation validator
- **Full system benchmark:** SEO → education → TTS → fluid motion → QC → export pipeline
- **Baseline audit:** `scripts/system_baseline_audit.py` → `data/audit/baseline_snapshot.json`

## Bugs fixed

- TTS synthesize treating empty path as valid file (IsADirectoryError on `.`)
- Project save/load mutating minimal idea dicts on rehydrate
- Cinematic fallback attempting subprocess with non-existent ffmpeg path
- SEO package circular import breaking standalone scripts

## Tests added

- `tests/test_agent_coordination.py` (2)
- `tests/test_repetition_booster.py` (3)
- `tests/test_quality_education.py` (4)

## Verified production

`~/Desktop/AI Start-up/videos/Test run 2 generational/Full_System_Benchmark_Mitochondria_Powerhouse.mp4`

- 25.4s, video+audio verified, quality 75.1, educational 84.8

## Known limitations

- 10 tests still fail (render engine sandbox, engine readiness metadata, asset_generation selection)
- `animation` engine registry still marked stub despite live performer path
- YouTube publish requires OAuth setup
- Channel credentials not in secrets manager
- Phoneme lip sync not yet implemented (energy-based sync only)

## Upgrade instructions

1. Pull latest on `release/1.0.0-rc2`
2. `./venv/bin/python -m pytest tests/ -q` — expect 890 passed, 10 failed
3. Run benchmark: `./venv/bin/python scripts/full_system_benchmark.py`
4. Capture baseline: `./venv/bin/python scripts/system_baseline_audit.py`

No database migrations. New data file: `data/repetition_booster/registry.json` (auto-created).
