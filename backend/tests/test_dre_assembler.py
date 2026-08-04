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
FIXTURE_JUN = Path(__file__).parent / "fixtures" / "sisjuri_2026_06.json"


@pytest.fixture
def snapshot() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.fixture
def snapshot_may() -> dict:
    return json.loads(FIXTURE_MAY.read_text(encoding="utf-8"))


@pytest.fixture
def snapshot_jun() -> dict:
    return json.loads(FIXTURE_JUN.read_text(encoding="utf-8"))


def _row(rows, key):
    return next(r for r in rows if r.get("key") == key)


def test_realizado_base_is_recebimento(snapshot):
    r = RealizadoInputs.from_snapshot(snapshot)
    # Workbook bases the Institucional DRE on Recebimento (cash), not Faturamento.
    assert r.recebimento == pytest.approx(319233.58, abs=0.05)
    assert r.faturamento == pytest.approx(534752.84, abs=0.05)


def test_custo_equipe_prefers_area_breakdown(snapshot):
    # Custo equipe comes from the per-person ``custo_equipe_deriv`` block (the
    # production basis, present in every v4 snapshot), NOT the coarse ``custo_area``
    # rollup. The 2026-08-04 fixture refresh gave the Feb fixture that block for the
    # first time — the old thin stub lacked it, so this pinned the fallback path.
    r = RealizadoInputs.from_snapshot(snapshot)
    assert r.custo_equipe == pytest.approx(220108.46, abs=0.05)


def test_recebimento_area_parsed_from_snapshot(snapshot):
    # Per-area recebimento uses the per-profissional RECEITA_REC basis rolled to the
    # home grupo (``recebimento_area_prof``), which is what the workbook shows — NOT
    # cash-by-case. Ties the workbook's own Feb "Areas Sintetico" Receita to the real
    # (Conten 159539 · Econ 119667 · Arb 62506). The old assertions here were the
    # cash-by-case figures, pinned only because the Feb stub lacked the prof block.
    r = RealizadoInputs.from_snapshot(snapshot)
    assert r.area_recebimento["Contencioso"] == pytest.approx(159538.62, abs=0.05)
    assert r.area_recebimento["Econômico"] == pytest.approx(119666.59, abs=0.05)
    assert r.area_recebimento["Arbitragem"] == pytest.approx(62506.41, abs=0.05)


def test_area_tab_recebimento_from_sisjuri(snapshot):
    # No manual overlay: the area tab's Recebimento realizado should come from the
    # snapshot (prof basis, see above), not require manual entry.
    sections = assemble_dre_sections(snapshot=snapshot, budget=None, period_label="Fev 2026")
    receb = _row(sections["contencioso"]["rows"], RECEBIMENTO)
    assert receb["Realizado"]["value"] == pytest.approx(159538.62, abs=0.05)


def test_recebimento_area_prof_is_preferred_and_ties_may_workbook():
    # 2026-07-14: the workbook's per-area Recebimento is the DEMONSTRATIVO
    # per-profissional basis (DB_RESULTADO_PROF.RECEITA_REC by NOMEGRUPO), NOT
    # cash-by-case. Proven vs the authoritative May book to R$1. The prof block
    # must take precedence over any legacy cash-by-case recebimento_area, and
    # "Não Alocados"/"Administração" grupos must be excluded (so the areas do NOT
    # sum to the sacred total — the workbook omits them too).
    snap = {
        "revenue": {"recebimento_bruto": 415927.84, "faturamento_bruto": 719988.05},
        # Real May grupo rollup from probe_recebimento_area_prof.sql:
        "recebimento_area_prof": [
            {"grupo": "Equipe Contencioso", "total": 240444.72, "fat": 336677.36},
            {"grupo": "Equipe Direito Econômico", "total": 166875.57, "fat": 177649.16},
            {"grupo": "Arbitragem", "total": 41997.50, "fat": 219430.24},
            {"grupo": "Equipe Ambiental", "total": -138.15, "fat": 5.97},
            {"grupo": "Não Alocados", "total": -33251.80, "fat": -13774.67},
            {"grupo": "Administração", "total": -0.01, "fat": -0.01},
        ],
        # A stray legacy cash-by-case block must NOT win over the prof basis.
        "recebimento_area": [
            {"area": "Contencioso", "total": 205157.46},
            {"area": "Direito Econômico", "total": 162472.56},
            {"area": "Arbitragem MV", "total": 48297.82},
        ],
    }
    r = RealizadoInputs.from_snapshot(snap)
    assert r.area_recebimento["Contencioso"] == pytest.approx(240444.72, abs=1.0)
    assert r.area_recebimento["Econômico"] == pytest.approx(166875.57, abs=1.0)
    # Arbitragem folds in Equipe Ambiental: 41997.50 + (-138.15) = 41859.35.
    assert r.area_recebimento["Arbitragem"] == pytest.approx(41859.35, abs=1.0)
    # Não Alocados / Administração are excluded → areas do NOT sum to sacred cash.
    assert sum(r.area_recebimento.values()) == pytest.approx(449179.64, abs=1.0)


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
    # base 159538.62 + 4362.575 + 1034.5535 = 164935.75
    assert conten["Realizado"]["value"] == pytest.approx(164935.75, abs=0.05)
    # base 62506.41 - 4362.575 - 1034.5535 - 1034.5535 = 56074.73
    assert arbitr["Realizado"]["value"] == pytest.approx(56074.73, abs=0.05)
    # base 119666.59 + 1034.5535 = 120701.14
    assert econ["Realizado"]["value"] == pytest.approx(120701.14, abs=0.05)


def test_recebimento_is_sisjuri_derived(snapshot):
    # Recebimento is SISJURI-derived (prof basis) with Resumo_Recebidas transfers
    # applied upstream — there is no manual per-area entry anymore.
    sections = assemble_dre_sections(
        snapshot=snapshot, budget=None, period_label="Fev 2026",
    )
    receb = _row(sections["contencioso"]["rows"], RECEBIMENTO)
    assert receb["Realizado"]["value"] == pytest.approx(159538.62, abs=0.05)


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


def test_per_area_custo_equipe_folds_lawyer_vale_june_workbook(snapshot_jun):
    """Lawyer Vale Refeição/Transporte (``custo_equipe_area``, 500.010.<SIGLA>)
    is part of per-área Custo equipe — folded by the lawyer's home area, exactly
    like the 030.010.* components.

    Client decision (2026-07 June validation): always include Vale. The June book
    is the proof — it books lawyer Vale where May left those rows blank:
      Contencioso 75.424,215 = 74.141,21 (030.010.*) + JVO Vale 1.283,00
      Econômico   80.536,845 = ... + VSR Vale 1.100,60
      Total das Áreas 210.345,00  (was 207.961,39 without Vale)
    Regression: without folding Vale, June rendered May's stale totals — the
    030.010.* components happen to be identical month-to-month, so Vale was the
    only mover, and dropping it made June == May."""
    r = RealizadoInputs.from_snapshot(snapshot_jun)
    assert r.area_custo_equipe["Contencioso"] == pytest.approx(75424.21, abs=0.05)
    assert r.area_custo_equipe["Econômico"] == pytest.approx(80536.85, abs=0.05)
    assert r.area_custo_equipe["Arbitragem"] == pytest.approx(54383.94, abs=0.05)
    assert sum(r.area_custo_equipe.values()) == pytest.approx(210345.00, abs=0.05)


#: Per-área Custo equipe for every closed month, from the production assembler over
#: the committed v4 fixtures. These are the exact cells ``scripts/reconcile_custo_equipe.py``
#: reconciles against the workbook to a 0,00 residual (18/18), and that the client
#: differences document cites. Jan/Mar/Abr had NO fixture guard before the 2026-08-04
#: refresh (handoff §4: "the biggest structural gap I am leaving behind") — pinning
#: them here closes it. May/Jun also live in test_workbook_targets / the test above;
#: kept together so a per-área custo regression fails in ONE obvious place.
_AREA_CUSTO_EQUIPE_2026 = {
    1: (73478.62, 75943.34, 62014.13),
    2: (76179.29, 80222.88, 63706.29),
    3: (74072.29, 78475.60, 49183.94),
    4: (76311.31, 81931.07, 55038.69),
    5: (75378.11, 79511.85, 54383.94),
    6: (75424.21, 80536.85, 54383.94),
}


def test_per_area_custo_equipe_is_pinned_every_closed_month():
    """Regression guard on all 18 per-área Custo equipe cells (3 áreas × 6 months).

    Promotes the stable output of ``scripts/reconcile_custo_equipe.py`` (which closes
    18/18 to 0,00 against the workbook, with each residual bucketed to a named cause).
    The script needs the workbook and hand-coded cause buckets, so it stays a script;
    this test pins the production numbers it validates so they cannot drift silently —
    the gap handoff §4 flagged for Jan/Mar/Abr specifically.
    """
    import json as _json
    from pathlib import Path as _Path

    fixtures_dir = _Path(__file__).parent / "fixtures"
    for month, (conten, econ, arb) in _AREA_CUSTO_EQUIPE_2026.items():
        snap = _json.loads(
            (fixtures_dir / f"sisjuri_2026_{month:02d}.json").read_text(encoding="utf-8")
        )
        ce = RealizadoInputs.from_snapshot(snap).area_custo_equipe
        assert ce["Contencioso"] == pytest.approx(conten, abs=0.05), f"2026-{month:02d}"
        assert ce["Econômico"] == pytest.approx(econ, abs=0.05), f"2026-{month:02d}"
        assert ce["Arbitragem"] == pytest.approx(arb, abs=0.05), f"2026-{month:02d}"


def test_custos_diretos_include_comissao(snapshot):
    # Client-confirmed (MEETING_2026-07-10): Custos Diretos = Custo equipe +
    # Participação/Comissão. The point of this test is that comissão is ADDED to
    # custo equipe. Custo equipe now comes from the SISJURI ``custo_equipe_deriv``
    # block (220108.46) which is authoritative over a ledger custo_equipe when
    # present (dre.py:613), so: 220108.46 + 1500 = 221608.46.
    snap = dict(snapshot)
    snap["ledger"] = {
        "custo_equipe": {"Contencioso": 76342.35, "Econômico": 78817.05, "Arbitragem": 61794.34},
        "comissao": {"Contencioso": 0.0, "Econômico": 1500.0, "Arbitragem": 0.0},
        "despesas_equipe": {"Contencioso": 0.0, "Econômico": 0.0, "Arbitragem": 0.0},
        "despesa_institucional_total": 0.0,
    }
    r = RealizadoInputs.from_snapshot(snap)
    assert r.comissao_total == pytest.approx(1500.0, abs=0.05)
    # Custos diretos = custo equipe (220108.46, deriv basis) + comissão (1500).
    assert r.custos_diretos == pytest.approx(221608.46, abs=0.05)


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


