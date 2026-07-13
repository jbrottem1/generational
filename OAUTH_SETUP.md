# OAuth Setup

Publishing platforms use OAuth-style access/refresh tokens managed under
**Settings → OAuth**.

## Supported platforms

YouTube · TikTok · Instagram · Facebook · LinkedIn · X

## Stored fields (encrypted / env)

| Field | Example env |
|---|---|
| Client ID | `YOUTUBE_CLIENT_ID` |
| Client Secret | `YOUTUBE_CLIENT_SECRET` |
| Access Token | `YOUTUBE_ACCESS_TOKEN` |
| Refresh Token | `YOUTUBE_REFRESH_TOKEN` |
| Expiration | runtime config `oauth.<platform>.expires_at` |

## Operator steps

1. Create an app in the platform developer console.
2. Copy Client ID / Secret into Settings → OAuth (or `.env`).
3. Complete the platform consent flow externally; paste Access + Refresh tokens.
4. Click **Connect / Save**, then **Test connection**.
5. Use **Disconnect** to remove stored tokens.

## Notes

- Browser-based consent redirect UI is not embedded yet — tokens are pasted after an external consent flow.
- `OAuthTokenManager` can refresh tokens when client credentials + refresh token exist.
- Never commit `.env` or `secrets.enc.json`.
