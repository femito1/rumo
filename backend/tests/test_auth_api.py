# backend/tests/test_auth_api.py
def test_login_success_returns_token_and_user(client):
    resp = client.post("/api/auth/login", json={"email": "admin@rumo.com.br", "password": "admin123"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"]
    assert body["user"]["role"] == "ADMIN"
    assert body["user"]["client_id"] is None

def test_login_wrong_password_401(client):
    resp = client.post("/api/auth/login", json={"email": "admin@rumo.com.br", "password": "nope"})
    assert resp.status_code == 401

def test_me_requires_token(client):
    assert client.get("/api/auth/me").status_code == 401

def test_me_returns_current_user(client):
    tok = client.post("/api/auth/login", json={"email": "financeiro@mbclaw.com.br", "password": "mbc123"}).json()["access_token"]
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {tok}"})
    assert resp.status_code == 200
    assert resp.json()["client_id"] == "mbc"
