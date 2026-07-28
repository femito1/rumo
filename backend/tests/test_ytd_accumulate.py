"""Accumulate per-month DRE sections into a year-to-date (acumulado) view.

The 2026-07 client checkpoint asked for a cumulative view of the closed months
Jan→competence. It is NOT a second render mode: in the workbook it is the column
group at the far right of 'Areas Sintetico atualizado' (06.2026 cols Z..AE) over
the SAME stacked rows, so we accumulate the already-assembled monthly sections
and expose them as one extra tab. Accumulation inherits every per-month rule
(per-área reserva, imposto, expense breakdown) for free.

Columns mirror the workbook's cumulative block values with corrected names (the
sheet's own headers are misleading: its "Orçado YTG" holds the ANNUAL budget and
its "Variação Mensal" holds a ratio):

    Linha | Orçado YTD | Realizado YTD | Variação | Desvio % | Orçado Anual | Falta p/ meta
"""
import pytest

from app.closing.ytd_accumulate import YTD_COLUMNS, accumulate_ytd


def _rich(rows, name="X"):
    return {"kind": "rich", "columns": ["Linha", "Orçado", "Realizado", "Desvio %"],
            "rows": rows, "name": name}


def _amount(label, key, orc, real, **kw):
    return {"Linha": label, "Orçado": {"value": orc, "source": "orcado"},
            "Realizado": {"value": real, "source": "realizado"}, "Desvio %": None,
            "key": key, "indent": kw.get("indent", 0),
            "is_total": kw.get("is_total", False),
            "kind": kw.get("kind", "amount")}


def _header(title):
    return {"Linha": title, "Orçado": None, "Realizado": None, "Desvio %": None,
            "key": f"hdr::{title}", "indent": 0, "is_total": True, "kind": "header"}


def _margin(label, key, real):
    return {"Linha": label, "Orçado": {"value": None, "source": "orcado"},
            "Realizado": {"value": real, "source": "realizado"}, "Desvio %": None,
            "key": key, "indent": 1, "is_total": False, "kind": "margin"}


def test_accumulate_sums_realizado_and_orcado_per_line():
    # Two months of one section; the acumulado view sums each line.
    jan = {"institucional": _rich([
        _amount("Recebimento", "recebimento", 100.0, 90.0),
        _amount("Custo equipe", "custo_equipe", 40.0, 30.0),
    ])}
    fev = {"institucional": _rich([
        _amount("Recebimento", "recebimento", 100.0, 110.0),
        _amount("Custo equipe", "custo_equipe", 40.0, 50.0),
    ])}
    annual = {"institucional": {"recebimento": 1200.0}}
    out = accumulate_ytd({1: jan, 2: fev}, annual_budget=annual, up_to_month=2)
    rows = {r["key"]: r for r in out["institucional"]["rows"]}
    assert out["institucional"]["columns"] == YTD_COLUMNS
    receb = rows["recebimento"]
    assert receb["Orçado YTD"]["value"] == pytest.approx(200.0)
    assert receb["Realizado YTD"]["value"] == pytest.approx(200.0)  # 90 + 110
    assert receb["Variação"]["value"] == pytest.approx(0.0)  # 200 − 200
    assert receb["Orçado Anual"]["value"] == pytest.approx(1200.0)
    # Workbook AE = annual − Realizado YTD (what is left to hit the plan).
    assert receb["Falta p/ meta"]["value"] == pytest.approx(1000.0)
    custo = rows["custo_equipe"]
    assert custo["Realizado YTD"]["value"] == pytest.approx(80.0)  # 30 + 50


