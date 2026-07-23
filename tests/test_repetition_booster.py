"""Tests for repetition booster."""

from services.repetition_booster import RepetitionBooster, fingerprint_inputs, should_regenerate


def test_fingerprint_stable():
    a = fingerprint_inputs({"text": "hello", "voice": "nova"})
    b = fingerprint_inputs({"voice": "nova", "text": "hello"})
    assert a == b


def test_should_not_regenerate_approved(tmp_path):
    reg_path = tmp_path / "registry.json"
    booster = RepetitionBooster(reg_path)
    fp = fingerprint_inputs({"scene": 1, "prompt": "cell membrane"})
    booster.record(fingerprint=fp, asset_type="image", uri="/tmp/a.png", approved=True)
    assert should_regenerate(fingerprint=fp, approved=True, registry=booster.load_registry()) is False
    assert should_regenerate(fingerprint=fp, force=True, registry=booster.load_registry()) is True


def test_invalidate_downstream(tmp_path):
    reg_path = tmp_path / "registry.json"
    booster = RepetitionBooster(reg_path)
    upstream = fingerprint_inputs({"script": "v1"})
    downstream = fingerprint_inputs({"script": "v1", "voice": "nova"})
    booster.record(fingerprint=upstream, asset_type="script", approved=True)
    booster.record(fingerprint=downstream, asset_type="voice", upstream=[upstream])
    stale = booster.invalidate_downstream(upstream)
    assert downstream in stale
    entry = booster.lookup(downstream)
    assert entry and entry.get("status") == "stale"
