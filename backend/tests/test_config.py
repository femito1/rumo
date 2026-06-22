import os
from app.config import Settings


def test_settings_read_from_env(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "s3cret")
    monkeypatch.setenv("JWT_TTL_MINUTES", "60")
    monkeypatch.setenv("CORS_ORIGINS", "http://a.com,http://b.com")
    s = Settings.from_env()
    assert s.jwt_secret == "s3cret"
    assert s.jwt_ttl_minutes == 60
    assert s.cors_origins == ["http://a.com", "http://b.com"]
