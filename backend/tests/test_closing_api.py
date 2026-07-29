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

def test_future_month_rejected_422(client):
    tok = _token(client, "admin@rumo.com.br", "admin123")
    resp = client.get("/api/clients/demo/closing?month=2999-01", headers={"Authorization": f"Bearer {tok}"})
    assert resp.status_code == 422


def test_open_current_month_is_served_as_an_explicit_partial(client):
    """Client asked for the in-progress month (2026-07-28, 6:45 — *"Por que ele não é
    online? ... Não é um fechamento mensal, mas para a gente aproveitar muito mais as
    informações"*). It must be SERVED, and must be explicitly labelled partial so it
    is never mistaken for a closing."""
    from datetime import date

    tok = _token(client, "admin@rumo.com.br", "admin123")
    today = date.today()
    resp = client.get(
        f"/api/clients/demo/closing?month={today.year:04d}-{today.month:02d}",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert resp.status_code == 200
    period = resp.json()["period"]
    assert period["is_partial"] is True
    assert period["is_closing"] is False
    # A PT-BR label the UI can show verbatim.
    assert "em aberto" in period["status_label"].lower()


def test_closed_month_is_marked_as_a_closing_not_a_partial(client):
    tok = _token(client, "admin@rumo.com.br", "admin123")
    period = client.get(
        "/api/clients/demo/closing?month=2026-05",
        headers={"Authorization": f"Bearer {tok}"},
    ).json()["period"]
    assert period["is_partial"] is False
    assert period["is_closing"] is True


def test_available_months_offers_the_open_month_flagged(client):
    from datetime import date

    tok = _token(client, "admin@rumo.com.br", "admin123")
    body = client.get("/api/clients/demo", headers={"Authorization": f"Bearer {tok}"}).json()
    today = date.today()
    open_month = f"{today.year:04d}-{today.month:02d}"
    # Back-compat: the plain list still exists and still means CLOSED months only.
    assert open_month not in body["available_months"]
    # The new detailed list leads with the open month, flagged.
    detail = body["available_months_detail"]
    assert detail[0] == {"ano_mes": open_month, "is_partial": True}
    assert all(d["is_partial"] is False for d in detail[1:])

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
