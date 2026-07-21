# V1 Launch Executive Dashboard

**Generated:** 2026-07-14T04:59:50.843753+00:00
**Pilot size:** 25 / 25
**Success rate:** 0.0
**MP4 deliverable rate:** 0.0
**Avg production time (ms):** 15134.6
**Avg program score:** 85.7

## Quality distribution

- 90+: 0
- 80-89: 25
- 70-79: 0
- <70: 0

## Strongest categories

- physics: 85.8
- astronomy: 85.8
- artificial_intelligence: 85.8
- medicine: 85.6
- psychology: 85.6

## Weakest categories

- medicine: 85.6
- psychology: 85.6
- biology: 85.6
- physics: 85.8
- astronomy: 85.8

## Failure causes

- missing_mp4 (n=25)
- animation unavailable — continued (n=25)

## Top 5 improvements

### 1. [P0] Production pipeline completes without a playable MP4
- Evidence: deliverable_mp4_rate=0.0 over 25 pilot runs; missing_mp4 count=25
- Expected: Stabilize existing ffmpeg/studio export path so production mode materializes verified MP4s (no new renderer)
- Impact: 90

### 2. [P0] Animation unavailable on most pilot runs
- Evidence: animation_unavailable n=25
- Expected: Cap cinematic/motion scores when animation skips; use existing motion graphics path honestly
- Impact: 40

### 3. [P1] Low average world continuity across validation runs
- Evidence: Mean score 65.0 over 25 productions
- Expected: Raising world_continuity toward 85+ via department tuning (not pipeline redesign)
- Impact: 25.0

### 4. [P1] Low average psychology effectiveness across validation runs
- Evidence: Mean score 70.0 over 25 productions
- Expected: Raising psychology_effectiveness toward 85+ via department tuning (not pipeline redesign)
- Impact: 20.0

### 5. [P1] Low average story flow across validation runs
- Evidence: Mean score 70.0 over 25 productions
- Expected: Raising story_flow toward 85+ via department tuning (not pipeline redesign)
- Impact: 20.0
