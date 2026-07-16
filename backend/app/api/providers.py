# backend/app/api/providers.py
from __future__ import annotations
from functools import lru_cache
from app.config import Settings
from app.tenancy.repository import Repository

@lru_cache
def get_settings() -> Settings:
    return Settings.from_env()

@lru_cache
def _build_supabase_repo() -> Repository:
    from supabase import create_client
    from app.tenancy.supabase_repository import SupabaseRepository
    s = get_settings()
    return SupabaseRepository(create_client(s.supabase_url, s.supabase_service_key))

@lru_cache
def _build_fixture_repo() -> Repository:
    from app.tenancy.fixture_repository import FixtureRepository
    return FixtureRepository.seeded()

def get_repo() -> Repository:
    # Dev/demo escape hatch: run the whole app with no external services.
    if get_settings().use_fake_repo:
        return _build_fixture_repo()
    return _build_supabase_repo()


@lru_cache
def _build_supabase_budget_repo():
    from supabase import create_client

    from app.budget.repository import SupabaseBudgetRepository
    s = get_settings()
    return SupabaseBudgetRepository(create_client(s.supabase_url, s.supabase_service_key))


@lru_cache
def _build_fixture_budget_repo():
    from app.budget.repository import InMemoryBudgetRepository
    return InMemoryBudgetRepository.seeded()


def get_budget_repo():
    if get_settings().use_fake_repo:
        return _build_fixture_budget_repo()
    return _build_supabase_budget_repo()


@lru_cache
def _build_supabase_transfers_repo():
    from supabase import create_client

    from app.manual.transfers import SupabaseAreaTransfersRepository
    s = get_settings()
    return SupabaseAreaTransfersRepository(
        create_client(s.supabase_url, s.supabase_service_key)
    )


@lru_cache
def _build_fixture_transfers_repo():
    from app.manual.transfers import InMemoryAreaTransfersRepository
    return InMemoryAreaTransfersRepository()


def get_transfers_repo():
    if get_settings().use_fake_repo:
        return _build_fixture_transfers_repo()
    return _build_supabase_transfers_repo()


@lru_cache
def _build_supabase_snapshot_store():
    from supabase import create_client

    from app.sources.supabase_snapshot_store import SupabaseSnapshotStore
    s = get_settings()
    return SupabaseSnapshotStore(
        create_client(s.supabase_url, s.supabase_service_key)
    )


@lru_cache
def _build_fs_snapshot_store():
    import os

    from app.sources.snapshot_store import SnapshotStore
    return SnapshotStore(os.environ.get("SNAPSHOT_DIR", "data/snapshots"))


def get_snapshot_store():
    """Production persists snapshots in Supabase; USE_FAKE_REPO / local dev keeps
    the filesystem store so the app runs with no external services."""
    if get_settings().use_fake_repo:
        return _build_fs_snapshot_store()
    return _build_supabase_snapshot_store()
