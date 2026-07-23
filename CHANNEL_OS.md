# Generational Multi-Channel Media Operating System

**Package:** `services/channel_os/`  
**CLI:** `scripts/channel_os.py`

Architecture is **frozen**. This is the business layer that lets one shared production pipeline operate many independent media brands.

Composes: existing `ChannelManager` · Voice Studio narrator profiles · Trend Opportunity handoff · Production Operations (`run_studio_ops`) · GenOS dashboard soft-link · Videos library organization.

---

## Channel Profiles

Each profile stores brand identity:

Brand Name · Description · Platforms · Target Audience · Topic Categories · Tone · Narrator Profile · Voice Profile · Visual Style · World Preferences · Thumbnail Style · Intro/Outro Rules · Upload Schedule · Hashtag Strategy · SEO Rules · Monetization Status · Publishing Status · Analytics History

Templates (configurable): Science Daily · AI Explained · Space Explorer · Human Biology · Medical Mysteries · Ancient History · Engineering Explained · Wildlife Earth · Psychology Lab · Future Technology

```bash
python scripts/channel_os.py templates
python scripts/channel_os.py install-samples
python scripts/channel_os.py list
```

---

## Content routing

Trend Intelligence → GenOS opportunity → **Channel OS route** → existing pipeline with profile constraints/context.

```bash
python scripts/channel_os.py route --topic "How Neural Networks Learn" --category artificial_intelligence
```

Soft-wired into `services/trend_opportunity/handoff.py` (`handoff_pipeline(..., route_channel=True)`).

---

## Produce for a channel

```bash
python scripts/channel_os.py produce science_daily --topic "Why Bees Are Disappearing" --category biology
python scripts/channel_os.py produce ai_explained --topic "How Tokens Turn Words Into Numbers" --dry-run
```

Publishing stays off unless you enable it separately via Publishing Intelligence.

---

## Content library layout

```
AI Start-UP/Videos/
└── {Channel Name}/
    └── {Category}/
        └── {Topic}/
            ├── Project/
            ├── Assets/
            ├── Audio/
            ├── Captions/
            ├── Thumbnail/
            ├── Export/
            ├── Reports/
            └── Analytics/
```

---

## Channel dashboard

```bash
python scripts/channel_os.py dashboard
```

Writes `CHANNEL_DASHBOARD.md` and `data/channel_os/CHANNEL_DASHBOARD.json`:

Active Channels · Videos Published · Videos Scheduled · Growth Metrics · Average Creative Score · Top Topics · Publishing Queue · Channel Health · Estimated Revenue (placeholder) · Recent Lessons

Also soft-linked on the GenOS operating dashboard as `channel_os`.

---

## Validation (3 sample brands)

```bash
python scripts/channel_os.py validate --execute
```

Runs one production each for Science Daily, AI Explained, and Space Explorer — verifies branding, voice, world preference injection, visual style, file tree, and reports.

```bash
./venv/bin/python -m pytest tests/test_channel_os.py -q
```
