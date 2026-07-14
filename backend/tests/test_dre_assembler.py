# backend/tests/test_dre_assembler.py
import json
from pathlib import Path

import pytest

from app.closing.dre import (
    CUSTO_EQUIPE,
    RECEBIMENTO,
    RealizadoInputs,
    assemble_dre_sections,
    bonus_reserve,
)

FIXTURE = Path(__file__).parent / "fixtures" / "sisjuri_2026_02.json"
FIXTURE_MAY = Path(__file__).parent / "fixtures" / "sisjuri_2026_05.json"


@pytest.fixture
def snapshot() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.fixture
def snapshot_may() -> dict:
    return json.loads(FIXTURE_MAY.read_text(encoding="utf-8"))


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
    # more than the tolerance (R$1,00), the cell is blanked (-> "ainda não temos").
    # Here we force a target that disagrees with the derived recebimento.
    targets = {"institucional": {RECEBIMENTO: 999999.0}}
    sections = assemble_dre_sections(
        snapshot=snapshot, budget=None, period_label="Fev 2026", targets=targets
    )
    receb = _row(sections["institucional"]["rows"], RECEBIMENTO)
    assert receb["Realizado"]["value"] is None


def test_hard_rule_keeps_realizado_when_it_matches_target(snapshot):
    # When the derived value matches the workbook target within tolerance, keep it.
    targets = {"institucional": {RECEBIMENTO: 319233.58}}
    sections = assemble_dre_sections(
        snapshot=snapshot, budget=None, period_label="Fev 2026", targets=targets
    )
    receb = _row(sections["institucional"]["rows"], RECEBIMENTO)
    assert receb["Realizado"]["value"] == pytest.approx(319233.58, abs=0.05)


def test_hard_rule_uses_workbook_targets_for_the_month(snapshot):
    # End-to-end: the workbook targets loader supplies Feb 2026 targets. The
    # fixture's derived Imposto (15% * 319233.58 = 47885.04) matches the workbook
    # target exactly, so it is shown; the Institucional Custo equipe (Custos
    # Diretos) derived from the fixture (215310.35) does NOT match the workbook
    # target (218453.74), so the hard rule blanks it.
    from app.closing.workbook_targets import targets_for

    targets = targets_for("2026-02")
    sections = assemble_dre_sections(
        snapshot=snapshot, budget=None, period_label="Fev 2026", targets=targets
    )
    inst = sections["institucional"]["rows"]
    assert _row(inst, "imposto")["Realizado"]["value"] == pytest.approx(47885.04, abs=0.05)
    # Custos Diretos differ from the workbook -> blanked (never show a wrong number).
    assert _row(inst, "custo_equipe")["Realizado"]["value"] is None
    # And per-area Custo equipe (noisy SISJURI custo_area) also blanks under the
    # area target until we have the correct per-area SISJURI extract. This is the
    # safety net: diverging cells go blank rather than showing a wrong number.
    conten = sections["contencioso"]["rows"]
    assert _row(conten, CUSTO_EQUIPE)["Realizado"]["value"] is None


def test_hard_rule_shows_value_when_no_target_given(snapshot):
    # Where there is no known target, the derived value is shown as usual.
    sections = assemble_dre_sections(
        snapshot=snapshot, budget=None, period_label="Fev 2026", targets={}
    )
    receb = _row(sections["institucional"]["rows"], RECEBIMENTO)
    assert receb["Realizado"]["value"] == pytest.approx(319233.58, abs=0.05)


def test_area_despesas_equipe_budget_flows_into_orcado(snapshot):
    # POINT 13: the client inputs a per-area "Orçamento Despesa" (Despesas Equipe
    # budget). It is keyed by (area, despesas_equipe) and must flow into the
    # Orçado column of the corresponding area tab.
    from app.closing.dre import DESPESAS_EQUIPE

    budget = {
        "Contencioso": {DESPESAS_EQUIPE: 2500.0},
        "Econômico": {DESPESAS_EQUIPE: 3100.0},
    }
    sections = assemble_dre_sections(
        snapshot=snapshot, budget=budget, period_label="Fev 2026"
    )
    conten = _row(sections["contencioso"]["rows"], DESPESAS_EQUIPE)
    econ = _row(sections["economico"]["rows"], DESPESAS_EQUIPE)
    assert conten["Orçado"]["value"] == pytest.approx(2500.0, abs=0.01)
    assert econ["Orçado"]["value"] == pytest.approx(3100.0, abs=0.01)


