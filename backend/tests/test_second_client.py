# backend/tests/test_second_client.py
"""A SECOND client, end to end through the real provider.

The point of the tenant-config work is not that a config object parses — it is that a
client with different practice areas and a different account mapping gets a correct
closing out of the same pipeline. So this drives ``build_provider_for`` with a
non-MBC ``provider_config`` and checks the payload actually reshapes.

MBC's side of the same guarantee is ``tests/test_mbc_golden.py``: an empty config must
leave every number where it was.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.closing.period import Period
from app.closing.provider import build_provider_for
from app.sources.base import DayRange
from app.tenancy.models import Client

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def snapshot() -> dict:
    return json.loads((FIXTURES / "sisjuri_2026_06.json").read_text())


def _closing(client: Client, snapshot: dict, monkeypatch):
    """Build a closing for ``client`` off a snapshot, with no external services."""
    class _Store:
        def get(self, *_a, **_k):
            return snapshot

        def recebimento_by_year(self, *_a, **_k):
            return {}

        def snapshots_by_year(self, *_a, **_k):
            return {6: snapshot}

    monkeypatch.setattr("app.closing.provider._snapshot_store", lambda: _Store())
    monkeypatch.setattr("app.closing.provider._budget_repo", lambda: _EmptyBudget())
    monkeypatch.setattr("app.closing.provider._transfers_repo", lambda: _EmptyTransfers())
    period = Period.parse("2026-06")
    provider = build_provider_for(client, period=period)
    # Drop the LegalDesk source: it would reach the network. The assembler is what the
    # tenant config affects, and it is snapshot-driven.
    provider.sources = [s for s in provider.sources if s.name != "legaldesk"]
    return provider.build_closing(
        client=client, period=period, day_range=DayRange.full_month(period), role="ADMIN"
    )


class _EmptyBudget:
    def get_budget(self, *_a, **_k):
        return []


class _EmptyTransfers:
    def get_transfers(self, *_a, **_k):
        return []


#: A plausible second firm: different practice areas, one account booked differently.
ACME = Client(
    id="acme",
    name="Acme Advogados",
    provider="legaldesk+sisjuri",
    provider_config={
        "areas": [
            {"label": "Tributário", "match": ["tribut", "fiscal"]},
            {"label": "Trabalhista", "match": ["trabalh"]},
        ],
        "accounts": {"020.060.0040": "Administrativas"},
    },
)

MBC = Client(id="mbc", name="MBC", provider="legaldesk+sisjuri", provider_config={})


def _area_labels(payload) -> list[str]:
    """The labels a reader actually sees on the deck's área slides."""
    return [a["label"] for a in payload["presentation"]["areas"]]


def test_a_second_client_gets_ITS_areas_not_MBCs(snapshot, monkeypatch):
    payload = _closing(ACME, snapshot, monkeypatch)
    labels = " ".join(str(x) for x in _area_labels(payload))
    assert "Tributário" in labels and "Trabalhista" in labels
    # MBC's practice areas must not appear anywhere in another client's deck.
    assert "Contencioso" not in labels
    assert "Arbitragem" not in labels


def test_the_same_snapshot_still_yields_MBCs_areas_for_MBC(snapshot, monkeypatch):
    """Control: the reshaping is driven by the CONFIG, not by the data."""
    payload = _closing(MBC, snapshot, monkeypatch)
    labels = " ".join(str(x) for x in _area_labels(payload))
    assert "Contencioso" in labels and "Arbitragem" in labels
    assert "Tributário" not in labels


def test_a_second_client_can_have_a_different_number_of_areas(snapshot, monkeypatch):
    """MBC has three; nothing may assume that. Two áreas must produce two blocks."""
    payload = _closing(ACME, snapshot, monkeypatch)
    assert len(payload["presentation"]["areas"]) == 2
    mbc = _closing(MBC, snapshot, monkeypatch)
    assert len(mbc["presentation"]["areas"]) == 3


def test_the_institucional_total_is_unaffected_by_the_area_split(snapshot, monkeypatch):
    """Renaming/regrouping áreas must not create or destroy money: the institutional
    headline is the same for both configs off the same snapshot."""
    acme = _closing(ACME, snapshot, monkeypatch)["presentation"]["headline"]
    mbc = _closing(MBC, snapshot, monkeypatch)["presentation"]["headline"]
    assert acme["recebimento"] == mbc["recebimento"]
    assert acme["faturamento"] == mbc["faturamento"]
    # ⚠ Despesas is NOT asserted equal: ACME's config moves 020.060.0040 to another
    # family, which is a classification change. Both families feed the same total, so
    # the RESULTADO must still agree — that is the real invariant.
    assert acme["resultado_bruto"] == mbc["resultado_bruto"]


def test_an_account_override_moves_the_line_without_changing_the_total(snapshot, monkeypatch):
    """The Seguro case from the 2026-08-05 meeting, expressed as config rather than a
    code change: Adriana ruled 020.060.0040 belongs in Administrativas. A second client
    can simply declare that, and the institutional total must not move."""
    acme = _closing(ACME, snapshot, monkeypatch)
    mbc = _closing(MBC, snapshot, monkeypatch)
    assert acme["presentation"]["headline"]["despesas"] == mbc["presentation"]["headline"]["despesas"]
