# backend/tests/test_budget_api.py
import pytest
from fastapi.testclient import TestClient

from app.api import providers
from app.budget.repository import InMemoryBudgetRepository
from app.config import Settings
from app.main import app
from tests.fakes import FakeRepository

TEST_SECRET = "test-secret"


@pytest.fixture
def budget_repo():
    return InMemoryBudgetRepository()


@pytest.fixture
def client(budget_repo):
    repo = FakeRepository.seeded()
    app.dependency_overrides[providers.get_repo] = lambda: repo
    app.dependency_overrides[providers.get_budget_repo] = lambda: budget_repo
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


def test_get_budget_returns_lines_and_areas(client):
    tok = _token(client, "financeiro@mbclaw.com.br", "mbc123")
    resp = client.get(
        "/api/clients/mbc/budget?ano=2026", headers={"Authorization": f"Bearer {tok}"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["ano"] == 2026
    assert "institucional" in body["areas"]
    assert any(line["key"] == "recebimento" for line in body["lines"])
    assert body["entries"] == []


def test_put_then_get_roundtrips_budget(client):
    tok = _token(client, "financeiro@mbclaw.com.br", "mbc123")
    payload = {"entries": [{"area": "institucional", "line_key": "recebimento", "annual_amount": 8060000}]}
    put = client.put(
        "/api/clients/mbc/budget?ano=2026",
        json=payload,
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert put.status_code == 200
    got = client.get(
        "/api/clients/mbc/budget?ano=2026", headers={"Authorization": f"Bearer {tok}"}
    ).json()
    assert got["entries"] == [
        {
            "area": "institucional",
            "line_key": "recebimento",
            "annual_amount": 8060000.0,
            "monthly_amounts": None,
        }
    ]


def test_client_cannot_edit_other_clients_budget(client):
    tok = _token(client, "financeiro@mbclaw.com.br", "mbc123")
    resp = client.put(
        "/api/clients/demo/budget?ano=2026",
        json={"entries": []},
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert resp.status_code == 403


def test_admin_can_edit_any_budget(client):
    tok = _token(client, "admin@rumo.com.br", "admin123")
    resp = client.put(
        "/api/clients/mbc/budget?ano=2026",
        json={"entries": [{"area": "institucional", "line_key": "imposto", "annual_amount": 1000}]},
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert resp.status_code == 200


def test_put_per_area_despesas_equipe_budget(client):
    # POINT 13: the per-area "Orçamento Despesa" (Despesas Equipe) budget is
    # stored per cost-center area and accepted by the API.
    tok = _token(client, "financeiro@mbclaw.com.br", "mbc123")
    payload = {
        "entries": [
            {"area": "Contencioso", "line_key": "despesas_equipe", "annual_amount": 30000},
            {"area": "Econômico", "line_key": "despesas_equipe", "annual_amount": 36000},
        ]
    }
    put = client.put(
        "/api/clients/mbc/budget?ano=2026",
        json=payload,
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert put.status_code == 200
    got = client.get(
        "/api/clients/mbc/budget?ano=2026", headers={"Authorization": f"Bearer {tok}"}
    ).json()
    keys = {(e["area"], e["line_key"]) for e in got["entries"]}
    assert ("Contencioso", "despesas_equipe") in keys
    assert ("Econômico", "despesas_equipe") in keys


def test_invalid_line_key_rejected(client):
    tok = _token(client, "admin@rumo.com.br", "admin123")
    resp = client.put(
        "/api/clients/mbc/budget?ano=2026",
        json={"entries": [{"area": "institucional", "line_key": "bogus", "annual_amount": 1}]},
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert resp.status_code == 422
