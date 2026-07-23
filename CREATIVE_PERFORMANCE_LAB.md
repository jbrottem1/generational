# Creative Performance Lab

Evidence feedback loop for Generational creative decisions.

Extends — does **not** duplicate — Optimization Lab, Publishing Intelligence, analytics, Voice Studio, Creative Excellence, and production history.

## What it does

1. Define controlled experiments (one primary variable).
2. Generate variants A/B/C via existing narration + render tooling.
3. Pre-publish comparison (**predictions labeled as predictions**).
4. Human review (scores/notes/override stored separately).
5. Attach real platform video IDs after manual publish.
6. Ingest analytics (YouTube first; TikTok/IG interfaces stubbed).
7. Compare prediction vs reality with evidence gates.
8. Store validated learnings; offer optional pre-production guidance.

## Commands

```bash
# Create experiment definition only
python scripts/creative_performance_lab.py create --topic "Why Octopuses Have Three Hearts" --variable hook_structure

# Generate variants + comparison + human-review package (never publishes)
python scripts/creative_performance_lab.py run \
  --topic "Why Octopuses Have Three Hearts" \
  --platform youtube_shorts --length 45 --narrator professor --style educational

# Open human review JSON
python scripts/creative_performance_lab.py review cpl_XXXXXXXXXXXX

# Record selection (1–10 scores optional)
python scripts/creative_performance_lab.py select cpl_XXXXXXXXXXXX \
  --winner B --scores A:7,B:9,C:8 --override --decision approve

# After you publish manually, attach platform IDs
python scripts/creative_performance_lab.py attach cpl_XXXXXXXXXXXX --variant B --video-id YOUTUBE_VIDEO_ID

# Refresh analytics + evaluate
python scripts/creative_performance_lab.py analytics cpl_XXXXXXXXXXXX
python scripts/creative_performance_lab.py evaluate cpl_XXXXXXXXXXXX --promote

# View learnings / pre-production guidance / dashboard board
python scripts/creative_performance_lab.py learnings
python scripts/creative_performance_lab.py guide --topic "octopus biology"
python scripts/creative_performance_lab.py dashboard
```

## Data

`data/creative_performance_lab/experiments/{id}/` — EXPERIMENT.json, variant packages, COMPARISON_REPORT, HUMAN_REVIEW, PREDICTED_WINNER  
`data/creative_performance_lab/creative_performance_knowledge.json` — validated learnings only  

## Dashboard

Studio Executive Dashboard → **Creative Performance Lab** board (+ Publishing Intelligence board).

## Rules

- No automatic publishing from the lab.
- Internal scores ≠ audience proof.
- Knowledge writes require sufficient sample evidence.
- Architecture frozen — no new engines.
