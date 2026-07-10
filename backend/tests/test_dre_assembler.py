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


def test_recebimento_area_parsed_from_snapshot(snapshot):
    # Per-area recebimento is now derived from SISJURI (CASO -> área jurídica),
    # verified to the centavo against the workbook (Fev 2026).
    r = RealizadoInputs.from_snapshot(snapshot)
    assert r.area_recebimento["Contencioso"] == pytest.approx(133202.74, abs=0.05)
    assert r.area_recebimento["Econômico"] == pytest.approx(117626.71, abs=0.05)
    assert r.area_recebimento["Arbitragem"] == pytest.approx(68404.13, abs=0.05)


def test_area_tab_recebimento_from_sisjuri(snapshot):
    # No manual overlay: the area tab's Recebimento realizado should come from
    # the snapshot's recebimento_area, not require manual entry.
    sections = assemble_dre_sections(snapshot=snapshot, budget=None, period_label="Fev 2026")
    receb = _row(sections["contencioso"]["rows"], RECEBIMENTO)
    assert receb["Realizado"]["value"] == pytest.approx(133202.74, abs=0.05)


def test_transfers_overlay_applied_to_area_recebimento(snapshot):
    # Resumo_Recebidas transfers net onto the SISJURI base per area.
    from app.manual.transfers import AreaTransfer

    transfers = [
        AreaTransfer("mbc", "2026-02", "Arbitragem", "Contencioso", 4362.575),
        AreaTransfer("mbc", "2026-02", "Arbitragem", "Contencioso", 1034.5535),
        AreaTransfer("mbc", "2026-02", "Arbitragem", "Econômico", 1034.5535),
    ]
    sections = assemble_dre_sections(
        snapshot=snapshot, budget=None, period_label="Fev 2026", transfers=transfers
    )
    conten = _row(sections["contencioso"]["rows"], RECEBIMENTO)
    arbitr = _row(sections["arbitragem"]["rows"], RECEBIMENTO)
    econ = _row(sections["economico"]["rows"], RECEBIMENTO)
    # base 133202.74 + 4362.575 + 1034.5535 = 138599.87
    assert conten["Realizado"]["value"] == pytest.approx(138599.87, abs=0.05)
    # base 68404.13 - 4362.575 - 1034.5535 - 1034.5535 = 61972.45
    assert arbitr["Realizado"]["value"] == pytest.approx(61972.45, abs=0.05)
    # base 117626.71 + 1034.5535 = 118661.26
    assert econ["Realizado"]["value"] == pytest.approx(118661.26, abs=0.05)


def test_manual_recebimento_is_ignored_sisjuri_wins(snapshot):
    # Recebimento is SISJURI-derived (CASO -> área jurídica) with Resumo_Recebidas
    # transfers applied upstream; a stray manual recebimento must NOT override it.
    sections = assemble_dre_sections(
        snapshot=snapshot, budget=None, period_label="Fev 2026",
        manual={"Contencioso": {RECEBIMENTO: 138600.13}},
    )
    receb = _row(sections["contencioso"]["rows"], RECEBIMENTO)
    assert receb["Realizado"]["value"] == pytest.approx(133202.74, abs=0.05)


def test_institutional_sections_roll_up_by_family(snapshot):
    r = RealizadoInputs.from_snapshot(snapshot)
    names = [s.name for s in r.sections]
    assert names[0] == "Ocupação"
    assert "Informática" in names
    ocup = next(s for s in r.sections if s.name == "Ocupação")
    # Verified vs Fechamento MBC 02.2026 (HANDOFF Appendix B): the workbook's
    # Ocupação = Aluguel+Condomínio+Energia+IPTU + Seguros ("Seguro Locação"),
    # and moves Manutenção e Conservação (020.010.0050) OUT to Despesas Gerais.
    assert ocup.total == pytest.approx(
        21707.78 + 4996 + 926.16 + 6916.97 + 182.71, abs=0.05
    )
    assert any("Aluguel" == n for n, _ in ocup.accounts)
    assert any("Seguros" == n for n, _ in ocup.accounts)
    assert not any("Manutenção e Conservação" == n for n, _ in ocup.accounts)


