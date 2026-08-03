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
            "Convênio médico de um advogado (JGS) em **fevereiro**, e aqui a própria "
            "planilha responde: em fevereiro ela mantém a **distribuição mensal "
            "(9.379,00, linha 70)** e o **pró-labore (1.621,00, linha 71)** desse "
            "advogado, mas deixa o **convênio (linha 69) em branco**. Quem continua "
            "recebendo distribuição e pró-labore está na folha naquele mês, então o "
            "plano de saúde é um custo real — e o sistema o tem lançado (1.911,95). A "
            "partir de março as três linhas dele ficam vazias nos dois lados (ele sai) e "
            "a Arbitragem passa a bater em 0,00. Em janeiro a diferença é de 50 centavos "
            "(1.911,95 × 1.911,45). **É uma omissão da coluna de fevereiro da planilha, "
            "não uma dúvida.**"
        ),
        "conferir": (
            "Planilha, linhas **69, 70 e 71**, coluna D (fevereiro): as duas últimas "
            "têm valor, a primeira está vazia."
        ),
        "precisamos": None,
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
            "(AASP). Fechamento por pessoa e por conta: **resíduo 0,00 nas 18 células** "
            "(3 áreas × 6 meses), conferido por `scripts/reconcile_custo_equipe.py`."
        ),
        "precisamos": None,
    },
    ("economico", "custo_equipe"): {
        "causa": (
            "Três coisas, todas identificadas:\n\n"
            "* **Convênio médico de janeiro e fevereiro — era um erro nosso, já "
            "corrigido.** A anotação (*memória de cálculo*) que o financeiro deixa no "
            "lançamento do convênio estava **desatualizada** nesses dois meses: ela "
            "descreve um plano de 968,65 quando o valor lançado no sistema era 2.122,30 "
            "(o mesmo nos seis meses). Nós estávamos usando a conta dessa anotação "
            "antiga; agora o sistema só a usa quando ela cita o valor efetivamente "
            "lançado no mês, o que resolve 90% da diferença de janeiro. O que ainda "
            "sobra é que, sem uma anotação válida, usamos o valor cheio do plano — daí "
            "a diferença mudar de sinal.\n"
            "* **Vale dos advogados** — regra confirmada por vocês (sempre incluir); as "
            "colunas de janeiro a maio da planilha não incluem.\n"
            "* **A estagiária do Direito Econômico**, que entra na planilha a partir de "
            "março e que nós reproduzimos ao centavo — é por causa dela que o sinal da "
            "diferença se inverte entre fevereiro e março."
        ),
        "conferir": (
            "Planilha, linhas **44 e 48** (convênio de EHF e RB: a mesma constante nos "
            "seis meses) e **52** (estagiária). No sistema, a anotação do lançamento da "
            "conta `030.010.0110`."
        ),
        "precisamos": (
            "Atualizar no sistema a memória de cálculo do convênio de **janeiro e "
            "fevereiro** (EHF e RB): ela ficou com os números de um plano anterior. Com "
            "a anotação corrigida, esses dois meses fecham sozinhos — não precisamos de "
            "nenhuma decisão, só do texto certo no lançamento."
        ),
    },
    ("contencioso", "despesa_institucional"): {
        "causa": (
            "**Não é uma diferença da área — é a despesa institucional TOTAL, rateada.** A conta é `Despesa Institucional da área = POOL × (custo de equipe da área ÷ custo de equipe total)`, onde o POOL é a despesa institucional menos as despesas de área (planilha, linha 207 = 198 − 203). Decompondo a diferença nos dois fatores (`scripts/audit_desp_inst_rateio.py`, exato ao centavo nas 18 células): a parte que vem da **participação de cada área soma ZERO em todos os meses** — é só redistribuição entre elas — e **toda a diferença de dinheiro vem do POOL** (Jan–Jun: −5.811,73). Ou seja: para explicar esta linha, olhe a linha *Despesas Indiretas* do institucional. **Junho prova o mecanismo:** o POOL difere exatamente **R$ 4,80** (a tarifa bancária que a planilha zera), a participação não muda nada, e por isso as três áreas ficam em centavos (1,72 / 1,84 / 1,24)."
        ),
        "conferir": "Planilha, linha **207** (`=198−203`) para o POOL, e linhas **5 / 30 / 60** para o custo de equipe de cada área. Rode `python -m scripts.audit_desp_inst_rateio`.",
        "precisamos": None,
    },
    ("economico", "despesa_institucional"): {
        "causa": (
            "Mesma origem do Contencioso: é o POOL institucional rateado, e a parte da "
            "participação por área soma zero. Ver a explicação em *Contencioso · Despesa "
            "Institucional*."
        ),
        "conferir": "Planilha, linha **207** (`=198−203`) para o POOL, e linhas **5 / 30 / 60** para o custo de equipe de cada área. Rode `python -m scripts.audit_desp_inst_rateio`.",
        "precisamos": None,
    },
    ("arbitragem", "despesa_institucional"): {
        "causa": (
            "Mesma origem do Contencioso: POOL institucional rateado. Ver a explicação em "
            "*Contencioso · Despesa Institucional*."
        ),
        "conferir": "Planilha, linha **207** (`=198−203`) para o POOL, e linhas **5 / 30 / 60** para o custo de equipe de cada área. Rode `python -m scripts.audit_desp_inst_rateio`.",
        "precisamos": None,
    },
    ("contencioso", "despesas_equipe"): {
        "causa": (
            "**Causa provada, não suposta:** a fórmula das linhas 204/205/206 da planilha lê as linhas da área SEGUINTE, de janeiro a maio. Verificado nos rótulos: a fórmula do Contencioso soma *“Eventos e Happy hour - Direito Econômico”*, a do Econômico soma *“... - Institucional”*, e a da Arbitragem soma *“... - Contencioso”* — cinco famílias cada (Eventos/HH, Material Gráfico, Patrocínio, Refeições, Viagens). **Medido:** recalculando janeiro a maio com a fórmula de junho, o erro absoluto total cai de 10.216,31 para 3.494,78 (**−66%**) e as células que batem vão de **4 para 11 de 18**. As fórmulas de junho já estão corretas."
            " O que sobra depois disso é **janeiro** e é conhecido: a planilha de janeiro não somou a AASP (195,40) nem o Canal de Arbitragem (1.204,47) — lançamentos reais que existem no sistema (o Canal de Arbitragem é exatamente o resíduo da Arbitragem). E as duas fatias de Associações: a planilha divide 700,10 para o Contencioso (linha 129) e 700,10 para o Econômico (linha 130), enquanto o sistema marca as duas no centro de custo do Econômico — por isso o nosso Econômico lê 1.400,19. Isso é o critério que a Renata já definiu: alocar pelo rótulo / centro de custo."
        ),
        "conferir": "Planilha, linhas **204 / 205 / 206** (colunas C a G) e as linhas 125–161 que elas somam. Rode `python -m scripts.audit_despesas_area` para ver a recomposição.",
        "precisamos": (
            "Confirmar se as fórmulas das linhas 204/205/206 de janeiro a maio podem ser "
            "copiadas de junho, que já está correto."
        ),
    },
    ("economico", "despesas_equipe"): {
        "causa": (
            "**Causa provada, não suposta:** a fórmula das linhas 204/205/206 da planilha lê as linhas da área SEGUINTE, de janeiro a maio. Verificado nos rótulos: a fórmula do Contencioso soma *“Eventos e Happy hour - Direito Econômico”*, a do Econômico soma *“... - Institucional”*, e a da Arbitragem soma *“... - Contencioso”* — cinco famílias cada (Eventos/HH, Material Gráfico, Patrocínio, Refeições, Viagens). **Medido:** recalculando janeiro a maio com a fórmula de junho, o erro absoluto total cai de 10.216,31 para 3.494,78 (**−66%**) e as células que batem vão de **4 para 11 de 18**. As fórmulas de junho já estão corretas. Ver *Contencioso · Despesas Equipe* para o resíduo de janeiro."
        ),
        "conferir": "Planilha, linhas **204 / 205 / 206** (colunas C a G) e as linhas 125–161 que elas somam. Rode `python -m scripts.audit_despesas_area` para ver a recomposição.",
        "precisamos": "Mesma confirmação das fórmulas 204/205/206.",
    },
    ("arbitragem", "despesas_equipe"): {
        "causa": (
            "**Causa provada, não suposta:** a fórmula das linhas 204/205/206 da planilha lê as linhas da área SEGUINTE, de janeiro a maio. Verificado nos rótulos: a fórmula do Contencioso soma *“Eventos e Happy hour - Direito Econômico”*, a do Econômico soma *“... - Institucional”*, e a da Arbitragem soma *“... - Contencioso”* — cinco famílias cada (Eventos/HH, Material Gráfico, Patrocínio, Refeições, Viagens). **Medido:** recalculando janeiro a maio com a fórmula de junho, o erro absoluto total cai de 10.216,31 para 3.494,78 (**−66%**) e as células que batem vão de **4 para 11 de 18**. As fórmulas de junho já estão corretas. Na Arbitragem o efeito é o maior dos três, porque as cinco "
            "linhas da própria área ficam fora da soma. O resíduo de janeiro "
            "(+1.204,47) é exatamente o **Canal de Arbitragem**, que a planilha daquele "
            "mês não somou."
        ),
        "conferir": "Planilha, linhas **204 / 205 / 206** (colunas C a G) e as linhas 125–161 que elas somam. Rode `python -m scripts.audit_despesas_area` para ver a recomposição.",
        "precisamos": "Mesma confirmação das fórmulas 204/205/206.",
    },
    ("contencioso", "resultado_bruto"): {
        "causa": (
            "**Não é uma diferença própria — é a soma das linhas acima.** Verificado nas "
            "18 células (3 áreas × 6 meses): a diferença do Resultado Bruto é igual a "
            "`Δreceita − Δcusto de equipe − Δcomissão − Δdespesas equipe − Δdespesa "
            "institucional`, com erro máximo de R$ 0,01. Então não há nada a explicar "
            "aqui que não esteja explicado nas linhas que o compõem."
        ),
        "conferir": (
            "Some as linhas acima da própria área na planilha (linhas 39 a 42 do "
            "Contencioso, 57 a 60 do Econômico, 75 a 78 da Arbitragem)."
        ),
        "precisamos": None,
    },
    ("economico", "resultado_bruto"): {
        "causa": (
            "**Não é uma diferença própria — é a soma das linhas acima.** Verificado nas "
            "18 células (3 áreas × 6 meses): a diferença do Resultado Bruto é igual a "
            "`Δreceita − Δcusto de equipe − Δcomissão − Δdespesas equipe − Δdespesa "
            "institucional`, com erro máximo de R$ 0,01. Então não há nada a explicar "
            "aqui que não esteja explicado nas linhas que o compõem."
        ),
        "conferir": (
            "Some as linhas acima da própria área na planilha (linhas 39 a 42 do "
            "Contencioso, 57 a 60 do Econômico, 75 a 78 da Arbitragem)."
        ),
        "precisamos": None,
    },
    ("arbitragem", "resultado_bruto"): {
        "causa": (
            "**Não é uma diferença própria — é a soma das linhas acima.** Verificado nas "
            "18 células (3 áreas × 6 meses): a diferença do Resultado Bruto é igual a "
            "`Δreceita − Δcusto de equipe − Δcomissão − Δdespesas equipe − Δdespesa "
            "institucional`, com erro máximo de R$ 0,01. Então não há nada a explicar "
            "aqui que não esteja explicado nas linhas que o compõem."
        ),
        "conferir": (
            "Some as linhas acima da própria área na planilha (linhas 39 a 42 do "
            "Contencioso, 57 a 60 do Econômico, 75 a 78 da Arbitragem)."
        ),
        "precisamos": None,
    },
    ("institucional", "despesas"): {
        "causa": (
            "Esta é a linha que **explica também a Despesa Institucional das três "
            "áreas** (ela é rateada a partir daqui). Decompondo por família de despesa, "
            "as partes somam **exatamente** a diferença de cada mês — são componentes "
            "do total, então não sobra resíduo:\n\n"
            "* **Vale do administrativo** (março −2.199,08 · abril −2.199,20 · maio "
            "−2.280,60): a planilha lançou o valor cheio da conta transitória, com as "
            "três pessoas, em Salários Administração; nós lançamos ali só a parte da "
            "pessoa do administrativo e mandamos os dois estagiários para o custo de "
            "equipe das áreas deles. Em janeiro, fevereiro e junho a planilha fez o "
            "mesmo e esses meses batem. Vocês já avaliaram que não vale corrigir.\n"
            "* **Aluguel** (abril e maio, +129,17 cada): o sistema usa o aluguel "
            "líquido da sublocação (crédito Belline). A Renata já autorizou: *“assumam "
            "que o banco está correto”*.\n"
            "* **Tarifa bancária** (+4,80/mês): vem do sistema e está zerada no Excel. "
            "É a única diferença que sobra em junho.\n"
            "* **Trocas de família que não mudam o total** (Endomarketing ↔ "
            "Investimentos em Prospecção, Ocupação ↔ Administrativas): a mesma conta "
            "aparece em famílias diferentes nos dois lados, mas as duas entram no total "
            "da linha 198 — o efeito no número final é **zero**. Em janeiro, por "
            "exemplo, os nossos 1.317,71 de Endomarketing são os mesmos 1.317,71 que a "
            "planilha põe em Investimentos em Prospecção.\n"
            "* **Janeiro, Associações** (+1.399,87): a planilha não somou a AASP "
            "(195,40) nem o Canal de Arbitragem (1.204,47) — lançamentos reais do "
            "sistema.\n"
            "* **Março**: um curso de Arbitragem (−815,49) que a planilha lança como "
            "institucional e que, sendo de uma área, vai para Despesas de Área; e "
            "Informática −237,60, que é `7.744,12 − 7.506,52` na conta `040.040.0030` "
            "(a planilha usou o valor bruto, nós usamos o líquido, que é a regra "
            "confirmada e faz 10 de 10 famílias baterem em maio)."
        ),
        "conferir": (
            "Planilha: linhas **122 e 123** (vale ADM), **86** (aluguel), **124** "
            "(tarifa/administrativas), **128–131** (Associações), **158** (Gestão do "
            "Conhecimento), **180** (Informática). O total da linha é a **198**."
        ),
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
    add("Quatro causas explicam tudo, e cada uma foi medida — não é suposição:")
    add("")
    add("1. **Despesa Institucional por área não é um problema por área: é o POOL**")
    add("   **institucional rateado.** Separando a diferença nos dois fatores da conta")
    add("   (POOL × participação de cada área), a parte da *participação* **soma zero em**")
    add("   **todos os meses** — é só redistribuição — e todo o dinheiro vem do POOL")
    add("   (Jan–Jun −5.811,73). Para explicar essas três linhas, olhe *Despesas")
    add("   Indiretas*. Junho prova: POOL difere R$ 4,80 (a tarifa bancária) e as três")
    add("   áreas ficam em 1,72 / 1,84 / 1,24.")
    add("2. **A fórmula das linhas 204/205/206 lê as linhas da área SEGUINTE, de janeiro**")
    add("   **a maio** — conferido nos rótulos, não deduzido. Recalculando com a fórmula")
    add("   de junho, o erro cai **66%** e as células que batem vão de 4 para 11 de 18.")
    add("   É a causa que mais pesa em Despesas Equipe.")
    add("3. **O vale dos advogados no custo de equipe** — regra confirmada por vocês")
    add("   (sempre incluir). Em junho o Custo equipe das três áreas fecha (0,00 no")
    add("   Contencioso e na Arbitragem, 0,01 no Econômico), porque a planilha passou a")
    add("   incluir o vale a partir desse mês.")
    add("4. **O convênio médico de fevereiro na Arbitragem** — aparece só em fevereiro")
    add("   (+1.911,95) e é a única diferença que ainda depende de uma definição de vocês.")
    add("")
    add("Uma observação que vale para ler todas as tabelas: **Resultado Bruto não tem**")
    add("**causa própria** — nas 18 células (3 áreas × 6 meses) a diferença dele é igual à")
    add("soma das diferenças das linhas que o compõem, com erro máximo de R$ 0,01.")
    add("")
    add("⚠ **Por que algumas diferenças CRESCERAM em relação à versão anterior deste**")
    add("**documento.** Corrigimos o convênio de janeiro e fevereiro (a anotação")
    add("desatualizada, explicada em *Econômico · Custo equipe*). Isso deixou cada linha")
    add("mais correta, mas fez os totais parecerem piores: o erro do Econômico estava")
    add("**cancelando** o da Arbitragem. Em fevereiro, por exemplo, as três áreas somavam")
    add("-1.267,37 (parecia perto) porque -3.016,26 do Econômico anulava +1.911,95 da")
    add("Arbitragem; agora somam +3.154,72. **Um total que fecha por cancelamento não é**")
    add("**um número validado** — preferimos cada linha certa a um total bonito. O erro")
    add("absoluto do custo de equipe por área em jan/fev caiu 53%.")
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

    add("## O que precisamos de vocês")
    add("")
    add("A lista encurtou: quase tudo que estava em aberto foi respondido pelos próprios")
    add("dados. **Sobrou uma coisa só que depende de vocês, e é pequena.**")
    add("")
    add("### 1. Atualizar duas anotações no sistema (não é uma decisão)")
    add("")
    add("A memória de cálculo do **convênio médico de EHF e RB, em janeiro e fevereiro**,")
    add("ficou com os números de um plano anterior: ela descreve um plano de 968,65")
    add("quando o valor lançado naquele mês já era 2.122,30. Com o texto atualizado no")
    add("lançamento, esses dois meses fecham sozinhos. Não precisamos de nenhuma")
    add("definição — só do texto certo.")
    add("")
    add("### 2. Um valor digitado no vale-transporte de janeiro: R$ 35,52")
    add("")
    add("Duas células de vale-transporte têm uma soma digitada à mão. **Uma das duas nós")
    add("conseguimos explicar inteira; a outra tem um pedaço que falta.**")
    add("")
    add("| Célula | Fórmula | Primeiro termo | Segundo termo |")
    add("|---|---|---|---|")
    add("| `E123` (março) | `=543,22+674` | ✅ VR 507,10 + VT 36,12 da estagiária | ✅ VT do mês das três pessoas (674,12) |")
    add("| `C123` (janeiro) | `=35,52+262,64` | ❓ **35,52 — não encontramos** | ✅ VT da pessoa do ADM (14 dias × 18,76) |")
    add("")
    add("**Março está resolvido, e a intuição de que era \"um VR mais um VT\" estava certa:**")
    add("os 543,22 são um pagamento de benefícios da estagiária feito **fora** da conta")
    add("transitória — `020.080.0050` Vale Refeição **507,10** + `020.080.0060` Vale")
    add("Transporte **36,12**. Os dois lançamentos estão no sistema, com o nome dela no")
    add("histórico.")
    add("")
    add("**Janeiro é o que falta.** Procuramos os 35,52 por todos os caminhos:")
    add("")
    add("* Não é vale-refeição: o VR é R$ 46,10/dia e nunca fica abaixo de R$ 783,70 no")
    add("  mês — 35,52 é pequeno demais.")
    add("* Todo vale do ano é um número inteiro de dias × uma diária (46,10 no VR; 10,80,")
    add("  18,76 e 33,60 no VT, por pessoa, e a conta vem escrita no próprio histórico do")
    add("  lançamento). **35,52 não é** nenhuma dessas combinações.")
    add("* Não existe como lançamento em nenhum dos oito meses, nem no extrato de contas")
    add("  de maio, nem no de junho.")
    add("* As contas de benefício da estagiária que explicam março (`020.080.*`) **não")
    add("  existem em janeiro** — naquele mês há exatamente quatro lançamentos de vale")
    add("  (VR e VT de duas pessoas), e nenhum é 35,52.")
    add("")
    add("**E sabemos que não é um pedaço faltando do nosso número.** Como todo vale é um")
    add("número inteiro de dias, dá para conferir mês a mês:")
    add("")
    add("| Mês | VR (dias) | VT (dias, ADM) | Diferença |")
    add("|---|---:|---:|---:|")
    add("| Janeiro | 18 | 14 | +4 |")
    add("| Fevereiro | 22 | 18 | +4 |")
    add("| Março | 20 | 17 | +3 |")
    add("| Abril | 20 | 16 | +4 |")
    add("| Maio | 17 | 14 | +3 |")
    add("| Junho | 22 | 17 | +5 |")
    add("")
    add("A diferença entre dias de VR e de VT fica entre **+3 e +5 em todos os meses** — o")
    add("VR é pago por dia trabalhado e o VT só pelos dias em que a pessoa veio. Janeiro,")
    add("com 14 dias de VT, está no mesmo padrão. A hipótese mais tentadora era que os")
    add("35,52 fossem dois dias de VT que faltavam (2 × 18,76 = 37,52, e aí janeiro fecharia")
    add("em 16 dias) — mas com 16 dias a diferença cairia para **+2**, que não acontece em")
    add("mês nenhum. Ou seja: **o nosso 262,64 é o vale-transporte completo dela em**")
    add("**janeiro**, e os 35,52 são algo somado em cima de um valor que já estava certo.")
    add("")
    add("**O que ajudaria:** de onde vêm esses R$ 35,52? Se for de outra competência ou um")
    add("acerto pontual, passamos a tratá-lo da mesma forma. Vale notar que é a **única**")
    add("coisa em todo o bloco de vale que continua sem explicação.")
    add("")
    add("### E o que NÃO precisa mais de vocês")
    add("")
    add("Ficam registrados aqui porque estavam na lista anterior:")
    add("")
    add("* **Fórmulas das linhas 204/205/206** — continuam deslocadas de janeiro a maio e")
    add("  vale corrigir na planilha, mas não muda nada no sistema: é a planilha que lê a")
    add("  linha da área seguinte. Junho já está certo.")
    add("* **Convênio da linha 69 em fevereiro** — respondido pela própria planilha: ela")
    add("  mantém a distribuição e o pró-labore desse advogado em fevereiro e zera só o")
    add("  convênio. Ele estava na folha, o plano era custo real.")
    add("* **Lançamentos avulsos de janeiro e fevereiro** — conferimos um a um e eles")
    add("  **estão** no sistema, dentro do lançamento único de distribuição. Exemplo:")
    add("  Andrielly em fevereiro, planilha 9.822,92 (cinco linhas) × sistema 9.822,92 —")
    add("  bate em **R$ 0,00**. Era diferença de apresentação, não de valor.")
    add("* **Associações de janeiro** — a planilha não somou a AASP (195,40) nem o Canal")
    add("  de Arbitragem (1.204,47); os dois existem no sistema.")
    add("* **Vale ADM de março a maio** e **aluguel** — já respondidos por vocês.")
    add("")

    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)}  ({len(materiais)} materiais, {len(menores)} menores)")


if __name__ == "__main__":
    main()
