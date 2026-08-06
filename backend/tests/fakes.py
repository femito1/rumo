from __future__ import annotations
from app.tenancy.in_memory import InMemoryTenancyStore
from app.tenancy.models import User, Client, Role
from app.auth.passwords import hash_password


class FakeRepository(InMemoryTenancyStore):
    """Test double. Shares the write logic with the FixtureRepository via
    ``InMemoryTenancyStore`` so a provisioning bug cannot pass here and fail there."""

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

