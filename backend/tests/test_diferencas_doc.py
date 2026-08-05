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
"""
from __future__ import annotations

import pytest

from scripts.build_diferencas_doc import LIMIAR, _delta, _material, _sgn


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
