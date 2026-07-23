# YouTube Search Intelligence

**Status:** Production  
**Provider key:** `youtube_search_intelligence` / trend adapter `youtube_search_trends`  
**Module:** `services/providers/youtube_search_intelligence.py`

Discovers what people are **actively watching** for each candidate topic — not a bare keyword search dump.

---

## Architecture

```
YOUTUBE_API_KEY
      │
      ▼
services/providers/youtube_provider.py     (auth, quota, HTTP)
      │
      ▼
services/providers/youtube_search_intelligence.py
  • search + video stats + channel sizes
  • parse duration / thumbnails / tags / category / language
  • VideoWatchSignal (structured JSON only)
  • market averages + UnifiedDiscoveryBrief
      │
      ├─► providers/trend_sources/youtube_search_trends.py → Trend
      │
      ▼
services/discovery/engine.py
  • cross-ref Google News / Google Trends / Reddit / Wikipedia / YouTube
  • unified discovery score on QueueItem
  • production_brief + script_handoff for Agent 3
```

**Rule:** Callers never see raw YouTube API JSON (`kind`, `etag`, `pageInfo`, …).

---

## Collected fields (per video)

| Field | Source |
|-------|--------|
| title, description, channel | `snippet` |
| publish date | `snippet.publishedAt` |
| view / like / comment counts | `statistics` |
| duration (seconds) | `contentDetails.duration` ISO-8601 → int |
| thumbnail | best of maxres→default |
| category | category ID → name map |
| tags | `snippet.tags` |
| language | `defaultAudioLanguage` / `defaultLanguage` |

---

## Scores (0–100)

| Score | Meaning |
|-------|---------|
| Popularity | Log-scaled views |
| Velocity | Views/day + engagement |
| Educational | Explainer / science cues + category |
| Evergreen | Guide / how-to longevity |
| Clickability | Title + thumbnail affordances |
| Trend Momentum | Recency × relative market performance |
| Thumbnail Quality | Resolution / presence |
| Competition | Crowding vs market average views |

**Market aggregates**

- Average View Count  
- Average Upload Frequency (per week)  
- Average Channel Size (subscribers)

---

## Unified Discovery Brief

Every topic report includes:

| Field | Use |
|-------|-----|
| `overall_opportunity_score` | Production attractiveness |
| `confidence` | Multi-source + signal quality |
| `reasoning` | Human-readable justification |
| `recommended_video_type` | `short` \| `long_form` \| `series` \| `live_update` |
| `estimated_audience` | Expected reach proxy |
| `expected_click_through_potential` | From clickability |
| `expected_watch_time_sec` | Type-normalized |
| `estimated_competition` | 0–1 |
| `unified_discovery_score` | Blend with Discovery Engine educational score |
| `target_platform` | `youtube_shorts` / `youtube_long` |
| `cross_reference` | Agreeing providers |

---

## Cross-reference

`agreeing_sources_for_topic` checks overlap with:

- Google News (`google_news`)
- Google Trends (`google_trends`)
- Reddit (`reddit_trends`)
- Wikipedia (`wikipedia_trending`)
- YouTube (`youtube_*`)

Agreement raises confidence and opportunity score.

---

## Agent 3 handoff

```python
from services.discovery import queue_item_to_script_context

ctx = queue_item_to_script_context(queue_item)
# ctx → ScriptGenerationEngine.run(ctx)
# keys: candidates, target_platform, research.opportunity_score, discovery_fed
```

`run_discovery()` also returns `script_handoff` for the top queue item automatically.

---

## Usage

```python
from services.providers import get_youtube_search_intelligence

intel = get_youtube_search_intelligence()
report = intel.analyze_topic("How cameras are made", category="science", limit=8)
print(report.to_dict())  # structured only
```

```bash
./venv/bin/python -m pytest tests/test_youtube_search_intelligence.py -q
./venv/bin/python scripts/verify_youtube_search_intelligence.py
```

---

## Future

- Retention curve estimates when Analytics API is connected  
- Competitor upload cadence forecasting  
- Automatic series arc from multi-part titles  
- Thumbnail OCR / face detection quality (optional)