def test_bonus_reserve_is_signed_for_a_loss_month():
    # Reserva de bônus = signed 10% do Resultado Líquido — NOT floored at zero.
    # A loss month CONSUMES accumulated provision (a negative reserva), matching
    # the client's model. Proven against the June 2026 book: líquido -99.559,25 →
    # reserva -9.955,93 (workbook + Rumo's PPTX slide 13, which states outright
    # "Positivo = acúmulo de provisão; Negativo = consumo" and accumulates the
    # signed monthly values to its printed YTD of -11,5K).
    assert bonus_reserve(-99559.25) == pytest.approx(-9955.93)
    assert bonus_reserve(0.0) == 0.0


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


def test_per_area_orcado_derived_from_institucional_budget(snapshot):
    # The workbook derives every per-area Orçado from the single institucional
    # budget (it does NOT type a per-area budget). Replicate:
    #  - Recebimento: 37.5% Contencioso, 37.5% Econômico, 25% Arbitragem
    #  - Custo equipe: the per-area custo_equipe budget (monthly)
    #  - Despesa Institucional: pool * (area custo share), pool = inst despesas
    #    budget − Σ per-area despesas_equipe budget
    #  - Resultado Bruto: derived (Recb − Custo − Comissão − DespEq − DespInst)
    #  - Comissão: no workbook budget → blank
    from app.closing.dre import (
        COMISSAO,
        CUSTO_EQUIPE,
        DESPESA_INSTITUCIONAL,
        DESPESAS,
        DESPESAS_EQUIPE,
        RECEBIMENTO,
        RESULTADO_BRUTO,
    )

    # Monthly budget (assemble_dre_sections receives annual/12 already split).
    recb_m = 8060000.04 / 12
    desp_m = 1331793.83 / 12
    ce = {"Contencioso": 881797.78 / 12, "Econômico": 914114.79 / 12,
          "Arbitragem": 607970.17 / 12}
    de = {"Contencioso": 2110.49, "Econômico": 3174.82, "Arbitragem": 1901.49}
    budget = {
        "institucional": {RECEBIMENTO: recb_m, DESPESAS: desp_m},
        "Contencioso": {CUSTO_EQUIPE: ce["Contencioso"], DESPESAS_EQUIPE: de["Contencioso"]},
        "Econômico": {CUSTO_EQUIPE: ce["Econômico"], DESPESAS_EQUIPE: de["Econômico"]},
        "Arbitragem": {CUSTO_EQUIPE: ce["Arbitragem"], DESPESAS_EQUIPE: de["Arbitragem"]},
    }
    sections = assemble_dre_sections(
        snapshot=snapshot, budget=budget, period_label="Fev 2026"
    )

    def orc(area_key, line):
        return _row(sections[area_key]["rows"], line)["Orçado"]["value"]

    # Recebimento split 37.5 / 37.5 / 25.
    assert orc("contencioso", RECEBIMENTO) == pytest.approx(recb_m * 0.375, abs=0.02)
    assert orc("economico", RECEBIMENTO) == pytest.approx(recb_m * 0.375, abs=0.02)
    assert orc("arbitragem", RECEBIMENTO) == pytest.approx(recb_m * 0.25, abs=0.02)

    # Despesa Institucional: pool * custo-equipe share.
    pool = desp_m - sum(de.values())
    tot_ce = sum(ce.values())
    for area_key, area in (("contencioso", "Contencioso"), ("economico", "Econômico"),
                           ("arbitragem", "Arbitragem")):
        exp_di = pool * ce[area] / tot_ce
        assert orc(area_key, DESPESA_INSTITUCIONAL) == pytest.approx(exp_di, abs=0.02)
        # Resultado Bruto Orçado = Recb − Custo − DespEq − DespInst (Comissão 0).
        recb_o = recb_m * (0.25 if area == "Arbitragem" else 0.375)
        exp_rb = round(recb_o - ce[area] - de[area] - exp_di, 2)
        assert orc(area_key, RESULTADO_BRUTO) == pytest.approx(exp_rb, abs=0.05)
        # Comissão Orçado stays blank (no per-area comissão budget).
        assert _row(sections[area_key]["rows"], COMISSAO)["Orçado"]["value"] is None


def test_area_rows_compute_imposto_amort_liquido_reserva(snapshot):
    # Per-area DRE now extends past Resultado Bruto to Imposto (15% x área
    # recebimento), Amortização (área custo-equipe share of total amort), Resultado
    # Líquido (RB − Imposto − Amort) and signed Reserva (10% x líquido) — matching
    # the workbook area tabs + Rumo's PPTX slide 13 (reserva by área × mês).
    from app.closing.dre import (
        AMORTIZACAO,
        IMPOSTO,
        RESERVA_BONUS,
        RESULTADO_LIQUIDO,
    )
    from app.closing.workbook_layouts import IMPOSTO_RATE

    sections = assemble_dre_sections(
        snapshot=snapshot, budget={}, period_label="Fev 2026"
    )
    r = RealizadoInputs.from_snapshot(snapshot)
    tot_custo = sum(r.area_custo_equipe.values())

    for area_key, area in (("contencioso", "Contencioso"),
                           ("economico", "Econômico"), ("arbitragem", "Arbitragem")):
        rows = sections[area_key]["rows"]
        receb = _row(rows, "recebimento")["Realizado"]["value"]
        rb = _row(rows, "resultado_bruto")["Realizado"]["value"]
        if receb is None or rb is None:
            continue  # blanked cell — skip (still must not crash)
        imposto = _row(rows, IMPOSTO)["Realizado"]["value"]
        amort = _row(rows, AMORTIZACAO)["Realizado"]["value"]
        liq = _row(rows, RESULTADO_LIQUIDO)["Realizado"]["value"]
        res = _row(rows, RESERVA_BONUS)["Realizado"]["value"]
        # Imposto = 15% x área recebimento.
        assert imposto == pytest.approx(round(receb * IMPOSTO_RATE, 2), abs=0.02)
        # Amortização = total amort x área custo share.
        exp_amort = round(r.amortizacao * r.area_custo_equipe.get(area, 0.0) / tot_custo, 2)
        assert amort == pytest.approx(exp_amort, abs=0.02)
        # Líquido = RB − Imposto − Amort; Reserva = signed 10% (loss → negative).
        assert liq == pytest.approx(round(rb - imposto - amort, 2), abs=0.02)
        assert res == pytest.approx(round(liq * 0.10, 2), abs=0.02)


def test_per_area_orcado_blank_without_institucional_recebimento_budget(snapshot):
    # No institucional recebimento budget → per-area Recebimento Orçado is blank
    # (no crash), and Resultado Bruto Orçado stays blank too.
    from app.closing.dre import RECEBIMENTO, RESULTADO_BRUTO

    sections = assemble_dre_sections(
        snapshot=snapshot, budget={"Contencioso": {"custo_equipe": 70000.0}},
        period_label="Fev 2026",
    )
    assert _row(sections["contencioso"]["rows"], RECEBIMENTO)["Orçado"]["value"] is None
    assert _row(sections["contencioso"]["rows"], RESULTADO_BRUTO)["Orçado"]["value"] is None


def test_per_area_orcado_ties_june_workbook_with_despesa_para_ratear(snapshot):
    # The BUG found live in the 2026-07 meeting: per-area Despesa Equipe + Despesa
    # Institucional Orçado were zero/wrong, so per-area Orçado Resultado Bruto
    # diverged (Econ 134.637 vs workbook 136.199). The workbook's real formula
    # (proven to the centavo vs Fechamento MBC 06.2026, June):
    #   DespEq[area]   = typed per-area Despesas Área budget
    #   DespInst[area] = "Despesa para ratear" pool × area custo-equipe rateio share
    #                    (share = area custo budget / Σ area custo budgets)
    #   RB[area]       = Recb(37.5/37.5/25) − Custo − DespEq − DespInst
    from app.closing.dre import (
        CUSTO_EQUIPE,
        DESPESA_INSTITUCIONAL,
        DESPESA_PARA_RATEAR,
        DESPESAS,
        DESPESAS_EQUIPE,
        RESULTADO_BRUTO,
    )

    # June monthly budget values (Orçamento 2026, col Jun).
    recb_m = 671666.67
    pool = 99043.94  # Despesa para ratear (June)
    ce = {"Contencioso": 74454.07, "Econômico": 75379.17, "Arbitragem": 49236.38}
    de = {"Contencioso": 2110.49, "Econômico": 3174.41, "Arbitragem": 1901.49}
    # Annual custo-equipe budget drives the FIXED rateio share (workbook "Rateio
    # anual"): C=0.369672 / E=0.374805 / A=0.255523.
    ce_annual = {"Contencioso": 901597.73, "Econômico": 914114.75, "Arbitragem": 623198.16}
    budget = {
        "institucional": {DESPESA_PARA_RATEAR: pool, DESPESAS: 106230.33,
                          "recebimento": recb_m},
        "Contencioso": {CUSTO_EQUIPE: ce["Contencioso"], DESPESAS_EQUIPE: de["Contencioso"]},
        "Econômico": {CUSTO_EQUIPE: ce["Econômico"], DESPESAS_EQUIPE: de["Econômico"]},
        "Arbitragem": {CUSTO_EQUIPE: ce["Arbitragem"], DESPESAS_EQUIPE: de["Arbitragem"]},
    }
    budget_annual = {
        "Contencioso": {CUSTO_EQUIPE: ce_annual["Contencioso"]},
        "Econômico": {CUSTO_EQUIPE: ce_annual["Econômico"]},
        "Arbitragem": {CUSTO_EQUIPE: ce_annual["Arbitragem"]},
    }
    sections = assemble_dre_sections(
        snapshot=snapshot, budget=budget, budget_annual=budget_annual,
        period_label="Jun 2026",
    )

    def orc(area_key, line):
        return _row(sections[area_key]["rows"], line)["Orçado"]["value"]

    # Despesa Equipe Orçado now fills (was blank) and ties the workbook.
    assert orc("economico", DESPESAS_EQUIPE) == pytest.approx(3174.41, abs=0.01)
    # Despesa Institucional Orçado uses the pool × custo share (not a self pool).
    for ak, want_di, want_rb in (
        ("contencioso", 36613.80, 138696.64),
        ("economico", 37122.12, 136199.31),
        ("arbitragem", 25308.02, 91470.78),
    ):
        assert orc(ak, DESPESA_INSTITUCIONAL) == pytest.approx(want_di, abs=0.10)
        assert orc(ak, RESULTADO_BRUTO) == pytest.approx(want_rb, abs=0.15)