def test_repeated_line_keys_accumulate_per_block():
    """areas_sintetico stacks 4 blocks that REPEAT the same line keys.

    Each block must accumulate on its own — a flat key->total map would show every
    block the sum of all four (institucional + the three áreas).
    """
    def month(values):
        rows = []
        for title, v in values:
            rows.append(_header(f"RESULTADO {title}"))
            rows.append(_amount("Recebimento", "recebimento", 750.0, v))
        return {"areas_sintetico": _rich(rows)}

    blocks = [("INSTITUCIONAL", 1000.0), ("CONTENCIOSO", 500.0),
              ("ECONOMICO", 300.0), ("ARBITRAGEM", 200.0)]
    out = accumulate_ytd({1: month(blocks)}, annual_budget={}, up_to_month=1)
    got = [
        r["Realizado YTD"]["value"]
        for r in out["areas_sintetico"]["rows"]
        if r["key"] == "recebimento"
    ]
    assert got == [1000.0, 500.0, 300.0, 200.0]


def test_header_rows_carry_ytd_column_keys():
    """Every row — including headers — must expose the YTD display keys FIRST.

    The frontend binds columns positionally off ``Object.keys(rows[0])`` and in
    areas_sintetico row 0 IS a header; a header keeping the monthly keys makes the
    whole table read the wrong cells (and leaks ``key`` into the last column).
    """
    sec = {"areas_sintetico": _rich([
        _header("RESULTADO INSTITUCIONAL"),
        _amount("Recebimento", "recebimento", 100.0, 90.0),
    ])}
    out = accumulate_ytd({1: sec}, annual_budget={}, up_to_month=1)
    for row in out["areas_sintetico"]["rows"]:
        assert list(row.keys())[: len(YTD_COLUMNS)] == YTD_COLUMNS


def test_only_allowlisted_dre_sections_are_accumulated():
    """Non-DRE sections have their own column shapes and no YTD meaning.

    Force-fitting them to the YTD columns produced empty/all-null tables
    (rateio_mensal, amortizacao, meta_dashboard, nacional) or all-null numbers
    (base_resultado has no Realizado column; dre_2026 has 12 month columns).
    """
    dre_row = [_amount("Recebimento", "recebimento", 100.0, 90.0)]
    months = {1: {
        "institucional": _rich(dre_row),
        "contencioso": _rich(dre_row),
        "economico": _rich(dre_row),
        "arbitragem": _rich(dre_row),
        "areas_sintetico": _rich(dre_row),
        # Not accumulable:
        "rateio_mensal": {"kind": "rich", "name": "Rateio",
                          "columns": ["Área", "Custo Equipe", "% do Total"], "rows": []},
        "amortizacao": {"kind": "rich", "name": "Amortização",
                        "columns": ["Origem", "Total Investido"], "rows": []},
        "meta_dashboard": {"kind": "rich", "name": "Meta",
                           "columns": ["Mês", "Meta", "Recebimento"], "rows": []},
        "base_resultado": {"kind": "rich", "name": "Base",
                           "columns": ["Linha", "Valor"], "rows": []},
        "dre_2026": {"kind": "rich", "name": "DRE",
                     "columns": ["Linha", "Anual", "Janeiro"], "rows": []},
        "nacional": {"kind": "rich", "name": "Nacional",
                     "columns": ["Fatura", "Cliente"], "rows": []},
    }}
    out = accumulate_ytd(months, annual_budget={}, up_to_month=1)
    assert set(out) == {
        "institucional", "contencioso", "economico", "arbitragem", "areas_sintetico",
    }


def test_falta_para_meta_is_annual_minus_realizado():
    """Locks the workbook's real year-to-go (06.2026 'Areas Sintetico' AE3).

    AE3 = Z3 − AB3 = annual − Realizado YTD = 8.060.000,04 − 3.463.471,64.
    (NOT annual − Orçado YTD, which is what an earlier implementation computed.)
    """
    jan = {"institucional": _rich([
        _amount("Faturamento", "recebimento", 4030000.02, 3463471.64),
    ])}
    annual = {"institucional": {"recebimento": 8060000.04}}
    out = accumulate_ytd({1: jan}, annual_budget=annual, up_to_month=1)
    row = out["institucional"]["rows"][0]
    assert row["Orçado Anual"]["value"] == pytest.approx(8060000.04)
    assert row["Falta p/ meta"]["value"] == pytest.approx(4596528.40)
    # Desvio % = Realizado YTD / Orçado YTD (workbook AD3).
    assert row["Desvio %"] == pytest.approx(0.8594, abs=0.0001)


