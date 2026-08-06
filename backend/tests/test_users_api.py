# backend/tests/test_users_api.py
"""User provisioning API + its privilege boundary.

Client commitment (2026-08-05 meeting, Adriana: *"como que a gente dá o acesso para
o cliente? Como é que vai ser?"*): RUMO creates clients and users, and a client's
own Gestor provisions its team.

Most of this file is the ESCALATION suite. A Gestor is the first role in this
product that can create credentials, so each way it could reach beyond its own
tenant gets its own named test. The recurring mistake these guard against is gating
on the request BODY instead of the STORED target: a body carries whatever the
attacker typed, so any route that mutates an existing user must resolve that user
first and check *its* role and client.
"""
import pytest

from app.auth.passwords import hash_password
from app.tenancy.models import Role


def _token(client, email, password):
    return client.post(
        "/api/auth/login", json={"email": email, "password": password}
    ).json()["access_token"]


def _hdr(client, email, password):
    return {"Authorization": f"Bearer {_token(client, email, password)}"}


@pytest.fixture
def gestor(repo):
    """A Gestor of `mbc`, and a second tenant's user to aim at."""
    repo.create_user(
        email="renata@mbclaw.com.br", password_hash=hash_password("g123"),
        role=Role.CLIENT_ADMIN, client_id="mbc",
    )
    return "renata@mbclaw.com.br", "g123"


# --- happy paths ------------------------------------------------------------

