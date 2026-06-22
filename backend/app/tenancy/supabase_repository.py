from __future__ import annotations
from app.tenancy.models import User, Client, Role

def row_to_user(row: dict) -> User:
    return User(
        id=str(row["id"]), email=row["email"], password_hash=row["password_hash"],
        role=Role(row["role"]), client_id=row.get("client_id"), active=row.get("active", True),
    )

def row_to_client(row: dict) -> Client:
    return Client(
        id=row["id"], name=row["name"], provider=row["provider"],
        provider_config=row.get("provider_config") or {}, active=row.get("active", True),
    )

class SupabaseRepository:
    """Production repository backed by supabase-py. Constructed with a supabase client."""
    def __init__(self, client) -> None:
        self._c = client

    def get_user_by_email(self, email: str) -> User | None:
        res = self._c.table("users").select("*").eq("email", email).limit(1).execute()
        rows = res.data or []
        return row_to_user(rows[0]) if rows else None

    def get_user_by_id(self, user_id: str) -> User | None:
        res = self._c.table("users").select("*").eq("id", user_id).limit(1).execute()
        rows = res.data or []
        return row_to_user(rows[0]) if rows else None

    def list_clients(self) -> list[Client]:
        res = self._c.table("clients").select("*").eq("active", True).execute()
        return [row_to_client(r) for r in (res.data or [])]

    def get_client(self, client_id: str) -> Client | None:
        res = self._c.table("clients").select("*").eq("id", client_id).limit(1).execute()
        rows = res.data or []
        return row_to_client(rows[0]) if rows else None
