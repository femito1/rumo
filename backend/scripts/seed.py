# backend/scripts/seed.py
"""Idempotent seed: creates the demo clients + the three seed users in Supabase.
Run once after applying schema.sql:  python -m scripts.seed
Passwords come from env (SEED_ADMIN_PASSWORD, SEED_MBC_PASSWORD, SEED_DEMO_PASSWORD)
with dev defaults; override in production.

⚠ This is a BOOTSTRAP, not a migration. The upsert rewrites `password_hash` for the
three seeded accounts on every run, so re-running it against a live database resets
those passwords to the env/dev values. Users created through the app (/usuarios) are
untouched — they are not in this list — but do not reach for this script to "refresh"
an existing deployment.
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
        # MBC really runs LegalDesk + the SISJURI snapshots; seeding plain "legaldesk"
        # would silently drop every expense/DRE block the second source provides.
        # `provider_config` stays empty on purpose — MBC's LegalDesk credentials come
        # from the environment; a SECOND tenant puts its own here instead.
        {"id": "mbc", "name": "MBC", "provider": "legaldesk+sisjuri", "provider_config": {}},
        # Demo tenant: inactive so it is neither listed NOR reachable by direct URL
        # (client decision 2026-08-05 — "hide the test client for now"). Flip `active`
        # to true to demo the app with no external services.
        {"id": "demo", "name": "Cliente Demonstração", "provider": "fixture",
         "provider_config": {}, "active": False},
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
