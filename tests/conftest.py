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


@pytest.fixture(scope="session", autouse=True)
def isolated_publishing_queue(tmp_path_factory):
    """The full pipeline now runs the publish stage, which persists jobs —
    point the default queue directory at a temp dir for the whole session
    so tests never write to the real data/publishing_queue store."""
    import services.publishing.queue as publishing_queue

    original = publishing_queue._DEFAULT_DIR
    publishing_queue._DEFAULT_DIR = str(tmp_path_factory.mktemp("publishing_queue"))
    yield
    publishing_queue._DEFAULT_DIR = original


@pytest.fixture(scope="session", autouse=True)
def isolated_analytics_data(tmp_path_factory):
    """Agent 9's analytics/learning stages persist records, memory, and
    experiments (data/analytics) and mirror performance rows into the
    Knowledge Base — point both at temp dirs for the whole session so
    tests never write to the real data/ stores."""
    import services.analytics.store as analytics_store
    import services.knowledge as knowledge

    original_dir = analytics_store._DEFAULT_DIR
    original_kb = knowledge._kb
    analytics_store._DEFAULT_DIR = str(tmp_path_factory.mktemp("analytics"))
    knowledge._kb = knowledge.KnowledgeBase(str(tmp_path_factory.mktemp("knowledge")))
    yield
    analytics_store._DEFAULT_DIR = original_dir
    knowledge._kb = original_kb


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
