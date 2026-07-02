# backend/tests/test_dre_assembler.py
import json
from pathlib import Path

import pytest

from app.closing.dre import (
    RECEBIMENTO,
    RealizadoInputs,
    assemble_dre_sections,
    bonus_reserve,
)

FIXTURE = Path(__file__).parent / "fixtures" / "sisjuri_2026_02.json"


@pytest.fixture
def snapshot() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _row(rows, key):
    return next(r for r in rows if r.get("key") == key)


def test_realizado_base_is_recebimento(snapshot):
    r = RealizadoInputs.from_snapshot(snapshot)
    # Workbook bases the Institucional DRE on Recebimento (cash), not Faturamento.
    assert r.recebimento == pytest.approx(319233.58, abs=0.05)
    assert r.faturamento == pytest.approx(534752.84, abs=0.05)


def test_custo_equipe_prefers_area_breakdown(snapshot):
    r = RealizadoInputs.from_snapshot(snapshot)
    expected = 70796.83 + 49941.93 + 94571.59  # the three custo_area rows
    assert r.custo_equipe == pytest.approx(expected, abs=0.05)


def test_institutional_sections_roll_up_by_family(snapshot):
    r = RealizadoInputs.from_snapshot(snapshot)
    names = [s.name for s in r.sections]
    assert names[0] == "Ocupação"
    assert "Informática" in names
    ocup = next(s for s in r.sections if s.name == "Ocupação")
    # Aluguel+Condominio+Energia+IPTU+Manutencao
    assert ocup.total == pytest.approx(21707.78 + 4996 + 926.16 + 6916.97 + 50, abs=0.05)
    assert any("Aluguel" == n for n, _ in ocup.accounts)


def test_resultado_bruto_and_liquido(snapshot):
    r = RealizadoInputs.from_snapshot(snapshot)
    assert r.resultado_bruto == pytest.approx(
        r.recebimento - r.custo_equipe - r.despesas, abs=0.05
    )
    assert r.resultado_liquido == pytest.approx(
        r.resultado_bruto - r.imposto - r.amortizacao, abs=0.05
    )


def test_bonus_reserve_is_ten_percent():
    assert bonus_reserve(100000.0) == pytest.approx(10000.0)


def test_institucional_tab_uses_workbook_vocabulary(snapshot):
    sections = assemble_dre_sections(snapshot=snapshot, budget=None, period_label="Fevereiro 2026")
    inst = sections["institucional"]
    assert inst["name"] == "Institucional"
    assert inst["columns"] == ["Linha", "Orçado", "Realizado", "Desvio %"]
    labels = [r["Linha"] for r in inst["rows"]]
    for expected in ["Recebimento", "Custo equipe", "Despesas", "Resultado Bruto", "Imposto", "Amortização", "Resultado Liquido"]:
        assert expected in labels
    receb = _row(inst["rows"], RECEBIMENTO)
    assert receb["Realizado"]["value"] == pytest.approx(319233.58, abs=0.05)


def test_orcado_and_desvio_when_budget_present(snapshot):
    budget = {"institucional": {RECEBIMENTO: 671666.67}}
    sections = assemble_dre_sections(snapshot=snapshot, budget=budget, period_label="Fev 2026")
    receb = _row(sections["institucional"]["rows"], RECEBIMENTO)
    assert receb["Orçado"]["value"] == pytest.approx(671666.67, abs=0.05)
    assert receb["Desvio %"] == pytest.approx(319233.58 / 671666.67, abs=0.001)


def test_snapshot_missing_flag_and_zeroed():
    sections = assemble_dre_sections(snapshot=None, budget=None, period_label="Jan 2026")
    inst = sections["institucional"]
    assert inst["snapshot_missing"] is True
    receb = _row(inst["rows"], RECEBIMENTO)
    assert receb["Realizado"]["value"] == pytest.approx(0.0)


def test_area_tabs_present_with_workbook_lines(snapshot):
    sections = assemble_dre_sections(snapshot=snapshot, budget=None, period_label="Fev 2026")
    for key in ("contencioso", "economico", "arbitragem"):
        assert key in sections
        labels = [r["Linha"] for r in sections[key]["rows"]]
        assert labels == [
            "Recebimento", "Custo equipe", "Comissão",
            "Despesas Equipe", "Despesa Institucional", "Resultado Bruto",
        ]


def test_expense_section_rows_in_institucional(snapshot):
    sections = assemble_dre_sections(snapshot=snapshot, budget=None, period_label="Fev 2026")
    rows = sections["institucional"]["rows"]
    # Section-total rows carry kind=section_total; sub-accounts indent=1.
    assert any(r.get("kind") == "section_total" for r in rows)
    assert any(r.get("indent") == 1 for r in rows)


def test_base_resultado_groups_per_lawyer_by_area(snapshot):
    from app.closing.dre import assemble_base_resultado

    tab = assemble_base_resultado(snapshot, "Fevereiro 2026")
    assert tab["columns"] == ["Linha", "Valor"]
    labels = [r["Linha"] for r in tab["rows"]]
    assert "Movimentação de Entrada" in labels
    assert "Custo equipe - Contencioso" in labels
    assert "Custo equipe - Econômico" in labels
    assert "Custo equipe - Arbitragem" in labels
    assert "Impostos" in labels
    # A per-lawyer sub-row is present and indented.
    prof_rows = [r for r in tab["rows"] if r["key"].startswith("prof::")]
    assert prof_rows and all(r["indent"] == 1 for r in prof_rows)


def test_base_resultado_lump_distribution_row(snapshot):
    from app.closing.dre import assemble_base_resultado

    tab = assemble_base_resultado(snapshot, "Fev 2026")
    lump = next(r for r in tab["rows"] if r["key"] == "distrib_fixa")
    assert lump["Valor"]["value"] == pytest.approx(172129.96, abs=0.05)