def test_amortizacao_defaults_to_fixed_monthly(snapshot):
    # POINT 12: with no budgeted amortização, the DRE uses the fixed 8.117/mês
    # default (workbook 'Amortização' line), preserving today's behavior.
    from app.closing.workbook_layouts import AMORTIZACAO_MENSAL

    r = RealizadoInputs.from_snapshot(snapshot)
    assert r.amortizacao == pytest.approx(AMORTIZACAO_MENSAL, abs=0.01)


def test_amortizacao_uses_budgeted_annual_over_twelve(snapshot):
    # POINT 12: the client inputs ONE annual amortização per year; the monthly
    # DRE line = annual / 12. The budget carries the monthly value already (the
    # budget layer splits annual/12), so a budgeted institucional.amortizacao
    # drives the Realizado amortização line instead of the 8.117 constant.
    from app.closing.dre import AMORTIZACAO

    # Annual 120000 -> monthly budget 10000 (budget splits before assembly).
    budget = {"institucional": {AMORTIZACAO: 10000.0}}
    r = RealizadoInputs.from_snapshot(snapshot, amortizacao_mensal=10000.0)
    assert r.amortizacao == pytest.approx(10000.0, abs=0.01)
    # And it flows through assemble_dre_sections via the budget.
    sections = assemble_dre_sections(
        snapshot=snapshot, budget=budget, period_label="Fev 2026"
    )
    amort = _row(sections["institucional"]["rows"], AMORTIZACAO)
    assert amort["Realizado"]["value"] == pytest.approx(10000.0, abs=0.01)


def test_amortizacao_budget_zero_falls_back_to_default(snapshot):
    # A zero/unset budget amortização must fall back to the 8.117 default, never
    # zero the line out.
    from app.closing.dre import AMORTIZACAO
    from app.closing.workbook_layouts import AMORTIZACAO_MENSAL

    budget = {"institucional": {AMORTIZACAO: 0.0}}
    sections = assemble_dre_sections(
        snapshot=snapshot, budget=budget, period_label="Fev 2026"
    )
    amort = _row(sections["institucional"]["rows"], AMORTIZACAO)
    assert amort["Realizado"]["value"] == pytest.approx(AMORTIZACAO_MENSAL, abs=0.01)


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


def test_custo_equipe_por_area_ties_workbook_may(snapshot_may):
    # Real May 2026 SISJURI snapshot. Two fixes make per-area Custo equipe tie
    # the workbook targets to the centavo (see HANDOFF_2026-07-13 "MAJOR WIN"):
    #   FIX 1 — Vale (custo_equipe_area, the 500.010.<SIGLA> personal-debit
    #           postings) must NOT be added to per-area Custo equipe; it belongs
    #           to the transitória/Salários-ADM path (200.010.0010), not team cost.
    #   FIX 2 — for convênio médico (030.010.0110) use the parsed "Parte MBC"
    #           value from convenio_memo, not the gross posted amount.
    r = RealizadoInputs.from_snapshot(snapshot_may)
    assert r.area_custo_equipe["Contencioso"] == pytest.approx(74141.21, abs=0.01)
    assert r.area_custo_equipe["Econômico"] == pytest.approx(79436.24, abs=0.01)
    assert r.area_custo_equipe["Arbitragem"] == pytest.approx(54383.94, abs=0.01)
    # Σ custo equipe = 207961.39; + comissão 2128.07 = Custos Diretos 210089.46.
    assert r.custo_equipe == pytest.approx(207961.39, abs=0.01)


def test_vale_adm_ties_salarios_administracao_may(snapshot_may):
    # T4: Vale-ADM (VR 2.719,90 + VT 607,04 = 3.326,94) is paid via transitória
    # 200.010.0010 (not 020.050.*). The extract emits a top-level ``vale_adm``
    # total; the assembler adds it to the institutional "Salários Administração"
    # section AND moves FGTS-ADM (020.050.0060 = 400) to Impostos, so the family
    # ties the workbook to the centavo: 12.344,91.
    snap = dict(snapshot_may)
    snap["vale_adm"] = 3326.94
    r = RealizadoInputs.from_snapshot(snap)
    sal = next(s for s in r.sections if s.name == "Salários Administração")
    assert sal.total == pytest.approx(12344.91, abs=0.01)
    # FGTS-ADM must have left Salários Adm (it belongs to Impostos in the workbook).
    assert not any("FGTS" in nome for nome, _ in sal.accounts)
    # Vale-ADM appears as a leaf under Salários Administração.
    assert any("Vale" in nome for nome, _ in sal.accounts)


