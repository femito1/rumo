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

def get_repo() -> Repository:
    return _build_supabase_repo()
