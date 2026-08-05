"""Guards for the client-facing differences document's two *presentation* contracts.

`docs/DIFERENCAS_ACUMULADO_2026.md` is read by finance, next to their own workbook, and its
credibility rests on the reader being able to add the printed numbers up. Two defects broke
that and neither was caught by anything — the causes are hand-written prose, and the
generator needs a live Supabase snapshot, so no test touched it at all:

1. **The same line printed two different accumulated totals.** Contencioso · Custo equipe
   was ``+R$ 3.140,19`` in the summary table and ``+R$ 3.140,20`` in its own detail table,
   because the summary summed ``round(o - b)`` per month while the detail table subtracted
   two separately-rounded accumulated columns. ``round(Σ) ≠ Σ(round)``.
2. **A line whose months cancelled was filed as immaterial.** Econômico · Despesas Equipe
   is −R$ 31,45 YTD out of −1.166,75 in February and +1.504,72 in May. A YTD-only
   materiality floor buried it under "Diferenças menores" — in a document that warns, two
   paragraphs into itself, that a total which nets to zero is not validated.

These test the pure helpers only (no Supabase, no workbook), which is what the defects
lived in.

The account-level breakdown (added 2026-08-05, so finance sees *which* despesas move rather
than only that a line moved) carries a third contract: it tells the reader that what it
lists is "exactly what explains that difference — nothing more". That is only true if the
unmatched leaves reconstruct the family delta, so ``_conciliar`` is pinned here too.
"""
from __future__ import annotations

import pytest

import scripts.build_diferencas_doc as bd
from scripts.build_diferencas_doc import (
    LIMIAR,
    _conciliar,
    _delta,
    _material,
    _pct,
    _sgn,
)


def test_delta_of_rounded_values_sums_to_the_printed_total():
    """Σ(printed month deltas) must equal the printed Acumulado, exactly.

    Real Contencioso · Custo equipe figures (ours, workbook) for Jan–Jun 2026 — the case
    that printed 3.140,19 and 3.140,20 for the same line of the same document.
    """
    # Exact values off the live assembly and the workbook — the workbook carries a
    # trailing half-centavo on every month, which is what makes the two definitions
    # diverge. Rounding these to the cent by hand hides the defect.
    pares = [
        (73478.62, 73576.315),
        (76179.29, 76342.345),
        (74072.29, 72845.495),
        (76311.31, 75374.055),
        (75378.11, 74141.215),
        (75424.21, 75424.215),
    ]
    mensais = [_delta(o, b) for o, b in pares]

    # What the summary row prints.
    soma_das_linhas = round(sum(mensais), 2)
    # What the detail table's Acumulado row prints: the two rounded columns, subtracted.
    acumulado = _delta(
        round(sum(round(o, 2) for o, _ in pares), 2),
        round(sum(round(b, 2) for _, b in pares), 2),
    )

    assert soma_das_linhas == acumulado == 3140.20
    # The old ``round(o - b, 2)`` definition is what disagreed; keep it pinned so nobody
    # reintroduces it thinking the two are interchangeable.
    assert round(sum(round(o - b, 2) for o, b in pares), 2) == 3140.19


def test_delta_rounds_each_side_before_subtracting():
    # A half-centavo on one side only: the raw subtraction keeps it and rounds the result
    # down, while rounding each side first lands on the value the table actually prints.
    assert _delta(10.0, 9.995) == 0.01
    assert round(10.0 - 9.995, 2) == 0.01  # agrees here...
    assert _delta(0.0, -0.005) == 0.01
    assert round(0.0 - (-0.005), 2) == 0.01
    # ...and the divergence is cumulative, not per-cell: see the test above, where six
    # such months differ by exactly one centavo in the total.
    assert _delta(1.0, 1.0) == 0.0
    assert _delta(-2.5, 1.25) == -3.75


def test_a_line_whose_months_cancel_is_material():
    """Econômico · Despesas Equipe: −31,45 YTD, but ±1.500 inside it."""
    mensais = [-471.62, -1166.75, 0.0, 102.20, 1504.72, 0.0]
    ytd = round(sum(mensais), 2)

    assert ytd == -31.45
    assert abs(ytd) < LIMIAR  # a YTD-only floor would have hidden it
    assert _material(ytd, mensais)


def test_material_requires_a_thousand_somewhere():
    assert not _material(-31.45, [-471.62, 102.20, 999.99])
    assert _material(-31.45, [-471.62, 102.20, 1000.0])
    assert _material(-5003.04, [-549.40, -2944.23])
    assert not _material(0.0, [0.0, 0.0])


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        (0.0, "R$ 0,00"),  # an exact tie gets NO sign — it is checked, not rounded-down
        (0.004, "R$ 0,00"),
        (1533.77, "+R$ 1.533,77"),
        (-4381.39, "-R$ 4.381,39"),
        (None, "—"),
    ],
)
def test_signed_money_reads_unambiguously(valor: float | None, esperado: str):
    assert _sgn(valor) == esperado


def test_percentages_use_a_comma():
    # The whole document is PT-BR: "34.95%" next to "R$ 1.234,56" reads as a thousands
    # separator to the reader this is written for.
    assert _pct(0.349468) == "34,95%"
    assert _pct(0.0) == "0,00%"