def test_per_area_orcado_imposto_and_amortizacao_tie_june_workbook(snapshot):
    """Adriana, 2026-07-28 14:30: *"Por que não está puxando aqui o orçado? O orçado
    amortização e impostos."* Present for Institucional, blank for all three áreas
    (Areas Sintetico AND the presentation deck, 30:30).

    The workbook types no per-área budget for either line — it derives both, and its
    formulas are explicit (``Areas Sintetico atualizado``, June Orçado col V):

        Impostos     =V36*$A$34             → área Recebimento Orçado × 15%
        Amortização  =V29*'Rateio Mensal'!M2 → inst Amortização Orçado × área share

    where ``Rateio Mensal`` M2:M4 = ``L/$L$5`` and L is the **annual** custo-equipe
    budget ('Rateio anual', L2 = 'DRE 2026'!B6) — the SAME fixed annual share that
    already drives Despesa Institucional here, not the month's custo. Verified to the
    centavo against Fechamento MBC 06.2026 for all three áreas.
    """
    from app.closing.dre import (
        AMORTIZACAO,
        CUSTO_EQUIPE,
        DESPESA_PARA_RATEAR,
        DESPESAS,
        DESPESAS_EQUIPE,
        IMPOSTO,
    )

    recb_m = 671666.67
    ce = {"Contencioso": 74454.07, "Econômico": 75379.17, "Arbitragem": 49236.38}
    de = {"Contencioso": 2110.49, "Econômico": 3174.41, "Arbitragem": 1901.49}
    ce_annual = {"Contencioso": 901597.73, "Econômico": 914114.75, "Arbitragem": 623198.16}
    budget = {
        "institucional": {
            DESPESA_PARA_RATEAR: 99043.94, DESPESAS: 106230.33,
            "recebimento": recb_m, AMORTIZACAO: 8117.0,
        },
        "Contencioso": {CUSTO_EQUIPE: ce["Contencioso"], DESPESAS_EQUIPE: de["Contencioso"]},
        "Econômico": {CUSTO_EQUIPE: ce["Econômico"], DESPESAS_EQUIPE: de["Econômico"]},
        "Arbitragem": {CUSTO_EQUIPE: ce["Arbitragem"], DESPESAS_EQUIPE: de["Arbitragem"]},
    }
    budget_annual = {a: {CUSTO_EQUIPE: v} for a, v in ce_annual.items()}
    sections = assemble_dre_sections(
        snapshot=snapshot, budget=budget, budget_annual=budget_annual,
        period_label="Jun 2026",
    )

    def orc(area_key, line):
        return _row(sections[area_key]["rows"], line)["Orçado"]["value"]

    # Workbook June Orçado: rows 46/47 (Conten), 64/65 (Econ), 82/83 (Arb).
    for ak, want_imposto, want_amort in (
        ("contencioso", 37781.25, 3000.63),
        ("economico", 37781.25, 3042.29),
        ("arbitragem", 25187.50, 2074.08),
    ):
        assert orc(ak, IMPOSTO) == pytest.approx(want_imposto, abs=0.01)
        assert orc(ak, AMORTIZACAO) == pytest.approx(want_amort, abs=0.01)


def test_per_area_orcado_amortizacao_blank_without_institucional_amort_budget(snapshot):
    # Amortização Orçado has no per-área fallback: without an institucional
    # amortização budget the line stays blank rather than inventing a share of the
    # 8.117 worksheet default (which is a *realizado* default, not a budget).
    from app.closing.dre import AMORTIZACAO, CUSTO_EQUIPE, IMPOSTO, RECEBIMENTO

    sections = assemble_dre_sections(
        snapshot=snapshot,
        budget={
            "institucional": {RECEBIMENTO: 671666.67},
            "Contencioso": {CUSTO_EQUIPE: 74454.07},
        },
        budget_annual={"Contencioso": {CUSTO_EQUIPE: 901597.73}},
        period_label="Jun 2026",
    )
    rows = sections["contencioso"]["rows"]
    # Imposto still derives (its base, área Recebimento Orçado, is budgeted)...
    assert _row(rows, IMPOSTO)["Orçado"]["value"] == pytest.approx(37781.25, abs=0.01)
    # ...but Amortização has no input, so it stays blank.
    assert _row(rows, AMORTIZACAO)["Orçado"]["value"] is None


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
            "Imposto", "Amortização", "Resultado Líquido", "Reserva de Bônus",
        ]


def test_ledger_block_drives_area_custo_comissao_despesas(snapshot):
    # When the snapshot carries a hand-ledger block (workbook Base_Resultado), the
    # area tabs use its per-area Comissão / Despesas Equipe and derive Despesa
    # Institucional via the rateio rule. Custo equipe, however, is authoritative from
    # the SISJURI ``custo_equipe_deriv`` block when present (dre.py:610-615) — the
    # ledger custo_equipe only wins when that block is ABSENT. The Feb fixture gained
    # the deriv block in the 2026-08-04 refresh, so Contencioso reads 76179.29 (the
    # DB-derived value), not the ledger's 76342.35.
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
    # Custo equipe: the SISJURI deriv block wins over the ledger when present.
    assert _row(conten, CUSTO_EQUIPE)["Realizado"]["value"] == pytest.approx(76179.29, abs=0.05)
    assert _row(conten, COMISSAO)["Realizado"]["value"] == pytest.approx(0.0, abs=0.05)
    assert _row(conten, DESPESAS_EQUIPE)["Realizado"]["value"] == pytest.approx(2129.32, abs=0.05)
    # Despesa Institucional (rateio): ratear = 95047.39 - (2129.32+3296.07+2633.69)
    # = 86988.31; Contencioso ratio = 76342.35 / 216953.74 -> 30609.71.
    assert _row(conten, DESPESA_INSTITUCIONAL)["Realizado"]["value"] == pytest.approx(
        30609.71, abs=0.05
    )
    econ = sections["economico"]["rows"]
    assert _row(econ, COMISSAO)["Realizado"]["value"] == pytest.approx(1500.0, abs=0.05)


def test_ledger_derived_despesa_institucional_uses_rateio(snapshot):
    # A ledger block makes Despesa Institucional derived via the rateio rule.
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
    )
    di = _row(sections["contencioso"]["rows"], DESPESA_INSTITUCIONAL)
    assert di["Realizado"]["value"] == pytest.approx(30609.71, abs=0.05)


def test_area_despesa_institucional_derived_from_db_without_ledger(snapshot_may):
    # Workbook-free path: with no `ledger` block, per-area Despesa Institucional
    # must still be DB-derived via the rateio rule (institutional overhead
    # apportioned by each area's share of total Custo equipe), NOT left blank.
    # NOTE: this checks the derivation runs and is self-consistent. The per-área
    # Despesas Área allocation (GAP 2) was RESOLVED by Renata (2026-07-16): allocate
    # by label/cost-center, which the DB already does; see
    # test_workbook_targets.test_may_per_area_resultado_bruto_uses_renata_despesas_area_ruling.
    #
    # The pool that is rateized is the institutional despesa MINUS the per-área
    # Despesas Equipe (dre.py:648-657) — those team expenses are carried on their own
    # área line and must not be double-counted in the institutional rateio. The May
    # fixture gained the ``despesas_equipe_area`` block in the 2026-08-04 refresh, so
    # this now exercises the carve-out; the old thin fixture had an empty
    # ``area_despesas_equipe`` and the pool equalled the full despesa.
    from app.closing.dre import DESPESA_INSTITUCIONAL, RealizadoInputs

    r = RealizadoInputs.from_snapshot(snapshot_may)
    assert not r.has_ledger  # the May fixture carries no workbook ledger
    total_desp = r.despesas
    tot_ce = sum(r.area_custo_equipe.values())
    pool = round(total_desp - sum(r.area_despesas_equipe.values()), 2)

    sections = assemble_dre_sections(
        snapshot=snapshot_may, budget=None, period_label="Maio 2026"
    )
    got = {}
    for area, key in (("Contencioso", "contencioso"), ("Econômico", "economico"),
                      ("Arbitragem", "arbitragem")):
        di = _row(sections[key]["rows"], DESPESA_INSTITUCIONAL)["Realizado"]["value"]
        assert di is not None, f"{area} Despesa Institucional blanked without a ledger"
        expected = round(pool * r.area_custo_equipe[area] / tot_ce, 2)
        assert di == pytest.approx(expected, abs=0.05)
        got[area] = di
    # Conservation: the three áreas sum to the POOL (not the full despesa — the
    # per-área Despesas Equipe were carved out first). A tautology given the shares
    # sum to 1, so it only proves no money leaks in the split, not that it is right.
    assert sum(got.values()) == pytest.approx(pool, abs=0.05)