def test_vale_adm_absent_leaves_salarios_unchanged(snapshot_may):
    # Without a vale_adm key the section is unchanged except FGTS still moves out
    # (FGTS reclassification is account-driven, not gated on vale_adm). The live
    # fixture now carries vale_adm, so drop it here to test the absent case.
    snap = dict(snapshot_may)
    snap.pop("vale_adm", None)
    r = RealizadoInputs.from_snapshot(snap)
    sal = next(s for s in r.sections if s.name == "Salários Administração")
    # 9417.97 (current) - 400 FGTS = 9017.97; no Vale added.
    assert sal.total == pytest.approx(9017.97, abs=0.01)
    assert not any("Vale" in nome for nome, _ in sal.accounts)


def test_comissao_may_ehf_folds_to_economico(snapshot_may):
    # T2: once the extract emits the EHF Participação Interna row (from
    # CONTASPAGAR.COD_ADVG, since LANCAMENTO.LANCPROFDEST is NULL), the assembler
    # folds it via EHF's home area (Econômico) -> Comissão total 2.128,06.
    snap = dict(snapshot_may)
    snap["comissao_deriv"] = [
        {"kind": "lawyer", "sigla": "EHF", "area": None, "valor": 2128.06},
    ]
    r = RealizadoInputs.from_snapshot(snap)
    assert r.area_comissao.get("Econômico") == pytest.approx(2128.06, abs=0.01)
    assert r.comissao_total == pytest.approx(2128.06, abs=0.01)
    # Custos Diretos = Σ custo equipe (207961.39) + comissão (2128.06) = 210089.45.
    assert r.custos_diretos == pytest.approx(210089.45, abs=0.01)


def test_derived_comissao_shows_on_area_tab_without_ledger(snapshot_may):
    # The SISJURI-derived comissão must surface on the area tab even when there is
    # no hand-ledger (May is fully SISJURI-derived). Econômico shows 2.128,06.
    snap = dict(snapshot_may)
    snap["comissao_deriv"] = [
        {"kind": "lawyer", "sigla": "EHF", "area": None, "valor": 2128.06},
    ]
    sections = assemble_dre_sections(
        snapshot=snap, budget=None, period_label="Maio 2026"
    )
    econ = _row(sections["economico"]["rows"], "comissao")
    conten = _row(sections["contencioso"]["rows"], "comissao")
    assert econ["Realizado"]["value"] == pytest.approx(2128.06, abs=0.01)
    assert conten["Realizado"]["value"] == pytest.approx(0.0, abs=0.01)


def test_custo_equipe_may_passes_hard_rule(snapshot_may):
    # With the two fixes, the per-area Custo equipe now MATCHES the workbook
    # targets, so the hard rule shows the value instead of blanking it.
    from app.closing.workbook_targets import targets_for

    targets = targets_for("2026-05")
    sections = assemble_dre_sections(
        snapshot=snapshot_may, budget=None, period_label="Maio 2026", targets=targets
    )
    conten = _row(sections["contencioso"]["rows"], CUSTO_EQUIPE)
    econ = _row(sections["economico"]["rows"], CUSTO_EQUIPE)
    arb = _row(sections["arbitragem"]["rows"], CUSTO_EQUIPE)
    assert conten["Realizado"]["value"] == pytest.approx(74141.21, abs=0.01)
    assert econ["Realizado"]["value"] == pytest.approx(79436.24, abs=0.01)
    assert arb["Realizado"]["value"] == pytest.approx(54383.94, abs=0.01)


def test_despesas_liquido_override_lowers_gross_when_present(snapshot):
    # When the snapshot carries despesas_liquido, institutional accounts use the NET
    # value (workbook basis) instead of the gross despesas_conta. Here we force a net
    # for Contabilidade (020.040.0050) well below its gross and check it flows through.
    snap = dict(snapshot)
    # Feb fixture has no despesas_liquido; add a minimal one for one account.
    gross_row = next(
        (r for r in snap.get("despesas_conta", [])
         if str(r.get("id_conta")) == "020.040.0050"), None
    )
    if gross_row is None:
        pytest.skip("fixture lacks 020.040.0050")
    snap["despesas_liquido"] = [
        {"id_conta": "020.040.0050", "liquido": 1.0, "bruto": gross_row["total"]}
    ]
    snap["despesas_desdobramento"] = []
    r = RealizadoInputs.from_snapshot(snap)
    consult = next(s for s in r.sections if s.name == "Consultoria")
    # Contabilidade now contributes its net (1.0), not the gross, to Consultoria.
    assert any(abs(v - 1.0) < 0.01 for _, v in consult.accounts)


