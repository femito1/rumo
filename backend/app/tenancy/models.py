from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class Role(str, Enum):
    """Who someone is.

    ``ADMIN``        RUMO staff. Every client, every tab, every mutation.
    ``CLIENT_ADMIN`` A client's own manager ("Gestor" in the UI). Reads exactly what
                     a CLIENT reads, and may additionally provision users for its
                     OWN client. Deliberately NOT ``is_admin``.
    ``CLIENT``       Reads its own client's presentation deck.
    """

    ADMIN = "ADMIN"
    CLIENT_ADMIN = "CLIENT_ADMIN"
    CLIENT = "CLIENT"

@dataclass(frozen=True)
class Client:
    id: str
    name: str
    provider: str
    provider_config: dict
    active: bool = True

@dataclass(frozen=True)
class User:
    id: str
    email: str
    password_hash: str
    role: Role
    client_id: str | None
    active: bool = True
    #: Set when the account was created with a generated temporary password. The SPA
    #: forces a change before anything else is usable.
    must_change_password: bool = False

    @property
    def is_admin(self) -> bool:
        """RUMO staff only. ⚠ A CLIENT_ADMIN must never satisfy this: it is what
        grants cross-tenant access below and gates ``require_admin``."""
        return self.role == Role.ADMIN

    def can_access_client(self, client_id: str) -> bool:
        if self.is_admin:
            return True
        return self.client_id == client_id

    def can_manage_users(self, client_id: str) -> bool:
        """May create/deactivate logins for ``client_id``. RUMO may do it anywhere; a
        Gestor only inside its own client."""
        if self.is_admin:
            return True
        return self.role == Role.CLIENT_ADMIN and self.client_id == client_id

    def may_grant_role(self, role: Role) -> bool:
        """Whether this user may hand out ``role``.

        A Gestor may create ordinary CLIENT users only — not another CLIENT_ADMIN
        (the role would become self-propagating within a tenant, so revoking
        client-side provisioning would mean auditing an unbounded set) and obviously
        not an ADMIN. RUMO mints Gestores; a Gestor mints team members.
        """
        if self.is_admin:
            return True
        if self.role == Role.CLIENT_ADMIN:
            return role == Role.CLIENT
        return False
