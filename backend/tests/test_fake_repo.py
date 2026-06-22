from tests.fakes import FakeRepository
from app.tenancy.models import Role


def test_fake_repo_lookup():
    repo = FakeRepository.seeded()
    admin = repo.get_user_by_email("admin@rumo.com.br")
    assert admin is not None and admin.role == Role.ADMIN
    assert repo.get_client("mbc").name == "MBC"
    assert {c.id for c in repo.list_clients()} == {"mbc", "demo"}
    assert repo.get_user_by_email("nobody@x") is None
