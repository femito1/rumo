# backend/tests/test_snapshot_store.py
import pytest

from app.sources.snapshot_store import SnapshotStore


def test_put_then_get_roundtrip(tmp_path):
    store = SnapshotStore(tmp_path)
    store.put("2026-02", {"a": 1, "nome": "Ocupação"})
    assert store.get("2026-02") == {"a": 1, "nome": "Ocupação"}
    assert store.has("2026-02")


def test_get_missing_returns_none(tmp_path):
    store = SnapshotStore(tmp_path)
    assert store.get("2026-01") is None
    assert not store.has("2026-01")


def test_put_overwrites_latest(tmp_path):
    store = SnapshotStore(tmp_path)
    store.put("2026-02", {"v": 1})
    store.put("2026-02", {"v": 2})
    assert store.get("2026-02") == {"v": 2}


def test_invalid_ano_mes_rejected(tmp_path):
    store = SnapshotStore(tmp_path)
    with pytest.raises(ValueError):
        store.put("nope", {})
