from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class Role(str, Enum):
    ADMIN = "ADMIN"
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

    @property
    def is_admin(self) -> bool:
        return self.role == Role.ADMIN

    def can_access_client(self, client_id: str) -> bool:
        if self.is_admin:
            return True
        return self.client_id == client_id