def test_despesas_liquido_excludes_custas_and_transporte(snapshot):
    # Accounts the workbook excludes from row-198 (Custas 020.030.0140, Transporte
    # 020.030.0060) are dropped when the líquido override is active.
    snap = dict(snapshot)
    snap["despesas_liquido"] = [
        {"id_conta": "020.030.0140", "liquido": 55.6, "bruto": 55.6},
        {"id_conta": "020.030.0060", "liquido": 968.1, "bruto": 968.1},
    ]
    snap["despesas_desdobramento"] = []
    r = RealizadoInputs.from_snapshot(snap)
    dg = next((s for s in r.sections if s.name == "Despesas Gerais"), None)
    if dg is not None:
        assert not any("Custas" in n for n, _ in dg.accounts)
        assert not any("Transporte" in n for n, _ in dg.accounts)


def test_margin_blanks_when_base_result_is_blanked(snapshot_may):
    # A margin (Margem Bruta / Líquida) must be hidden whenever its base result
    # (Resultado Bruto / Líquido) is blanked by the hard rule — otherwise the UI
    # shows a % for a value it is deliberately withholding (looks like a bug).
    # May: despesas doesn't tie -> Resultado Bruto/Líquido blank -> margins blank.
    from app.closing.workbook_targets import targets_for

    sections = assemble_dre_sections(
        snapshot=snapshot_may, budget=None, period_label="Maio 2026",
        targets=targets_for("2026-05"),
    )
    rows = sections["institucional"]["rows"]
    rb = _row(rows, "resultado_bruto")["Realizado"]["value"]
    mb = _row(rows, "margem_bruta")["Realizado"]["value"]
    rl = _row(rows, "resultado_liquido")["Realizado"]["value"]
    ml = _row(rows, "margem_liquida")["Realizado"]["value"]
    # Base results are blanked (despesas gap), so their margins must be blank too.
    assert rb is None and mb is None
    assert rl is None and ml is None


def test_margin_shows_when_base_result_shows(snapshot):
    # Conversely, when the base result is shown (no targets => hard rule is a
    # no-op), the margin is shown as usual.
    sections = assemble_dre_sections(
        snapshot=snapshot, budget=None, period_label="Fev 2026", targets={},
    )
    rows = sections["institucional"]["rows"]
    assert _row(rows, "resultado_bruto")["Realizado"]["value"] is not None
    assert _row(rows, "margem_bruta")["Realizado"]["value"] is not None


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


def test_bonus_equipe_from_account_150_snapshot_key():
    # POINT 16: team bonus = sum of individual employee bonuses held in the
    # accounting account 150.000.0000. The extract emits a top-level
    # ``bonus_equipe`` key (Σ of GERENC_LANCAMENTORESUMO ID_CONTA like '150.%').
    # It feeds the Base_Resultado "Bônus equipe" line and the block total.
    from app.closing.dre import assemble_base_resultado

    snap = {"bonus_equipe": 42000.0}
    tab = assemble_base_resultado(snap, "Fev 2026")
    bonus = next(r for r in tab["rows"] if r["key"] == "extra::bonus_equipe")
    assert bonus["Valor"]["value"] == pytest.approx(42000.0, abs=0.05)
    total = next(r for r in tab["rows"] if r["key"] == "distrib_extras")
    assert total["Valor"]["value"] == pytest.approx(42000.0, abs=0.05)


def test_bonus_equipe_explicit_extras_wins_over_top_level():
    # If the finance-entered distribuicao_extras.bonus_equipe is present it takes
    # precedence over the derived top-level ``bonus_equipe`` (explicit override).
    from app.closing.dre import assemble_base_resultado

    snap = {
        "bonus_equipe": 42000.0,
        "distribuicao_extras": {"bonus_equipe": 50000.0},
    }
    tab = assemble_base_resultado(snap, "Fev 2026")
    bonus = next(r for r in tab["rows"] if r["key"] == "extra::bonus_equipe")
    assert bonus["Valor"]["value"] == pytest.approx(50000.0, abs=0.05)


def test_bonus_equipe_blank_when_account_150_absent():
    # POINT 16: robust to the partner-split (POINT 17) not having arrived — when
    # no 150.* data is present, the line renders blank ("ainda não temos"),
    # never an invented number.
    from app.closing.dre import assemble_base_resultado

    tab = assemble_base_resultado({}, "Fev 2026")
    bonus = next(r for r in tab["rows"] if r["key"] == "extra::bonus_equipe")
    assert bonus["Valor"] is None


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
