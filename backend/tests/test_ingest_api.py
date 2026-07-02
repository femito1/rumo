# backend/tests/test_ingest_api.py
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.ingest_router import get_snapshot_store, get_ingest_token
from app.main import app
from app.sources.snapshot_store import SnapshotStore

TOKEN = "test-ingest-token"


@pytest.fixture
def client(tmp_path: Path):
    store = SnapshotStore(tmp_path)
    app.dependency_overrides[get_snapshot_store] = lambda: store
    app.dependency_overrides[get_ingest_token] = lambda: TOKEN
    yield TestClient(app), store
    app.dependency_overrides.clear()


def _snapshot(ano_mes="2026-02"):
    return {"meta": {"ano_mes": ano_mes}, "revenue": {"recebimento_bruto": 1.0}}


def test_ingest_requires_bearer_token(client):
    c, _ = client
    resp = c.post("/api/ingest", json=_snapshot())
    assert resp.status_code == 401


def test_ingest_rejects_wrong_token(client):
    c, _ = client
    resp = c.post(
        "/api/ingest", json=_snapshot(), headers={"Authorization": "Bearer nope"}
    )
    assert resp.status_code == 401


def test_ingest_stores_snapshot_by_ano_mes(client):
    c, store = client
    resp = c.post(
        "/api/ingest",
        json=_snapshot("2026-02"),
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert resp.status_code == 200
    assert resp.json()["ano_mes"] == "2026-02"
    assert store.get("2026-02")["revenue"]["recebimento_bruto"] == 1.0


def test_ingest_rejects_snapshot_without_ano_mes(client):
    c, _ = client
    resp = c.post(
        "/api/ingest",
        json={"revenue": {}},
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert resp.status_code == 422


def test_ingest_disabled_when_no_token_configured(client):
    c, _ = client
    app.dependency_overrides[get_ingest_token] = lambda: ""
    resp = c.post(
        "/api/ingest",
        json=_snapshot(),
        headers={"Authorization": "Bearer anything"},
    )
    assert resp.status_code == 503


def test_summary_requires_token(client):
    c, _ = client
    assert c.get("/api/ingest/2026-02/summary").status_code == 401


def test_summary_404_when_absent(client):
    c, _ = client
    resp = c.get(
        "/api/ingest/2026-02/summary", headers={"Authorization": f"Bearer {TOKEN}"}
    )
    assert resp.status_code == 404


def test_summary_reports_structure_after_ingest(client):
    c, store = client
    store.put(
        "2026-02",
        {
            "meta": {"ano_mes": "2026-02"},
            "revenue": {"recebimento_bruto": 319233.58, "faturamento_bruto": 10.0},
            "despesas_conta": [{"a": 1}, {"a": 2}],
            "prolabore": [{"s": "x"}],
        },
    )
    resp = c.get(
        "/api/ingest/2026-02/summary", headers={"Authorization": f"Bearer {TOKEN}"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["counts"]["despesas_conta"] == 2
    assert body["counts"]["prolabore"] == 1
    assert body["revenue"]["recebimento_bruto"] == 319233.58
