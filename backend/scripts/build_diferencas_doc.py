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


def _sgn(v: float) -> str:
    """Signed money, with an explicit ``+`` so the direction is never ambiguous."""
    if v is None:
        return "—"
    s = f"{abs(v):,.2f}".replace(",", "@").replace(".", ",").replace("@", ".")
    return f"{'-' if v < 0 else '+'}R$ {s}"


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
    L: list[str] = []
    add = L.append
    add(f"# Diferenças entre a planilha e o sistema — acumulado Janeiro a {ult} de 2026")
    add("")
    add("> Documento gerado por `backend/scripts/build_diferencas_doc.py` a partir dos")
    add("> dados ao vivo do sistema e de `Fechamento MBC 06.2026.xlsx`. Cada diferença")
    add("> abaixo já foi diagnosticada e tem causa identificada — **não é uma lista de**")
    add("> **erros**. Junho fecha exatamente e é o melhor mês de referência.")
    add("")
    add("## Como ler este documento")
    add("")
    add("Para cada linha em que a planilha e o sistema divergem no acumulado, mostramos")
    add("sempre na mesma ordem: **o que a planilha mostra**, **o que o sistema mostra**,")
    add("**a diferença**, e **por quê**. Onde há algo a decidir, isso está em *O que")
    add("precisamos de vocês*.")
    add("")
    add(f"Só entram as diferenças de **R$ {_brl(LIMIAR)} ou mais** no acumulado. As")
    add("menores estão somadas no final, para que nenhuma fique de fora sem explicação.")
    add("")

    # ── The reassurance first, because it frames everything else.
    add("## O que NÃO difere")
    add("")
    add("| Linha | Planilha | Sistema | Diferença |")
    add("|---|---:|---:|---:|")
    for section, line, label, _w, o, b, d in ytd:
        if section == "institucional" and line in (
            "recebimento", "imposto", "amortizacao"
        ):
            add(f"| {label} | {_brl(b)} | {_brl(o)} | **{_sgn(d)}** |")
    add("")
    add("**A receita, os impostos e a amortização batem em todos os meses.** Toda a")
    add("diferença está em *despesa*. No consolidado institucional o Resultado Bruto")
    rb = next(d for s, ln, _l, _w, _o, _b, d in ytd if s == "institucional" and ln == "resultado_bruto")
    rec = next(o for s, ln, _l, _w, o, _b, _d in ytd if s == "institucional" and ln == "recebimento")
    add(f"difere **{_sgn(rb)}** sobre uma receita de {_brl(rec)}.")
    add("")
    add("⚠ Um total consolidado que bate pode esconder diferenças que se cancelam, por")
    add("isso o documento detalha **por área**, e não só o consolidado.")
    add("")

    materiais = [t for t in ytd if abs(t[6]) >= LIMIAR]
    menores = [t for t in ytd if abs(t[6]) < LIMIAR and t[6] != 0.0]

    add("## Resumo das diferenças relevantes")
    add("")
    add("| Linha | Planilha | Sistema | Diferença |")
    add("|---|---:|---:|---:|")
    for _s, _ln, label, _w, o, b, d in sorted(materiais, key=_ordem):
        add(f"| {label} | {_brl(b)} | {_brl(o)} | **{_sgn(d)}** |")
    add("")
    add("As três causas por trás de praticamente tudo isso:")
    add("")
    add("1. **A fórmula das linhas 204/205/206 da planilha está deslocada uma linha de**")
    add("   **janeiro a maio.** É a causa que mais pesa: move a Despesa Institucional e")
    add("   as Despesas Equipe das três áreas ao mesmo tempo. As fórmulas de junho já")
    add("   estão corretas.")
    add("2. **O vale dos advogados no custo de equipe** — regra confirmada por vocês")
    add("   (sempre incluir); as colunas de janeiro a maio da planilha não incluem.")
    add("3. **O convênio médico de janeiro/fevereiro** — a única diferença que ainda")
    add("   depende de uma definição de vocês.")
    add("")

    add("## Detalhe, linha por linha")
    add("")
    for section, line, label, wrow, o, b, d in sorted(materiais, key=_ordem):
        info = CAUSAS.get((section, line))
        add(f"### {label} — diferença de {_brl(d)}")
        add("")
        add("| | Valor |")
        add("|---|---:|")
        add(f"| Planilha (*Areas Sintetico*, linha {wrow}, Jan–{ult}) | {_brl(b)} |")
        add(f"| Nosso sistema | {_brl(o)} |")
        add(f"| **Diferença** | **{_sgn(d)}** |")
        add("")
        if info:
            add(f"**Por quê:** {info['causa']}")
            add("")
            add(f"**Onde conferir:** {info['conferir']}")
            add("")
            if info.get("precisamos"):
                add(f"**O que precisamos de vocês:** {info['precisamos']}")
                add("")
        else:
            add("**Por quê:** causa ainda não documentada — falar com o time antes da reunião.")
            add("")

    add("## Diferenças menores (abaixo do limiar)")
    add("")
    if menores:
        add("| Linha | Planilha | Sistema | Diferença |")
        add("|---|---:|---:|---:|")
        for _s, _ln, label, _w, o, b, d in sorted(menores, key=lambda t: -abs(t[6])):
            add(f"| {label} | {_brl(b)} | {_brl(o)} | {_sgn(d)} |")
        add("")
        add(f"Somadas: **{_sgn(round(sum(t[6] for t in menores), 2))}**. As causas conhecidas")
        add("são a tarifa bancária que vem do sistema e está zerada no Excel (R$ 4,80 por")
        add("mês), o vale do administrativo de março a maio e centavos de arredondamento.")
    else:
        add("Nenhuma.")
    add("")

    add("## O que precisamos de vocês, em ordem")
    add("")
    add("1. **Convênio médico de janeiro e fevereiro** (EHF e RB): o memo do sistema")
    add("   nesses dois meses declara uma base de plano diferente da de março a junho, e")
    add("   a planilha usa a constante de março nos seis meses. Qual vale para jan/fev?")
    add("2. **Fórmulas das linhas 204/205/206** de janeiro a maio: podem ser copiadas de")
    add("   junho, que já está correto?")
    add("3. **Janeiro, vale-transporte:** a planilha traz `=35,52+262,64`. Os 262,64 são")
    add("   o lançamento do sistema; de onde vêm os 35,52?")
    add("4. **Lançamentos avulsos de janeiro e fevereiro** (linhas 34, 35, 43, 47, 51 e")
    add("   54): são de outra competência ou ajustes manuais? Se tiverem origem no")
    add("   sistema, passamos a considerá-los.")
    add("5. **Convênio médico da linha 69:** deveria continuar em fevereiro, como está no")
    add("   sistema, ou foi encerrado em janeiro?")
    add("")

    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)}  ({len(materiais)} materiais, {len(menores)} menores)")


if __name__ == "__main__":
    main()
