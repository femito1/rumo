from __future__ import annotations
from app.tenancy.models import User, Client, Role
from app.auth.passwords import hash_password


class FakeRepository:
    def __init__(self, users: list[User], clients: list[Client]) -> None:
        self._users = {u.email: u for u in users}
        self._users_by_id = {u.id: u for u in users}
        self._clients = {c.id: c for c in clients}

    @classmethod
    def seeded(cls) -> "FakeRepository":
        clients = [
            Client(id="mbc", name="MBC", provider="legaldesk", provider_config={}),
            Client(id="demo", name="Cliente Demonstração", provider="fixture", provider_config={}),
        ]
        users = [
            User(id="u-admin", email="admin@rumo.com.br", password_hash=hash_password("admin123"), role=Role.ADMIN, client_id=None),
            User(id="u-mbc", email="financeiro@mbclaw.com.br", password_hash=hash_password("mbc123"), role=Role.CLIENT, client_id="mbc"),
            User(id="u-demo", email="demo@cliente.com.br", password_hash=hash_password("demo123"), role=Role.CLIENT, client_id="demo"),
        ]
        return cls(users, clients)

    def get_user_by_email(self, email: str) -> User | None:
        return self._users.get(email)

    def get_user_by_id(self, user_id: str) -> User | None:
        return self._users_by_id.get(user_id)

    def list_clients(self) -> list[Client]:
        return [c for c in self._clients.values() if c.active]

    def get_client(self, client_id: str) -> Client | None:
        return self._clients.get(client_id)