def test_per_area_desp_inst_rateio_identity_holds_every_closed_month():
    """Per-área Despesa Institucional = POOL × (área custo share), exact, all months.

    Promotes ``scripts/audit_desp_inst_rateio.py`` to a guarded test. That script
    proved (live, 2026-08-03) that the per-área Despesa Institucional is an IDENTITY,
    not an estimate: it is the institutional pool apportioned by each área's share of
    total Custo equipe, exact to R$0,01, and the three áreas conserve the pool in
    every month. Nothing protected that finding — the client differences document
    leans on it (a per-área difference here comes from the POOL, i.e. the institutional
    total, never from a per-área cause). Uses the production assembler over all six
    committed fixtures; needs no workbook.
    """
    import json as _json
    from pathlib import Path as _Path

    from app.closing.dre import DESPESA_INSTITUCIONAL, RealizadoInputs

    fixtures_dir = _Path(__file__).parent / "fixtures"
    for month in range(1, 7):
        snap = _json.loads(
            (fixtures_dir / f"sisjuri_2026_{month:02d}.json").read_text(encoding="utf-8")
        )
        r = RealizadoInputs.from_snapshot(snap)
        if r.has_ledger:  # ledger months take the workbook rateio, not this identity
            continue
        tot_ce = sum(r.area_custo_equipe.values())
        assert tot_ce, f"2026-{month:02d}: no per-área custo equipe to rateize by"
        pool = round(r.despesas - sum(r.area_despesas_equipe.values()), 2)

        sections = assemble_dre_sections(
            snapshot=snap, budget=None, period_label=f"2026-{month:02d}"
        )
        got = {}
        for area, key in (("Contencioso", "contencioso"), ("Econômico", "economico"),
                          ("Arbitragem", "arbitragem")):
            di = _row(sections[key]["rows"], DESPESA_INSTITUCIONAL)["Realizado"]["value"]
            assert di is not None, f"2026-{month:02d} {area} Despesa Institucional blank"
            expected = round(pool * r.area_custo_equipe[area] / tot_ce, 2)
            assert di == pytest.approx(expected, abs=0.05), f"2026-{month:02d} {area}"
            got[area] = di
        # The three áreas conserve the pool — no money leaks in the redistribution.
        assert sum(got.values()) == pytest.approx(pool, abs=0.05), f"2026-{month:02d}"


# Real May cost-center rollup of the Grupo='S' Despesas Área families — the AUTHORITATIVE
# live values from the re-run extract's ``despesas_equipe_area`` block (Σ 5.994,78):
#   ECT = AASP 217,40 + IBRAC 700,09 = 917,49
#   EDE = IBRAC 700,10 + Cursos 1.600 + passagens 1.358,72 + pão-de-queijo/reunião WM 146 = 3.804,82
#   ESP = Patrocínio 1.204,47 + assento 68 = 1.272,47
MAY_DESPESAS_EQUIPE_AREA = [
    {"cc": "ECT", "total": 917.49, "n": 2},
    {"cc": "EDE", "total": 3804.82, "n": 4},
    {"cc": "ESP", "total": 1272.47, "n": 2},
]


def test_despesas_equipe_area_from_db_cost_center(snapshot_may):
    # GAP 2 (DB-only): per-area Despesas Equipe is the Grupo='S' family lines tagged
    # by cost-center (ECT=Contencioso / EDE=Econômico / ESP=Arbitragem), from the
    # extract's ``despesas_equipe_area`` block. No manual input, no ledger.
    from app.closing.dre import DESPESAS_EQUIPE, RealizadoInputs

    snap = dict(snapshot_may)
    snap["despesas_equipe_area"] = MAY_DESPESAS_EQUIPE_AREA
    r = RealizadoInputs.from_snapshot(snap)
    assert r.area_despesas_equipe["Contencioso"] == pytest.approx(917.49, abs=0.05)
    assert r.area_despesas_equipe["Econômico"] == pytest.approx(3804.82, abs=0.05)
    assert r.area_despesas_equipe["Arbitragem"] == pytest.approx(1272.47, abs=0.05)

    sections = assemble_dre_sections(snapshot=snap, budget=None, period_label="Maio 2026")
    de = _row(sections["contencioso"]["rows"], DESPESAS_EQUIPE)["Realizado"]["value"]
    assert de == pytest.approx(917.49, abs=0.05)


def test_area_despesa_institucional_carves_out_despesas_equipe(snapshot_may):
    # With per-area Despesas Equipe present (GAP 2), the Despesa Institucional rateio
    # apportions only the REMAINDER (despesas_total − ΣDespesasÁrea), and the whole
    # institutional despesa is still conserved: ΣDespesasEquipe + ΣDespesaInstitucional
    # == despesas_total. (The centavo-tie to the May book — 35.555 / 38.095 / 26.081 —
    # is validated against the LIVE snapshot, whose despesas total is 105.640,60; this
    # fixture predates the líquido re-run so its total differs, hence structural checks
    # here rather than the book's exact numbers.) The workbook's own ΣDespesasÁrea
    # (5.780,79) differs from the DB's self-consistent 5.848,78 due to a spreadsheet
    # quirk (a mis-referenced Viagens row + a dropped R$68 line); DB is authoritative.
    from app.closing.dre import DESPESA_INSTITUCIONAL, RealizadoInputs

    snap = dict(snapshot_may)
    snap["despesas_equipe_area"] = MAY_DESPESAS_EQUIPE_AREA
    r = RealizadoInputs.from_snapshot(snap)
    sections = assemble_dre_sections(snapshot=snap, budget=None, period_label="Maio 2026")

    di_sum = 0.0
    tot_ce = sum(r.area_custo_equipe.values())
    ratear = r.despesas - sum(r.area_despesas_equipe.values())
    for area, key in (("Contencioso", "contencioso"), ("Econômico", "economico"),
                      ("Arbitragem", "arbitragem")):
        di = _row(sections[key]["rows"], DESPESA_INSTITUCIONAL)["Realizado"]["value"]
        assert di is not None
        # rateio is of the REMAINDER, by CE share
        assert di == pytest.approx(ratear * r.area_custo_equipe[area] / tot_ce, abs=0.05)
        di_sum += di
    # Conservation across the full institutional despesa.
    assert di_sum + sum(r.area_despesas_equipe.values()) == pytest.approx(r.despesas, abs=0.05)


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
    # Real May 2026 SISJURI snapshot. Per-area Custo equipe = 030.010.* per-lawyer
    # components + lawyer Vale (custo_equipe_area) folded by home area, with the
    # convênio médico (030.010.0110) using the parsed "Parte MBC" value from
    # convenio_memo (not the gross posted amount).
    #
    # RE-BASELINED 2026-07 (client "always include Vale"): May now folds JVO Vale
    # 1.236,90 → Contencioso and VSR Vale 75,60 → Econômico, matching the JUNE
    # methodology. The May book's Custo-equipe cells left Vale blank, so these
    # exceed the old May-book targets by exactly the Vale amounts — the targets
    # file was re-baselined in lock-step (workbook_targets_2026.json).
    r = RealizadoInputs.from_snapshot(snapshot_may)
    assert r.area_custo_equipe["Contencioso"] == pytest.approx(75378.11, abs=0.01)
    assert r.area_custo_equipe["Econômico"] == pytest.approx(79511.85, abs=0.01)
    assert r.area_custo_equipe["Arbitragem"] == pytest.approx(54383.94, abs=0.01)
    # Σ custo equipe = 209273.90; + comissão 2128.06 = Custos Diretos 211401.96.
    assert r.custo_equipe == pytest.approx(209273.90, abs=0.01)


def test_convenio_memo_is_ignored_when_it_does_not_describe_this_month(snapshot_jun):
    """A ``convenio_memo`` that cites a plan value which was NOT posted is STALE.

    Found 2026-08-03 while decomposing the jan/fev convênio difference, which I had
    written up as "needs a finance ruling". It does not — the DB answers it:

    * EHF's posted 030.010.0110 is **2.122,30 in all six months** (one plan all year).
    * The mar–jun memo cites exactly that 2.122,30 and derives Parte MBC 1.564,10.
    * The jan/fev memo cites **968,65** — a value never posted in those months — and
      derives 603,50 off it. Same for RB in February (memo says 3.543,45, posted
      3.427,58).

    So jan/fev carries a leftover note from an older plan while the posting had already
    moved. Trusting it understated Econômico by 2.962,41/month and Arbitragem by
    1.911,95 in February. The workbook uses the standing Parte MBC in every month, which
    is what the POSTED plan implies — so the book was right and we were wrong.

    The guard: only apply the memo override when the memo mentions the amount actually
    posted for that lawyer that month. This is self-detecting from the data — no
    hardcoded month, no fitting to the workbook.
    """
    snap = json.loads(json.dumps(snapshot_jun))  # deep copy
    posted = next(
        r["valor"]
        for r in snap["custo_equipe_deriv"]
        if r.get("sigla") == "EHF" and r.get("id_conta") == "030.010.0110"
    )
    assert posted == pytest.approx(2122.30, abs=0.01)

    # A CURRENT memo (mentions the posted 2.122,30) must still be applied: June's
    # client-validated Econômico stands.
    assert RealizadoInputs.from_snapshot(snap).area_custo_equipe[
        "Econômico"
    ] == pytest.approx(80536.85, abs=0.01)

    # Now make the memo STALE the way jan/fev are: it derives a Parte MBC from a plan
    # value (968,65) that was never posted this month.
    for memo in snap["convenio_memo"]:
        if memo["sigla"] == "EHF":
            memo["raw_memo"] = (
                "Convêno Médico  EHF- Plano: SOHO60E - Valor968,65  A parte de "
                "dependentes EHF e upgrade estão lançadas na conta 500.EHF**\r\n\r\n"
                "1.795,86-1.192,36 ( Parte MBC)=603,50"
            )
            memo["parsed_valor"] = 603.50
    stale = RealizadoInputs.from_snapshot(snap).area_custo_equipe["Econômico"]

    # The stale 603,50 must NOT be applied. With NO cross-month information (a
    # single-month caller passes no ``convenio_shares``) what stands is the POSTED gross
    # (2.122,30) — the honest answer when this month's data alone cannot recover the MBC
    # share. Deliberately NOT hardcoding 1.564,10 here: that would be fitting to the
    # workbook from a month that does not contain it.
    #
    # A caller that DOES have the other months closes this properly — see
    # ``test_stale_convenio_memo_rebuilds_parte_mbc_from_the_learned_share``.
    assert stale == pytest.approx(81095.04, abs=0.02), (
        "a stale memo must fall back to the POSTED value, not apply its own figure"
    )
    assert stale > 80536.85, "ignoring a stale discount must not lower the cost"


