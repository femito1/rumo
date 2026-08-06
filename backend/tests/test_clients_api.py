# backend/tests/test_clients_api.py
def _token(client, email, password):
    return client.post("/api/auth/login", json={"email": email, "password": password}).json()["access_token"]

def test_admin_lists_all_clients(client):
    tok = _token(client, "admin@rumo.com.br", "admin123")
    resp = client.get("/api/clients", headers={"Authorization": f"Bearer {tok}"})
    assert resp.status_code == 200
    ids = {c["id"] for c in resp.json()}
    assert ids == {"mbc", "demo"}

def test_client_user_cannot_list_clients(client):
    tok = _token(client, "financeiro@mbclaw.com.br", "mbc123")
    resp = client.get("/api/clients", headers={"Authorization": f"Bearer {tok}"})
    assert resp.status_code == 403

def test_client_detail_allows_own(client):
    tok = _token(client, "financeiro@mbclaw.com.br", "mbc123")
    resp = client.get("/api/clients/mbc", headers={"Authorization": f"Bearer {tok}"})
    assert resp.status_code == 200
    assert resp.json()["id"] == "mbc"
    assert "available_months" in resp.json()

def test_no_client_response_ever_carries_provider_config(client, repo):
    """`provider_config` now holds a tenant's LegalDesk password. CLAUDE.md: upstream
    credentials never reach the browser. Asserted on the ADMIN (widest) responses so
    nothing narrower can leak either."""
    from app.tenancy.models import Client

    # The `fixture` provider so the closing renders without external services; the
    # secret is what matters here, not which upstream would have been called.
    repo._clients["demo"] = Client(
        id="demo", name="Cliente Demonstração", provider="fixture",
        provider_config={"legaldesk": {"user": "integracao", "password": "s3cr3t"}},
    )
    tok = _token(client, "admin@rumo.com.br", "admin123")
    headers = {"Authorization": f"Bearer {tok}"}
    listing = client.get("/api/clients", headers=headers)
    detail = client.get("/api/clients/demo", headers=headers)
    closing = client.get("/api/clients/demo/closing?month=2026-05", headers=headers)
    for resp in (listing, detail, closing):
        assert resp.status_code == 200
        assert "provider_config" not in resp.text
        assert "s3cr3t" not in resp.text


def test_client_detail_blocks_other(client):
    tok = _token(client, "financeiro@mbclaw.com.br", "mbc123")
    resp = client.get("/api/clients/demo", headers={"Authorization": f"Bearer {tok}"})
    assert resp.status_code == 403
