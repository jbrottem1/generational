# Trend & Opportunity Intelligence

**Status:** Production  
**Service:** `services/trend_opportunity/`  
**CLI:** `scripts/trend_opportunity.py`

Executive intelligence layer that decides **what Generational should produce next**.

Does **not** replace Research Engine, Audience Intelligence, or Publishing Intelligence.  
Does **not** redesign the production pipeline or add a renderer.

---

## Pipeline position

```
Internet Signals
      ↓
Trend & Opportunity Intelligence
      ↓
Opportunity Ranking
      ↓
Research → Psychology → Script → Scene → World → Visual Asset Director
→ Cinematic → Voice → Renderer → CPL → Audience Intelligence → Publishing
```

Every production begins with a ranked, production-ready brief — no manual topic selection required.

---

## Data sources (modular interfaces)

Mission keys map onto existing `providers/trend_sources/*` adapters:

YouTube Trending · YouTube Search · Google Trends · Google News · Reddit · TikTok · Instagram · X · RSS

Future APIs plug in without changing this architecture (`list_provider_interfaces()`).

---

## Outputs

| Artifact | Path |
|----------|------|
| `TOP_OPPORTUNITIES.json` | `data/trend_opportunity/reports/` |
| `OPPORTUNITY_REPORT.json` | same |
| `TREND_REPORT.md` | same |
| `PRODUCTION_BRIEF.md` | #1 brief |
| `CONTENT_CALENDAR.json` | same |
| `OPPORTUNITY_LIBRARY.db` | `data/trend_opportunity/OPPORTUNITY_LIBRARY.db` |

---

## Opportunity score (0–100)

Trend · Curiosity · Educational · Retention · Competition (openness) · Visual · Thumbnail · Platform · Revenue → **Overall Opportunity Score**

Validation rejects: oversaturated · weak education · low curiosity · poor visual · overproduced · low confidence · outside content policy.

---

## Automatic production brief

Feeds Research + Studio Ops with `manual_editing_required: false`:

topic · objective · audience · hook · research goals · world · narrator · style · visual/thumbnail direction · platform · duration · `command`

```bash
python scripts/trend_opportunity.py run --category science --top 25
python scripts/trend_opportunity.py selftest
python scripts/trend_opportunity.py handoff --brief-json path/to/brief.json
```

---

## Learning loop

After production, `record_actual_performance(...)` compares predicted vs actual CTR / retention / AVD / shares / comments / likes / subs / watch time and stores lessons in the Opportunity Library (feeds future scores).

---

## Compose-only integrations

Discovery Engine · Trend providers · Audience Intelligence (soft) · World Builder · Visual Asset Director styles · Production Operations `run_studio_ops` / enqueue

```bash
./venv/bin/python -m pytest tests/test_trend_opportunity.py -q
```