def test_admin_creates_a_user_and_gets_the_temp_password_once(client):
    resp = client.post(
        "/api/clients/mbc/users",
        json={"email": "novo@mbclaw.com.br", "role": "CLIENT"},
        headers=_hdr(client, "admin@rumo.com.br", "admin123"),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "novo@mbclaw.com.br"
    assert body["role"] == "CLIENT"
    assert body["must_change_password"] is True
    # The generated password is returned exactly once, on creation...
    assert len(body["temp_password"]) >= 12
    # ...and the hash is never exposed.
    assert "password_hash" not in body

    # ...and never again on any subsequent read.
    listed = client.get(
        "/api/clients/mbc/users", headers=_hdr(client, "admin@rumo.com.br", "admin123")
    ).json()
    entry = next(u for u in listed if u["email"] == "novo@mbclaw.com.br")
    assert "temp_password" not in entry and "password_hash" not in entry


def test_the_temp_password_actually_logs_in_and_forces_a_change(client):
    created = client.post(
        "/api/clients/mbc/users",
        json={"email": "novo@mbclaw.com.br", "role": "CLIENT"},
        headers=_hdr(client, "admin@rumo.com.br", "admin123"),
    ).json()
    login = client.post(
        "/api/auth/login",
        json={"email": "novo@mbclaw.com.br", "password": created["temp_password"]},
    )
    assert login.status_code == 200
    assert login.json()["user"]["must_change_password"] is True

    tok = login.json()["access_token"]
    changed = client.post(
        "/api/auth/change-password",
        json={"current_password": created["temp_password"], "new_password": "uma-senha-longa"},
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert changed.status_code == 200
    assert changed.json()["must_change_password"] is False
    # The new password works and the flag stays cleared.
    again = client.post(
        "/api/auth/login",
        json={"email": "novo@mbclaw.com.br", "password": "uma-senha-longa"},
    )
    assert again.status_code == 200
    assert again.json()["user"]["must_change_password"] is False


def test_gestor_provisions_an_ordinary_user_for_its_own_client(client, gestor):
    resp = client.post(
        "/api/clients/mbc/users",
        json={"email": "equipe@mbclaw.com.br", "role": "CLIENT"},
        headers=_hdr(client, *gestor),
    )
    assert resp.status_code == 200


def test_admin_creates_a_client(client):
    resp = client.post(
        "/api/clients",
        json={"id": "acme", "name": "Acme Advogados", "provider": "fixture"},
        headers=_hdr(client, "admin@rumo.com.br", "admin123"),
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == "acme"
    # Credentials must never be echoed back (they live in provider_config).
    assert "provider_config" not in resp.json()


def test_deactivating_a_user_ends_its_access(client):
    created = client.post(
        "/api/clients/mbc/users",
        json={"email": "sai@mbclaw.com.br", "role": "CLIENT"},
        headers=_hdr(client, "admin@rumo.com.br", "admin123"),
    ).json()
    resp = client.patch(
        f"/api/clients/mbc/users/{created['id']}",
        json={"active": False},
        headers=_hdr(client, "admin@rumo.com.br", "admin123"),
    )
    assert resp.status_code == 200
    assert resp.json()["active"] is False
    denied = client.post(
        "/api/auth/login",
        json={"email": "sai@mbclaw.com.br", "password": created["temp_password"]},
    )
    assert denied.status_code == 401


# --- escalation: one test per way a Gestor could reach too far ---------------

def test_gestor_cannot_create_an_admin(client, gestor):
    resp = client.post(
        "/api/clients/mbc/users",
        json={"email": "fake-admin@x.com", "role": "ADMIN"},
        headers=_hdr(client, *gestor),
    )
    assert resp.status_code == 403


def test_gestor_cannot_create_another_gestor(client, gestor):
    """Deliberate: the role would be self-propagating inside a tenant, so revoking
    client-side provisioning would mean auditing an unbounded set. RUMO mints
    Gestores; a Gestor mints team members."""
    resp = client.post(
        "/api/clients/mbc/users",
        json={"email": "outro@mbclaw.com.br", "role": "CLIENT_ADMIN"},
        headers=_hdr(client, *gestor),
    )
    assert resp.status_code == 403


def test_gestor_cannot_create_a_user_under_another_client(client, gestor):
    resp = client.post(
        "/api/clients/demo/users",
        json={"email": "invasor@x.com", "role": "CLIENT"},
        headers=_hdr(client, *gestor),
    )
    assert resp.status_code == 403


def test_no_endpoint_can_change_a_role_at_all(client, gestor):
    """Elevation is structurally impossible, not merely guarded: no route accepts a
    role. Asserted with the ADMIN actor, who clears every other check, so the only
    thing that can refuse is the absence of the field itself. Changing a role means
    deactivating and re-creating — deliberate, and visible in the user list."""
    me = client.get("/api/auth/me", headers=_hdr(client, *gestor)).json()
    resp = client.patch(
        f"/api/clients/mbc/users/{me['id']}",
        json={"role": "ADMIN"},
        headers=_hdr(client, "admin@rumo.com.br", "admin123"),
    )
    assert resp.status_code == 422  # "Nada a alterar" — the role key is not read
    assert client.get("/api/auth/me", headers=_hdr(client, *gestor)).json()["role"] == "CLIENT_ADMIN"


def test_gestor_cannot_manage_itself_or_another_gestor(client, gestor, repo):
    """A Gestor may only manage users whose role it could have granted, i.e. ordinary
    CLIENT users. That excludes itself — so it cannot deactivate its own account and
    lock the firm out — and excludes its peers."""
    me = client.get("/api/auth/me", headers=_hdr(client, *gestor)).json()
    resp = client.patch(
        f"/api/clients/mbc/users/{me['id']}",
        json={"active": False},
        headers=_hdr(client, *gestor),
    )
    assert resp.status_code == 404
    assert repo.get_user_by_email("renata@mbclaw.com.br").active is True

    peer = repo.create_user(
        email="outro-gestor@mbclaw.com.br", password_hash=hash_password("x"),
        role=Role.CLIENT_ADMIN, client_id="mbc",
    )
    assert client.patch(
        f"/api/clients/mbc/users/{peer.id}",
        json={"active": False},
        headers=_hdr(client, *gestor),
    ).status_code == 404


def test_admin_can_still_manage_a_gestor(client, gestor, repo):
    """The corollary: RUMO must remain able to disable a client's manager, otherwise
    the "only RUMO mints Gestores" rule would have no way to unmint one."""
    gid = repo.get_user_by_email("renata@mbclaw.com.br").id
    resp = client.patch(
        f"/api/clients/mbc/users/{gid}",
        json={"active": False},
        headers=_hdr(client, "admin@rumo.com.br", "admin123"),
    )
    assert resp.status_code == 200
    assert resp.json()["active"] is False


def test_gestor_cannot_deactivate_a_rumo_admin(client, gestor, repo):
    """The path segment says `mbc` (which the Gestor may manage) while the target is
    RUMO's own account. Gating on the path alone would let this through."""
    admin_id = repo.get_user_by_email("admin@rumo.com.br").id
    resp = client.patch(
        f"/api/clients/mbc/users/{admin_id}",
        json={"active": False},
        headers=_hdr(client, *gestor),
    )
    assert resp.status_code == 404
    assert repo.get_user_by_email("admin@rumo.com.br").active is True


def test_gestor_cannot_touch_a_user_of_another_client_via_its_own_path(client, gestor, repo):
    """HOLE: `require_client_access` validates the {client_id} PATH SEGMENT, not the
    target. A Gestor of `mbc` passing client_id=mbc with another tenant's user_id
    would otherwise sail through. 404, not 403, so it does not confirm the id
    exists somewhere else."""
    victim = repo.get_user_by_email("demo@cliente.com.br").id
    resp = client.patch(
        f"/api/clients/mbc/users/{victim}",
        json={"active": False},
        headers=_hdr(client, *gestor),
    )
    assert resp.status_code == 404
    assert repo.get_user_by_email("demo@cliente.com.br").active is True


def test_gestor_cannot_reset_an_admins_password(client, gestor, repo):
    """HOLE (worst of the set): a password-reset body carries no role and no
    client_id, so a guard that inspects only the BODY passes vacuously and hands
    back a working credential for admin@rumo.com.br. The route must resolve the
    stored target and gate on ITS role."""
    admin_id = repo.get_user_by_email("admin@rumo.com.br").id
    before = repo.get_user_by_email("admin@rumo.com.br").password_hash
    resp = client.post(
        f"/api/clients/mbc/users/{admin_id}/reset-password",
        headers=_hdr(client, *gestor),
    )
    assert resp.status_code == 404
    assert "temp_password" not in resp.json()
    assert repo.get_user_by_email("admin@rumo.com.br").password_hash == before


def test_gestor_cannot_list_another_clients_users(client, gestor):
    resp = client.get("/api/clients/demo/users", headers=_hdr(client, *gestor))
    assert resp.status_code == 403


def test_gestor_cannot_create_a_client(client, gestor):
    resp = client.post(
        "/api/clients",
        json={"id": "acme", "name": "Acme", "provider": "fixture"},
        headers=_hdr(client, *gestor),
    )
    assert resp.status_code == 403


def test_a_plain_client_user_can_do_none_of_it(client):
    hdr = _hdr(client, "financeiro@mbclaw.com.br", "mbc123")
    assert client.get("/api/clients/mbc/users", headers=hdr).status_code == 403
    assert client.post(
        "/api/clients/mbc/users", json={"email": "x@y.com", "role": "CLIENT"}, headers=hdr
    ).status_code == 403
    assert client.post(
        "/api/clients", json={"id": "z", "name": "Z", "provider": "fixture"}, headers=hdr
    ).status_code == 403


def test_provisioning_requires_authentication(client):
    assert client.get("/api/clients/mbc/users").status_code == 401
    assert client.post(
        "/api/clients/mbc/users", json={"email": "x@y.com", "role": "CLIENT"}
    ).status_code == 401


# --- validation -------------------------------------------------------------

def test_duplicate_email_is_a_ptbr_422_not_a_500(client):
    hdr = _hdr(client, "admin@rumo.com.br", "admin123")
    body = {"email": "financeiro@mbclaw.com.br", "role": "CLIENT"}
    resp = client.post("/api/clients/mbc/users", json=body, headers=hdr)
    assert resp.status_code == 422
    assert "já cadastrado" in resp.json()["detail"].lower()


def test_unknown_role_and_malformed_email_are_rejected(client):
    hdr = _hdr(client, "admin@rumo.com.br", "admin123")
    assert client.post(
        "/api/clients/mbc/users", json={"email": "a@b.com", "role": "SUPERUSER"}, headers=hdr
    ).status_code == 422
    assert client.post(
        "/api/clients/mbc/users", json={"email": "not-an-email", "role": "CLIENT"}, headers=hdr
    ).status_code == 422


def test_creating_a_user_for_an_unknown_client_is_404(client):
    resp = client.post(
        "/api/clients/nope/users",
        json={"email": "a@b.com", "role": "CLIENT"},
        headers=_hdr(client, "admin@rumo.com.br", "admin123"),
    )
    assert resp.status_code == 404


def test_change_password_rejects_a_wrong_current_password(client):
    resp = client.post(
        "/api/auth/change-password",
        json={"current_password": "nope", "new_password": "uma-senha-longa"},
        headers=_hdr(client, "financeiro@mbclaw.com.br", "mbc123"),
    )
    assert resp.status_code == 401


def test_change_password_enforces_a_minimum_length(client):
    resp = client.post(
        "/api/auth/change-password",
        json={"current_password": "mbc123", "new_password": "curta"},
        headers=_hdr(client, "financeiro@mbclaw.com.br", "mbc123"),
    )
    assert resp.status_code == 422