def test_unmatched_leaves_reconstruct_the_family_delta():
    """The breakdown claims to list *exactly* what explains a difference.

    Real Salários Administração, March: the workbook posts the full 3-person transitória in
    two rows; we post MLA-only plus the estagiária's two separate accounts. Nothing matches
    by label, but Convênio and Salário do match by value and must drop out.
    """
    nossas = [
        ("Salários", 4498.50),
        ("Convênio Médico - ADM", 1269.46),
        ("Vale Refeição", 507.10),
        ("Vale Transporte", 36.12),
        ("Vale Refeição/Transporte - ADM", 1240.92),
    ]
    planilha = [
        ("Convênio Médico - ADM", 1269.46, 118),
        ("Salario ADM", 4498.50, 121),
        ("Vale Refeição- ADM", 2766.00, 122),
        ("Vale Transporte", 1217.22, 123),
    ]
    batem, so_nossas, so_planilha = _conciliar(nossas, planilha)

    assert batem == 2  # Convênio 1.269,46 and Salário 4.498,50 agree and are netted out
    assert so_nossas == [
        ("Vale Refeição", 507.10),
        ("Vale Transporte", 36.12),
        ("Vale Refeição/Transporte - ADM", 1240.92),
    ]
    assert so_planilha == [
        ("Vale Refeição- ADM", 2766.00, 122),
        ("Vale Transporte", 1217.22, 123),
    ]
    # The listed remainder IS the family difference — that is the claim the doc makes.
    delta = round(sum(v for _, v in so_nossas) - sum(v for _, v, _ in so_planilha), 2)
    assert delta == -2199.08


def test_conciliar_matches_by_value_not_label():
    # Same value, different label on each side: still the same lançamento. Matching by
    # label is impossible here — our one "Serviços de Informática" is the book's "Suporte
    # de Informática" + "Suporte Totvs", and the book splits Associações three ways.
    batem, so_nossas, so_planilha = _conciliar(
        [("Energia Elétrica", 863.59)], [("Energia", 863.59, 89)]
    )
    assert (batem, so_nossas, so_planilha) == (1, [], [])


def test_conciliar_keeps_repeated_values_separate():
    # Two leaves at the same value on one side and one on the other: exactly one pairs off.
    batem, so_nossas, so_planilha = _conciliar(
        [("A", 700.10), ("B", 700.10)], [("X", 700.10, 129)]
    )
    assert batem == 1
    assert so_nossas == [("B", 700.10)]
    assert so_planilha == []


def test_onde_esta_finds_a_value_split_across_two_families(monkeypatch):
    """The January Ocupação delta the reader could not find.

    Our single ``Seguros`` 2.722,55 is the book's *Seguro Locação* 182,71 (Ocupação) **plus**
    *Seguro de Responsabilidade Civil* 2.539,84 — which sits in **Administrativas**. So
    Ocupação differs by +2.539,84 while no Ocupação row on either side holds that number.
    A within-family view can never show this; ``_onde_esta`` names the other family.
    """
    folhas = {
        ("Ocupação", 1): [("Seguro Locação", 182.71, 91)],
        ("Administrativas", 1): [("Seguro de Responsabilidade Civil", 2539.84, 133)],
    }
    monkeypatch.setattr(
        bd, "FAMILIAS", {"Ocupação": (85, 92), "Administrativas": (124, 137)}
    )
    monkeypatch.setattr(
        bd, "_folhas_planilha", lambda base, fam, m: folhas.get((fam, m), [])
    )

    partes = bd._onde_esta(2722.55, "Ocupação", 1, base=None)

    assert [(n, v, r, f) for n, v, r, f in partes] == [
        ("Seguro Locação", 182.71, 91, "Ocupação"),
        ("Seguro de Responsabilidade Civil", 2539.84, 133, "Administrativas"),
    ]
    # And the part that is elsewhere is exactly the unexplained delta.
    assert round(sum(v for _, v, _, f in partes if f != "Ocupação"), 2) == 2539.84


def test_onde_esta_is_silent_when_the_value_is_inside_its_own_family(monkeypatch):
    # Aluguel differs because we net the sublocação credit, not because it moved family.
    # Reporting a "resto" here would invent a cross-family story that does not exist.
    monkeypatch.setattr(bd, "FAMILIAS", {"Ocupação": (85, 92)})
    monkeypatch.setattr(
        bd,
        "_folhas_planilha",
        lambda base, fam, m: [("Aluguel", 24230.60, 86), ("Condomínio", 4996.0, 87)],
    )
    assert bd._onde_esta(24359.77, "Ocupação", 5, base=None) == []


def test_conciliar_reports_one_sided_families():
    # January Investimentos em Prospecção: the book has two rows, we have none — the whole
    # family moved to Endomarketing on our side. Nothing may be silently dropped.
    batem, so_nossas, so_planilha = _conciliar(
        [], [("Eventos - Contencioso", 146.0, 139), ("Eventos - Inst.", 1171.71, 141)]
    )
    assert batem == 0
    assert so_nossas == []
    assert len(so_planilha) == 2
    assert round(-sum(v for _, v, _ in so_planilha), 2) == -1317.71