def test_convenio_share_is_learned_only_from_trustworthy_months():
    """``convenio_mbc_shares`` reads the Parte MBC share off the months whose memo is
    CURRENT, and ignores the stale ones.

    The share is what lets a stale month show the MBC share instead of the posted gross.
    It must come from the data — never a constant — so this pins the extraction, not a
    number: a stale month must not contribute, and a lawyer whose trusted months
    DISAGREE must get no share at all (falling back beats averaging two plans into a
    figure nobody wrote).
    """
    from app.closing.dre import convenio_mbc_shares

    def month(posted: float, memo_value: float, memo_text: str) -> dict:
        return {
            "custo_equipe_deriv": [
                {"sigla": "XX", "id_conta": "030.010.0110", "valor": posted}
            ],
            "convenio_memo": [
                {"sigla": "XX", "parsed_valor": memo_value, "raw_memo": memo_text}
            ],
        }

    # A CURRENT memo (mentions the posted 1.000,00) yields the share 0,70.
    current = month(1000.0, 700.0, "Plano - Valor R$ 1.000,00 ... (Parte MBC) = 700,00")
    assert convenio_mbc_shares({3: current})["XX"] == pytest.approx(0.70, abs=1e-9)

    # A STALE memo (cites 500,00, never posted) must contribute NOTHING.
    stale = month(1000.0, 350.0, "Plano - Valor R$ 500,00 ... (Parte MBC) = 350,00")
    assert convenio_mbc_shares({1: stale}) == {}

    # Stale alongside current: only the current one counts.
    assert convenio_mbc_shares({1: stale, 3: current})["XX"] == pytest.approx(0.70, abs=1e-9)

    # Two CURRENT months that disagree on the share => no share (do not average).
    other = month(2000.0, 1000.0, "Plano - Valor R$ 2.000,00 ... (Parte MBC) = 1.000,00")
    assert convenio_mbc_shares({3: current, 4: other}) == {}


def test_stale_convenio_memo_rebuilds_parte_mbc_from_the_learned_share(snapshot_jun):
    """A stale memo borrows the SHARE from the lawyer's current months — never the amount.

    This is what removed the convênio from the "needs a finance ruling" list
    (2026-08-04). The old fallback booked the posted GROSS, which overstates the
    lawyer's cost by their personal slice; the memo's own numbers are chronically
    unmaintained (``603,50 / 524,28`` appears in ALL TWELVE months of 2025 and into
    Feb 2026 while the posted plan changed twice underneath it).

    What is applied is ``share × THIS month's posted`` — so the amount is always the
    month's own and only the ratio is carried. On the real data (see
    ``scripts/audit_convenio_share.py``) February's Econômico goes from +1.405,83 to
    −53,85 against the workbook and the YTD Resultado Bruto gap closes from −7.640,50
    to −5.003,04.

    ⚠ The share is EXACTLY DETERMINED by one observation per lawyer, so it is a
    restatement of the trusted month, not an independently validated law. It is solid
    where the posted amount is unchanged between the trusted and the stale month, and an
    EXTRAPOLATION where it moved (RB January 2026 — documented as an estimate).
    """
    snap = json.loads(json.dumps(snapshot_jun))  # deep copy
    # Make EHF's memo stale exactly as jan/fev are.
    for memo in snap["convenio_memo"]:
        if memo["sigla"] == "EHF":
            memo["raw_memo"] = (
                "Convêno Médico  EHF- Plano: SOHO60E - Valor968,65\r\n\r\n"
                "1.795,86-1.192,36 ( Parte MBC)=603,50"
            )
            memo["parsed_valor"] = 603.50

    # No shares: falls back to the posted gross (the old behaviour).
    gross = RealizadoInputs.from_snapshot(snap).area_custo_equipe["Econômico"]

    # With the share EHF shows in its current months, the MBC share is rebuilt and the
    # área returns to the client-validated June figure.
    share = 1564.10 / 2122.30
    fixed = RealizadoInputs.from_snapshot(
        snap, convenio_shares={"EHF": share}
    ).area_custo_equipe["Econômico"]
    assert fixed == pytest.approx(80536.85, abs=0.02)
    assert fixed < gross, "rebuilding the MBC share must remove the personal slice"

    # A lawyer with no learned share still falls back to the gross — never guessed.
    assert RealizadoInputs.from_snapshot(
        snap, convenio_shares={"ZZZ": 0.5}
    ).area_custo_equipe["Econômico"] == pytest.approx(gross, abs=0.02)


def test_convenio_share_handles_roster_churn():
    """A lawyer joining or leaving mid-year must never get another lawyer's share.

    Roster churn is NOT hypothetical — 2026 alone has VSR joining in March, AVN in April,
    and JGS/JCT/MAM/VC leaving. Three things have to hold for a newcomer:

    * **No memo at all ⇒ the posted GROSS stands, untouched.** This is the common case and
      it is CORRECT, not a gap: only three lawyers have ever had a memo (EHF, RB, JGS
      across 2024–2026), because a memo exists only where dependents/upgrade are split
      onto a personal-debit account. Verified against the workbook: VC's book value
      1.409,09 IS the DB posted amount to the centavo, and JGS's matches within R$0,50.
      A lawyer with no personal slice has nothing to strip.
    * **A share is never borrowed from a different lawyer.** The share dict is keyed on
      sigla, so an unknown sigla falls back rather than inheriting.
    * **A newcomer with one valid month gets their own share** — the rule starts working
      for them immediately, with no roster list to maintain anywhere.
    """
    from app.closing.dre import convenio_mbc_shares

    def month(sigla: str, posted: float, memo_value: float, plan: str) -> dict:
        return {
            "custo_equipe_deriv": [
                {"sigla": sigla, "id_conta": "030.010.0110", "valor": posted}
            ],
            "convenio_memo": [
                {
                    "sigla": sigla,
                    "parsed_valor": memo_value,
                    "raw_memo": f"Plano - Valor R$ {plan} ... (Parte MBC) = x",
                }
            ],
        }

    # A newcomer with NO memo contributes nothing and inherits nothing.
    no_memo = {4: {"custo_equipe_deriv": [
        {"sigla": "NEW", "id_conta": "030.010.0110", "valor": 1500.0}
    ]}}
    assert convenio_mbc_shares(no_memo) == {}

    # An established lawyer's share must not leak onto the newcomer.
    mixed = dict(no_memo)
    mixed[3] = month("EHF", 2122.30, 1564.10, "2.122,30")
    shares = convenio_mbc_shares(mixed)
    assert set(shares) == {"EHF"}, "a share must never be shared between lawyers"

    # The newcomer's own first valid month is enough to start deriving for them.
    mixed[5] = month("NEW", 1000.0, 700.0, "1.000,00")
    shares = convenio_mbc_shares(mixed)
    assert shares["NEW"] == pytest.approx(0.70, abs=1e-9)
    assert shares["EHF"] == pytest.approx(1564.10 / 2122.30, abs=1e-9)


def test_convenio_share_is_dropped_when_a_lawyers_plan_share_really_changes():
    """A genuine mid-year plan change must DISABLE the share, not average across it.

    Plan changes are common in this data (AM's posted convênio goes 3.182,83 → 4.774,27 in
    May; RB's 2.355,73 → 3.427,58 in February). If a lawyer's trusted months disagree on
    the share, averaging them would invent a figure nobody wrote — so the share is dropped
    and those months fall back to the posted gross.

    Why the fallback direction is the safe one: the rule always books LESS than the gross,
    so it can never inflate a cost. The residual risk is UNDERSTATING when a true share
    moved up while that month's memo was stale, bounded by (1 − share) × posted ≈ 26%.
    That is exactly the RB-January situation, which is why it is flagged as an estimate in
    the differences document rather than presented as derived fact.
    """
    from app.closing.dre import convenio_mbc_shares

    def month(posted: float, memo_value: float, plan: str) -> dict:
        return {
            "custo_equipe_deriv": [
                {"sigla": "XX", "id_conta": "030.010.0110", "valor": posted}
            ],
            "convenio_memo": [
                {
                    "sigla": "XX",
                    "parsed_valor": memo_value,
                    "raw_memo": f"Plano - Valor R$ {plan} ... (Parte MBC) = x",
                }
            ],
        }

    # Same share either side of a plan change => still usable.
    consistent = {1: month(1000.0, 700.0, "1.000,00"), 6: month(2000.0, 1400.0, "2.000,00")}
    assert convenio_mbc_shares(consistent)["XX"] == pytest.approx(0.70, abs=1e-9)

    # DIFFERENT share => dropped entirely, never averaged to 0.60.
    inconsistent = {1: month(1000.0, 700.0, "1.000,00"), 6: month(2000.0, 1000.0, "2.000,00")}
    assert convenio_mbc_shares(inconsistent) == {}


def test_a_current_convenio_memo_ignores_the_learned_share(snapshot_jun):
    """The share is a FALLBACK. When the memo is current its own stated Parte MBC wins,
    so passing a (deliberately absurd) share must change nothing."""
    base = RealizadoInputs.from_snapshot(snapshot_jun).area_custo_equipe["Econômico"]
    with_share = RealizadoInputs.from_snapshot(
        snapshot_jun, convenio_shares={"EHF": 0.01, "RB": 0.01}
    ).area_custo_equipe["Econômico"]
    assert with_share == pytest.approx(base, abs=0.005)
    assert base == pytest.approx(80536.85, abs=0.02)


def test_per_area_despesa_institucional_ratears_only_the_pool_june(snapshot_jun):
    """Per-área Despesa Institucional splits the "Despesa para ratear" POOL, not
    the whole institutional despesa.

    Client-reported (June validation): Contencioso should be ~32.563, we showed
    36.913,79. The workbook carves the per-área Despesas Área OUT first
    (Base_Resultado Mensal_V2 H198 − H203 = H207):

        Despesa Institucional  105.927,36
        − Despesas Área         15.115,27   (Conten 2.442,49 · Econ 1.075,09 · Arb 11.597,70)
        = Despesa para ratear    90.812,09

    then splits the pool by each área's custo-equipe share (35,8574 / 38,2880 /
    25,8546 %) → Conten 32.562,84 · Econ 34.770,11 · Arb 23.479,14.

    The code already subtracted ``area_desp_equipe``; what starved the pool was the
    Arbitragem Assinatura (client-platform licence, 10.340,35) being filed under
    institutional Informática instead of Despesas Área — Σ was 4.774,92, not
    15.115,27. Tolerance is 2,00: an unresolved 4,80 remains in Administrativas
    (pending Renata on 040.030.0020) which shifts each share slightly.
    """
    from app.closing.dre import DESPESA_INSTITUCIONAL, DESPESAS_EQUIPE

    sections = assemble_dre_sections(
        snapshot=snapshot_jun, budget=None, period_label="Jun 2026", period_month=6,
    )
    expected = {
        "contencioso": (2442.48, 32562.84),
        "economico": (1075.09, 34770.11),
        "arbitragem": (11597.70, 23479.14),
    }
    for sec, (desp_eq, desp_inst) in expected.items():
        rows = sections[sec]["rows"]
        assert _row(rows, DESPESAS_EQUIPE)["Realizado"]["value"] == pytest.approx(
            desp_eq, abs=0.02
        ), sec
        assert _row(rows, DESPESA_INSTITUCIONAL)["Realizado"]["value"] == pytest.approx(
            desp_inst, abs=2.0
        ), sec


