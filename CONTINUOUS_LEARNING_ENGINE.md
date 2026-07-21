# Continuous Learning & Self-Improvement Engine

**Status:** Production  
**Engines:** `continuous_learning` (pre-production consult) · `learning` (post-publish mining)  
**Service:** `services/learning/`

The permanent memory and optimization layer for the Generational AI Media Operating System.  
Every production is recorded. Every published video teaches the next one.

---

## Loop

```
continuous_learning (consult) → psychology → script → … → publish → analytics → learning
```

1. **Before creation** — search history, compare winners/losers, inject recommendations  
2. **After production** — permanently store production memory  
3. **After publish** — collect analytics (YouTube first)  
4. **Learn** — mine patterns, grow memory, expand knowledge graph, update experiments  

---

## Production memory

Every video stores topic, platform, length, script, all quality scores, thumbnail, timings, export size, pipeline, model/prompt versions → `data/analytics/productions.json` (append-only, never discarded).

---

## Self-Optimization API

```python
from services.learning import get_optimization_api

api = get_optimization_api()
api.for_script("infrared")       # best openings
api.for_psychology("infrared")   # curiosity patterns
api.for_seo("infrared")          # winning titles
api.for_visual("infrared")       # thumbnail / pacing
api.for_animation("infrared")    # camera movement
api.for_voice("infrared")        # narration style
api.for_discovery()              # niche opportunity
```

Psychology, Script, SEO, and Visual engines consult this before execution.

---

## Predictions (pre-export)

Expected views · CTR · watch time · retention · shares · revenue · subscribers · virality · confidence intervals.

---

## Knowledge graph

Topics · platforms · psychology · visual/voice/thumbnail styles · retention patterns → `data/analytics/knowledge_graph.json`

---

## A/B experiments

Hooks, thumbnails, voice, camera movement, pacing, caption style, intro/outro, and more via `ExperimentManager`.

---

## Dashboard

Studio → **Dashboard** → Continuous Learning panel (top topics, CTR, hooks, improvements, viral queue).

---

## CLI

```bash
./venv/bin/python scripts/verify_continuous_learning.py
./venv/bin/python -m pytest tests/test_continuous_learning.py -q
```
