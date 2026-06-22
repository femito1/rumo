# backend/scripts/seed.py
"""Idempotent seed: creates the demo clients + the three seed users in Supabase.
Run once after applying schema.sql:  python -m scripts.seed
Passwords come from env (SEED_ADMIN_PASSWORD, SEED_MBC_PASSWORD, SEED_DEMO_PASSWORD)
with dev defaults; override in production.
"""
from __future__ import annotations
import os
from supabase import create_client
from app.auth.passwords import hash_password
from app.config import Settings

def main() -> None:
    s = Settings.from_env()
    c = create_client(s.supabase_url, s.supabase_service_key)
    clients = [
        {"id": "mbc", "name": "MBC", "provider": "legaldesk", "provider_config": {}},
        {"id": "demo", "name": "Cliente Demonstração", "provider": "fixture", "provider_config": {}},
    ]
    for row in clients:
        c.table("clients").upsert(row).execute()
    users = [
        {"email": "admin@rumo.com.br", "role": "ADMIN", "client_id": None,
         "password_hash": hash_password(os.environ.get("SEED_ADMIN_PASSWORD", "admin123"))},
        {"email": "financeiro@mbclaw.com.br", "role": "CLIENT", "client_id": "mbc",
         "password_hash": hash_password(os.environ.get("SEED_MBC_PASSWORD", "mbc123"))},
        {"email": "demo@cliente.com.br", "role": "CLIENT", "client_id": "demo",
         "password_hash": hash_password(os.environ.get("SEED_DEMO_PASSWORD", "demo123"))},
    ]
    for row in users:
        c.table("users").upsert(row, on_conflict="email").execute()
    print("Seed complete.")

if __name__ == "__main__":
    main()