def test_vale_adm_derived_from_vale_prof_may(snapshot_may):
    # Vale-ADM is derived from the per-person ``vale_prof`` slices (v3+), keyed on
    # home grupo == Administração — Maria Luiza ONLY (Renata's 2026-07-30 ruling; JVO
    # and VSR are estagiários of the áreas, not ADM). May: MLA VR 783,70 + VT 262,64 =
    # 1.046,34. The assembler adds it to "Salários Administração" as a leaf and moves
    # FGTS-ADM (020.050.0060 = 400) to Impostos.
    #
    # ⚠ This does NOT tie the workbook, and that is CORRECT: the May book types the
    # full 3-person transitória (VR 2.719,90 + VT 607,04 = 3.326,94) into Salários
    # Adm, a documented −2.280,60 difference (DIFERENCAS_ACUMULADO_2026.md). The old
    # test injected ``vale_adm = 3326.94`` as a scalar to hit 12.344,91, but the v2
    # scalar contract is gone (extract v3) — the fixture now carries ``vale_prof`` and
    # that injected key is ignored. Salários Adm = 9.017,97 base + 1.046,34 = 10.064,31.
    snap = dict(snapshot_may)
    assert "vale_adm" not in snap  # v3+: per-person slices, no pre-split scalar
    assert sum(
        v["valor"] for v in snap["vale_prof"] if v["sigla"] == "MLA"
    ) == pytest.approx(1046.34, abs=0.01)
    r = RealizadoInputs.from_snapshot(snap)
    sal = next(s for s in r.sections if s.name == "Salários Administração")
    assert sal.total == pytest.approx(10064.31, abs=0.01)
    vale = next(v for nome, v in sal.accounts if "Vale" in nome)
    assert vale == pytest.approx(1046.34, abs=0.01)
    # FGTS-ADM must have left Salários Adm (it belongs to Impostos in the workbook).
    assert not any("FGTS" in nome for nome, _ in sal.accounts)


#: Real per-person VR/VT slices, straight off ``probe_vale_desdobramento.sql`` run
#: live on 2026-07-30 (block B). One entry per CPDESDOBRAMENTO slice destined for
#: ``500.010.<SIGLA>``. This is what the v3 extract emits as ``vale_prof``.
_VALE_PROF_2026 = {
    1: [("JVO", 829.80), ("JVO", 168.00), ("MLA", 262.64), ("MLA", 829.80)],
    2: [("JVO", 235.20), ("JVO", 1014.20), ("MLA", 337.68), ("MLA", 1014.20)],
    3: [("JVO", 922.00), ("JVO", 268.80), ("MLA", 318.92), ("MLA", 922.00),
        ("VSR", 86.40), ("VSR", 922.00)],
    4: [("JVO", 268.80), ("JVO", 922.00), ("MLA", 300.16), ("MLA", 922.00),
        ("VSR", 86.40), ("VSR", 922.00)],
    5: [("JVO", 968.10), ("JVO", 268.80), ("MLA", 783.70), ("MLA", 262.64),
        ("VSR", 75.60)],
    6: [("JVO", 1014.20), ("JVO", 268.80), ("MLA", 1014.20), ("MLA", 318.92),
        ("VSR", 1014.20), ("VSR", 86.40)],
}

#: The three Vale people's SISJURI grupo, stable across 2026-01..07.
_HOME_AREA_2026 = {
    "JVO": "Equipe Contencioso",
    "MLA": "Administração",
    "VSR": "Equipe Direito Econômico",
}


def _vale_prof(month: int) -> list[dict]:
    return [{"sigla": s, "valor": v} for s, v in _VALE_PROF_2026[month]]


def _with_vale(snap: dict, month: int, **home_overrides: str) -> dict:
    """June fixture + a given month's per-person slices.

    ``home_area`` is MERGED, never replaced: the fixture carries 69 siglas and
    dropping the rest orphans every other lawyer, collapsing the área totals.
    """
    out = dict(snap)
    out.pop("vale_adm", None)  # v3 emits no pre-split total
    out["vale_prof"] = _vale_prof(month)
    out["home_area"] = {
        **(out.get("home_area") or {}), **_HOME_AREA_2026, **home_overrides
    }
    return out


def _vale_leaf(snap: dict) -> float:
    r = RealizadoInputs.from_snapshot(snap)
    sal = next(s for s in r.sections if s.name == "Salários Administração")
    return next(v for nome, v in sal.accounts if "Vale" in nome)


def test_vale_adm_derives_adm_only_from_per_person_slices(snapshot_jun):
    """The ADM share of Vale is derived PER PERSON, keyed on ``home_area``.

    Renata (voice notes, 2026-07-30): the transitória lançamento único "depois ele
    abre isso dentro do sistema... dizendo pra QUAL PESSOA é essa despesa", and "o
    ideal é que tenha lançamentos feitos para o ADM e lançamentos feitos para as
    áreas específicas, porque são DOIS ESTAGIÁRIOS dentro de cada área, e tem a
    Maria Luiza que é da parte administrativa."

    So: sum only the slices whose sigla has ``home_area == Administração``.
    """
    snap = _with_vale(snapshot_jun, 6)
    assert _vale_leaf(snap) == pytest.approx(1333.12, abs=0.01)  # MLA 1.014,20+318,92
    r = RealizadoInputs.from_snapshot(snap)
    sal = next(s for s in r.sections if s.name == "Salários Administração")
    assert sal.total == pytest.approx(6312.19, abs=0.01)  # workbook June H116


def test_vale_adm_per_person_ties_february(snapshot_jun):
    # The other month Renata had already adjusted: MLA 337,68 + 1.014,20 = 1.351,88
    # (workbook D122+D123). The Vale leaf comes entirely from vale_prof, so the June
    # fixture only supplies the surrounding sections.
    assert _vale_leaf(_with_vale(snapshot_jun, 2)) == pytest.approx(1351.88, abs=0.01)


def test_vale_adm_follows_the_adm_tag_not_a_hardcoded_sigla(snapshot_jun):
    # The automation claim, tested: move the Administração tag to a DIFFERENT person
    # and the derived Vale must follow the tag. If someone later hardcodes "MLA",
    # this fails. VSR as ADM = 1.014,20 + 86,40 = 1.100,60.
    snap = _with_vale(
        snapshot_jun, 6, MLA="Equipe Contencioso", VSR="Administração"
    )
    assert _vale_leaf(snap) == pytest.approx(1100.60, abs=0.01)


def test_vale_adm_per_person_does_NOT_tie_march_april_may(snapshot_jun):
    """Mar/Abr/Mai must DIFFER from the workbook — asserted so nobody "fixes" it.

    Renata, 2026-07-30: "teve um mês que ficou tudo na Malu... e depois que eu
    percebi que tinha valores separados de cada um, alocados dentro das áreas
    específicas, e aí eu acabei ajustando" + "não vale a pena corrigir, o valor é
    muito irrisório." Abr/Mai in her book are the FULL 3-person lump and Mar is a
    partial hand-fix, so a derivation reproducing all six months would be fitting to
    hand-entry — the trap that made "Econômico ties" look correct in the per-área
    YTD (see scripts/audit_area_ytd_formulas.py).
    """
    for month, typed in {3: 3983.22, 4: 3421.36, 5: 3326.94}.items():
        derived = _vale_leaf(_with_vale(snapshot_jun, month))
        assert derived < typed - 1000, (
            f"month {month}: derived {derived} unexpectedly close to the workbook's "
            f"un-adjusted {typed} — do not fit to hand-entry"
        )


def test_vale_prof_adm_slice_is_excluded_from_area_custo_equipe(snapshot_jun):
    """The ADM person's Vale must NOT also land in an área's Custo equipe.

    ``custo_equipe_area`` is a RAW per-person feed and it DOES contain the ADM person
    in some months (April 2026: MLA 1.222,16). That is why the previously rejected
    shortcut ``lump − Σ custo_equipe_area`` produced exactly 0,00 for April — it
    subtracted the ADM share from itself. Counting MLA in an área would double-count
    her from the other direction, so the same ``home_area`` test filters her out.
    """
    snap = _with_vale(snapshot_jun, 6)
    # April's shape: the ADM person appears in the per-área Vale feed too.
    snap["custo_equipe_area"] = [
        {"sigla": "JVO", "valor": 1283.00, "id_conta": "030.010.0100/0220"},
        {"sigla": "MLA", "valor": 1222.16, "id_conta": "030.010.0100/0220"},
        {"sigla": "VSR", "valor": 1100.60, "id_conta": "030.010.0100/0220"},
    ]
    r = RealizadoInputs.from_snapshot(snap)
    # The áreas keep their estagiários' Vale (June's client-validated numbers)…
    assert r.area_custo_equipe["Contencioso"] == pytest.approx(75424.21, abs=0.01)
    assert r.area_custo_equipe["Econômico"] == pytest.approx(80536.85, abs=0.01)
    # …and MLA's 1.222,16 is nowhere in the three áreas.
    assert sum(r.area_custo_equipe.values()) == pytest.approx(210345.00, abs=0.02)


