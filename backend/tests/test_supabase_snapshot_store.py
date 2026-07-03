# backend/tests/test_supabase_snapshot_store.py
"""SupabaseSnapshotStore: client-scoped, jsonb-backed snapshot persistence.

Uses a tiny fake supabase client that records upserts and answers selects,
mirroring the shape of supabase-py's fluent query builder.
"""
import pytest

from app.sources.supabase_snapshot_store import SupabaseSnapshotStore


class _FakeResult:
    def __init__(self, data):
        self.data = data


class _FakeQuery:
    def __init__(self, table):
        self._table = table
        self._filters = {}

    def select(self, *_a, **_k):
        return self

    def eq(self, col, val):
        self._filters[col] = val
        return self

    def execute(self):
        rows = [
            r
            for r in self._table.rows
            if all(r.get(k) == v for k, v in self._filters.items())
        ]
        return _FakeResult(rows)


class _FakeTable:
    def __init__(self, name):
        self.name = name
        self.rows = []
        self.upserts = []

    def select(self, *a, **k):
        return _FakeQuery(self).select(*a, **k)

    def upsert(self, payload, on_conflict=None):
        self.upserts.append((payload, on_conflict))
        # emulate upsert semantics keyed by the primary key
        for row in payload:
            key = (row["client_id"], row["ano_mes"])
            self.rows = [
                r for r in self.rows if (r["client_id"], r["ano_mes"]) != key
            ]
            self.rows.append(dict(row))
        return _FakeExecutable(payload)


class _FakeExecutable:
    """Builder returned by upsert(); real supabase-py defers to .execute()."""

    def __init__(self, payload):
        self._payload = payload

    def execute(self):
        return _FakeResult(self._payload)


class _FakeClient:
    def __init__(self):
        self._tables = {}

    def table(self, name):
        return self._tables.setdefault(name, _FakeTable(name))


def test_put_then_get_roundtrip_scoped_by_client():
    store = SupabaseSnapshotStore(_FakeClient())
    store.put("2026-02", {"a": 1, "nome": "Ocupação"}, client_id="mbc")
    assert store.get("2026-02", client_id="mbc") == {"a": 1, "nome": "Ocupação"}
    assert store.has("2026-02", client_id="mbc")


def test_get_missing_returns_none():
    store = SupabaseSnapshotStore(_FakeClient())
    assert store.get("2026-01", client_id="mbc") is None
    assert not store.has("2026-01", client_id="mbc")


def test_two_clients_same_month_do_not_collide():
    store = SupabaseSnapshotStore(_FakeClient())
    store.put("2026-02", {"who": "mbc"}, client_id="mbc")
    store.put("2026-02", {"who": "acme"}, client_id="acme")
    assert store.get("2026-02", client_id="mbc") == {"who": "mbc"}
    assert store.get("2026-02", client_id="acme") == {"who": "acme"}


def test_put_overwrites_latest():
    store = SupabaseSnapshotStore(_FakeClient())
    store.put("2026-02", {"v": 1}, client_id="mbc")
    store.put("2026-02", {"v": 2}, client_id="mbc")
    assert store.get("2026-02", client_id="mbc") == {"v": 2}


def test_invalid_ano_mes_rejected():
    store = SupabaseSnapshotStore(_FakeClient())
    with pytest.raises(ValueError):
        store.put("nope", {}, client_id="mbc")