def test_margin_recomputed_within_its_own_block():
    """A ratio can't be summed — and must divide by ITS OWN block's base.

    Two stacked blocks with different bases: each margem uses its own block's
    accumulated resultado ÷ recebimento. The Orçado margin is recomputed too
    (workbook AA26 = AA25/AA3).
    """
    def block(title, receb, rl, receb_orc, rl_orc):
        return [
            _header(f"RESULTADO {title}"),
            _amount("Recebimento", "recebimento", receb_orc, receb),
            _amount("Resultado Liquido", "resultado_liquido", rl_orc, rl,
                    is_total=True, kind="subtotal"),
            _margin("Margem liquida", "margem_liquida", rl / receb),
        ]

    rows = block("INSTITUCIONAL", 1000.0, 200.0, 1000.0, 400.0)
    rows += block("CONTENCIOSO", 400.0, 40.0, 500.0, 100.0)
    out = accumulate_ytd({1: {"areas_sintetico": _rich(rows)}},
                         annual_budget={}, up_to_month=1)
    margins = [
        r for r in out["areas_sintetico"]["rows"] if r["key"] == "margem_liquida"
    ]
    assert margins[0]["Realizado YTD"]["value"] == pytest.approx(0.20)  # 200/1000
    assert margins[1]["Realizado YTD"]["value"] == pytest.approx(0.10)  # 40/400
    # Orçado margin recomputed from the accumulated Orçado base, per block.
    assert margins[0]["Orçado YTD"]["value"] == pytest.approx(0.40)  # 400/1000
    assert margins[1]["Orçado YTD"]["value"] == pytest.approx(0.20)  # 100/500


def test_tolerates_month_with_different_row_count():
    """Institucional block 3 emits one row per account PRESENT that month, so row
    counts genuinely vary. A month missing a sub-account still contributes the
    rows it shares (occurrence keying, not raw row index)."""
    jan = {"institucional": _rich([
        _amount("Recebimento", "recebimento", 100.0, 90.0),
        _amount("Ocupação", "acct::Indiretas::Ocupação", None, 10.0, indent=1),
        _amount("Informática", "acct::Indiretas::Informática", None, 5.0, indent=1),
    ])}
    fev = {"institucional": _rich([
        _amount("Recebimento", "recebimento", 100.0, 110.0),
        # Informática absent this month.
        _amount("Ocupação", "acct::Indiretas::Ocupação", None, 20.0, indent=1),
    ])}
    out = accumulate_ytd({1: jan, 2: fev}, annual_budget={}, up_to_month=2)
    rows = {r["key"]: r for r in out["institucional"]["rows"]}
    assert rows["recebimento"]["Realizado YTD"]["value"] == pytest.approx(200.0)
    assert rows["acct::Indiretas::Ocupação"]["Realizado YTD"]["value"] == pytest.approx(30.0)


def test_accumulate_skips_months_after_the_competence_month():
    jan = {"institucional": _rich([_amount("Recebimento", "recebimento", 100.0, 90.0)])}
    mar = {"institucional": _rich([_amount("Recebimento", "recebimento", 100.0, 500.0)])}
    out = accumulate_ytd({1: jan, 3: mar}, annual_budget={}, up_to_month=2)
    rows = {r["key"]: r for r in out["institucional"]["rows"]}
    assert rows["recebimento"]["Realizado YTD"]["value"] == pytest.approx(90.0)


def test_no_present_month_returns_empty():
    assert accumulate_ytd({}, annual_budget={}, up_to_month=6) == {}
