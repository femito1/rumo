"""Accumulate per-month DRE sections into a year-to-date (acumulado) view.

The 2026-07 client checkpoint asked for a mensal↔acumulado toggle exposing, per
line: Orçado YTD, Realizado YTD (accumulated Jan→competence), Variação, and
Orçado YTG (year-to-go = annual budget − Orçado YTD). Accumulation is a per-line
sum of the already-assembled monthly sections, so it inherits every per-month
rule (per-área reserva, imposto, expense breakdown) for free. Margins/percent
rows are recomputed from the accumulated base, not summed.
"""
import pytest

from app.closing.ytd_accumulate import accumulate_ytd


def _rich(rows):
    return {"kind": "rich", "columns": ["Linha", "Orçado", "Realizado", "Desvio %"],
            "rows": rows, "name": "X"}


def _amount(label, key, orc, real, **kw):
    return {"Linha": label, "Orçado": {"value": orc, "source": "orcado"},
            "Realizado": {"value": real, "source": "realizado"}, "Desvio %": None,
            "key": key, "indent": 0, "is_total": kw.get("is_total", False),
            "kind": kw.get("kind", "amount")}


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
    # Annual budget for YTG (recebimento 1200/yr).
    annual = {"institucional": {"recebimento": 1200.0}}
    out = accumulate_ytd(
        {1: jan, 2: fev}, annual_budget=annual, up_to_month=2
    )
    rows = {r["key"]: r for r in out["institucional"]["rows"]}
    # Columns now carry YTD/YTG/Variação.
    assert out["institucional"]["columns"] == [
        "Linha", "Orçado YTD", "Realizado YTD", "Variação", "Orçado YTG",
    ]
    receb = rows["recebimento"]
    assert receb["Orçado YTD"]["value"] == pytest.approx(200.0)
    assert receb["Realizado YTD"]["value"] == pytest.approx(200.0)  # 90 + 110
    assert receb["Variação"]["value"] == pytest.approx(0.0)  # 200 − 200
    # YTG = annual − Orçado YTD = 1200 − 200 = 1000.
    assert receb["Orçado YTG"]["value"] == pytest.approx(1000.0)
    custo = rows["custo_equipe"]
    assert custo["Realizado YTD"]["value"] == pytest.approx(80.0)  # 30 + 50


def test_accumulate_skips_missing_months_and_recomputes_margin():
    # Margin rows (kind == "margin") are recomputed from the accumulated base, not
    # summed. Here margem = resultado / recebimento on the accumulated totals.
    def month(receb, rl):
        return {"institucional": _rich([
            _amount("Recebimento", "recebimento", 100.0, receb),
            _amount("Resultado Liquido", "resultado_liquido", 10.0, rl, is_total=True,
                    kind="subtotal"),
            {"Linha": "Margem liquida", "Orçado": {"value": None, "source": "orcado"},
             "Realizado": {"value": (rl / receb if receb else None), "source": "realizado"},
             "Desvio %": None, "key": "margem_liquida", "indent": 1, "is_total": False,
             "kind": "margin"},
        ])}
    out = accumulate_ytd({1: month(100.0, 20.0), 2: month(200.0, 40.0)},
                         annual_budget={}, up_to_month=2)
    rows = {r["key"]: r for r in out["institucional"]["rows"]}
    # Accumulated recebimento 300, resultado 60 → margem 0.20 (recomputed, not 0.20+0.20).
    assert rows["resultado_liquido"]["Realizado YTD"]["value"] == pytest.approx(60.0)
    assert rows["margem_liquida"]["Realizado YTD"]["value"] == pytest.approx(0.20, abs=0.001)


def test_accumulate_preserves_non_value_rows():
    # Header/section rows (no numeric Realizado) pass through unchanged in position.
    jan = {"institucional": _rich([
        {"Linha": "DESPESAS", "key": "hdr::x", "kind": "header", "indent": 0,
         "is_total": False},
        _amount("Recebimento", "recebimento", 100.0, 90.0),
    ])}
    out = accumulate_ytd({1: jan}, annual_budget={}, up_to_month=1)
    labels = [r["Linha"] for r in out["institucional"]["rows"]]
    assert labels[0] == "DESPESAS"
