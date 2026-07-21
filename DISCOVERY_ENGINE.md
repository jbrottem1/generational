# Trend Intelligence & Discovery Engine

**Status:** Production-ready architecture (local-first)  
**Entry points:** `services.discovery.run_discovery` · `engines.discovery_engine.DiscoveryEngine` · `scripts/run_discovery_engine.py`

---

## Purpose

Transform Generational from a content generator into a **real-time content discovery engine**.

Nothing is scripted until opportunities are:

1. Discovered across modular providers  
2. Scored for educational trust (not clicks alone)  
3. Verified when breaking  
4. Packaged for multi-platform discovery  
5. Queued and continuously re-ranked  

---

## Architecture

```
Providers (trend_sources/*)
        ↓
TrendDiscoveryManager  (Agent 1)
        ↓
Discovery Scoring      (educational trust weights)
        ↓
Breaking News Gate     (multi-source verification)
        ↓
Series Detection       (topical authority)
        ↓
Platform Packaging     (distinct metadata / platform)
        ↓
Production Queue       (data/discovery/PRODUCTION_QUEUE.json)
```

### Modular providers

Drop a new file under `providers/trend_sources/` implementing `TrendSourceProvider`.  
No redesign required. Live APIs replace placeholder `discover()` bodies when credentials exist.

Current providers include Google Trends, YouTube trending/search, TikTok, Instagram, X, Reddit, RSS, News, Wikipedia trending, Google News, academic publications, and more.

---

## Topic scoring (Discovery weights)

| Factor | Weight |
|--------|--------|
| Educational value | 0.14 |
| Brand alignment | 0.12 |
| Factual confidence | 0.12 |
| Search demand | 0.11 |
| Growth velocity | 0.10 |
| Longevity | 0.10 |
| Audience engagement | 0.08 |
| Virality potential | 0.08 |
| Visual asset readiness | 0.06 |
| Geographic reach | 0.05 |
| Competition openness | 0.04 |

Clicks alone never win. Factual confidence is a hard discount on the total.

---

## Breaking News Mode

Before production on breaking candidates:

- Require ≥2 independent reputable source classes  
- Separate confirmed facts vs developing claims  
- Reject rumor language without corroboration  
- Defer when confidence &lt; 0.72  

Statuses: `verified` · `developing` · `deferred` · `rejected`

---

## Multi-platform optimization

Each queue item includes distinct packages for:

YouTube · YouTube Shorts · TikTok · Instagram · Facebook · Pinterest · X · LinkedIn

Fields: title, description, keywords, tags, hashtags, hook, CTA, thumbnail concept, length.

Identical metadata across platforms is forbidden by design.

---

## Series detection

Related opportunities auto-recommend:

- Multi-part series  
- Playlists  
- Long-form documentaries (when evergreen)  
- Companion Shorts  

---

## Real-time queue

Persisted at:

`data/discovery/PRODUCTION_QUEUE.json`

Each item includes topic, trend score, discovery score, audience, growth, competition, length, priority, confidence, verification, platform packages, series id.

---

## Local usage

```bash
./venv/bin/python scripts/run_discovery_engine.py
./venv/bin/python scripts/run_discovery_engine.py --subject "turtle evolution" --category science
```

Pipeline engine:

```python
from engines.registry import get_engine
get_engine("discovery").run({"command": "science education", "persist_discovery_queue": True})
```

---

## Philosophy

Build a trusted educational media company.

Prioritize:

- High audience interest  
- High factual confidence  
- Strong educational value  
- High production quality  
- Long-term discoverability  

---

## Adding a live API provider

1. Create `providers/trend_sources/my_source.py`  
2. Subclass `TrendSourceProvider`  
3. Implement `discover()` → `list[Trend]`  
4. Gate with `is_available()` on API keys  
5. Keep demo fallback when unavailable  

No engine rewrite. No registry edits.