def test_vale_adm_excludes_lawyer_vale_already_in_custo_equipe(snapshot_jun):
    """June end-to-end: the estagiários' Vale must not be counted twice.

    Their slice belongs to per-área Custo equipe (``custo_equipe_area``,
    500.010.<SIGLA>); counting it in Salários Administração too inflated Despesa
    Institucional and every área's rateio share (June reserva read −10.194,80
    instead of −9.956,44).

    Under v3 the split is per-person, from ``vale_prof`` keyed on ``home_area``
    (the June fixture carries the real slices off probe_vale_desdobramento.sql):
        JVO 1.283,00 + VSR 1.100,60 = 2.383,60  -> áreas
        MLA 1.014,20 +      318,92  = 1.333,12  -> Salários Administração
    Workbook June: Base_Resultado H116 = 6.312,19, H122+H123 = 1.333,12.
    """
    snap = dict(snapshot_jun)
    # v3 emits per-person slices, not a pre-split total. Guards the fixture.
    assert "vale_adm" not in snap
    assert sum(
        r["valor"] for r in snap["vale_prof"] if r["sigla"] == "MLA"
    ) == pytest.approx(1333.12, abs=0.01)
    r = RealizadoInputs.from_snapshot(snap)
    sal = next(s for s in r.sections if s.name == "Salários Administração")
    assert sal.total == pytest.approx(6312.19, abs=0.01)
    vale = next(v for nome, v in sal.accounts if "Vale" in nome)
    assert vale == pytest.approx(1333.12, abs=0.01)
    # And the estagiários' slice stays where it belongs — per-área Custo equipe.
    assert r.area_custo_equipe["Contencioso"] == pytest.approx(75424.21, abs=0.01)
    assert r.area_custo_equipe["Econômico"] == pytest.approx(80536.85, abs=0.01)


def test_vale_adm_absent_leaves_salarios_unchanged(snapshot_may):
    # With no vale source at all the section is unchanged except FGTS still moves out
    # (FGTS reclassification is account-driven, not gated on the vale). The live v4
    # fixture carries ``vale_prof`` (the per-person slices), so drop that to test the
    # truly-absent case — dropping the obsolete ``vale_adm`` scalar would no longer do
    # it, since the derivation reads ``vale_prof`` now.
    snap = dict(snapshot_may)
    snap.pop("vale_prof", None)
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
    # Custos Diretos = Σ custo equipe (209273.90, Vale-inclusive) + comissão
    # (2128.06) = 211401.96.
    assert r.custos_diretos == pytest.approx(211401.96, abs=0.01)


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
    # The Vale-inclusive per-area Custo equipe MATCHES the re-baselined workbook
    # targets, so the hard rule shows the value instead of blanking it.
    from app.closing.workbook_targets import targets_for

    targets = targets_for("2026-05")
    sections = assemble_dre_sections(
        snapshot=snapshot_may, budget=None, period_label="Maio 2026", targets=targets
    )
    conten = _row(sections["contencioso"]["rows"], CUSTO_EQUIPE)
    econ = _row(sections["economico"]["rows"], CUSTO_EQUIPE)
    arb = _row(sections["arbitragem"]["rows"], CUSTO_EQUIPE)
    assert conten["Realizado"]["value"] == pytest.approx(75378.11, abs=0.01)
    assert econ["Realizado"]["value"] == pytest.approx(79511.85, abs=0.01)
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


def test_distribuicao_extras_absent_lines_are_dash_not_missing():
    # DL extras are discretionary, event-driven distributions (team bonus ~1x/yr
    # in Feb; DL excedente Jan/Mar; DL Extraordinária a 2024 one-off; Cacione
    # never). When a line is absent for the month it is *correctly* empty (the
    # event did not happen), NOT data we are still waiting for. So each extras
    # child row must carry ``empty_dash`` → the UI renders "—", never the
    # "ainda não temos" pending-data placeholder.
    from app.closing.dre import assemble_base_resultado

    # A month with no extras at all (e.g. May): every extras child is dash-empty.
    tab = assemble_base_resultado({}, "Mai 2026")
    extras = [r for r in tab["rows"] if r["key"].startswith("extra::")]
    assert len(extras) == 5
    for r in extras:
        assert r["Valor"] is None
        assert r["empty_dash"] is True, f"{r['Linha']} should be dash-empty when absent"


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


def test_manual_override_diverging_from_db_is_flagged_not_silent():
    # Workbook-free guard (item 2): an explicit distribuicao_extras override still
    # WINS (finance can correct), but when it diverges from the DB-derived value it
    # must NOT be silent — the row carries an ``override`` marker with the DB value
    # it replaced, so a stale manual number can never quietly mask the DB.
    from app.closing.dre import assemble_base_resultado

    snap = {
        "bonus_equipe": 94696.15,       # DB-derived (150.*)
        "bonus_equipe_030": 7009.84,    # DB-derived (030.010.0010) -> DB total 101705.99
        "distribuicao_extras": {"bonus_equipe": 50000.0},  # stale/diverging override
    }
    tab = assemble_base_resultado(snap, "Fev 2026")
    bonus = next(r for r in tab["rows"] if r["key"] == "extra::bonus_equipe")
    # The override still wins as the displayed value.
    assert bonus["Valor"]["value"] == pytest.approx(50000.0, abs=0.05)
    # ...but it is flagged, and the DB value it diverged from is preserved.
    assert bonus["override"] is True
    assert bonus["db_value"] == pytest.approx(101705.99, abs=0.05)


def test_manual_override_matching_db_is_not_flagged():
    # When the override equals the DB value (no real divergence) there is nothing to
    # warn about — no override flag.
    from app.closing.dre import assemble_base_resultado

    snap = {
        "bonus_equipe": 42000.0,
        "distribuicao_extras": {"bonus_equipe": 42000.0},
    }
    tab = assemble_base_resultado(snap, "Fev 2026")
    bonus = next(r for r in tab["rows"] if r["key"] == "extra::bonus_equipe")
    assert bonus["Valor"]["value"] == pytest.approx(42000.0, abs=0.05)
    assert bonus.get("override") is not True


def test_bonus_equipe_blank_when_account_150_absent():
    # POINT 16: robust to the partner-split (POINT 17) not having arrived — when
    # no 150.* data is present, the line renders blank ("ainda não temos"),
    # never an invented number.
    from app.closing.dre import assemble_base_resultado

    tab = assemble_base_resultado({}, "Fev 2026")
    bonus = next(r for r in tab["rows"] if r["key"] == "extra::bonus_equipe")
    assert bonus["Valor"] is None


def test_bonus_equipe_adds_030_010_0010_lines():
    # Proven vs Feb (2026-07-14 probe): the workbook "Bônus equipe" = 94.696,15
    # (150.*) + 7.009,84 (a bonus booked in 030.010.0010, e.g. JGS) = 101.705,84.
    # The extract emits both ``bonus_equipe`` (Σ 150.%) and ``bonus_equipe_030``
    # (Bônus histórico lines in 030.010.0010); the assembler sums them.
    from app.closing.dre import assemble_base_resultado

    snap = {"bonus_equipe": 94696.15, "bonus_equipe_030": 7009.84}
    tab = assemble_base_resultado(snap, "Fev 2026")
    bonus = next(r for r in tab["rows"] if r["key"] == "extra::bonus_equipe")
    assert bonus["Valor"]["value"] == pytest.approx(101705.99, abs=0.05)


def test_bonus_equipe_030_alone_still_shows():
    # If only the 030.010.0010 bonus is present (no 150.* that month) the line
    # still renders that amount rather than blanking.
    from app.closing.dre import assemble_base_resultado

    tab = assemble_base_resultado({"bonus_equipe_030": 7009.84}, "Fev 2026")
    bonus = next(r for r in tab["rows"] if r["key"] == "extra::bonus_equipe")
    assert bonus["Valor"]["value"] == pytest.approx(7009.84, abs=0.05)


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


def test_dl_excedente_socios_from_top_level_key():
    # POINT 17 (automated by us, 2026-07-14): the partners' excess distribution
    # is booked in 030.010.0010 with histórico "DL excedente <SIGLA> - Reserva".
    # The extract splits it by CAD_PROFISSIONAL.SOCIO into a top-level
    # ``dl_excedente_socios`` (the 3 core sócios: AM/DC/RB) and ``dl_excedente_mv``
    # (Martim, kept separate to mirror the workbook). Proven vs the 05.2026 book:
    # Jan sócios = 164.477,34 (row 193), Mar MV = 6.627 (row 194).
    from app.closing.dre import assemble_base_resultado

    snap = {"dl_excedente_socios": 164477.34}
    tab = assemble_base_resultado(snap, "Jan 2026")
    socios = next(r for r in tab["rows"] if r["key"] == "extra::dl_excedente_socios")
    assert socios["Valor"]["value"] == pytest.approx(164477.34, abs=0.05)
    total = next(r for r in tab["rows"] if r["key"] == "distrib_extras")
    assert total["Valor"]["value"] == pytest.approx(164477.34, abs=0.05)


def test_dl_excedente_mv_from_top_level_key():
    from app.closing.dre import assemble_base_resultado

    snap = {"dl_excedente_mv": 6627.0}
    tab = assemble_base_resultado(snap, "Mar 2026")
    mv = next(r for r in tab["rows"] if r["key"] == "extra::dl_excedente_mv")
    assert mv["Valor"]["value"] == pytest.approx(6627.0, abs=0.05)


def test_dl_excedente_explicit_extras_wins_over_top_level():
    # A finance-entered distribuicao_extras value still overrides the derived
    # top-level key, exactly like bonus_equipe.
    from app.closing.dre import assemble_base_resultado

    snap = {
        "dl_excedente_socios": 164477.34,
        "distribuicao_extras": {"dl_excedente_socios": 200000.0},
    }
    tab = assemble_base_resultado(snap, "Jan 2026")
    socios = next(r for r in tab["rows"] if r["key"] == "extra::dl_excedente_socios")
    assert socios["Valor"]["value"] == pytest.approx(200000.0, abs=0.05)


def test_dl_excedente_blank_when_absent():
    # Robust to months with no excedente (e.g. May): the lines stay blank
    # ("ainda não temos"), never an invented zero.
    from app.closing.dre import assemble_base_resultado

    tab = assemble_base_resultado({}, "Mai 2026")
    socios = next(r for r in tab["rows"] if r["key"] == "extra::dl_excedente_socios")
    mv = next(r for r in tab["rows"] if r["key"] == "extra::dl_excedente_mv")
    assert socios["Valor"] is None
    assert mv["Valor"] is None


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


def test_dre_2026_has_amortizacao_row_defaulting_to_worksheet(snapshot):
    # Amortização is a fixed worksheet value (8.117/mês); the DRE 2026 tab must
    # carry it even when the client budgeted no amortização, so the row never blanks.
    from app.closing.workbook_layouts import AMORTIZACAO_MENSAL

    sections = assemble_dre_sections(
        snapshot=snapshot, budget={"institucional": {RECEBIMENTO: 671666.67}},
        period_label="x",
    )
    dre = sections["dre_2026"]
    amort = next(r for r in dre["rows"] if r.get("key") == "amortizacao")
    assert amort["Anual"]["value"] == pytest.approx(AMORTIZACAO_MENSAL * 12, abs=0.5)
    assert amort["Janeiro"]["value"] == pytest.approx(AMORTIZACAO_MENSAL, abs=0.01)


