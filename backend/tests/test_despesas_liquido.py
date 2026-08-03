# backend/tests/test_despesas_liquido.py
"""Institutional despesas at LÍQUIDO + desdobramento (docs/SISJURI_DB.md).

Reconciled to the centavo against Fechamento MBC 05.2026 (May): 10/10 families tie,
total residual R$129,17 (the client's own aluguel pending, not ours). These tests
lock the key reclassification rules on a slice of the real May data.
"""
import pytest

from app.closing.despesas_liquido import net_by_account


def test_uses_liquido_not_bruto():
    # Contabilidade (Ozai): gross 8570 -> net 8042.94 (workbook).
    net = net_by_account(
        [{"id_conta": "020.040.0050", "liquido": 8042.94, "bruto": 8570.0, "n": 1}],
        [],
    )
    assert net["020.040.0050"] == 8042.94


def test_desdobramento_folds_into_destination_account():
    net = net_by_account(
        [],
        [
            {"id_conta": "020.060.0020", "valor": 700.09, "historico": "IBRAC"},
            {"id_conta": "020.060.0020", "valor": 700.10, "historico": "IBRAC"},
        ],
    )
    assert net["020.060.0020"] == round(700.09 + 700.10, 2)


def test_software_slice_reclassified_from_copa_to_informatica():
    # "Contratação do Claude" (2166.53) is booked to Material de Copa (020.030.0020)
    # but is a software license -> moves to Informática (020.040.0010).
    net = net_by_account(
        [{"id_conta": "020.030.0020", "liquido": 630.0, "bruto": 630.0, "n": 1}],
        [
            {"id_conta": "020.030.0020", "valor": 2166.53,
             "historico": "Contratação do Claude para todos"},
            {"id_conta": "020.030.0020", "valor": 257.36,
             "historico": "Mercado Livre - kit"},
        ],
    )
    # Copa keeps 630 + 257.36 = 887.36 (the workbook Material Higiene leaf).
    assert net["020.030.0020"] == 887.36
    # The Claude slice moved to Informática.
    assert net["020.040.0010"] == 2166.53


def test_client_platform_licence_reclassified_to_assinaturas():
    """June: the "Licenças para uso da plataforma de faturamento do cliente" slice
    is an ASSINATURA per área, not institutional Informática.

    10.340,35 is booked to 040.040.0030 (Licenças de Uso de Software), which our
    ``040.040.`` prefix folds into Informática. The workbook books it as
    "Assinaturas - Arbitragem e Compliance" (Base_Resultado Mensal_V2 H127, inside
    Administrativas H124) — and that matters twice over: it is what makes the
    Despesas Área total tie (H203 = 15.115,27, giving the "Despesa para ratear"
    pool H207 = 90.812,09), which in turn drives every área's Despesa Institucional
    rateio share. Left in Informática it also starved that pool by 10.340,35.

    Only client-platform licences move; ordinary software licences (Claude, Adobe)
    stay in Informática.
    """
    net = net_by_account(
        [{"id_conta": "040.040.0030", "liquido": 4527.12, "bruto": 4569.5, "n": 4}],
        [
            {"id_conta": "040.040.0030", "valor": 10340.35,
             "historico": "Licenças para uso da plataforma de faturamento do "
                          "cliente 136 - O valor pago em "},
            {"id_conta": "040.040.0030", "valor": 2122.02,
             "historico": "Contratação do Claude para toda a equipe"},
            {"id_conta": "040.040.0030", "valor": 110.0,
             "historico": "PPRO*Adobe R$110,00 referente maio 2026"},
        ],
    )
    # The client-platform slice becomes an Assinaturas (020.060.0010) line.
    assert net["020.060.0010"] == 10340.35
    # Claude + Adobe + the direct líquido stay put: 4527.12 + 2122.02 + 110 = 6759.14
    assert net["040.040.0030"] == 6759.14


def test_custas_and_transporte_excluded():
    net = net_by_account(
        [
            {"id_conta": "020.030.0140", "liquido": 55.60, "bruto": 55.60, "n": 1},
            {"id_conta": "020.030.0060", "liquido": 968.10, "bruto": 968.10, "n": 1},
            {"id_conta": "020.030.0080", "liquido": 21.94, "bruto": 21.94, "n": 1},
        ],
        [],
    )
    assert "020.030.0140" not in net  # Custas -> Despesas para Clientes
    assert "020.030.0060" not in net  # Transporte e Frete -> out of row-198
    assert net["020.030.0080"] == 21.94  # Taxi stays in Despesas Gerais


def test_aluguel_uses_gerenc_net_over_contaspagar_gross():
    # CONTASPAGAR aluguel is the gross 27477.67; the GERENC net (24359.77, already
    # net of the "Belline" sublet credit) must override it.
    net = net_by_account(
        [{"id_conta": "020.010.0010", "liquido": 27477.67, "bruto": 27477.67, "n": 1}],
        [],
        aluguel_gerenco_net=24359.77,
    )
    assert net["020.010.0010"] == 24359.77


