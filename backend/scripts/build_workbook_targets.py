#!/usr/bin/env python3
"""Regenerate the workbook targets JSON used by the hard rule.

The hard rule (docs/MEETING_2026-07-10.md §V; app/closing/verification.py) blanks
any Realizado cell that diverges from the workbook by more than R$0,01. Those
targets come from the AUTHORITATIVE ``Fechamento MBC 05.2026.xlsx`` (05.2026 wins
on any conflict), sheet "Areas Sintetico atualizado".

Layout of that sheet (verified 2026-07-10):
  - Row 1 carries month headers; each month occupies 4 columns
    (Orçado | Realizado | Variação | Desvio%). Realizado columns:
    Jan=3, Fev=7, Mar=11, Abr=15, Mai=19.
  - Institucional block (Resultado Institucional), 1-based rows:
      4  Receita (recebimento)
      6  Custos Diretos  -> our "custo_equipe" line (= equipe + comissão)
      13 Despesas Indiretas -> "despesas"
      25 Resultado Bruto
      28 Impostos (15% do recebimento)
      29 Investimento amortização (8.117/mês)
      30 Resultado Liquido após impostos
      32 Bonus (10% do líquido; segue o sinal do líquido)
  - Per-area blocks start at: Contencioso=35, Econômico=53, Arbitragem=71.
    Within a block: Receita=+1, Custo Equipe=+4, Resultado Bruto=+8.

Run:  python backend/scripts/build_workbook_targets.py
Writes: backend/app/closing/workbook_targets_2026.json
"""
from __future__ import annotations

import json
from pathlib import Path

import openpyxl

REPO = Path(__file__).resolve().parents[2]
WORKBOOK = REPO / "reference" / "workbook" / "Fechamento MBC 05.2026.xlsx"
SHEET = "Areas Sintetico atualizado"
OUT = REPO / "backend" / "app" / "closing" / "workbook_targets_2026.json"

MONTH_REALIZADO_COL = {
    "2026-01": 3, "2026-02": 7, "2026-03": 11, "2026-04": 15, "2026-05": 19,
}
INST_ROWS = {
    "recebimento": 4, "custo_equipe": 6, "despesas": 13, "resultado_bruto": 25,
    "imposto": 28, "amortizacao": 29, "resultado_liquido": 30, "reserva_bonus": 32,
}
AREA_BASE = {"contencioso": 35, "economico": 53, "arbitragem": 71}
AREA_LINES = {"recebimento": 1, "custo_equipe": 4, "resultado_bruto": 8}

# Client-authorized target overrides (Renata, 2026-07-14): "assume the DB is
# correct for the aluguel–Belline numbers (ONLY those)". Our GERENC-net aluguel
# (net of the Belline sublet credit) is authoritative; the workbook typed a value
# R$129,17 lower. For the months where the ONLY divergence from the workbook is
# this aluguel delta (Apr + May 2026 — verified per-family to the centavo), bump
# the ``despesas`` target by the delta and propagate through the dependent tail so
# the hard rule stops blanking Despesas / Resultado Bruto / Líquido / Reserva.
# This is aluguel-scoped ONLY; do NOT extend it to absorb other residuals.
ALUGUEL_BELLINE_DELTA = 129.17
ALUGUEL_TARGET_OVERRIDE_MONTHS = ("2026-04", "2026-05")


def _apply_aluguel_override(inst: dict[str, float]) -> None:
    """In place: raise despesas by the authorized aluguel delta and recompute the
    tail (resultado_bruto/liquido drop by the same delta; reserva = 10% of líquido).
    Imposto (15% of recebimento) and amortização are unaffected by a despesa change.
    """
    d = ALUGUEL_BELLINE_DELTA
    if "despesas" in inst:
        inst["despesas"] = round(inst["despesas"] + d, 2)
    if "resultado_bruto" in inst:
        inst["resultado_bruto"] = round(inst["resultado_bruto"] - d, 2)
    if "resultado_liquido" in inst:
        inst["resultado_liquido"] = round(inst["resultado_liquido"] - d, 2)
        # Reserva de bônus = 10% do líquido (segue o sinal), recomputed from the
        # corrected líquido so the whole chain stays internally consistent.
        inst["reserva_bonus"] = round(inst["resultado_liquido"] * 0.10, 2)


def main() -> None:
    wb = openpyxl.load_workbook(WORKBOOK, data_only=True, read_only=True)
    ws = wb[SHEET]
    rows = list(ws.iter_rows(min_row=1, max_row=120, max_col=30, values_only=True))

    def cell(row1: int, col1: int) -> float | None:
        v = rows[row1 - 1][col1 - 1]
        return round(float(v), 2) if isinstance(v, (int, float)) else None

    targets: dict[str, dict[str, dict[str, float]]] = {}
    for month, col in MONTH_REALIZADO_COL.items():
        sec: dict[str, dict[str, float]] = {}
        sec["institucional"] = {
            k: v for k, rn in INST_ROWS.items() if (v := cell(rn, col)) is not None
        }
        for area, base in AREA_BASE.items():
            sec[area] = {
                k: v
                for k, off in AREA_LINES.items()
                if (v := cell(base + off, col)) is not None
            }
        # Client-authorized aluguel-Belline override (see constants above).
        if month in ALUGUEL_TARGET_OVERRIDE_MONTHS:
            _apply_aluguel_override(sec["institucional"])
        targets[month] = sec

    final = {
        "_meta": {
            "_source": WORKBOOK.name,
            "_sheet": SHEET,
            "_note": (
                "Alvos Realizado por competencia (regra dura: divergencia > R$0,01 "
                "=> celula em branco). Gerado por scripts/build_workbook_targets.py."
            ),
        },
        "targets": targets,
    }
    OUT.write_text(json.dumps(final, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT} ({len(targets)} months)")


if __name__ == "__main__":
    main()