def test_institucional_ano_amortizacao_orcado_defaults_to_worksheet(snapshot):
    # The annual Institucional tab's Orçado amortização must show the worksheet
    # value (8.117 * 12), not "ainda não temos" — WITH or WITHOUT a budget amort.
    from app.closing.workbook_layouts import AMORTIZACAO_MENSAL

    # No amort in the budget: still defaults to the worksheet annual.
    sections = assemble_dre_sections(
        snapshot=snapshot, budget={"institucional": {RECEBIMENTO: 671666.67}},
        period_label="Fev 2026",
    )
    amort = _row(sections["institucional_ano"]["rows"], "amortizacao")
    assert amort["Orçado (ano)"]["value"] == pytest.approx(AMORTIZACAO_MENSAL * 12, abs=0.5)
    assert amort["Realizado"]["value"] == pytest.approx(AMORTIZACAO_MENSAL, abs=0.01)

    # An explicit budget amort overrides the default.
    sections2 = assemble_dre_sections(
        snapshot=snapshot,
        budget={"institucional": {RECEBIMENTO: 671666.67, "amortizacao": 10000.0}},
        period_label="Fev 2026",
    )
    amort2 = _row(sections2["institucional_ano"]["rows"], "amortizacao")
    assert amort2["Orçado (ano)"]["value"] == pytest.approx(120000.0, abs=0.5)


def test_fluxo_consolidado_fills_from_db_without_manual(snapshot_may):
    """Fluxo consolidado must render per-area Recebimento/Despesas/Margem from the
    SISJURI-derived values (like the area tabs), NOT require manual entry. With a
    real snapshot every per-area line is populated."""
    sections = assemble_dre_sections(
        snapshot=snapshot_may, budget=None, period_label="Mai 2026"
    )
    rows = sections["fluxo_consolidado"]["rows"]
    for area in ("Contencioso", "Econômico", "Arbitragem"):
        receb = next(r for r in rows if r["key"] == f"{area}::receb")
        despesas = next(r for r in rows if r["key"] == f"{area}::despesas")
        margem = next(r for r in rows if r["key"] == f"{area}::margem")
        assert receb["Valor"]["value"] is not None, f"{area} recebimento blank"
        assert despesas["Valor"]["value"] is not None, f"{area} despesas blank"
        assert margem["Valor"]["value"] is not None, f"{area} margem blank"
    # Recebimento ties the SISJURI per-area prof basis (RECEITA_REC by home grupo).
    # May Contencioso = 240.444,72, the same figure the prof-basis precedence test
    # pins at line ~80. The old 205.157,46 was the legacy cash-by-case value, which
    # the pre-refresh fixture used only because it lacked ``recebimento_area_prof``.
    receb_c = next(r for r in rows if r["key"] == "Contencioso::receb")
    assert receb_c["Valor"]["value"] == pytest.approx(240444.72, abs=0.01)


#: Per-day vale rates, taken from the lançamento histórico itself — SISJURI writes the
#: arithmetic in ("Calculo: 14 dias x R$ 18,76"; June words it "Vale Transporte: 17 dias *
#: R$ 18,76 = Total: 318,92"). VR is the same for everyone; VT is per person.
#: Only May and June carry that tail — Jan–Abr/Jul/Ago have the bare label, which is how
#: finance typed them, not an extract truncation (confirmed after the v4 re-extract).
_VALE_RATES = {"VSR": 10.80, "MLA": 18.76, "JVO": 33.60}
_VR_RATE = 46.10


def test_every_vale_row_is_a_whole_number_of_days():
    """Every vale posting must be N WHOLE days at its per-person rate.

    This is the cheapest possible validation of a vale figure, and it exists because it
    settled a real question: the workbook's hand-typed ``=35,52+262,64`` (January, r123)
    could not be a missing slice of MLA's vale, since 35,52 is not a whole number of days
    at any rate — while every real vale row is, exactly.

    Iterates ALL SIX closed-month fixtures. It used to read only Feb/May/Jun and its
    docstring claimed "41 rows across the eight months" — but Feb and May had NO
    ``vale_prof`` key at all (pre-v4 stubs), so the loop body ran for June alone and
    actually checked 6 rows. After the 2026-08-04 fixture refresh all six carry the
    block; the row-count floor below makes a silently-empty fixture FAIL rather than
    pass vacuously. Rates are DB facts (see the module note above), not invented.
    """
    import json as _json
    from pathlib import Path as _Path

    fixtures_dir = _Path(__file__).parent / "fixtures"
    checked = 0
    for month in range(1, 7):
        label = f"2026-{month:02d}"
        snap = _json.loads(
            (fixtures_dir / f"sisjuri_2026_{month:02d}.json").read_text(encoding="utf-8")
        )
        for row in snap.get("vale_prof") or []:
            sigla = str(row.get("sigla") or "")
            valor = round(float(row.get("valor") or 0.0), 2)
            hist = str(row.get("historico") or "").lower()
            is_vr = "refei" in hist or "vr" in hist
            rate = _VR_RATE if is_vr else _VALE_RATES.get(sigla)
            if not rate or not valor:
                continue
            dias = valor / rate
            assert abs(dias - round(dias)) < 0.001, (
                f"{label} {sigla} {valor} is {dias:.4f} days at {rate}/day — a vale is "
                f"always a whole number of days; check the rate or the posting"
            )
            checked += 1
    # Floor guards against the vacuous-pass trap that hid the old 6-of-41 coverage: a
    # fixture that loses ``vale_prof`` (or gains an unrecognised sigla) drops the count
    # and fails here instead of quietly checking nothing. 31 rows across the six
    # closed-month fixtures on 2026-08-04.
    assert checked >= 31, f"only {checked} vale rows checked — a fixture lost vale_prof"


#: Institucional Despesas Indiretas, fully decomposed 2026-08-04 by
#: ``scripts/audit_despesas_indiretas.py``: every centavo of the YTD difference against the
#: workbook has a named account or a named workbook behaviour behind it (unattributed R$0,00).
#: These pin the two findings that are OUR derivation being right, so a future change cannot
#: quietly "converge" onto the workbook's inconsistency.
def test_vale_adm_is_mla_only_in_every_month_even_where_the_book_disagrees():
    """Vale-ADM is Maria Luiza ONLY, consistently, in all six closed months.

    Renata ruled (2026-07-30) that JVO/VSR are estagiários of the ÁREAS, so their vale
    belongs to per-área Custo equipe and never to institucional Salários Administração.
    We apply that in every month. **The workbook does not**: its rows 122/123 are MLA-only
    in fev/jun, ALL THREE people in abril, and neither in jan/mar/mai — three different
    bases across six months (mar/abr/mai are the ones Renata called *"não vale a pena
    corrigir"*).

    So the −R$ 7.257,62 YTD difference on this line is not a gap to close: converging on it
    would mean reproducing an inconsistency. This test exists to make that deliberate —
    if a future change makes Vale-ADM include the estagiários in ANY month, it fails.
    """
    import json as _json
    from pathlib import Path as _Path

    from app.closing.dre import RealizadoInputs, is_adm_grupo

    fixtures_dir = _Path(__file__).parent / "fixtures"
    for month in range(1, 7):
        snap = _json.loads(
            (fixtures_dir / f"sisjuri_2026_{month:02d}.json").read_text(encoding="utf-8")
        )
        home = snap.get("home_area") or {}
        rows = snap.get("vale_prof") or []
        assert rows, f"2026-{month:02d} has no vale_prof — fixture lost the block"

        adm = [r for r in rows if is_adm_grupo(home.get(str(r.get("sigla"))))]
        # Exactly one person is ADM, and it is MLA in every month.
        assert {str(r.get("sigla")) for r in adm} == {"MLA"}, f"2026-{month:02d}"

        expected = round(sum(float(r["valor"]) for r in adm), 2)
        sal = next(
            s for s in RealizadoInputs.from_snapshot(snap).sections
            if s.name == "Salários Administração"
        )
        vale_leaf = next(v for nome, v in sal.accounts if "Vale Refeição/Transporte" in nome)
        assert vale_leaf == pytest.approx(expected, abs=0.01), f"2026-{month:02d}"

        # The estagiários' slice must NOT be in the institucional vale leaf.
        estagiarios = round(sum(float(r["valor"]) for r in rows if r not in adm), 2)
        if estagiarios:
            assert vale_leaf < estagiarios + expected, f"2026-{month:02d} double-counts"


def test_seguros_is_an_annual_premium_not_a_monthly_charge():
    """`020.060.0040` posts a LUMP annual premium, and that is correct.

    January posts 2.722,55 (and July does it again) while the workbook types a flat 182,71
    every month. `2.722,55 − 182,71 = 2.539,84` is exactly January's Ocupação difference,
    and the workbook books the same premium under *Administrativas* r133 "Seguro de
    Responsabilidade Civil" — so it is a family-label difference plus a timing difference,
    never missing money. Pinned because a future reader seeing a 15× jump in one month
    could easily "fix" it into a smoothed 182,71 and silently invent an accrual the DB
    does not have.
    """
    import json as _json
    from pathlib import Path as _Path

    fixtures_dir = _Path(__file__).parent / "fixtures"
    by_month = {}
    for month in range(1, 7):
        snap = _json.loads(
            (fixtures_dir / f"sisjuri_2026_{month:02d}.json").read_text(encoding="utf-8")
        )
        row = next(
            (r for r in snap.get("despesas_conta") or []
             if r.get("id_conta") == "020.060.0040"),
            None,
        )
        assert row is not None, f"2026-{month:02d} lost the Seguros account"
        by_month[month] = round(float(row["total"]), 2)

    assert by_month[1] == pytest.approx(2722.55, abs=0.01), "January is the annual premium"
    for month in range(2, 7):
        assert by_month[month] == pytest.approx(182.71, abs=0.01), f"2026-{month:02d}"
    # The premium/monthly gap IS the January Ocupação difference.
    assert round(by_month[1] - by_month[2], 2) == pytest.approx(2539.84, abs=0.01)
