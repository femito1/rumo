from app.tenancy.models import User, Role

def test_admin_user_has_no_client():
    u = User(id="u1", email="admin@rumo.com.br", password_hash="x", role=Role.ADMIN, client_id=None, active=True)
    assert u.is_admin is True
    assert u.can_access_client("mbc") is True  # admin can access any

def test_client_user_scoped_to_own_client():
    u = User(id="u2", email="fin@mbc", password_hash="x", role=Role.CLIENT, client_id="mbc", active=True)
    assert u.is_admin is False
    assert u.can_access_client("mbc") is True
    assert u.can_access_client("demo") is False


def _gestor(client_id="mbc"):
    return User(id="u3", email="gestor@mbc", password_hash="x",
                role=Role.CLIENT_ADMIN, client_id=client_id, active=True)


def test_client_admin_is_not_a_rumo_admin():
    """A CLIENT_ADMIN ("Gestor") manages its OWN client's logins. It must NOT be
    ``is_admin`` — that property is what grants cross-tenant access in
    ``can_access_client`` and gates ``require_admin`` (e.g. GET /api/clients, which
    lists every client). Scoped exactly like a CLIENT for DATA."""
    u = _gestor()
    assert u.is_admin is False
    assert u.can_access_client("mbc") is True
    assert u.can_access_client("demo") is False


def test_only_admin_and_client_admin_may_manage_users():
    assert _gestor().can_manage_users("mbc") is True
    # ...but never another tenant's users, even though the role name is the same.
    assert _gestor().can_manage_users("demo") is False
    admin = User(id="u1", email="a@rumo", password_hash="x", role=Role.ADMIN,
                 client_id=None, active=True)
    assert admin.can_manage_users("mbc") is True
    plain = User(id="u2", email="fin@mbc", password_hash="x", role=Role.CLIENT,
                 client_id="mbc", active=True)
    assert plain.can_manage_users("mbc") is False


def test_a_gestor_may_only_grant_roles_at_or_below_its_own():
    """A CLIENT_ADMIN may create ordinary CLIENT users but NOT another CLIENT_ADMIN
    and NOT an ADMIN. Denying self-propagation keeps "who granted this?" answerable:
    RUMO mints client managers, a manager mints team members."""
    g = _gestor()
    assert g.may_grant_role(Role.CLIENT) is True
    assert g.may_grant_role(Role.CLIENT_ADMIN) is False
    assert g.may_grant_role(Role.ADMIN) is False
    admin = User(id="u1", email="a@rumo", password_hash="x", role=Role.ADMIN,
                 client_id=None, active=True)
    assert all(admin.may_grant_role(r) for r in Role)