def test_custos_diretos_include_comissao(snapshot):
    # Client-confirmed (MEETING_2026-07-10): Custos Diretos = Custo equipe +
    # Participação/Comissão. Feb workbook: 216953.74 (equipe) + 1500 (comissão) =
    # 218453.74. The Institucional Resultado Bruto must subtract comissão too.
    from app.closing.dre import assemble_dre_sections

    snap = dict(snapshot)
    snap["ledger"] = {
        "custo_equipe": {"Contencioso": 76342.35, "Econômico": 78817.05, "Arbitragem": 61794.34},
        "comissao": {"Contencioso": 0.0, "Econômico": 1500.0, "Arbitragem": 0.0},
        "despesas_equipe": {"Contencioso": 0.0, "Econômico": 0.0, "Arbitragem": 0.0},
        "despesa_institucional_total": 0.0,
    }
    r = RealizadoInputs.from_snapshot(snap)
    assert r.comissao_total == pytest.approx(1500.0, abs=0.05)
    # Custos diretos = custo equipe (216953.74) + comissão (1500) = 218453.74
    assert r.custos_diretos == pytest.approx(218453.74, abs=0.05)


def test_imposto_is_fifteen_percent_of_recebimento(snapshot):
    # Client-confirmed (MEETING_2026-07-10): the DRE Imposto line is 15% of the
    # Recebimento (sacred), NOT the sum of the ledger tax accounts. Feb 2026:
    # 0.15 * 319233.58 = 47885.04 (matches the official dashboard exactly).
    r = RealizadoInputs.from_snapshot(snapshot)
    assert r.imposto == pytest.approx(0.15 * r.recebimento, abs=0.01)
    assert r.imposto == pytest.approx(47885.04, abs=0.05)


