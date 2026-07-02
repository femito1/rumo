# backend/app/tenancy/fixture_repository.py
"""In-memory repository for local development and demos (NO external services).

Enabled by setting ``USE_FAKE_REPO=1``. It serves the same three seed accounts
as ``scripts/seed.py`` so the whole app can run with zero Supabase setup:

- admin@rumo.com.br      (ADMIN)        password: env SEED_ADMIN_PASSWORD or "admin123"
- financeiro@mbclaw.com.br (CLIENT->mbc) password: env SEED_MBC_PASSWORD or "mbc123"
- demo@cliente.com.br    (CLIENT->demo) password: env SEED_DEMO_PASSWORD or "demo123"

This must never be used in production; ``get_repo`` only selects it behind the
explicit env flag.
"""
from __future__ import annotations

import os

from app.auth.passwords import hash_password
from app.tenancy.models import Client, Role, User


class FixtureRepository:
    def __init__(self, users: list[User], clients: list[Client]) -> None:
        self._users_by_email = {u.email: u for u in users}
        self._users_by_id = {u.id: u for u in users}
        self._clients = {c.id: c for c in clients}

    @classmethod
    def seeded(cls) -> "FixtureRepository":
        clients = [
            Client(id="mbc", name="MBC", provider="legaldesk+sisjuri", provider_config={}),
            Client(
                id="demo",
                name="Cliente Demonstração",
                provider="fixture",
                provider_config={},
            ),
        ]
        users = [
            User(
                id="u-admin",
                email="admin@rumo.com.br",
                password_hash=hash_password(os.environ.get("SEED_ADMIN_PASSWORD", "admin123")),
                role=Role.ADMIN,
                client_id=None,
            ),
            User(
                id="u-mbc",
                email="financeiro@mbclaw.com.br",
                password_hash=hash_password(os.environ.get("SEED_MBC_PASSWORD", "mbc123")),
                role=Role.CLIENT,
                client_id="mbc",
            ),
            User(
                id="u-demo",
                email="demo@cliente.com.br",
                password_hash=hash_password(os.environ.get("SEED_DEMO_PASSWORD", "demo123")),
                role=Role.CLIENT,
                client_id="demo",
            ),
        ]
        return cls(users, clients)

    def get_user_by_email(self, email: str) -> User | None:
        return self._users_by_email.get(email)

    def get_user_by_id(self, user_id: str) -> User | None:
        return self._users_by_id.get(user_id)

    def list_clients(self) -> list[Client]:
        return [c for c in self._clients.values() if c.active]

    def get_client(self, client_id: str) -> Client | None:
        return self._clients.get(client_id)
