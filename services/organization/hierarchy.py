"""Organization → Brand → Channel → Platform Account → Series → Project hierarchy.

Prepares multi-account scale without cross-account credential leakage.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from typing import Any


def _uid(prefix: str) -> str:
    return f"{prefix}{uuid.uuid4().hex[:10]}"


@dataclass
class Organization:
    org_id: str = field(default_factory=lambda: _uid("org_"))
    name: str = ""
    brands: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Brand:
    brand_id: str = field(default_factory=lambda: _uid("brand_"))
    org_id: str = ""
    name: str = ""
    visual_profile: dict[str, Any] = field(default_factory=dict)
    voice_profile: dict[str, Any] = field(default_factory=dict)
    content_pillars: list[str] = field(default_factory=list)
    budget_daily_usd: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Channel:
    channel_id: str = field(default_factory=lambda: _uid("ch_"))
    brand_id: str = ""
    name: str = ""
    audience_profile: dict[str, Any] = field(default_factory=dict)
    posting_schedule: dict[str, Any] = field(default_factory=dict)
    approval_policy: str = "manual"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PlatformAccount:
    account_id: str = field(default_factory=lambda: _uid("acct_"))
    channel_id: str = ""
    platform: str = ""
    credential_ref: str = ""  # env key or secrets-manager ref — never raw tokens
    brand_guidelines_id: str = ""
    rate_limit: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Series:
    series_id: str = field(default_factory=lambda: _uid("series_"))
    channel_id: str = ""
    title: str = ""
    season: int = 1
    running_questions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProjectScope:
    project_id: str = field(default_factory=lambda: _uid("proj_"))
    series_id: str = ""
    account_id: str = ""
    brand_id: str = ""
    objective: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Publication:
    publication_id: str = field(default_factory=lambda: _uid("pub_"))
    project_id: str = ""
    account_id: str = ""
    platform: str = ""
    export_path: str = ""
    status: str = "draft"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_isolation(
    publication: Publication | dict[str, Any],
    account: PlatformAccount | dict[str, Any],
    asset_brand_id: str,
) -> dict[str, Any]:
    """Ensure publish target matches brand/account scope."""
    pub = publication if isinstance(publication, Publication) else Publication(**publication)
    acct = account if isinstance(account, PlatformAccount) else PlatformAccount(**account)
    errors: list[str] = []
    if pub.account_id and acct.account_id and pub.account_id != acct.account_id:
        errors.append("publication_account_mismatch")
    if asset_brand_id and acct.channel_id and not acct.channel_id:
        errors.append("missing_channel_scope")
    return {"ok": not errors, "errors": errors}
