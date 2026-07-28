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


def test_admin_sees_only_the_kept_tabs(client):
    # 2026-07 cleanup: the removed detail tabs (institucional, per-área, meta,
    # nacional, moedas, faturas_analitico) are no longer in tab_order.
    tok = _token(client, "admin@rumo.com.br", "admin123")
    body = client.get(
        "/api/clients/demo/closing?month=2026-05",
        headers={"Authorization": f"Bearer {tok}"},
    ).json()
    removed = {"institucional", "contencioso", "economico", "arbitragem",
               "meta", "meta_dashboard", "nacional", "moedas", "faturas_analitico"}
    assert not (set(body["tab_order"]) & removed)
    # Only KEEP-set tabs survive (the fixture demo emits base_resultado).
    keep = {"base_resultado", "areas_sintetico", "dre_2026", "orcamento_2026",
            "rateio_mensal", "amortizacao"}
    assert set(body["tab_order"]) <= keep
    assert "base_resultado" in body["tab_order"]


def test_client_role_gets_no_detail_tabs(client):
    # A CLIENT sees the presentation panel only; the detail tabs/data are withheld
    # server-side (not merely hidden). KPIs + presentation still ship (panel renders).
    tok = _token(client, "demo@cliente.com.br", "demo123")
    body = client.get(
        "/api/clients/demo/closing?month=2026-05",
        headers={"Authorization": f"Bearer {tok}"},
    ).json()
    assert body["tab_order"] == []
    assert body["tabs"] == {}
    assert "kpis" in body
    # The presentation panel data is always present (both roles).
    pres = body["presentation"]
    assert pres["titulo"]
    assert "headline" in pres and "areas" in pres
    assert len(pres["areas"]) == 3


def test_closing_carries_no_render_mode(client):
    # The cumulative view is a TAB, not a render mode — there is no ``mode`` param
    # and no ``mode`` in the payload. A stale ``?mode=`` URL is simply ignored.
    tok = _token(client, "admin@rumo.com.br", "admin123")
    resp = client.get(
        "/api/clients/demo/closing?month=2026-05&mode=acumulado",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert resp.status_code == 200
    assert "mode" not in resp.json()
