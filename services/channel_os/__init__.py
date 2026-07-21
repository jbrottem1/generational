"""Multi-Channel Media Operating System — business layer over frozen production stack."""

from __future__ import annotations

from services.channel_os.dashboard import build_channel_dashboard, write_channel_dashboard
from services.channel_os.production import install_sample_profiles, produce_for_channel, route_and_produce
from services.channel_os.profiles import CHANNEL_TEMPLATES, build_profile_from_template, list_template_ids
from services.channel_os.routing import route_opportunity
from services.channel_os.store import get_profile, list_profiles, save_profile

__all__ = [
    "CHANNEL_TEMPLATES",
    "build_channel_dashboard",
    "build_profile_from_template",
    "get_profile",
    "install_sample_profiles",
    "list_profiles",
    "list_template_ids",
    "produce_for_channel",
    "route_and_produce",
    "route_opportunity",
    "save_profile",
    "write_channel_dashboard",
]
