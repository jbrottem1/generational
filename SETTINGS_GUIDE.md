# Settings Guide

The Settings tab is the operator control plane for Generational.

## Tabs

| Tab | Purpose |
|---|---|
| **General** | Model, voice, research, quality gate, app info |
| **Providers** | Catalog by category, enable/disable, connection tests, model defaults |
| **Publishing** | Publishing provider status + OAuth summary |
| **Analytics** | Analytics provider catalog + preferred provider |
| **API Keys** | Add / update / delete / import / validate (masked) |
| **OAuth** | Connect / reconnect / disconnect / test platform tokens |
| **Storage** | Data paths for projects, secrets, queues, analytics |
| **Costs** | Session spend, tokens, images, video/voice minutes, per-provider |
| **Logs** | Audit trail (no secrets) |
| **Health** | Live provider health, recover / blacklist |
| **Diagnostics** | System checks + credential inventory |

## Security rules

- Secrets are never re-displayed after save.
- Prefer `PROVIDER_SECRETS_PASSPHRASE` so keys encrypt to `data/provider_runtime/secrets.enc.json`.
- Environment variables always override when set.
- Audit actions are recorded without secret values.

## Model defaults

Roles: `default_text`, `reasoning`, `research`, `image`, `video`, `voice`, `music`,
`publishing`, `analytics`. Stored in provider runtime config (not secrets file).
