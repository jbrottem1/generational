import pytest

from services.channels import ChannelStatus


def test_create_channel_defaults(channel_manager):
    channel = channel_manager.create_channel(
        "Mind Matters",
        "Psychology",
        brand_voice="calm, curious",
        platforms=["youtube", "tiktok"],
        posting_schedule={"youtube": "daily 18:00"},
    )
    assert channel["status"] == ChannelStatus.ACTIVE
    assert channel["metrics"]["videos_published"] == 0
    assert channel_manager.channel_count() == 1


def test_duplicate_channel_name_rejected(channel_manager):
    channel_manager.create_channel("Mind Matters", "Psychology")
    with pytest.raises(ValueError):
        channel_manager.create_channel("Mind Matters", "Finance")


def test_update_status_and_metrics(channel_manager):
    channel_manager.create_channel("Mind Matters", "Psychology")

    channel_manager.set_status("Mind Matters", ChannelStatus.PAUSED)
    assert channel_manager.get_channel("Mind Matters")["status"] == ChannelStatus.PAUSED

    channel = channel_manager.record_metrics("Mind Matters", total_views=1500, followers=80)
    assert channel["metrics"]["total_views"] == 1500
    assert channel["metrics"]["videos_published"] == 0  # untouched keys preserved


def test_list_channels_filters_by_status(channel_manager):
    channel_manager.create_channel("Active One", "Space")
    channel_manager.create_channel("Paused One", "Finance")
    channel_manager.set_status("Paused One", ChannelStatus.PAUSED)

    active = channel_manager.list_channels(status=ChannelStatus.ACTIVE)
    assert [c["name"] for c in active] == ["Active One"]


def test_delete_channel(channel_manager):
    channel_manager.create_channel("Temp", "Health")
    assert channel_manager.delete_channel("Temp") is True
    assert channel_manager.get_channel("Temp") is None


def test_update_missing_channel_raises(channel_manager):
    with pytest.raises(ValueError):
        channel_manager.update_channel("Ghost", niche="Space")
