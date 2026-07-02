# backend/tests/test_manual_api.py
import pytest
from fastapi.testclient import TestClient

from app.api import providers
from app.config import Settings
from app.main import app
from app.manual.repository import InMemoryManualActualsRepository
from tests.fakes import FakeRepository

TEST_SECRET = "test-secret"


@pytest.fixture
def manual_repo():
    return InMemoryManualActualsRepository()


@pytest.fixture
def client(manual_repo):
    repo = FakeRepository.seeded()
    app.dependency_overrides[providers.get_repo] = lambda: repo
    app.dependency_overrides[providers.get_manual_repo] = lambda: manual_repo
    app.dependency_overrides[providers.get_settings] = lambda: Settings(
        jwt_secret=TEST_SECRET, jwt_ttl_minutes=60, cors_origins=["*"],
        supabase_url="", supabase_service_key="", use_fake_repo=False,
    )
    yield TestClient(app)
    app.dependency_overrides.clear()


def _token(client, email, password):
    return client.post(
        "/api/auth/login", json={"email": email, "password": password}
    ).json()["access_token"]


def test_get_manual_returns_areas_and_lines(client):
    tok = _token(client, "financeiro@mbclaw.com.br", "mbc123")
    resp = client.get(
        "/api/clients/mbc/manual?ano_mes=2026-02",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["ano_mes"] == "2026-02"
    assert "Contencioso" in body["areas"]
    assert any(line["key"] == "recebimento" for line in body["lines"])
    assert body["entries"] == []


def test_put_then_get_roundtrips_manual(client):
    tok = _token(client, "financeiro@mbclaw.com.br", "mbc123")
    payload = {"entries": [{"area": "Contencioso", "line_key": "recebimento", "valor": 138600.13}]}
    put = client.put(
        "/api/clients/mbc/manual?ano_mes=2026-02",
        json=payload,
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert put.status_code == 200
    got = client.get(
        "/api/clients/mbc/manual?ano_mes=2026-02",
        headers={"Authorization": f"Bearer {tok}"},
    ).json()
    assert got["entries"] == [
        {"area": "Contencioso", "line_key": "recebimento", "valor": 138600.13}
    ]


def test_invalid_area_rejected(client):
    tok = _token(client, "admin@rumo.com.br", "admin123")
    resp = client.put(
        "/api/clients/mbc/manual?ano_mes=2026-02",
        json={"entries": [{"area": "Nope", "line_key": "recebimento", "valor": 1}]},
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert resp.status_code == 422


def test_invalid_ano_mes_rejected(client):
    tok = _token(client, "admin@rumo.com.br", "admin123")
    resp = client.get(
        "/api/clients/mbc/manual?ano_mes=2026-2",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert resp.status_code == 422


def test_client_cannot_edit_other_clients_manual(client):
    tok = _token(client, "financeiro@mbclaw.com.br", "mbc123")
    resp = client.put(
        "/api/clients/demo/manual?ano_mes=2026-02",
        json={"entries": []},
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert resp.status_code == 403
