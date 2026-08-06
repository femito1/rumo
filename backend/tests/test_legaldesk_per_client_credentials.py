# backend/tests/test_legaldesk_per_client_credentials.py
"""Per-client LegalDesk credentials via ``clients.provider_config``.

Why this exists: ``_LegalDeskSettings`` read ``os.environ`` as DATACLASS FIELD
DEFAULTS, evaluated once at import, with a module-level ``SETTINGS`` singleton — and
the base URL defaulted to MBC's own host. One process could therefore only ever
reach ONE LegalDesk tenant, which made a second client impossible regardless of how
cleanly the rest of the app is keyed by ``client_id``. ``provider_config`` is a jsonb
column that already existed and nothing read.

MBC must keep working with no config at all, so an empty config falls back to env.
"""
from app.closing.provider import build_provider_for
from app.sources.legaldesk_client import _LegalDeskSettings
from app.tenancy.models import Client


def _client(provider="legaldesk+sisjuri", **cfg):
    return Client(id="c", name="C", provider=provider, provider_config=cfg)


def test_empty_config_falls_back_to_the_environment(monkeypatch):
    """MBC's row carries ``provider_config = {}`` in every fixture and in prod, so an
    empty config must behave exactly as before this change."""
    monkeypatch.setenv("LEGALDESK_BASE", "https://env.example.com/API/v1/X")
    monkeypatch.setenv("LEGALDESK_USER", "env-user")
    monkeypatch.setenv("LEGALDESK_PASSWORD", "env-pass")
    s = _LegalDeskSettings.from_provider_config({})
    assert s.api_base == "https://env.example.com/API/v1/X"
    assert s.api_user == "env-user"
    assert s.api_password == "env-pass"


def test_env_is_read_at_call_time_not_at_import_time(monkeypatch):
    """The original bug: field defaults froze the environment at import, so the
    process was pinned to one tenant for its whole life."""
    monkeypatch.setenv("LEGALDESK_USER", "first")
    assert _LegalDeskSettings.from_provider_config({}).api_user == "first"
    monkeypatch.setenv("LEGALDESK_USER", "second")
    assert _LegalDeskSettings.from_provider_config({}).api_user == "second"


def test_provider_config_overrides_the_environment(monkeypatch):
    monkeypatch.setenv("LEGALDESK_BASE", "https://env.example.com/API/v1/X")
    monkeypatch.setenv("LEGALDESK_USER", "env-user")
    monkeypatch.setenv("LEGALDESK_PASSWORD", "env-pass")
    s = _LegalDeskSettings.from_provider_config(
        {
            "legaldesk": {
                "base": "https://outro.example.com/API/v1/Y/",
                "user": "outro-user",
                "password": "outro-pass",
                "timeout": 42,
                "top": 99,
            }
        }
    )
    assert s.api_base == "https://outro.example.com/API/v1/Y"  # trailing / stripped
    assert s.api_user == "outro-user"
    assert s.api_password == "outro-pass"
    assert s.request_timeout == 42
    assert s.default_top == 99


def test_a_partial_config_only_overrides_what_it_names(monkeypatch):
    """Two tenants on one LegalDesk host differ only by credentials, so naming just
    the user/password must not blank the base URL."""
    monkeypatch.setenv("LEGALDESK_BASE", "https://shared.example.com/API/v1/X")
    monkeypatch.setenv("LEGALDESK_PASSWORD", "env-pass")
    s = _LegalDeskSettings.from_provider_config({"legaldesk": {"user": "só-o-user"}})
    assert s.api_user == "só-o-user"
    assert s.api_base == "https://shared.example.com/API/v1/X"
    assert s.api_password == "env-pass"


def test_two_clients_resolve_to_different_credentials():
    """The actual multi-tenancy claim: two Client rows, two credential sets, in one
    process."""
    a = _LegalDeskSettings.from_provider_config(
        {"legaldesk": {"base": "https://a.example.com", "user": "a", "password": "pa"}}
    )
    b = _LegalDeskSettings.from_provider_config(
        {"legaldesk": {"base": "https://b.example.com", "user": "b", "password": "pb"}}
    )
    assert (a.api_base, a.api_user) != (b.api_base, b.api_user)


def _legaldesk_source(provider_obj):
    return next(s for s in provider_obj.sources if s.name == "legaldesk")


def test_both_provider_branches_carry_the_clients_credentials(monkeypatch):
    """Covers BOTH dispatch branches: 'legaldesk' and 'legaldesk+sisjuri'. The three
    fixtures disagree on which one MBC uses (seed.py and tests/fakes say 'legaldesk',
    FixtureRepository says 'legaldesk+sisjuri'), so testing one proves nothing about
    the other."""
    monkeypatch.setattr("app.closing.provider._snapshot_store", lambda: _NoSnapshots())
    cfg = {"legaldesk": {"base": "https://tenant.example.com", "user": "u", "password": "p"}}
    for provider in ("legaldesk", "legaldesk+sisjuri"):
        src = _legaldesk_source(build_provider_for(_client(provider=provider, **cfg)))
        assert src.settings is not None
        assert src.settings.api_base == "https://tenant.example.com"
        assert src.settings.api_user == "u"


def test_building_a_provider_opens_no_http_session(monkeypatch):
    """The credentials must be resolved lazily. `build_provider_for` runs on every
    closing request, and the HTTP client is often never used (a recorded payload or a
    SISJURI snapshot answers instead), so constructing a requests.Session here would
    be waste on the hot path."""
    monkeypatch.setattr("app.closing.provider._snapshot_store", lambda: _NoSnapshots())

    def _boom(*_a, **_k):  # pragma: no cover - must not be reached
        raise AssertionError("LegalDeskClient was constructed eagerly")

    monkeypatch.setattr("app.sources.legaldesk.LegalDeskClient", _boom)
    build_provider_for(_client())


class _NoSnapshots:
    def get(self, *_a, **_k):
        return None

    def recebimento_by_year(self, *_a, **_k):
        return {}

    def snapshots_by_year(self, *_a, **_k):
        return {}
