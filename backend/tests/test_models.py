from app.tenancy.models import User, Client, Role

def test_admin_user_has_no_client():
    u = User(id="u1", email="admin@rumo.com.br", password_hash="x", role=Role.ADMIN, client_id=None, active=True)
    assert u.is_admin is True
    assert u.can_access_client("mbc") is True  # admin can access any

def test_client_user_scoped_to_own_client():
    u = User(id="u2", email="fin@mbc", password_hash="x", role=Role.CLIENT, client_id="mbc", active=True)
    assert u.is_admin is False
    assert u.can_access_client("mbc") is True
    assert u.can_access_client("demo") is False
