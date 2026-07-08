"""Shared pytest fixtures.

Tests run against isolated tmp directories — they never touch the real
data/ folder.
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.jobs import JobQueue  # noqa: E402
from core.storage.json_store import JsonProjectStore  # noqa: E402
from services.channels import ChannelManager  # noqa: E402
from services.knowledge import KnowledgeBase  # noqa: E402


@pytest.fixture
def project_store(tmp_path):
    return JsonProjectStore(directory=str(tmp_path / "projects"))


@pytest.fixture
def channel_manager(tmp_path):
    return ChannelManager(directory=str(tmp_path / "channels"))


@pytest.fixture
def knowledge_base(tmp_path):
    return KnowledgeBase(directory=str(tmp_path / "knowledge"))


@pytest.fixture
def job_queue():
    return JobQueue()