def test_resultado_bruto_and_liquido(snapshot):
    r = RealizadoInputs.from_snapshot(snapshot)
    # Resultado Bruto = Recebimento − Custos Diretos (equipe + comissão) − Despesas.
    assert r.resultado_bruto == pytest.approx(
        r.recebimento - r.custos_diretos - r.despesas, abs=0.05
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


def test_hard_rule_blanks_realizado_when_it_diverges_from_workbook_target(snapshot):
    # Client rule (MEETING_2026-07-10): NEVER show a Realizado number that does
    # not match the workbook. If the derived value differs from a known target by
    # more than R$0,01, the cell is blanked (null -> "ainda não temos").
    # Here we force a target that disagrees with the derived recebimento.
    targets = {"institucional": {RECEBIMENTO: 999999.0}}
    sections = assemble_dre_sections(
        snapshot=snapshot, budget=None, period_label="Fev 2026", targets=targets
    )
    receb = _row(sections["institucional"]["rows"], RECEBIMENTO)
    assert receb["Realizado"]["value"] is None


def test_hard_rule_keeps_realizado_when_it_matches_target(snapshot):
    # When the derived value matches the workbook target within R$0,01, keep it.
    targets = {"institucional": {RECEBIMENTO: 319233.58}}
    sections = assemble_dre_sections(
        snapshot=snapshot, budget=None, period_label="Fev 2026", targets=targets
    )
    receb = _row(sections["institucional"]["rows"], RECEBIMENTO)
    assert receb["Realizado"]["value"] == pytest.approx(319233.58, abs=0.05)


def test_hard_rule_shows_value_when_no_target_given(snapshot):
    # Where there is no known target, the derived value is shown as usual.
    sections = assemble_dre_sections(
        snapshot=snapshot, budget=None, period_label="Fev 2026", targets={}
    )
    receb = _row(sections["institucional"]["rows"], RECEBIMENTO)
    assert receb["Realizado"]["value"] == pytest.approx(319233.58, abs=0.05)


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


def test_ledger_block_drives_area_custo_comissao_despesas(snapshot):
    # When the snapshot carries a hand-ledger block (workbook Base_Resultado),
    # the area tabs use its per-area Custo equipe / Comissão / Despesas Equipe
    # (overriding the SISJURI custo_area aggregation), and derive Despesa
    # Institucional via the rateio rule. Values are the Feb 2026 workbook figures.
    from app.closing.dre import (
        COMISSAO,
        CUSTO_EQUIPE,
        DESPESA_INSTITUCIONAL,
        DESPESAS_EQUIPE,
    )

    snap = dict(snapshot)
    snap["ledger"] = {
        "custo_equipe": {"Contencioso": 76342.35, "Econômico": 78817.05, "Arbitragem": 61794.34},
        "comissao": {"Contencioso": 0.0, "Econômico": 1500.0, "Arbitragem": 0.0},
        "despesas_equipe": {"Contencioso": 2129.32, "Econômico": 3296.07, "Arbitragem": 2633.69},
        "despesa_institucional_total": 95047.39,
    }
    sections = assemble_dre_sections(snapshot=snap, budget=None, period_label="Fev 2026")
    conten = sections["contencioso"]["rows"]
    # Custo equipe comes from the ledger, NOT the SISJURI custo_area (49941.93).
    assert _row(conten, CUSTO_EQUIPE)["Realizado"]["value"] == pytest.approx(76342.35, abs=0.05)
    assert _row(conten, COMISSAO)["Realizado"]["value"] == pytest.approx(0.0, abs=0.05)
    assert _row(conten, DESPESAS_EQUIPE)["Realizado"]["value"] == pytest.approx(2129.32, abs=0.05)
    # Despesa Institucional (rateio): ratear = 95047.39 - (2129.32+3296.07+2633.69)
    # = 86988.31; Contencioso ratio = 76342.35 / 216953.74 -> 30609.71.
    assert _row(conten, DESPESA_INSTITUCIONAL)["Realizado"]["value"] == pytest.approx(
        30609.71, abs=0.05
    )
    econ = sections["economico"]["rows"]
    assert _row(econ, COMISSAO)["Realizado"]["value"] == pytest.approx(1500.0, abs=0.05)


def test_ledger_derived_despesa_institucional_overrides_manual(snapshot):
    # A ledger block makes Despesa Institucional derived; a stray manual value
    # must not shadow the rateio.
    from app.closing.dre import DESPESA_INSTITUCIONAL

    snap = dict(snapshot)
    snap["ledger"] = {
        "custo_equipe": {"Contencioso": 76342.35, "Econômico": 78817.05, "Arbitragem": 61794.34},
        "comissao": {"Contencioso": 0.0, "Econômico": 0.0, "Arbitragem": 0.0},
        "despesas_equipe": {"Contencioso": 2129.32, "Econômico": 3296.07, "Arbitragem": 2633.69},
        "despesa_institucional_total": 95047.39,
    }
    sections = assemble_dre_sections(
        snapshot=snap, budget=None, period_label="Fev 2026",
        manual={"Contencioso": {DESPESA_INSTITUCIONAL: 999999.0}},
    )
    di = _row(sections["contencioso"]["rows"], DESPESA_INSTITUCIONAL)
    assert di["Realizado"]["value"] == pytest.approx(30609.71, abs=0.05)


def test_derived_block_drives_area_custo_equipe(snapshot):
    # The SISJURI-derived custo_equipe_deriv block (per-lawyer components +
    # rateio_grupo + home_area) is authoritative for per-area Custo equipe,
    # overriding both the noisy custo_area aggregation AND any ledger block.
    from app.closing.dre import CUSTO_EQUIPE

    snap = dict(snapshot)
    snap["home_area"] = {
        "DC": "Equipe Contencioso",
        "MV": "Arbitragem",
        "AM": "Equipe Direito Econômico",
    }
    snap["rateio_grupo"] = [
        {"sigla": "AM", "grupo": "Equipe Contencioso", "percentual": 50},
        {"sigla": "AM", "grupo": "Equipe Direito Econômico", "percentual": 50},
    ]
    snap["custo_equipe_deriv"] = [
        {"sigla": "DC", "id_conta": "030.010.0010", "valor": 23379.0},
        {"sigla": "DC", "id_conta": "030.010.0050", "valor": 324.20},  # INSS excl
        {"sigla": "MV", "id_conta": "030.010.0010", "valor": 23379.0},
        {"sigla": "AM", "id_conta": "030.010.0010", "valor": 23379.0},
    ]
    # A stray ledger block must NOT win over the derived block.
    snap["ledger"] = {
        "custo_equipe": {"Contencioso": 1.0, "Econômico": 2.0, "Arbitragem": 3.0},
        "comissao": {}, "despesas_equipe": {}, "despesa_institucional_total": 0.0,
    }
    sections = assemble_dre_sections(snapshot=snap, budget=None, period_label="Fev 2026")
    conten = _row(sections["contencioso"]["rows"], CUSTO_EQUIPE)["Realizado"]["value"]
    econ = _row(sections["economico"]["rows"], CUSTO_EQUIPE)["Realizado"]["value"]
    arb = _row(sections["arbitragem"]["rows"], CUSTO_EQUIPE)["Realizado"]["value"]
    # DC 23.379 -> Contencioso; AM 23.379 split 50/50; MV 23.379 -> Arbitragem.
    assert conten == pytest.approx(23379.0 + 11689.5, abs=0.05)
    assert econ == pytest.approx(11689.5, abs=0.05)
    assert arb == pytest.approx(23379.0, abs=0.05)


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


def test_base_resultado_distribuicao_extras_block(snapshot):
    from app.closing.dre import assemble_base_resultado

    tab = assemble_base_resultado(snapshot, "Fev 2026")
    labels = [r["Linha"] for r in tab["rows"]]
    assert "Distribuição de Lucros extras" in labels
    for line in ("Bônus equipe", "DL excedente dos sócios", "DL Extraordinária",
                 "DL excedente MV", "Repasse Cacione"):
        assert line in labels, f"missing extras line: {line}"
    # The block total row carries the section_total kind.
    block = next(r for r in tab["rows"] if r["key"] == "distrib_extras")
    assert block["kind"] == "section_total"


def test_base_resultado_extras_values_from_snapshot():
    from app.closing.dre import assemble_base_resultado

    snap = {
        "distribuicao_extras": {
            "bonus_equipe": 101705.84,
            "dl_extraordinaria": 164477.34,
        }
    }
    tab = assemble_base_resultado(snap, "Fev 2026")
    bonus = next(r for r in tab["rows"] if r["key"] == "extra::bonus_equipe")
    assert bonus["Valor"]["value"] == pytest.approx(101705.84, abs=0.05)
    total = next(r for r in tab["rows"] if r["key"] == "distrib_extras")
    assert total["Valor"]["value"] == pytest.approx(266183.18, abs=0.05)


def test_base_resultado_lump_distribution_row(snapshot):
    from app.closing.dre import assemble_base_resultado

    tab = assemble_base_resultado(snapshot, "Fev 2026")
    lump = next(r for r in tab["rows"] if r["key"] == "distrib_fixa")
    assert lump["Valor"]["value"] == pytest.approx(172129.96, abs=0.05)


def test_all_workbook_tabs_emitted(snapshot):
    sections = assemble_dre_sections(
        snapshot=snapshot,
        budget={"institucional": {RECEBIMENTO: 671666.67}},
        period_label="Fev 2026",
    )
    for key in (
        "institucional", "institucional_ano", "contencioso", "economico",
        "arbitragem", "areas_sintetico", "base_resultado", "rateio_mensal",
        "amortizacao", "dre_2026", "fluxo_consolidado",
    ):
        assert key in sections, f"missing tab: {key}"


def test_dre_2026_has_twelve_month_columns_all_orcado():
    sections = assemble_dre_sections(
        snapshot=None,
        budget={"institucional": {RECEBIMENTO: 671666.67}},
        period_label="x",
    )
    dre = sections["dre_2026"]
    assert len(dre["columns"]) == 14  # Linha + Anual + 12 months
    row = dre["rows"][0]
    keys = list(row.keys())[: len(dre["columns"])]
    assert "is_total" not in keys  # metadata must not leak into columns
    assert row["Janeiro"]["value"] == pytest.approx(671666.67, abs=0.05)


def test_fluxo_consolidado_per_area_margin():
    sections = assemble_dre_sections(
        snapshot=None,
        budget=None,
        period_label="x",
        manual={"Contencioso": {RECEBIMENTO: 100000.0}},
    )
    rows = sections["fluxo_consolidado"]["rows"]
    margem = next(r for r in rows if r["key"] == "Contencioso::margem")
    assert margem["Valor"]["value"] is not None
