import pytest

from tests.fakes import FakeRepository
from app.tenancy.models import Role


def test_fake_repo_lookup():
    repo = FakeRepository.seeded()
    admin = repo.get_user_by_email("admin@rumo.com.br")
    assert admin is not None and admin.role == Role.ADMIN
    assert repo.get_client("mbc").name == "MBC"
    assert {c.id for c in repo.list_clients()} == {"mbc", "demo"}
    assert repo.get_user_by_email("nobody@x") is None


def test_create_user_then_find_it_by_both_keys():
    """The in-memory repos index users by BOTH email and id, so every write has to
    update both — a write that touched one index left the other stale, which reads
    as "the user exists until you log in as them"."""
    repo = FakeRepository.seeded()
    u = repo.create_user(
        email="renata@mbclaw.com.br", password_hash="h",
        role=Role.CLIENT_ADMIN, client_id="mbc", must_change_password=True,
    )
    assert u.id
    assert repo.get_user_by_email("renata@mbclaw.com.br").id == u.id
    assert repo.get_user_by_id(u.id).email == "renata@mbclaw.com.br"
    assert repo.get_user_by_id(u.id).must_change_password is True


def test_create_user_rejects_a_duplicate_email():
    repo = FakeRepository.seeded()
    with pytest.raises(ValueError):
        repo.create_user(
            email="financeiro@mbclaw.com.br", password_hash="h",
            role=Role.CLIENT, client_id="mbc",
        )


def test_list_users_for_client_is_scoped_and_includes_inactive():
    """Scoped so one tenant can never enumerate another's people. Inactive users are
    INCLUDED: the UI has to show who was deactivated, otherwise a disabled account
    silently vanishes and gets re-created."""
    repo = FakeRepository.seeded()
    u = repo.create_user(email="x@mbc", password_hash="h", role=Role.CLIENT, client_id="mbc")
    repo.set_user_active(u.id, False)
    emails = {x.email for x in repo.list_users_for_client("mbc")}
    assert "financeiro@mbclaw.com.br" in emails
    assert "x@mbc" in emails
    assert "demo@cliente.com.br" not in emails
    # The ADMIN belongs to no client, so it appears in nobody's list.
    assert "admin@rumo.com.br" not in emails


def test_set_user_active_round_trips_and_returns_none_for_unknown():
    repo = FakeRepository.seeded()
    u = repo.get_user_by_email("financeiro@mbclaw.com.br")
    assert repo.set_user_active(u.id, False).active is False
    assert repo.get_user_by_email("financeiro@mbclaw.com.br").active is False
    assert repo.set_user_active(u.id, True).active is True
    assert repo.set_user_active("no-such-id", False) is None


def test_set_password_clears_the_forced_change_flag():
    repo = FakeRepository.seeded()
    u = repo.create_user(
        email="y@mbc", password_hash="old", role=Role.CLIENT, client_id="mbc",
        must_change_password=True,
    )
    got = repo.set_password(u.id, "new-hash")
    assert got.password_hash == "new-hash"
    assert got.must_change_password is False
    assert repo.get_user_by_email("y@mbc").password_hash == "new-hash"


def test_create_client_is_listed_and_fetchable():
    repo = FakeRepository.seeded()
    c = repo.create_client(id="acme", name="Acme Advogados", provider="fixture")
    assert c.active is True
    assert repo.get_client("acme").name == "Acme Advogados"
    assert "acme" in {x.id for x in repo.list_clients()}
    with pytest.raises(ValueError):
        repo.create_client(id="acme", name="dup", provider="fixture")
