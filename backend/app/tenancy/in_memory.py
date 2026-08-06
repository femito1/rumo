# backend/app/tenancy/in_memory.py
"""Shared in-memory tenancy storage.

``FixtureRepository`` (USE_FAKE_REPO) and ``tests.fakes.FakeRepository`` are the same
store with different seed data, so the write logic lives here once. That matters
more than saving lines: users are indexed by BOTH e-mail and id, ``User``/``Client``
are frozen dataclasses (so every "update" is a rebuild), and a write that refreshed
only one index left the other stale — a bug that reads as "the user exists until you
try to log in as them". One implementation, one place to get that right.
"""
from __future__ import annotations

import uuid
from dataclasses import replace

from app.tenancy.models import Client, Role, User


class InMemoryTenancyStore:
    def __init__(self, users: list[User], clients: list[Client]) -> None:
        self._users_by_email = {u.email: u for u in users}
        self._users_by_id = {u.id: u for u in users}
        self._clients = {c.id: c for c in clients}

    # --- reads ---------------------------------------------------------------

    def get_user_by_email(self, email: str) -> User | None:
        return self._users_by_email.get(email)

    def get_user_by_id(self, user_id: str) -> User | None:
        return self._users_by_id.get(user_id)

    def list_clients(self) -> list[Client]:
        return [c for c in self._clients.values() if c.active]

    def get_client(self, client_id: str) -> Client | None:
        return self._clients.get(client_id)

    # --- writes --------------------------------------------------------------

    def _put(self, user: User) -> User:
        """Write a user into BOTH indices. Every mutation goes through here."""
        self._users_by_email[user.email] = user
        self._users_by_id[user.id] = user
        return user

    def create_user(
        self,
        *,
        email: str,
        password_hash: str,
        role: Role,
        client_id: str | None,
        must_change_password: bool = False,
    ) -> User:
        if email in self._users_by_email:
            raise ValueError(f"e-mail já cadastrado: {email}")
        return self._put(
            User(
                # Postgres generates this via gen_random_uuid(); mirror the shape so
                # ids look the same in dev and prod.
                id=str(uuid.uuid4()),
                email=email,
                password_hash=password_hash,
                role=role,
                client_id=client_id,
                active=True,
                must_change_password=must_change_password,
            )
        )

    def list_users_for_client(self, client_id: str) -> list[User]:
        return [u for u in self._users_by_id.values() if u.client_id == client_id]

    def set_user_active(self, user_id: str, active: bool) -> User | None:
        user = self._users_by_id.get(user_id)
        if user is None:
            return None
        return self._put(replace(user, active=active))

    def set_password(self, user_id: str, password_hash: str) -> User | None:
        user = self._users_by_id.get(user_id)
        if user is None:
            return None
        return self._put(
            replace(user, password_hash=password_hash, must_change_password=False)
        )

    def create_client(
        self, *, id: str, name: str, provider: str, provider_config: dict | None = None
    ) -> Client:
        if id in self._clients:
            raise ValueError(f"cliente já existe: {id}")
        client = Client(
            id=id, name=name, provider=provider,
            provider_config=provider_config or {}, active=True,
        )
        self._clients[id] = client
        return client
