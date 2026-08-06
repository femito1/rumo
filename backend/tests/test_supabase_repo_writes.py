# backend/tests/test_supabase_repo_writes.py
"""SupabaseRepository provisioning writes.

The in-memory repos are exercised by test_fake_repo.py; this pins the SQL-shaped
half — that ids come back from the INSERT rather than being invented client-side,
that a deactivation filters on the right column, and that `list_users_for_client`
does NOT filter on `active`. Uses a small fake mirroring supabase-py's fluent
builder (same approach as test_supabase_snapshot_store.py).
"""
import pytest

from app.tenancy.models import Role
from app.tenancy.supabase_repository import SupabaseRepository


class _FakeResult:
    def __init__(self, data):
        self.data = data


class _FakeQuery:
    def __init__(self, table):
        self._t = table
        self._filters: dict = {}
        self._op = "select"
        self._payload: dict | None = None

    def select(self, *_a, **_k):
        self._op = "select"
        return self

    def insert(self, payload, *_a, **_k):
        self._op, self._payload = "insert", payload
        return self

    def update(self, payload, *_a, **_k):
        self._op, self._payload = "update", payload
        return self

    def eq(self, col, val):
        self._filters[col] = val
        return self

    def limit(self, _n):
        return self

    def _matches(self, row):
        return all(row.get(k) == v for k, v in self._filters.items())

    def execute(self):
        if self._op == "insert":
            row = dict(self._payload)
            # Postgres supplies the uuid default; the repo must read it back.
            row.setdefault("id", f"generated-{len(self._t.rows)}")
            self._t.rows.append(row)
            return _FakeResult([row])
        if self._op == "update":
            hit = [r for r in self._t.rows if self._matches(r)]
            for r in hit:
                r.update(self._payload)
            return _FakeResult(hit)
        return _FakeResult([r for r in self._t.rows if self._matches(r)])


class _FakeTable:
    def __init__(self, rows):
        self.rows = rows


class _FakeClient:
    def __init__(self, users=None, clients=None):
        self.tables = {"users": _FakeTable(users or []), "clients": _FakeTable(clients or [])}

    def table(self, name):
        return _FakeQuery(self.tables[name])


def _repo(**kw):
    c = _FakeClient(**kw)
    return SupabaseRepository(c), c


def test_create_user_reads_the_db_generated_id_back():
    repo, c = _repo()
    u = repo.create_user(
        email="renata@mbclaw.com.br", password_hash="h",
        role=Role.CLIENT_ADMIN, client_id="mbc", must_change_password=True,
    )
    assert u.id == "generated-0"
    assert u.role is Role.CLIENT_ADMIN
    assert u.must_change_password is True
    # The role is stored as its string value, which is what the CHECK constraint sees.
    assert c.tables["users"].rows[0]["role"] == "CLIENT_ADMIN"


def test_create_user_rejects_a_duplicate_email_before_hitting_the_constraint():
    """`users.email` is unique, so relying on the DB would surface an opaque 500
    instead of a PT-BR message."""
    repo, _ = _repo(users=[{"id": "u1", "email": "a@b", "password_hash": "h",
                            "role": "CLIENT", "client_id": "mbc"}])
    with pytest.raises(ValueError):
        repo.create_user(email="a@b", password_hash="h", role=Role.CLIENT, client_id="mbc")


def test_list_users_for_client_keeps_inactive_users():
    repo, _ = _repo(users=[
        {"id": "u1", "email": "a@b", "password_hash": "h", "role": "CLIENT",
         "client_id": "mbc", "active": True},
        {"id": "u2", "email": "c@d", "password_hash": "h", "role": "CLIENT",
         "client_id": "mbc", "active": False},
        {"id": "u3", "email": "e@f", "password_hash": "h", "role": "CLIENT",
         "client_id": "demo", "active": True},
    ])
    got = repo.list_users_for_client("mbc")
    assert {u.email for u in got} == {"a@b", "c@d"}


def test_set_user_active_and_set_password_target_one_user():
    repo, c = _repo(users=[
        {"id": "u1", "email": "a@b", "password_hash": "old", "role": "CLIENT",
         "client_id": "mbc", "active": True, "must_change_password": True},
        {"id": "u2", "email": "c@d", "password_hash": "old", "role": "CLIENT",
         "client_id": "mbc", "active": True, "must_change_password": True},
    ])
    assert repo.set_user_active("u1", False).active is False
    assert c.tables["users"].rows[1]["active"] is True  # untouched

    got = repo.set_password("u1", "new")
    assert got.password_hash == "new"
    # Changing the password is what clears the forced-change flag.
    assert got.must_change_password is False
    assert c.tables["users"].rows[1]["must_change_password"] is True


def test_set_user_active_returns_none_for_an_unknown_id():
    repo, _ = _repo()
    assert repo.set_user_active("nope", False) is None
    assert repo.set_password("nope", "h") is None


class _RaisingQuery(_FakeQuery):
    """Emulates supabase-py raising on execute (constraint violation / unknown column)."""

    def __init__(self, table, message):
        super().__init__(table)
        self._message = message

    def execute(self):
        if self._op in ("insert", "update"):
            raise RuntimeError(self._message)
        return super().execute()


class _RaisingClient(_FakeClient):
    def __init__(self, message, **kw):
        super().__init__(**kw)
        self._message = message

    def table(self, name):
        return _RaisingQuery(self.tables[name], self._message)


def test_a_database_error_becomes_a_ValueError_not_a_bare_500():
    """Observed in production before the migration was applied: the users table still
    had the two-value role CHECK and no must_change_password, so `.insert()` raised a
    supabase APIError that escaped the router as an opaque **500**. The repo must
    translate any write failure into ValueError so the router can answer 422 with a
    PT-BR message — an operator seeing "500" learns nothing about a missing migration.
    """
    for message in (
        'violates check constraint "users_role_check"',
        "Could not find the 'must_change_password' column of 'users' in the schema cache",
    ):
        repo = SupabaseRepository(_RaisingClient(message))
        with pytest.raises(ValueError) as e:
            repo.create_user(
                email="a@b.com", password_hash="h", role=Role.CLIENT_ADMIN, client_id="mbc"
            )
        # The original cause must survive, or the operator cannot tell WHY.
        assert message.split()[0].lower() in str(e.value).lower() or message in str(e.value)


def test_a_failing_update_also_surfaces_as_ValueError():
    repo = SupabaseRepository(
        _RaisingClient("boom", users=[{"id": "u1", "email": "a@b", "password_hash": "h",
                                       "role": "CLIENT", "client_id": "mbc", "active": True}])
    )
    with pytest.raises(ValueError):
        repo.set_user_active("u1", False)
    with pytest.raises(ValueError):
        repo.set_password("u1", "h")


def test_create_client_defaults_provider_config_to_empty():
    repo, c = _repo()
    got = repo.create_client(id="acme", name="Acme", provider="fixture")
    assert got.active is True and got.provider_config == {}
    assert c.tables["clients"].rows[0]["id"] == "acme"
    with pytest.raises(ValueError):
        repo.create_client(id="acme", name="dup", provider="fixture")
