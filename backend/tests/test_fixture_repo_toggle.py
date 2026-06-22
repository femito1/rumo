from __future__ import annotations

from app.config import Settings
from app.tenancy.fixture_repository import FixtureRepository
from app.tenancy.models import Role


def test_fixture_repo_serves_seed_accounts():
    repo = FixtureRepository.seeded()

    admin = repo.get_user_by_email("admin@rumo.com.br")
    assert admin is not None and admin.role is Role.ADMIN and admin.client_id is None

    mbc = repo.get_user_by_email("financeiro@mbclaw.com.br")
    assert mbc is not None and mbc.role is Role.CLIENT and mbc.client_id == "mbc"

    assert {c.id for c in repo.list_clients()} == {"mbc", "demo"}
    assert repo.get_client("demo") is not None
    assert repo.get_user_by_id("u-admin") is admin


def test_use_fake_repo_flag_parsing(monkeypatch):
    monkeypatch.setenv("USE_FAKE_REPO", "1")
    assert Settings.from_env().use_fake_repo is True

    monkeypatch.setenv("USE_FAKE_REPO", "0")
    assert Settings.from_env().use_fake_repo is False

    monkeypatch.delenv("USE_FAKE_REPO", raising=False)
    assert Settings.from_env().use_fake_repo is False


def test_get_repo_selects_fixture_when_flag_set(monkeypatch):
    from app.api import providers

    providers.get_settings.cache_clear()
    providers._build_fixture_repo.cache_clear()
    monkeypatch.setenv("USE_FAKE_REPO", "1")
    try:
        repo = providers.get_repo()
        assert isinstance(repo, FixtureRepository)
    finally:
        providers.get_settings.cache_clear()
        providers._build_fixture_repo.cache_clear()
