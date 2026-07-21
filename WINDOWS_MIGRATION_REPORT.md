# Generational — Windows Migration Report

Prepared for cloning onto a Windows AI workstation without carrying generated media or secrets.

## Repository

| Field | Value |
| --- | --- |
| Repository name | `generational` |
| GitHub URL | https://github.com/jbrottem1/generational.git |
| Migration branch | `migration/windows-workstation` |
| Source branch (untouched tip) | `cursor/cloud-agent-1783814511168-rowab` @ `9edfcd377f841ff1d30f2b739ee6cdc33bb06a0d` |
| `main` | Untouched by this migration |
| Latest migration commit | *(filled after commit; see `git log -1` on this branch)* |

## Project overview

Generational is an AI-powered content operating system: research → scripting → assets → animation → render → audio → publishing → analytics. Primary UI is Streamlit (`app.py`). ProviderRuntime is the AI gateway.

## Languages used

- Python (primary)
- Streamlit UI
- Markdown documentation / specs
- JSON configuration, registries, character metadata
- Minor Node mock packages under `data/universe/productions/` (optional)

## Dependencies

Install from `requirements.txt`:

- streamlit
- openai
- python-dotenv
- plotly
- imageio-ffmpeg
- Pillow
- elevenlabs

Also install on the workstation:

- Python 3.11+ recommended
- ffmpeg (on PATH)
- Git
- Optional: Blender (on PATH) for animation runtime
- Optional: Node.js only if working with Dash mock packages

## Setup instructions (Windows)

```bat
git clone -b migration/windows-workstation https://github.com/jbrottem1/generational.git
cd generational
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
REM Edit .env and paste API keys (names below). Never commit .env.
streamlit run app.py
```

## Required software

1. Git for Windows
2. Python 3.11+ 
3. ffmpeg
4. Cursor / preferred IDE
5. Blender (optional, animation)
6. Internet access for provider APIs

## Environment variables required (names only)

Copy from `.env.example`. Recreate locally on Windows — values stay only in `.env`.

Core:

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GOOGLE_API_KEY`
- `XAI_API_KEY`
- `OLLAMA_HOST`
- `LOCAL_LLM_ENDPOINT`

Image / video:

- `BFL_API_KEY`
- `IDEOGRAM_API_KEY`
- `STABILITY_API_KEY`
- `RUNWAY_API_KEY`
- `PIKA_API_KEY`
- `KLING_API_KEY`
- `LUMA_API_KEY`
- `REPLICATE_API_TOKEN`
- `FAL_KEY`

Audio:

- `ELEVENLABS_API_KEY`
- `ELEVENLABS_DEFAULT_VOICE_ID`
- `ELEVENLABS_VOICE_FOUNDER`
- `ELEVENLABS_MODEL_ID`
- `ELEVENLABS_OUTPUT_FORMAT`
- `ELEVENLABS_REQUEST_TIMEOUT`
- `ELEVENLABS_MAX_RETRIES`
- `ELEVENLABS_ALLOW_FALLBACK`
- `MUSIC_PROVIDER_API_KEY`
- `MUSIC_PROVIDER_ENDPOINT`

Publishing:

- `YOUTUBE_API_KEY`
- `YOUTUBE_ACCESS_TOKEN`
- `YOUTUBE_REFRESH_TOKEN`
- `YOUTUBE_CLIENT_ID`
- `YOUTUBE_CLIENT_SECRET`
- `TIKTOK_ACCESS_TOKEN`
- `TIKTOK_REFRESH_TOKEN`
- `TIKTOK_CLIENT_KEY`
- `TIKTOK_CLIENT_SECRET`
- `INSTAGRAM_ACCESS_TOKEN`
- `INSTAGRAM_BUSINESS_ACCOUNT_ID`
- `FACEBOOK_ACCESS_TOKEN`
- `FACEBOOK_PAGE_ID`
- `X_ACCESS_TOKEN`
- `X_REFRESH_TOKEN`
- `X_CLIENT_ID`
- `X_CLIENT_SECRET`
- `LINKEDIN_ACCESS_TOKEN`
- `LINKEDIN_REFRESH_TOKEN`
- `LINKEDIN_CLIENT_ID`
- `LINKEDIN_CLIENT_SECRET`
- `LINKEDIN_AUTHOR_URN`

Local / optional:

- `COMFYUI_ENDPOINT`
- `LOCAL_DIFFUSION_ENDPOINT`
- `PROVIDER_CONFIG_PATH`
- `PROVIDER_SECRETS_PATH`
- `PROVIDER_SECRETS_PASSPHRASE`
- `REDDIT_USER_AGENT`

## Folders excluded from Git (do not expect them after clone)

These remain local on the Mac (or must be copied manually if needed):

- `.env` (secrets)
- `venv/` / `.venv/`
- `data/animation_runtime/` (frame sequences, Blender scenes, golden motion runs)
- `data/renders/`
- `data/media/`
- `data/provider_runtime/cache/`
- `data/voice_studio/comparisons/`
- `data/logs/`, `data/analytics/`, other runtime caches listed in `.gitignore`
- `*.mp4`, `*.mov`, `*.blend`, `*.blend1` (new media not added)
- Generated plates under `data/character_world_studio/packages/**/plates/`
- Experiment binary outputs under `data/creative_performance_lab/experiments/`
- Local SQLite `*.db` files

## Folders that must be copied manually (if needed on Windows)

Only if you need prior renders/assets immediately (not required to start coding):

1. Mac `.env` → Windows project-root `.env` (preferred: recreate from `.env.example`)
2. `data/animation_runtime/` (large; optional)
3. `data/studio_assets/**/RUNTIME/*.blend` and large character production blends (optional)
4. `data/renders/` and Desktop export library `~/Desktop/AI Start-UP/Videos/` (optional)
5. Any local SQLite libraries if you need prior metrics continuity

## What this migration commit includes

- All pending source-code changes under `core/`, `engines/`, `services/`, `providers/`, `ui/`, `scripts/`, `tests/`, `api/`, `app.py`
- Documentation (`*.md`) including this report
- Configuration (`.env.example`, `.gitignore`, `requirements.txt`, `pytest.ini`, `.streamlit/`)
- Reusable JSON/MD metadata (creative direction, character registries, world libraries, voice profile config)
- Small Reality catalog images under `data/reality/images/`

## Windows readiness notes

- Export paths currently assume macOS Desktop spellings (`AI Start-UP` / `AI Start-Up`). On Windows, create an equivalent folder or set paths via future `EXPORT_ROOT` work.
- Blender discovery prefers `/Applications/Blender.app/...` on macOS; on Windows install Blender and ensure `blender` is on PATH.
- Prefer cloning to a short path without spaces, e.g. `C:\dev\generational`.

## Recommended first steps on Windows

1. Clone `migration/windows-workstation` (command in handoff section of chat / below).
2. Create venv and `pip install -r requirements.txt`.
3. Copy `.env.example` → `.env` and fill keys.
4. Confirm `ffmpeg -version`.
5. Run `streamlit run app.py` and open Studio.
6. Run a small smoke test, e.g. `python scripts/foundation_v2_turtles.py --smoke` if available.
7. Do **not** merge to `main` until you intentionally review on Windows.

## Clone command

```bat
git clone -b migration/windows-workstation https://github.com/jbrottem1/generational.git
```
