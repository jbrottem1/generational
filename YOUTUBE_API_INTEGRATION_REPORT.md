# YouTube Data API v3 — Integration Report

**Date:** 2026-07-12  
**Mission:** Production-grade secret management + centralized YouTube provider  
**Status:** COMPLETE

---

## Confirmation: no secrets committed

| Check | Result |
|-------|--------|
| `.env` in `.gitignore` | ✓ (line 4) |
| `git check-ignore .env` | ✓ ignored |
| `.env` `YOUTUBE_API_KEY=` | ✓ empty placeholder (paste your key here) |
| `.env.example` | ✓ `YOUTUBE_API_KEY=` empty |
| Hardcoded keys in provider | ✓ none |
| Logs / exceptions | ✓ keys masked / redacted |

**You paste the real key locally into `.env` only. Never commit `.env`.**

---

## Environment variables required

```bash
# Project root .env  (already gitignored)
YOUTUBE_API_KEY=<PASTE_KEY_HERE>
```

Optional (existing publishing OAuth — separate from Data API key):

- `YOUTUBE_ACCESS_TOKEN`
- `YOUTUBE_REFRESH_TOKEN`
- `YOUTUBE_CLIENT_ID`
- `YOUTUBE_CLIENT_SECRET`

Credential resolution order (`services/provider_runtime/config.py`):

1. Runtime overrides  
2. Process environment  
3. Project-root `.env` (python-dotenv)  
4. Encrypted SecretManager (if configured)

---

## Files modified / added

### Added
- `services/providers/__init__.py`
- `services/providers/youtube_provider.py` — centralized Data API client
- `scripts/validate_youtube_api.py` — Agent 0 startup validation CLI
- `tests/test_youtube_provider.py`
- `YOUTUBE_API_INTEGRATION_REPORT.md` (this file)

### Updated
- `.env` / `.env.example` — `YOUTUBE_API_KEY=`
- `core/env.py` — core key list + YouTube startup validation lines
- `app.py` — Streamlit startup status (never prints the key)
- `providers/trend_sources/youtube_trending.py` — live API when key present
- `providers/trend_sources/youtube_search_trends.py` — live API when key present
- `services/discovery/engine.py` — YouTube opportunity enrichment

---

## Provider architecture

```
.env  →  get_credential("YOUTUBE_API_KEY")
              ↓
    YouTubeProvider (services/providers/youtube_provider.py)
              ↓
   ┌──────────┼──────────────┐
   ↓          ↓              ↓
Trend sources  Discovery    Agent 0 / app boot
(youtube_*)    Engine       validate_youtube_startup()
```

### Methods

| Method | Purpose |
|--------|---------|
| `search_videos()` | Keyword / query video search |
| `keyword_search()` | Alias for keyword search |
| `search_topics()` | Educational-biased topic search |
| `search_trending()` | `chart=mostPopular` |
| `category_search()` | Trending by category id |
| `search_channels()` | Channel search |
| `related_videos()` | Similarity via title search |
| `video_statistics()` | Views / likes / comments |
| `channel_statistics()` | Channel stats |
| `discover_opportunities()` | Discovery Engine helper |
| `validate()` | Auth + quota + trending probe |

Quota hooks: in-process `YouTubeQuotaTracker` (units used / remaining estimate).

---

## Agent 0 startup report

On app boot (`startup_credential_report`) and via:

```bash
./venv/bin/python scripts/validate_youtube_api.py
```

Expected when key is valid:

```
✓ YouTube API detected
✓ Authentication successful
✓ API quota accessible
✓ Trending search test passed
```

If the key is missing or invalid: clear error message, **no crash**, key never printed.

---

## How to rotate the API key

1. Create a new key in Google Cloud Console → APIs & Services → Credentials  
2. Enable **YouTube Data API v3** on the project  
3. Replace the value in project-root `.env`:
   ```bash
   YOUTUBE_API_KEY=new_key_here
   ```
4. Restrict the old key (or delete it) in Google Cloud  
5. Restart Streamlit / re-run `scripts/validate_youtube_api.py`  
6. Never commit `.env`; never paste keys into chat, tickets, or git

---

## Test results

```
tests/test_youtube_provider.py   → passed
tests/test_discovery_engine.py   → passed
(16 tests in combined run)
```

Unit tests use an injectable HTTP transport — **no live key required**.

After you paste your key:

```bash
./venv/bin/python scripts/validate_youtube_api.py
./venv/bin/python scripts/run_discovery_engine.py --subject "science education"
```

---

## Discovery Engine integration

When `YOUTUBE_API_KEY` is set, discovery automatically pulls:

- Trending videos (region-aware)
- Topic / educational search hits
- View counts, engagement rates
- Upload / velocity proxies from stats
- Normalized `Trend` objects for ranking + production queue

Without a key, trend providers fall back to deterministic demo signals (no crash).
