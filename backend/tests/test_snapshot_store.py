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


def test_client_scoped_files_do_not_collide(tmp_path):
    store = SnapshotStore(tmp_path)
    store.put("2026-02", {"who": "mbc"}, client_id="mbc")
    store.put("2026-02", {"who": "acme"}, client_id="acme")
    assert store.get("2026-02", client_id="mbc") == {"who": "mbc"}
    assert store.get("2026-02", client_id="acme") == {"who": "acme"}


def test_legacy_clientless_file_still_resolves_for_default_client(tmp_path):
    # A snapshot written by the old layout (no client_id in the name).
    (tmp_path / "sisjuri_2026-02.json").write_text('{"legacy": true}', encoding="utf-8")
    store = SnapshotStore(tmp_path)
    assert store.get("2026-02") == {"legacy": True}
    assert store.has("2026-02")


def test_invalid_client_id_rejected(tmp_path):
    store = SnapshotStore(tmp_path)
    with pytest.raises(ValueError):
        store.put("2026-02", {}, client_id="../etc")


def test_recebimento_by_year_maps_stored_months(tmp_path):
    store = SnapshotStore(tmp_path)
    store.put("2026-01", {"revenue": {"recebimento_bruto": 279821.07}}, client_id="mbc")
    store.put("2026-03", {"revenue": {"recebimento_bruto": 612501.76}}, client_id="mbc")
    got = store.recebimento_by_year(2026, client_id="mbc")
    # Only stored months appear; a month with no file (Feb) is omitted.
    assert got == {1: pytest.approx(279821.07), 3: pytest.approx(612501.76)}


def test_recebimento_by_year_is_client_scoped(tmp_path):
    store = SnapshotStore(tmp_path)
    store.put("2026-01", {"revenue": {"recebimento_bruto": 100.0}}, client_id="mbc")
    store.put("2026-01", {"revenue": {"recebimento_bruto": 200.0}}, client_id="acme")
    assert store.recebimento_by_year(2026, client_id="mbc") == {1: pytest.approx(100.0)}
    assert store.recebimento_by_year(2026, client_id="acme") == {1: pytest.approx(200.0)}
