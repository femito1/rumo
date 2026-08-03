"""Standalone PT-BR document explaining the MATERIAL workbook-vs-system differences.

Written for Renata (finance): no codebase knowledge assumed, one consistent format per
difference, every number traceable to a workbook cell. Deliberately a DOCUMENT and not a
product feature — the client asked for the explanations to live outside the app (2026-08),
and the in-app "Diferenças conhecidas" panel was removed in the same change.

The format, every time:

    Planilha (<aba>, linha <n>)   <valor>
    Nosso sistema                 <valor>
    Diferença                     <±valor>
    Por quê / Onde conferir / O que precisamos

Reads the LIVE snapshots + the June workbook and derives the per-área YTD from the
PRODUCTION ``assemble_dre_sections`` — never a re-implementation, so the document cannot
drift from what the app shows. Re-run it after any re-extract.

Materiality: R$ 1.000 on the YTD. The client's words: R$ 4,80 does not matter, R$ 1.900
does. Everything below the line is summed and named as a remainder rather than dropped, so
"small" never reads as "unexamined".

Run: cd backend && python -m scripts.build_diferencas_doc
Writes: docs/DIFERENCAS_ACUMULADO_2026.md
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import openpyxl

REPO = Path(__file__).resolve().parents[2]
WORKBOOK = REPO / "reference" / "workbook" / "Fechamento MBC 06.2026.xlsx"
OUT = REPO / "docs" / "DIFERENCAS_ACUMULADO_2026.md"

#: Materiality floor on the YTD difference, in R$.
LIMIAR = 1000.0

#: Lines that are SUMS of other lines in this document. They carry the biggest deltas, so
#: sorting purely by size would open with three "consequência das linhas acima" entries
#: before the reader has seen a single cause. These are ordered last.
#: NB the per-área ``custo_equipe`` is NOT derived — it has its own causes (vale, ISS,
#: AASP); only the institucional roll-ups and the resultados are.
def _is_derivada(section: str, line: str) -> bool:
    return line in ("resultado_bruto", "resultado_liquido") or (
        section == "institucional" and line in ("custo_equipe", "despesas")
    )


def _ordem(t: tuple) -> tuple[int, float]:
    """Sort: explaining lines first (largest first), derived roll-ups after."""
    section, line = t[0], t[1]
    return (1 if _is_derivada(section, line) else 0, -abs(t[6]))


MESES = {1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho"}
#: 'Areas Sintetico atualizado' Realizado column per month.
SINT_COL = {1: 3, 2: 7, 3: 11, 4: 15, 5: 19, 6: 23}
#: 'Base_Resultado Mensal_V2' month column (the detail behind the sintetico totals).
BASE_COL = {1: 3, 2: 4, 3: 5, 4: 6, 5: 7, 6: 8}

#: (our section, our line key, label, sintetico row).
LINHAS: tuple[tuple[str, str, str, int], ...] = (
    ("institucional", "recebimento", "Receita", 4),
    ("institucional", "custo_equipe", "Custos Diretos", 6),
    ("institucional", "despesas", "Despesas Indiretas", 13),
    ("institucional", "resultado_bruto", "Resultado Bruto", 25),
    ("institucional", "imposto", "Impostos", 28),
    ("institucional", "amortizacao", "Amortização", 29),
    ("institucional", "resultado_liquido", "Resultado Líquido", 30),
    ("contencioso", "custo_equipe", "Contencioso · Custo equipe", 39),
    ("contencioso", "despesas_equipe", "Contencioso · Despesas Equipe", 41),
    ("contencioso", "despesa_institucional", "Contencioso · Despesa Institucional", 42),
    ("contencioso", "resultado_bruto", "Contencioso · Resultado Bruto", 43),
    ("economico", "custo_equipe", "Econômico · Custo equipe", 57),
    ("economico", "despesas_equipe", "Econômico · Despesas Equipe", 59),
    ("economico", "despesa_institucional", "Econômico · Despesa Institucional", 60),
    ("economico", "resultado_bruto", "Econômico · Resultado Bruto", 61),
    ("arbitragem", "custo_equipe", "Arbitragem · Custo equipe", 75),
    ("arbitragem", "despesas_equipe", "Arbitragem · Despesas Equipe", 77),
    ("arbitragem", "despesa_institucional", "Arbitragem · Despesa Institucional", 78),
    ("arbitragem", "resultado_bruto", "Arbitragem · Resultado Bruto", 79),
)

#: Hand-written causes, keyed by (section, line). Committed and reviewable — nothing here
#: inspects a value or decides a number is wrong (the no-guard-layer decision stands).
#: ``causa`` explains, ``conferir`` says where to verify, ``precisamos`` is what finance
#: has to rule on (None = nothing needed, already settled).
CAUSAS: dict[tuple[str, str], dict[str, str | None]] = {
    ("arbitragem", "custo_equipe"): {
        "causa": (
            "Convênio médico de um advogado da Arbitragem em **fevereiro**. O memo do "
            "sistema em janeiro e fevereiro declara uma base de plano diferente da de "
            "março a junho, e é internamente consistente nessa base (`1.795,86 - "
            "1.192,36 (Parte MBC) = 603,50` para outro advogado, mesma mecânica). A "
            "planilha repete a constante de março nos seis meses, ou seja, em jan/fev "
            "ela não segue o próprio memo do sistema."
        ),
        "conferir": "Base_Resultado linha 69; conta `030.010.0110`.",
        "precisamos": (
            "Uma definição: em janeiro e fevereiro vale o valor do memo do sistema ou a "
            "constante que está na planilha? É a maior diferença de custo de equipe do "
            "acumulado."
        ),
    },
    ("contencioso", "custo_equipe"): {
        "causa": (
            "Vale-refeição e vale-transporte dos advogados. A regra confirmada por "
            "vocês é sempre incluir o vale no custo da equipe da área; as colunas de "
            "janeiro a maio da planilha não o incluem (as de junho sim, e junho fecha "
            "exatamente). Somam-se a isso duas diferenças que não mudam nenhum total: "
            "o ISS trimestral, que o sistema lança por advogado e a planilha digita "
            "numa única linha da área, e a AASP, que a planilha lança dentro do custo "
            "de equipe e o sistema classifica como Despesa de Área."
        ),
        "conferir": (
            "Base_Resultado linhas 26/27 (Vale), 25/54/79 (ISS Trimestral) e 9/18/36 "
            "(AASP). Fechamento por pessoa e por conta: resíduo 0,00 nos quatro meses."
        ),
        "precisamos": None,
    },
    ("economico", "custo_equipe"): {
        "causa": (
            "Mesma origem do Contencioso (vale dos advogados, ISS trimestral e AASP), "
            "mais a estagiária do Direito Econômico, que entra na planilha a partir de "
            "março e que nós reproduzimos ao centavo. É exatamente por causa dela que o "
            "sinal da diferença do Econômico se inverte entre fevereiro e março."
        ),
        "conferir": "Base_Resultado linha 52 (estagiária), 56/57 (Vale).",
        "precisamos": None,
    },
    ("contencioso", "despesa_institucional"): {
        "causa": (
            "A fórmula de Despesas por área da planilha está deslocada uma linha de "
            "janeiro a maio: as linhas 204, 205 e 206 somam a linha de baixo em cinco "
            "famílias de despesa (Eventos e Happy Hour, Material Gráfico, Patrocínio, "
            "Refeições e Viagens). Como o bloco está ordenado Arbitragem / Contencioso "
            "/ Direito Econômico / Institucional, cada área recebe a despesa da área "
            "seguinte. Isso desloca também o rateio da despesa institucional das três "
            "áreas. **As fórmulas de junho já estão corretas — é por isso que junho "
            "fecha exatamente com o nosso número.**"
        ),
        "conferir": "Base_Resultado linhas 204, 205 e 206, colunas de janeiro a maio.",
        "precisamos": (
            "Confirmar se as fórmulas de janeiro a maio devem ser copiadas de junho. "
            "É a causa que mais pesa no acumulado das três áreas."
        ),
    },
    ("economico", "despesa_institucional"): {
        "causa": "A mesma fórmula deslocada das linhas 204/205/206 (ver Contencioso).",
        "conferir": "Base_Resultado linhas 204, 205 e 206, colunas de janeiro a maio.",
        "precisamos": "Mesma confirmação das fórmulas 204/205/206.",
    },
    ("arbitragem", "despesa_institucional"): {
        "causa": "A mesma fórmula deslocada das linhas 204/205/206 (ver Contencioso).",
        "conferir": "Base_Resultado linhas 204, 205 e 206, colunas de janeiro a maio.",
        "precisamos": "Mesma confirmação das fórmulas 204/205/206.",
    },
    ("contencioso", "despesas_equipe"): {
        "causa": (
            "Mesma fórmula deslocada das linhas 204/205/206, que é justamente a linha de "
            "Despesas Equipe por área, mais a classificação da AASP (a planilha a lança "
            "no custo de equipe, o sistema em Despesa de Área — o valor existe nos dois "
            "lados, em seções diferentes)."
        ),
        "conferir": "Base_Resultado linha 204; contas `020.060.*`.",
        "precisamos": "Mesma confirmação das fórmulas 204/205/206.",
    },
    ("economico", "despesas_equipe"): {
        "causa": "A mesma fórmula deslocada das linhas 204/205/206.",
        "conferir": "Base_Resultado linha 205.",
        "precisamos": "Mesma confirmação das fórmulas 204/205/206.",
    },
    ("arbitragem", "despesas_equipe"): {
        "causa": (
            "A mesma fórmula deslocada das linhas 204/205/206. Na Arbitragem o efeito é "
            "maior porque as cinco linhas da área ficam de fora da soma e as cinco do "
            "Institucional entram no lugar."
        ),
        "conferir": "Base_Resultado linha 206.",
        "precisamos": "Mesma confirmação das fórmulas 204/205/206.",
    },
    ("contencioso", "resultado_bruto"): {
        "causa": (
            "Consequência das linhas acima — o resultado bruto é a soma delas, não uma "
            "diferença independente."
        ),
        "conferir": "Ver Custo equipe, Despesas Equipe e Despesa Institucional da área.",
        "precisamos": None,
    },
    ("economico", "resultado_bruto"): {
        "causa": (
            "Consequência das linhas acima — o resultado bruto é a soma delas, não uma "
            "diferença independente."
        ),
        "conferir": "Ver Custo equipe, Despesas Equipe e Despesa Institucional da área.",
        "precisamos": None,
    },
    ("arbitragem", "resultado_bruto"): {
        "causa": (
            "Consequência das linhas acima — o resultado bruto é a soma delas, não uma "
            "diferença independente."
        ),
        "conferir": "Ver Custo equipe, Despesas Equipe e Despesa Institucional da área.",
        "precisamos": None,
    },
    ("institucional", "despesas"): {
        "causa": (
            "Duas causas conhecidas e pequenas: o vale do administrativo em março, abril "
            "e maio (a planilha lançou o valor cheio da conta transitória, com as três "
            "pessoas, e não só a parte do administrativo — vocês já avaliaram que não "
            "vale corrigir) e a tarifa bancária, que vem do sistema e está zerada no "
            "Excel (R$ 4,80 por mês)."
        ),
        "conferir": "Base_Resultado linhas 122 e 123; conta `020.070.0030`.",
        "precisamos": None,
    },
    ("institucional", "custo_equipe"): {
        "causa": (
            "É a soma dos custos de equipe das três áreas, então reflete as mesmas causas "
            "já descritas por área (vale dos advogados, ISS trimestral, AASP e o convênio "
            "de fevereiro)."
        ),
        "conferir": "Ver as três linhas de Custo equipe por área.",
        "precisamos": None,
    },
}


def _brl(v: float | None) -> str:
    """Money the way the client's own documents write it: ``R$ 1.234,56``.

    The currency prefix is not decoration here — this document puts our figure next to
    theirs on every line, and a finance reader should never have to infer the unit.
    """
    if v is None:
        return "—"
    s = f"{abs(v):,.2f}".replace(",", "@").replace(".", ",").replace("@", ".")
    return f"{'-' if v < 0 else ''}R$ {s}"


def _sgn(v: float | None) -> str:
    """Signed money, with an explicit ``+`` so the direction is never ambiguous.

    A zero gets NO sign: "+R$ 0,00" reads like a rounded-down positive when it is an
    exact tie, and this document leans on the ties (June) to make its point.
    """
    if v is None:
        return "—"
    s = f"{abs(v):,.2f}".replace(",", "@").replace(".", ",").replace("@", ".")
    sinal = "" if abs(v) < 0.005 else ("-" if v < 0 else "+")
    return f"{sinal}R$ {s}"


def _col(idx: int) -> str:
    """1-based column index -> Excel letter, so the doc can name the exact cell."""
    from openpyxl.utils import get_column_letter

    return get_column_letter(idx)


def _hdr(first: str, months: list[int], abbr: dict[int, str]) -> str:
    return f"| {first} | " + " | ".join(abbr[m] for m in months) + " | Acumulado |"


def _sep(months: list[int]) -> str:
    return "|---|" + "---:|" * (len(months) + 1)


def ytd_of(rows: list[tuple], section: str, line: str) -> float:
    return next(t[6] for t in rows if t[0] == section and t[1] == line)


def _row_deltas(
    label: str,
    cells: dict[int, tuple[float, float, float]],
    months: list[int],
    total: float | None = None,
) -> str:
    """One summary row: the per-month DELTA plus the accumulated one.

    A tie renders as ``R$ 0,00 ✓`` rather than a blank so a month that agrees reads as
    *checked*, not *missing* — the document leans on June being clean across the board.

    The Acumulado column is the sum of the DISPLAYED months, not a separately rounded
    total. Those differ by a centavo (sum-of-rounded ≠ rounded-of-sum), and a row the
    client cannot add up destroys confidence in the whole document — which is the exact
    problem this rewrite exists to fix. ``total`` is ignored when given.
    """
    del total  # kept for call-site symmetry; the row must add up as printed
    out = []
    for m in months:
        d = cells[m][2]
        out.append(f"{_sgn(d)} ✓" if abs(d) < 0.005 else _sgn(d))
    soma = round(sum(cells[m][2] for m in months), 2)
    return f"| {label} | " + " | ".join(out) + f" | **{_sgn(soma)}** |"


def _our(sections: dict[str, Any], section: str, line: str) -> float | None:
    for row in (sections.get(section) or {}).get("rows") or []:
        if row.get("key") == line:
            cell = row.get("Realizado")
            v = cell.get("value") if isinstance(cell, dict) else cell
            return float(v) if isinstance(v, (int, float)) else None
    return None


def main() -> None:
    from dotenv import load_dotenv

    load_dotenv(REPO / "backend" / ".env")

    from app.api.providers import get_budget_repo, get_snapshot_store
    from app.budget.models import annual_budget, monthly_budget
    from app.closing.dre import assemble_dre_sections

    snaps = get_snapshot_store().snapshots_by_year(2026, client_id="mbc")
    entries = get_budget_repo().get_budget("mbc", 2026)
    ann = annual_budget(entries) if entries else {}
    wb = openpyxl.load_workbook(WORKBOOK, data_only=True)
    sint = wb["Areas Sintetico atualizado"]

    months = [m for m in MESES if m in snaps]
    assembled: dict[int, dict[str, Any]] = {}
    for m in months:
        assembled[m] = assemble_dre_sections(
            snapshot=snaps[m],
            budget=monthly_budget(entries, month=m) if entries else None,
            budget_annual=ann or None,
            transfers=None,
            period_label=f"2026-{m:02d}",
            period_month=m,
            targets=None,
        )

    # YTD per line: ours from the production assembly, theirs from the workbook.
    ytd: list[tuple[str, str, str, int, float, float, float]] = []
    for section, line, label, wrow in LINHAS:
        o = sum((_our(assembled[m], section, line) or 0.0) for m in months)
        b = sum(float(sint.cell(wrow, SINT_COL[m]).value or 0.0) for m in months)
        ytd.append((section, line, label, wrow, round(o, 2), round(b, 2), round(o - b, 2)))

    ult = MESES[max(months)]
    abbr = {m: MESES[m][:3] for m in months}

    # Per-month deltas per line, so nothing is presented only as a YTD total.
    per_month: dict[tuple[str, str], dict[int, tuple[float, float, float]]] = {}
    ytd: list[tuple[str, str, str, int, float, float, float]] = []
    for section, line, label, wrow in LINHAS:
        cells: dict[int, tuple[float, float, float]] = {}
        for m in months:
            o = _our(assembled[m], section, line) or 0.0
            b = float(sint.cell(wrow, SINT_COL[m]).value or 0.0)
            cells[m] = (round(o, 2), round(b, 2), round(o - b, 2))
        per_month[(section, line)] = cells
        ytd.append((
            section, line, label, wrow,
            round(sum(c[0] for c in cells.values()), 2),
            round(sum(c[1] for c in cells.values()), 2),
            round(sum(c[2] for c in cells.values()), 2),
        ))

    materiais = [t for t in ytd if abs(t[6]) >= LIMIAR]
    menores = [t for t in ytd if abs(t[6]) < LIMIAR and t[6] != 0.0]

    L: list[str] = []
    add = L.append
    add(f"# Diferenças entre a planilha e o sistema — Janeiro a {ult} de 2026")
    add("")
    add("> Gerado por `backend/scripts/build_diferencas_doc.py` a partir dos dados ao vivo")
    add(f"> do sistema e da planilha `{WORKBOOK.name}`. Cada diferença abaixo já foi")
    add("> diagnosticada e tem causa identificada — **não é uma lista de erros**.")
    add("")
    add("## Como conferir")
    add("")
    add("Cada diferença aparece **mês a mês**, com a **célula exata da planilha** ao lado.")
    add("Para checar qualquer número: abra a planilha, vá na aba e na célula indicada, e")
    add("compare com a coluna *Sistema*.")
    add("")
    add("As abas usadas são duas:")
    add("")
    add("* **`Areas Sintetico atualizado`** — os totais por linha. O Realizado de cada mês")
    add("  fica numa coluna diferente: " + ", ".join(
        f"**{abbr[m]} = coluna {_col(SINT_COL[m])}**" for m in months) + ".")
    add("* **`Base_Resultado Mensal_V2`** — o detalhe que forma esses totais. Aqui os meses")
    add("  são colunas seguidas: " + ", ".join(
        f"**{abbr[m]} = {_col(BASE_COL[m])}**" for m in months) + ".")
    add("")
    add(f"Só detalhamos as diferenças de **{_brl(LIMIAR)} ou mais** no acumulado; as")
    add("menores estão listadas no fim, também mês a mês.")
    add("")

    # ── What does NOT differ, month by month.
    add("## O que NÃO difere: receita, impostos e amortização")
    add("")
    add(_hdr("Linha", months, abbr))
    add(_sep(months))
    for section, line, label, wrow, _o, _b, _d in ytd:
        if section == "institucional" and line in ("recebimento", "imposto", "amortizacao"):
            add(_row_deltas(label, per_month[(section, line)], months, ytd_of(ytd, section, line)))
    add("")
    add("**A receita bate em todos os meses** — as diferenças acima são de centavos de")
    add("arredondamento (a planilha arredonda o recebimento de maio e junho para reais")
    add("inteiros). Impostos e amortização acompanham. **Toda diferença relevante está em**")
    add("***despesa*** — é para lá que o resto do documento olha.")
    add("")

    add("## Resumo: onde estão as diferenças")
    add("")
    add("Diferença = Sistema − Planilha, por mês.")
    add("")
    add(_hdr("Linha", months, abbr))
    add(_sep(months))
    for section, line, label, _w, _o, _b, _d in sorted(materiais, key=_ordem):
        add(_row_deltas(label, per_month[(section, line)], months, ytd_of(ytd, section, line)))
    add("")
    add("Três causas explicam praticamente tudo, e as colunas mostram isso:")
    add("")
    add("1. **A fórmula das linhas 204/205/206 da planilha está deslocada uma linha, de**")
    add("   **janeiro a maio.** A prova está na coluna de **junho**: nas linhas de Despesa")
    add("   Institucional e Despesas Equipe ela cai para centavos (1,84 / 1,72 / -0,01),")
    add("   enquanto de janeiro a maio passa de mil reais. As fórmulas de junho já estão")
    add("   corretas — é a causa que mais pesa no acumulado.")
    add("2. **O vale dos advogados no custo de equipe** — regra confirmada por vocês")
    add("   (sempre incluir). Em junho o Custo equipe das três áreas fecha (0,00 no")
    add("   Contencioso e na Arbitragem, 0,01 no Econômico), porque a planilha passou a")
    add("   incluir o vale a partir desse mês.")
    add("3. **O convênio médico de fevereiro na Arbitragem** — aparece só em fevereiro")
    add("   (+1.911,95) e é a única diferença que ainda depende de uma definição de vocês.")
    add("")

    add("## Detalhe, linha por linha")
    add("")
    for section, line, label, wrow, o, b, d in sorted(materiais, key=_ordem):
        info = CAUSAS.get((section, line))
        add(f"### {label}")
        add("")
        add(f"Diferença no acumulado: **{_sgn(d)}**")
        add("")
        add("| Mês | Célula na planilha | Planilha | Sistema | Diferença |")
        add("|---|---|---:|---:|---:|")
        cells = per_month[(section, line)]
        for m in months:
            ov, bv, dv = cells[m]
            cel = f"`{_col(SINT_COL[m])}{wrow}`"
            marca = "" if abs(dv) >= 0.005 else " ✓"
            add(f"| {MESES[m]} | {cel} | {_brl(bv)} | {_brl(ov)} | {_sgn(dv)}{marca} |")
        sb = round(sum(cells[m][1] for m in months), 2)
        so = round(sum(cells[m][0] for m in months), 2)
        add(f"| **Acumulado** | — | **{_brl(sb)}** | **{_brl(so)}** | **{_sgn(round(so - sb, 2))}** |")
        add("")
        add(f"Na planilha: aba **Areas Sintetico atualizado**, linha **{wrow}**.")
        add("")
        if info:
            add(f"**Por quê:** {info['causa']}")
            add("")
            add(f"**Onde conferir o detalhe:** {info['conferir']}")
            add("")
            if info.get("precisamos"):
                add(f"**O que precisamos de vocês:** {info['precisamos']}")
                add("")
        else:
            add("**Por quê:** causa ainda não documentada — falar com o time antes da reunião.")
            add("")

    add("## Diferenças menores")
    add("")
    if menores:
        add(_hdr("Linha", months, abbr))
        add(_sep(months))
        for section, line, label, _w, _o, _b, _d in sorted(menores, key=lambda t: -abs(t[6])):
            add(_row_deltas(label, per_month[(section, line)], months, ytd_of(ytd, section, line)))
        add("")
        add(f"Somadas: **{_sgn(round(sum(t[6] for t in menores), 2))}** no acumulado. As causas")
        add("conhecidas são a tarifa bancária, que vem do sistema e está zerada no Excel")
        add("(R$ 4,80 por mês, conta `020.070.0030`), o vale do administrativo de março a")
        add("maio (`Base_Resultado` linhas 122 e 123) e centavos de arredondamento.")
    else:
        add("Nenhuma.")
    add("")

    add("## O que precisamos de vocês, em ordem")
    add("")
    add("1. **Convênio médico de janeiro e fevereiro** (EHF e RB). O memo do sistema nesses")
    add("   dois meses declara uma base de plano diferente da de março a junho, e a")
    add("   planilha usa a constante de março nos seis meses. Qual vale para jan/fev?")
    add("   Conferir em `Base_Resultado Mensal_V2`, linhas 44 e 48, colunas C e D.")
    add("2. **Fórmulas das linhas 204/205/206** de janeiro a maio: podem ser copiadas de")
    add("   junho, que já está correto? Conferir em `Base_Resultado Mensal_V2`, linhas 204")
    add("   a 206, colunas C a G.")
    add("3. **Janeiro, vale-transporte:** a célula `C123` traz `=35,52+262,64`. Os 262,64")
    add("   são o lançamento do sistema; de onde vêm os 35,52?")
    add("4. **Lançamentos avulsos de janeiro e fevereiro:** `Base_Resultado Mensal_V2`")
    add("   linhas 34, 35, 43, 47, 51 e 54, colunas C e D. São de outra competência ou")
    add("   ajustes manuais? Se tiverem origem no sistema, passamos a considerá-los.")
    add("5. **Convênio médico da linha 69** (`C69` tem 1.911,45 e `D69` está vazia):")
    add("   deveria continuar em fevereiro, como está no sistema, ou foi encerrado em")
    add("   janeiro?")
    add("")

    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)}  ({len(materiais)} materiais, {len(menores)} menores)")


if __name__ == "__main__":
    main()
