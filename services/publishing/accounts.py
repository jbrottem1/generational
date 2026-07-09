"""Account architecture — multi-brand / multi-channel publishing accounts.

INTERFACES ONLY. No real credentials are stored anywhere: every secret slot
is an explicit placeholder that a future `CredentialProvider` implementation
(secrets manager, OAuth flow, vault) fills at publish time. The engine and
manager only ever see account *references*, never tokens.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone

PUBLISHING_ACCOUNT_FIELDS = (
    "account_id",
    "brand_id",
    "channel_id",
    "platform",
    "handle",
    "credentials",     # placeholder — resolved by a CredentialProvider later
    "permissions",     # placeholder — granted scopes land here later
    "token",           # placeholder — never a real token in this system
    "status",
    "created_at",
)


def build_publishing_account(
    brand_id: str,
    channel_id: str,
    platform: str,
    handle: str = "",
) -> dict:
    """A placeholder PublishingAccount — structure now, secrets never."""
    return {
        "account_id": f"acct_{uuid.uuid4().hex[:10]}",
        "brand_id": brand_id,
        "channel_id": channel_id,
        "platform": platform,
        "handle": handle,
        "credentials": {"placeholder": True, "provider": "unset"},
        "permissions": {"placeholder": True, "scopes": []},
        "token": {"placeholder": True, "expires_at": None},
        "status": "unlinked",   # unlinked | linked | expired | revoked
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


class CredentialProvider(ABC):
    """Future contract for resolving real platform credentials.

    Implementations (OAuth flows, secret managers) plug in without any
    engine change — the manager asks for credentials by account reference
    at publish time and never persists what it receives.
    """

    key: str = ""

    @abstractmethod
    def resolve(self, account: dict) -> dict:
        """Return live credentials for an account (never stored)."""

    @abstractmethod
    def refresh(self, account: dict) -> dict:
        """Refresh an expired token; returns the updated account."""


class AccountRegistry:
    """In-memory registry of publishing accounts per brand/channel/platform.

    Persistence intentionally deferred: real account storage arrives with
    the credential provider work and must live behind a secrets boundary.
    """

    def __init__(self) -> None:
        self._accounts: "dict[str, dict]" = {}

    def register(self, account: dict) -> dict:
        self._accounts[account["account_id"]] = account
        return account

    def get(self, account_id: str) -> "dict | None":
        return self._accounts.get(account_id)

    def find(
        self,
        brand_id: str = "",
        channel_id: str = "",
        platform: str = "",
    ) -> "list[dict]":
        matches = list(self._accounts.values())
        if brand_id:
            matches = [a for a in matches if a.get("brand_id") == brand_id]
        if channel_id:
            matches = [a for a in matches if a.get("channel_id") == channel_id]
        if platform:
            matches = [a for a in matches if a.get("platform") == platform]
        return matches

    def account_for(self, brand_id: str, channel_id: str, platform: str) -> dict:
        """The matching account, or a fresh placeholder if none is linked."""
        matches = self.find(brand_id=brand_id, channel_id=channel_id, platform=platform)
        if matches:
            return matches[0]
        return self.register(build_publishing_account(brand_id, channel_id, platform))


_registry = AccountRegistry()


def get_account_registry() -> AccountRegistry:
    return _registry
