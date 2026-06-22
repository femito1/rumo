# backend/tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api import providers
from app.config import Settings
from tests.fakes import FakeRepository

TEST_SECRET = "test-secret"

@pytest.fixture
def repo():
    return FakeRepository.seeded()

@pytest.fixture
def client(repo):
    app.dependency_overrides[providers.get_repo] = lambda: repo
    app.dependency_overrides[providers.get_settings] = lambda: Settings(
        jwt_secret=TEST_SECRET, jwt_ttl_minutes=60, cors_origins=["*"],
        supabase_url="", supabase_service_key="",
    )
    yield TestClient(app)
    app.dependency_overrides.clear()
