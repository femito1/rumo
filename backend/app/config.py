from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    jwt_secret: str
    jwt_ttl_minutes: int
    cors_origins: list[str]
    supabase_url: str
    supabase_service_key: str

    @classmethod
    def from_env(cls) -> "Settings":
        origins = os.environ.get("CORS_ORIGINS", "http://localhost:5173")
        return cls(
            jwt_secret=os.environ.get("JWT_SECRET", "dev-insecure-secret"),
            jwt_ttl_minutes=int(os.environ.get("JWT_TTL_MINUTES", "720")),
            cors_origins=[o.strip() for o in origins.split(",") if o.strip()],
            supabase_url=os.environ.get("SUPABASE_URL", ""),
            supabase_service_key=os.environ.get("SUPABASE_SERVICE_KEY", ""),
        )
