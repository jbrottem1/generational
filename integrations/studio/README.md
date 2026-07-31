# Generational → Generational Studio client

**Additive integration only.** This folder does not merge repositories or overwrite `.env`.

## Purpose

Prefer Generational Studio’s shared Integration Center (LLM, voice, health) when the platform is running, instead of duplicating provider wiring.

## Client

Python client lives in the ecosystem control plane:

`C:\Users\JCBro\development\AI_Company\packages\studio-client-py\studio_client.py`

Copy or add that path to `PYTHONPATH` when calling from scripts:

```python
import sys
sys.path.insert(0, r"C:\Users\JCBro\development\AI_Company\packages\studio-client-py")
from studio_client import StudioClient

studio = StudioClient()
if studio.prefer_studio_providers():
    print("Studio healthy — prefer Studio adapters for shared providers")
else:
    print("Studio offline — use local provider_runtime connectors")
```

## Config (names only)

Use existing Generational `.env` keys. Optionally set (without removing local keys):

- `GENERATIONAL_STUDIO_URL=http://127.0.0.1:3000`
- `GENERATIONAL_BRIDGE_URL=http://127.0.0.1:8787`

## Reversibility

Delete this `integrations/studio` folder to remove the documentation pointer. No core app imports are required yet.