def test_may_families_reconcile_to_workbook():
    # The real May slice: feeding the proven inputs must reproduce the workbook leaf
    # net values (within the R$129,17 aluguel residual the client owns).
    direct = [
        {"id_conta": "020.010.0010", "liquido": 27477.67, "bruto": 27477.67},
        {"id_conta": "020.010.0020", "liquido": 4996.0, "bruto": 4996.0},
        {"id_conta": "020.010.0030", "liquido": 863.59, "bruto": 863.59},
        {"id_conta": "020.010.0040", "liquido": 6916.97, "bruto": 6916.97},
        {"id_conta": "020.060.0040", "liquido": 182.71, "bruto": 182.71},
        {"id_conta": "020.020.0010", "liquido": 65.29, "bruto": 65.29},
        {"id_conta": "020.020.0030", "liquido": 759.72, "bruto": 759.72},
        {"id_conta": "020.030.0020", "liquido": 630.0, "bruto": 630.0},
        {"id_conta": "020.030.0080", "liquido": 21.94, "bruto": 21.94},
        {"id_conta": "020.030.0100", "liquido": 1914.41, "bruto": 1966.76},
        {"id_conta": "020.030.0150", "liquido": 215.0, "bruto": 215.0},
        {"id_conta": "020.040.0010", "liquido": 9252.45, "bruto": 9653.09},
        {"id_conta": "020.040.0030", "liquido": 3346.68, "bruto": 3984.15},
        {"id_conta": "020.040.0050", "liquido": 8042.94, "bruto": 8570.0},
        {"id_conta": "020.060.0020", "liquido": 1204.47, "bruto": 1204.47},
        {"id_conta": "040.030.0010", "liquido": 14705.80, "bruto": 14705.80},
        {"id_conta": "040.040.0030", "liquido": 7129.10, "bruto": 12430.61},
        {"id_conta": "030.010.0180", "liquido": 1600.0, "bruto": 1600.0},
    ]
    desdobr = [
        {"id_conta": "020.030.0020", "valor": 2166.53, "historico": "Contratação do Claude"},
        {"id_conta": "020.030.0020", "valor": 257.36, "historico": "Mercado Livre kit"},
        {"id_conta": "020.060.0020", "valor": 1617.59, "historico": "AASP/IBRAC"},
        {"id_conta": "020.090.0040", "valor": 205.98, "historico": "IFood bolo"},
        {"id_conta": "040.040.0010", "valor": 904.68, "historico": "Mercado Livre notebooks"},
        {"id_conta": "040.040.0020", "valor": 399.99, "historico": "Mercado Livre SSD"},
        {"id_conta": "040.040.0030", "valor": 110.0, "historico": "Adobe"},
    ]
    net = net_by_account(direct, desdobr, aluguel_gerenco_net=24359.77)

    # Assert the per-account net values the module owns (the family folding is the
    # assembler's job via section_for, tested elsewhere). These are the workbook leaves:
    assert net["020.010.0010"] == pytest.approx(24359.77)          # aluguel net of Belline
    assert net["020.040.0010"] == pytest.approx(11418.98)          # Serv Info + Claude
    assert net["020.030.0020"] == pytest.approx(887.36)            # copa (Claude moved out)
    assert net["020.040.0050"] == pytest.approx(8042.94)           # contabilidade líquido
    assert net["040.040.0030"] == pytest.approx(7239.10)           # licenças net + card Adobe
    assert net["030.010.0180"] == pytest.approx(1600.0)            # cursos
    assert "020.030.0140" not in net                 # custas out
    assert "020.030.0060" not in net                 # transporte out

    # Ocupação leaves sum ties within the R$129,17 the client owns (aluguel pending).
    ocup = net["020.010.0010"] + net["020.010.0020"] + net["020.010.0030"] \
        + net["020.010.0040"] + net["020.060.0040"]
    assert abs(ocup - 37189.87) <= 129.20


#: The exact `020.030.0020` (Material de Copa) desdobramento históricos that sit AT the
#: extract's old 80-char cap, with the value each carries. Captured 2026-08-03, before
#: widening `SUBSTR(d.DESCHISTORICO,1,80)` to 300 in `ops/sisjuri-agent/extract.sql`.
#:
#: Widening is not cosmetic: `net_by_account` decides reclassifications by searching the
#: histórico for markers ("claude", "software", "saas", "licen", "cloud"), so a longer
#: string can match where the truncated one did not and move money from Copa to
#: Informática. These rows are the whole exposure — they are the only ones on a reclass
#: account that were being cut. Each is a Mercado Livre copa/limpeza purchase, so the
#: correct post-widening behaviour is that NOTHING moves.
_COPA_AT_THE_CAP: tuple[tuple[str, float], ...] = (
    ("Mercado Livre - Compra de 100 unidade de bolacha, 400 unidades de açucar em sa", 202.06),
    ("Mercado livre- Valor original da compra 383,39 - Compra de azeite e vinagre ba", 88.99),
    ("Mercado Livre - Compra de saleiro e suporte de mangueira, aromatizador de ambi", 132.72),
    ("Mercado Livre - Compra de papel toalha, água sanitária, detergente e desinfeta", 273.11),
    ('"Mercado Livre - Compora de material de copa:\r\n\r\n4 un. - Café bravo\r\n2 Caixas ', 250.95),
    ('"Mercado Livre - Compra de material de copa para a sede \r\nJarra de 2.27LTS; e ', 142.95),
)


def test_widening_the_historico_must_not_move_copa_to_informatica():
    """Regression guard for the extract's `DESCHISTORICO` widening (80 -> 300 chars).

    The re-extract makes these históricos LONGER. If a fuller text happened to contain a
    software marker, the money would silently jump account. This pins the intended
    outcome for every row that was actually being truncated on a reclass account: they
    stay in Material de Copa, and Informática gains nothing.

    If this test fails after a re-extract, do NOT relax it — read the new full histórico
    and decide deliberately whether that line really is software.
    """
    desdobr = [
        {"id_conta": "020.030.0020", "valor": valor, "historico": hist}
        for hist, valor in _COPA_AT_THE_CAP
    ]
    net = net_by_account([], desdobr)
    total = round(sum(v for _h, v in _COPA_AT_THE_CAP), 2)
    assert net["020.030.0020"] == pytest.approx(total, abs=0.01)
    assert "020.040.0010" not in net, (
        "a truncated copa histórico gained a software marker when widened — verify the "
        "full text before accepting the move"
    )
