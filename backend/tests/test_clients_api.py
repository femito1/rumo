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

def test_client_detail_blocks_other(client):
    tok = _token(client, "financeiro@mbclaw.com.br", "mbc123")
    resp = client.get("/api/clients/demo", headers={"Authorization": f"Bearer {tok}"})
    assert resp.status_code == 403
