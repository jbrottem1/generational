# AGENTS.md

## Cursor Cloud specific instructions

Generational is a single-product Python/Streamlit app (no monorepo, no DB/Docker/CI). Everything runs in one process. See `README.md` for the canonical getting-started and `INTEGRATION_CHECKLIST.md` for the end-to-end demo flow.

### Environment
- Python 3.12. Dependencies are installed into a project-local virtualenv at `venv/` by the startup update script (`venv/bin/pip install -r requirements-dev.txt`, which also pulls in `requirements.txt`).
- Activate before running anything: `source venv/bin/activate` (or call binaries directly, e.g. `venv/bin/streamlit`, `venv/bin/pytest`).
- Creating the venv requires the system package `python3.12-venv` (installed once during environment setup; it persists in the VM snapshot, so the update script does not reinstall it).

### Running the app (dev)
- `streamlit run app.py --server.port 8501 --server.headless true` (default port 8501; health endpoint: `GET /_stcore/health` returns `ok`).
- Runs in **Demo Mode** with no API key — the full intelligence + media pipeline works using deterministic heuristics and demo data. Set `OPENAI_API_KEY` (via `.env`, copied from `.env.example`, or the Settings tab) to enable real AI generation.
- Persistence is local JSON under `data/` (auto-created, gitignored). No external services needed.

### Tests
- `python -m pytest` runs the suite (~80s, no server needed; `tests/conftest.py` isolates temp dirs).
- Known caveat: 4 tests in `tests/test_research_engine.py` fail because of a pre-existing application bug in `providers/wikipedia.py` (`niche` is referenced in `_live_search` but not passed in), which only triggers when the live Wikipedia API is reachable from the environment. This is unrelated to environment setup. At runtime the research manager (`services/research/manager.py`) catches provider exceptions and falls back gracefully, so the app is unaffected.
