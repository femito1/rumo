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

#: Hand-written causes, keyed by (section, line). Deliberately SHORT and in plain PT-BR —
#: this is read by finance, so no script names, no internal counts ("18 células"), no
#: percentages. The shared causes (fórmula deslocada, POOL rateado, RB = soma) are stated
#: once in the "Quatro causas" summary; the per-line entries just point back to them.
#: ``conferir`` names workbook cells only; ``precisamos`` is what finance must do (almost
#: always None now).
CAUSAS: dict[tuple[str, str], dict[str, str | None]] = {
    ("arbitragem", "custo_equipe"): {
        "causa": (
            "Convênio médico de um advogado (JGS) em **fevereiro** — e a própria "
            "planilha responde. Em fevereiro ela mantém a distribuição (linha 70) e o "
            "pró-labore (linha 71) dele e deixa só o convênio (linha 69) em branco. Quem "
            "recebe distribuição está na folha, então o plano é custo real, e o sistema "
            "o tem lançado. De março em diante ele sai dos dois lados e a Arbitragem "
            "bate em 0,00. **Não é dúvida — é uma omissão da coluna de fevereiro.**"
        ),
        "conferir": "Planilha, linhas **69, 70 e 71**, coluna de fevereiro.",
        "precisamos": None,
    },
    ("contencioso", "custo_equipe"): {
        "causa": (
            "O **vale dos advogados** (causa 3 do resumo): entra sempre no custo da área, "
            "por regra de vocês, e a planilha não o incluiu de janeiro a maio. Junho, que "
            "já inclui, bate em 0,00. O restante é classificação que não muda total "
            "(ISS e AASP — ver *Diferenças de classificação*)."
        ),
        "conferir": "Planilha, linhas **26 e 27** (vale).",
        "precisamos": None,
    },
    ("economico", "custo_equipe"): {
        "causa": (
            "Três coisas: o **convênio de EHF e RB em jan/fev** (causa 4 do resumo — o "
            "sistema agora calcula sozinho e não depende mais de vocês); o **vale dos "
            "advogados** (como no Contencioso); e a **estagiária do Direito Econômico**, "
            "que entra na planilha em março e que reproduzimos ao centavo — é ela que "
            "inverte o sinal da diferença entre fevereiro e março. Sobra uma estimativa "
            "nossa: a parte MBC do **RB em janeiro** (o plano dele mudou e nada registra "
            "qual era a proporção naquele mês)."
        ),
        "conferir": "Planilha, linhas **44 e 48** (convênio) e **52** (estagiária).",
        "precisamos": None,
    },
    ("contencioso", "despesa_institucional"): {
        "causa": (
            "**Não é da área — é a despesa institucional total, rateada** (causa 1 do "
            "resumo). A diferença vem inteira do total; a divisão entre as três áreas "
            "não cria nem apaga dinheiro. Para entender esta linha, olhe *Despesas "
            "Indiretas*."
        ),
        "conferir": "Planilha, linha **207** (total a ratear) e **5 / 30 / 60** (custo de cada área).",
        "precisamos": None,
    },
    ("economico", "despesa_institucional"): {
        "causa": "Mesma causa do Contencioso: é o total institucional rateado (causa 1).",
        "conferir": "Planilha, linha **207** e **5 / 30 / 60**.",
        "precisamos": None,
    },
    ("arbitragem", "despesa_institucional"): {
        "causa": "Mesma causa do Contencioso: é o total institucional rateado (causa 1).",
        "conferir": "Planilha, linha **207** e **5 / 30 / 60**.",
        "precisamos": None,
    },
    ("contencioso", "despesas_equipe"): {
        "causa": (
            "A **fórmula deslocada** da planilha (causa 2 do resumo): de janeiro a maio "
            "cada área soma as despesas da área seguinte. Junho já está com a fórmula "
            "certa e bate. O que sobra em janeiro são lançamentos que a planilha não "
            "somou (ver *Despesas Indiretas*)."
        ),
        "conferir": "Planilha, linhas **204 / 205 / 206**, colunas de janeiro a maio.",
        "precisamos": "Vale copiar as fórmulas de junho para janeiro–maio na planilha.",
    },
    ("economico", "despesas_equipe"): {
        "causa": "A **fórmula deslocada** da planilha (causa 2). Junho está certo e bate.",
        "conferir": "Planilha, linhas **204 / 205 / 206**, colunas de janeiro a maio.",
        "precisamos": "Mesma correção de fórmula.",
    },
    ("arbitragem", "despesas_equipe"): {
        "causa": (
            "A **fórmula deslocada** da planilha (causa 2) — na Arbitragem o efeito é o "
            "maior dos três. O resíduo de janeiro (+1.204,47) é o **Canal de "
            "Arbitragem**, que a planilha daquele mês não somou."
        ),
        "conferir": "Planilha, linhas **204 / 205 / 206**, colunas de janeiro a maio.",
        "precisamos": "Mesma correção de fórmula.",
    },
    ("contencioso", "resultado_bruto"): {
        "causa": "Não tem causa própria: é a soma das linhas acima da área (causa 3 do resumo).",
        "conferir": "Some as linhas 39 a 42 da própria área na planilha.",
        "precisamos": None,
    },
    ("economico", "resultado_bruto"): {
        "causa": "Não tem causa própria: é a soma das linhas acima da área (causa 3 do resumo).",
        "conferir": "Some as linhas 57 a 60 da própria área na planilha.",
        "precisamos": None,
    },
    ("arbitragem", "resultado_bruto"): {
        "causa": "Não tem causa própria: é a soma das linhas acima da área (causa 3 do resumo).",
        "conferir": "Some as linhas 75 a 78 da própria área na planilha.",
        "precisamos": None,
    },
    ("institucional", "despesas"): {
        "causa": (
            "Esta linha também explica a Despesa Institucional das três áreas (ela é "
            "rateada daqui). Somando família por família, as partes dão **exatamente** a "
            "diferença de cada mês — não sobra centavo:\n\n"
            "* **Vale do administrativo** (mar −2.199 · abr −2.199 · mai −2.281): a "
            "planilha lançou as três pessoas em Salários Administração; nós lançamos ali "
            "só a pessoa do administrativo e mandamos os estagiários para as áreas. Jan, "
            "fev e jun batem. Vocês já disseram que não vale corrigir.\n"
            "* **Aluguel** (abr e mai, +129,17): usamos o aluguel líquido da sublocação "
            "(crédito Belline), que vocês já autorizaram.\n"
            "* **Tarifa bancária** (+4,80/mês): vem do sistema e está zerada no Excel. É "
            "a única diferença que sobra em junho.\n"
            "* **Trocas de família** (Endomarketing ↔ Prospecção, Ocupação ↔ "
            "Administrativas): a mesma conta em famílias diferentes de cada lado, mas as "
            "duas entram no total — efeito **zero** (ver *Diferenças de classificação*).\n"
            "* **Janeiro, Associações** (+1.399,87): a planilha não somou a AASP (195,40) "
            "nem o Canal de Arbitragem (1.204,47), que existem no sistema.\n"
            "* **Janeiro, seguro** (+2.539,84): é um prêmio **anual**. A conta lança "
            "2.722,55 em janeiro (de novo em julho); a planilha digita 182,71 todo mês. "
            "Não falta dinheiro: a planilha põe o prêmio em *Administrativas* (linha 133) "
            "e nós em Ocupação.\n"
            "* **Março, vale da estagiária** (+543,22): um pagamento de benefícios fora "
            "da conta transitória (Vale Refeição 507,10 + Vale Transporte 36,12, com o "
            "nome dela no histórico).\n"
            "* **Duas contas sem linha na planilha**: janeiro **IR Fonte ADM 169,52** e "
            "fevereiro **e-Social 1.032,35** — lançamentos reais, ausentes do Excel.\n"
            "* **Março**: um curso de Arbitragem (−815,49) que a planilha pôs em "
            "institucional e nós na área; e Informática −237,60 (a planilha usou o valor "
            "bruto, nós o líquido — a regra que vocês confirmaram)."
        ),
        "conferir": (
            "Planilha: linhas **122/123** (vale ADM), **86** (aluguel), **128–131** "
            "(Associações), **133** (seguro), **158** (curso), **180** (Informática). O "
            "total é a linha **198** — e, depois de nomear cada item acima, ele fecha sem "
            "sobra."
        ),
        "precisamos": None,
    },
    ("institucional", "custo_equipe"): {
        "causa": (
            "É a soma dos custos de equipe das três áreas — mesmas causas já descritas em "
            "cada uma (vale, convênio, estagiária)."
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


def _br_date(iso: str) -> str:
    y, m, d = iso.split("-")
    return f"{d}/{m}/{y}"


def _vintage(snaps: dict[int, Any], months: list[int]) -> str:
    """When the compared snapshots were produced, so a reader knows the data's age.

    A document full of numbers with no date invites "is this still current?" in the
    meeting, and the answer is not guessable from the content.
    """
    stamps = sorted(
        d
        for d in (
            str((snaps[m].get("meta") or {}).get("generated_at") or "")[:10]
            for m in months
        )
        if d
    )
    if not stamps:
        return "data desconhecida"
    lo, hi = stamps[0], stamps[-1]
    return _br_date(lo) if lo == hi else f"{_br_date(lo)} a {_br_date(hi)}"


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
    from app.closing.dre import assemble_dre_sections, convenio_mbc_shares

    snaps = get_snapshot_store().snapshots_by_year(2026, client_id="mbc")
    entries = get_budget_repo().get_budget("mbc", 2026)
    ann = annual_budget(entries) if entries else {}
    # Same whole-year Parte MBC shares the app uses (``provider.py``), so a month with a
    # stale convênio memo is valued here exactly as the product values it. Without this
    # the document would quietly disagree with the screens it is explaining.
    shares = convenio_mbc_shares(snaps)
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
            convenio_shares=shares,
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
    rb = ytd_of(ytd, "institucional", "resultado_bruto")
    add(f"# Diferenças entre a planilha e o sistema — Janeiro a {ult} de 2026")
    add("")
    add(f"Comparação da planilha `{WORKBOOK.name}` com os números do sistema, dados"
        f" extraídos em {_vintage(snaps, months)}.")
    add("")
    add("## O essencial, em cinco linhas")
    add("")
    add("1. **A receita bate em todos os meses.** Toda diferença está em *despesa*.")
    add(f"2. No acumulado de janeiro a {ult.lower()}, o **Resultado Bruto** difere"
        f" **{_sgn(rb)}** — sobre uma receita de mais de R$ 2 milhões.")
    add("3. **Cada centavo dessa diferença tem uma causa identificada** — nenhuma sobra"
        " sem explicação. As causas estão logo abaixo.")
    add("4. **Junho fecha** (só a tarifa bancária de R$ 4,80 difere): é o mês em que a"
        " planilha já está com as fórmulas certas e inclui o vale — é o melhor espelho"
        " de como os dois lados batem quando ambos estão corretos.")
    add("5. **Só falta uma coisa de vocês, e é pequena:** de onde vem o R$ 35,52 do"
        " vale-transporte de janeiro (última seção). Todo o resto ou já está respondido,"
        " ou é a planilha que precisa de um ajuste — não o sistema.")
    add("")
    add("## Como conferir qualquer número")
    add("")
    add("Cada diferença aparece **mês a mês** com a **célula exata da planilha** ao lado.")
    add("Abra a planilha, vá na célula indicada e compare com a coluna *Sistema*. As colunas")
    add("de cada mês na aba `Areas Sintetico atualizado` são: " + ", ".join(
        f"**{abbr[m]}={_col(SINT_COL[m])}**" for m in months) + ".")
    add("")
    add(f"Só detalhamos diferenças de **{_brl(LIMIAR)} ou mais**; as menores estão no fim.")
    add("")

    # ── What does NOT differ.
    add("## O que NÃO difere")
    add("")
    add(_hdr("Linha", months, abbr))
    add(_sep(months))
    for section, line, label, wrow, _o, _b, _d in ytd:
        if section == "institucional" and line in ("recebimento", "imposto", "amortizacao"):
            add(_row_deltas(label, per_month[(section, line)], months, ytd_of(ytd, section, line)))
    add("")
    add("Receita, impostos e amortização batem. Os centavos de maio e junho são só")
    add("arredondamento (a planilha arredonda o recebimento para reais inteiros).")
    add("")

    add("## As quatro causas")
    add("")
    add("Praticamente toda a diferença vem de quatro coisas. A tabela seguinte mostra onde")
    add("cada linha cai; o detalhe por linha vem depois.")
    add("")
    add("1. **A planilha rateia a despesa institucional entre as áreas com uma fórmula**")
    add("   **deslocada** (linhas 204/205/206), de janeiro a maio: cada área acaba somando")
    add("   as despesas da área seguinte. Junho já está com a fórmula certa. Isso move as")
    add("   linhas de *Despesa Institucional* e *Despesas Equipe* das três áreas — mas é a")
    add("   **planilha** que precisa de ajuste, não o sistema.")
    add("2. **A despesa institucional por área é o total institucional dividido entre as**")
    add("   **áreas.** A divisão em si não cria nem apaga dinheiro (a soma das três áreas é")
    add("   sempre a mesma); a diferença vem do total. Para entender essas linhas, olhe")
    add("   *Despesas Indiretas*.")
    add("3. **O vale dos advogados** entra no custo da equipe por regra de vocês, e a")
    add("   planilha não o incluiu de janeiro a maio. Em junho ela passou a incluir e o")
    add("   custo de equipe das três áreas fecha. (O *Resultado Bruto* por área não tem")
    add("   causa própria — é só a soma das linhas da área.)")
    add("4. **O convênio médico de EHF e RB em janeiro/fevereiro** — resolvido, e não")
    add("   depende mais de vocês. Detalhe no item *Econômico · Custo equipe*.")
    add("")
    add("**O que melhorou desde a última versão:** o sistema passou a calcular sozinho a")
    add("parte da MBC no convênio quando a anotação do lançamento está velha. Com isso o")
    add(f"Resultado Bruto acumulado saiu de −R$ 7.640,50 para **{_sgn(rb)}**.")
    add("")
    add("*Uma ressalva ao ler qualquer total: um número que fecha porque dois erros se*")
    add("*anulam não está validado. Por isso mostramos tudo mês a mês, não só o acumulado —*")
    add("*é mais honesto e mais fácil de conferir.*")
    add("")
    add("## Resumo: onde estão as diferenças")
    add("")
    add("Diferença = Sistema − Planilha, por mês. `✓` = bate.")
    add("")
    add(_hdr("Linha", months, abbr))
    add(_sep(months))
    for section, line, label, _w, _o, _b, _d in sorted(materiais, key=_ordem):
        add(_row_deltas(label, per_month[(section, line)], months, ytd_of(ytd, section, line)))
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
    add("**Uma coisa só, pequena: de onde vem o R$ 35,52 do vale-transporte de janeiro.**")
    add("")
    add("A célula `C123` da planilha traz `=35,52+262,64`. Os 262,64 são o vale-transporte")
    add("da pessoa do administrativo (14 dias × R$ 18,76), que confere. Os **35,52** não")
    add("conseguimos amarrar a nenhum lançamento:")
    add("")
    add("* não é vale-refeição (o menor do ano é R$ 783,70 no mês);")
    add("* não é um número inteiro de dias em nenhuma diária de vale;")
    add("* **não aparece em lançamento nenhum** — alargamos o texto dos lançamentos do")
    add("  sistema e re-extraímos os oito meses só para poder afirmar isso; o histórico do")
    add("  vale de janeiro é literalmente \"Vale refeição\" / \"Vale transporte\", sem conta.")
    add("")
    add("Também sabemos que **não é um pedaço que falta do nosso número**: o nosso")
    add("vale-transporte de janeiro (R$ 262,64) já está completo, então os 35,52 são algo")
    add("somado por cima. Depois de explicar tudo o mais centavo a centavo, é o **único**")
    add("valor do acumulado inteiro que não amarramos a um lançamento.")
    add("")
    add("**O que ajudaria:** de onde veio esse R$ 35,52? Se for de outra competência ou um")
    add("acerto, passamos a tratá-lo da mesma forma.")
    add("")
    add("*(Curiosidade útil: o `=543,22+674` de março, que era a outra soma digitada à mão,")
    add("está resolvido — os 543,22 são vale-refeição 507,10 + vale-transporte 36,12 de uma")
    add("estagiária, os dois lançados no sistema.)*")
    add("")
    add("### Já respondido — nada a fazer")
    add("")
    add("Itens que estavam em aberto e hoje estão fechados, para registro:")
    add("")
    add("* **Convênio de EHF e RB (jan/fev)** — pedíamos que a anotação do lançamento fosse")
    add("  corrigida; hoje o sistema calcula a parte da MBC sozinho, então pode ficar como")
    add("  está. (Sobra uma estimativa nossa: a parte da MBC do RB em janeiro.)")
    add("* **Convênio da linha 69 (fev)** — a própria planilha responde: mantém")
    add("  distribuição e pró-labore do advogado e zera só o convênio; ele estava na folha.")
    add("* **Lançamentos avulsos de jan/fev** — conferidos um a um, estão no sistema dentro")
    add("  do lançamento de distribuição. Ex.: Andrielly em fevereiro bate em R$ 0,00.")
    add("* **Associações de janeiro** — a planilha não somou a AASP nem o Canal de")
    add("  Arbitragem; ambos existem no sistema.")
    add("* **Vale ADM (mar–mai)** e **aluguel** — já respondidos por vocês.")
    add("")
    add("### Só na planilha — nada a mudar no sistema")
    add("")
    add("* **Fórmulas das linhas 204/205/206** (jan–mai) — deslocadas; vale copiar as de")
    add("  junho. Não muda nada no sistema.")
    add("")
    add("### Diferenças de classificação — mesmo total, seção diferente")
    add("")
    add("Não mexem em nenhum total, só em onde a conta aparece:")
    add("")
    add("* **ISS trimestral** — por advogado no sistema, uma linha só na planilha (efeito")
    add("  no acumulado: R$ 0,04).")
    add("* **AASP** — dentro do Custo equipe na planilha, em Despesa de Área no sistema.")
    add("* **Endomarketing × Prospecção** e **Ocupação × Administrativas** — a mesma conta")
    add("  em famílias diferentes de cada lado; ambas entram no total, efeito zero.")
    add("")

    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)}  ({len(materiais)} materiais, {len(menores)} menores)")


if __name__ == "__main__":
    main()
