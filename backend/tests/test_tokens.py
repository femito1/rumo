import pytest
from app.auth.tokens import create_access_token, decode_token, TokenError

SECRET = "unit-secret"

def test_roundtrip_carries_claims():
    tok = create_access_token(sub="u1", role="ADMIN", client_id=None, secret=SECRET, ttl_minutes=60)
    claims = decode_token(tok, secret=SECRET)
    assert claims["sub"] == "u1"
    assert claims["role"] == "ADMIN"
    assert claims["client_id"] is None

def test_expired_token_rejected():
    tok = create_access_token(sub="u1", role="CLIENT", client_id="mbc", secret=SECRET, ttl_minutes=-1)
    with pytest.raises(TokenError):
        decode_token(tok, secret=SECRET)

def test_wrong_secret_rejected():
    tok = create_access_token(sub="u1", role="CLIENT", client_id="mbc", secret=SECRET, ttl_minutes=60)
    with pytest.raises(TokenError):
        decode_token(tok, secret="other")
