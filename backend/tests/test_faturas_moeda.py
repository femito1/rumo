# backend/tests/test_faturas_moeda.py
"""Per-invoice faturamento lists — workbook tabs 'Nacional' (BRL) and 'Moedas'
(foreign: EUR/USD).

Built from the SISJURI snapshot's ``faturas_moeda`` block (LDESK.DB_VW_FATURASEMI_REC,
per-invoice, validated to the centavo vs the sacred faturamento). The backend splits
by currency: nacional rows (``moeda`` == ``moeda_nac``) vs foreign rows.
"""
import pytest

from app.closing.dre import assemble_dre_sections

# A minimal faturas_moeda block: 2 BRL invoices + 1 USD invoice.
FATURAS_MOEDA = [
    {"numero": 4141, "cliente": "132", "caso": "Caso A", "data_emissao": "2026-05-06",
     "vencimento": "2026-06-08", "recebimento": "2026-06-03", "moeda": "R$",
     "moeda_nac": "R$", "honorarios": 1575.0, "honorarios_nac": 1575.0,
     "despesas": 0.0, "despesas_nac": 0.0, "recebido_hon": 0.0, "recebido_hon_nac": 0.0},
    {"numero": 4143, "cliente": "6", "caso": "Caso B", "data_emissao": "2026-05-06",
     "vencimento": "2026-06-08", "recebimento": None, "moeda": "R$",
     "moeda_nac": "R$", "honorarios": 4068.0, "honorarios_nac": 4068.0,
     "despesas": 0.0, "despesas_nac": 0.0, "recebido_hon": 0.0, "recebido_hon_nac": 0.0},
    {"numero": 4200, "cliente": "136", "caso": "Deere", "data_emissao": "2026-05-20",
     "vencimento": "2026-06-20", "recebimento": None, "moeda": "US$",
     "moeda_nac": "R$", "honorarios": 3316.66, "honorarios_nac": 11328.87,
     "despesas": 0.0, "despesas_nac": 0.0, "recebido_hon": 0.0, "recebido_hon_nac": 0.0},
]


def test_nacional_tab_emitted():
    sections = assemble_dre_sections(
        snapshot={"faturas_moeda": FATURAS_MOEDA}, budget=None, period_label="Maio 2026",
    )
    assert "nacional" in sections
    tab = sections["nacional"]
    assert tab["kind"] == "rich"
    # Only the two BRL invoices, one row each (per-invoice grain).
    body = [r for r in tab["rows"] if r.get("kind") != "total"]
    assert len(body) == 2
    assert {r["Fatura"] for r in body} == {4141, 4143}


def test_moedas_tab_only_foreign():
    sections = assemble_dre_sections(
        snapshot={"faturas_moeda": FATURAS_MOEDA}, budget=None, period_label="Maio 2026",
    )
    tab = sections["moedas"]
    body = [r for r in tab["rows"] if r.get("kind") != "total"]
    assert len(body) == 1
    row = body[0]
    assert row["Fatura"] == 4200
    assert row["Moeda"] == "US$"
    # Foreign row carries both the foreign honorários and its BRL conversion.
    assert row["Honorários"]["value"] == pytest.approx(3316.66, abs=0.01)
    assert row["Honorários (R$)"]["value"] == pytest.approx(11328.87, abs=0.01)


def test_faturas_moeda_totals_tie_to_sacred_split():
    sections = assemble_dre_sections(
        snapshot={"faturas_moeda": FATURAS_MOEDA}, budget=None, period_label="Maio 2026",
    )
    nac_total = next(r for r in sections["nacional"]["rows"] if r.get("kind") == "total")
    moe_total = next(r for r in sections["moedas"]["rows"] if r.get("kind") == "total")
    # Nacional totals the BRL honorários; Moedas totals the BRL-converted column.
    assert nac_total["Honorários (R$)"]["value"] == pytest.approx(1575.0 + 4068.0, abs=0.01)
    assert moe_total["Honorários (R$)"]["value"] == pytest.approx(11328.87, abs=0.01)


def test_faturas_moeda_empty_when_absent():
    sections = assemble_dre_sections(
        snapshot={}, budget=None, period_label="Maio 2026",
    )
    for key in ("nacional", "moedas"):
        body = [r for r in sections[key]["rows"] if r.get("kind") != "total"]
        assert body == []
