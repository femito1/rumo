# backend/tests/test_closing_api.py
def _token(client, email, password):
    return client.post("/api/auth/login", json={"email": email, "password": password}).json()["access_token"]

def test_demo_closing_returns_payload(client):
    tok = _token(client, "admin@rumo.com.br", "admin123")
    resp = client.get("/api/clients/demo/closing?month=2026-05", headers={"Authorization": f"Bearer {tok}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["client"]["id"] == "demo"
    assert body["period"]["ano_mes"] == "2026-05"
    assert body["day_range"]["is_full_month"] is True

def test_open_month_rejected_422(client):
    tok = _token(client, "admin@rumo.com.br", "admin123")
    resp = client.get("/api/clients/demo/closing?month=2999-01", headers={"Authorization": f"Bearer {tok}"})
    assert resp.status_code == 422

def test_client_cannot_read_other_clients_closing(client):
    tok = _token(client, "financeiro@mbclaw.com.br", "mbc123")
    resp = client.get("/api/clients/demo/closing?month=2026-05", headers={"Authorization": f"Bearer {tok}"})
    assert resp.status_code == 403

def test_day_range_marks_partial(client):
    tok = _token(client, "admin@rumo.com.br", "admin123")
    resp = client.get("/api/clients/demo/closing?month=2026-05&from=1&to=15", headers={"Authorization": f"Bearer {tok}"})
    assert resp.status_code == 200
    assert resp.json()["day_range"]["is_full_month"] is False

def test_day_beyond_month_length_rejected_422(client):
    tok = _token(client, "admin@rumo.com.br", "admin123")
    # February 2026 has 28 days; day 30 is invalid.
    resp = client.get("/api/clients/demo/closing?month=2026-02&from=1&to=30", headers={"Authorization": f"Bearer {tok}"})
    assert resp.status_code == 422
    assert "28 dias" in resp.json()["detail"]

def test_last_valid_day_of_february_accepted(client):
    tok = _token(client, "admin@rumo.com.br", "admin123")
    resp = client.get("/api/clients/demo/closing?month=2026-02&from=1&to=28", headers={"Authorization": f"Bearer {tok}"})
    assert resp.status_code == 200
