from __future__ import annotations
from typing import Protocol
from app.tenancy.models import User, Client, Role

class Repository(Protocol):
    def get_user_by_email(self, email: str) -> User | None: ...
    def get_user_by_id(self, user_id: str) -> User | None: ...
    def list_clients(self) -> list[Client]: ...
    def get_client(self, client_id: str) -> Client | None: ...

    # --- provisioning writes -------------------------------------------------
    # Implemented by SupabaseRepository (prod), FixtureRepository (USE_FAKE_REPO)
    # and tests.fakes.FakeRepository. All three must stay in step — mypy checks
    # them structurally at the Depends(get_repo) annotation sites.

    def create_user(
        self,
        *,
        email: str,
        password_hash: str,
        role: Role,
        client_id: str | None,
        must_change_password: bool = False,
    ) -> User:
        """Create a user. Raises ``ValueError`` if the e-mail is already taken."""
        ...

    def list_users_for_client(self, client_id: str) -> list[User]:
        """Every user of one client, INCLUDING deactivated ones (the UI must show
        who was disabled)."""
        ...

    def set_user_active(self, user_id: str, active: bool) -> User | None:
        """Enable/disable a login. ``None`` if no such user."""
        ...

    def set_password(self, user_id: str, password_hash: str) -> User | None:
        """Replace the hash and clear ``must_change_password``. ``None`` if no such
        user."""
        ...

    def create_client(
        self, *, id: str, name: str, provider: str, provider_config: dict | None = None
    ) -> Client:
        """Create a tenant. Raises ``ValueError`` if the id is taken."""
        ...
