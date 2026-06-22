from __future__ import annotations
from datetime import datetime, timedelta, timezone
import jwt

class TokenError(Exception):
    pass

def create_access_token(*, sub: str, role: str, client_id: str | None,
                         secret: str, ttl_minutes: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "role": role,
        "client_id": client_id,
        "iat": now,
        "exp": now + timedelta(minutes=ttl_minutes),
    }
    return jwt.encode(payload, secret, algorithm="HS256")

def decode_token(token: str, *, secret: str) -> dict:
    try:
        return jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise TokenError(str(exc)) from exc
