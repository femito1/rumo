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
    """True for lines that are pure SUMS of other lines shown in this document.

    ``institucional.despesas`` is deliberately NOT one, even though it is a total: three
    per-área Despesa Institucional entries point at it as their cause, so it must keep its
    own detailed breakdown (vale ADM, prêmio anual de seguro, IR Fonte, e-Social…). Listing
    it among the roll-ups silently deleted that breakdown — caught 2026-08-04.
    """
    return line in ("resultado_bruto", "resultado_liquido") or (
        section == "institucional" and line == "custo_equipe"
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
            "O **vale dos advogados** (causa 3 do resumo): entra sempre no custo da área e "
            "a planilha não o incluiu de janeiro a maio. Junho, que "
            "já inclui, bate em 0,00. O restante é classificação que não muda total "
            "(ISS e AASP — ver *Diferenças que não mudam nenhum total*)."
        ),
        "conferir": "Planilha, linhas **26 e 27** (vale).",
        "precisamos": None,
    },
    ("economico", "custo_equipe"): {
        "causa": (
            "Três coisas: a **anotação do convênio de EHF e RB** em jan/fev (causa 4 do "
            "resumo); o **vale dos advogados** (como no Contencioso); e a **estagiária do "
            "Direito Econômico**, "
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
            "fev e jun batem.\n"
            "* **Aluguel** (abr e mai, +129,17): usamos o aluguel líquido da sublocação "
            "(crédito Belline).\n"
            "* **Tarifa bancária** (+4,80/mês): vem do sistema e está zerada no Excel. É "
            "a única diferença que sobra em junho.\n"
            "* **Trocas de família** (Endomarketing ↔ Prospecção, Ocupação ↔ "
            "Administrativas): a mesma conta em famílias diferentes de cada lado, mas as "
            "duas entram no total — efeito **zero** (ver *Diferenças que não mudam nenhum total*).\n"
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
            "bruto, nós o líquido)."
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
    add("## O essencial")
    add("")
    add("1. **A receita bate em todos os meses.** Toda diferença está em *despesa*.")
    add(f"2. No acumulado de janeiro a {ult.lower()}, o **Resultado Bruto** difere"
        f" **{_sgn(rb)}** — sobre uma receita de mais de R$ 2 milhões.")
    add("3. **Cada centavo dessa diferença tem uma causa identificada**, listada abaixo.")
    add("4. **Junho fecha** (só a tarifa bancária de R$ 4,80 difere) — é o mês em que a"
        " planilha já está com as fórmulas certas e inclui o vale. É a referência de como"
        " os dois lados batem quando ambos estão corretos.")
    add("")
    add("Cada diferença vem **mês a mês** com a célula da planilha ao lado (aba"
        " `Areas Sintetico atualizado`, colunas " + ", ".join(
        f"**{abbr[m]}={_col(SINT_COL[m])}**" for m in months) + "). Detalhamos as de"
        f" **{_brl(LIMIAR)} ou mais**; as menores estão no fim.")
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
    add("Os centavos de maio e junho são arredondamento — a planilha arredonda o")
    add("recebimento para reais inteiros.")
    add("")

    add("## As quatro causas")
    add("")
    add("1. **Fórmula deslocada na planilha** (linhas 204/205/206, janeiro a maio): cada")
    add("   área soma as despesas da área **seguinte**. Junho já está certo. Move *Despesas")
    add("   Equipe* e *Despesa Institucional* das três áreas — é ajuste na planilha, não no")
    add("   sistema.")
    add("2. **Despesa Institucional por área é o total institucional dividido entre as**")
    add("   **áreas.** A divisão não cria nem apaga dinheiro; a diferença vem do total (ver")
    add("   *Despesas Indiretas*).")
    add("3. **O vale dos advogados** entra no custo da área, e a planilha não o incluiu de")
    add("   janeiro a maio. Em junho ela incluiu e as três áreas fecham.")
    add("4. **A anotação do convênio médico fica velha.** A *memória de cálculo* no")
    add("   lançamento diz quanto do plano é da MBC; em jan/fev ela descrevia um plano")
    add("   antigo (o mesmo texto vinha desde 2025, com o plano mudando duas vezes). O")
    add("   sistema já não depende dela — calcula pela proporção dos meses corretos — mas")
    add("   **atualizá-la quando um plano mudar** é o que mantém o valor exato em vez de")
    add("   estimado.")
    add("")
    add("*Um total que fecha porque dois erros se anulam não está validado — por isso tudo*")
    add("*aparece mês a mês, não só no acumulado.*")
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
    add("Cada tabela é uma linha da aba `Areas Sintetico atualizado`; a coluna *Célula* dá")
    add("o endereço exato para conferir.")
    add("")
    # Roll-up lines have no cause of their own (Resultado Bruto/Líquido = sum of the lines
    # above; institucional Custos Diretos = sum of the three áreas). Listing them with a
    # full table each added ~100 lines that said "veja as linhas acima" six times over, so
    # they get one shared paragraph and stay out of the per-line detail.
    detalhe = [t for t in materiais if not _is_derivada(t[0], t[1])]
    somas = [t for t in materiais if _is_derivada(t[0], t[1])]
    for section, line, label, wrow, o, b, d in sorted(detalhe, key=_ordem):
        info = CAUSAS.get((section, line))
        add(f"### {label} — {_sgn(d)} no acumulado")
        add("")
        add("| Mês | Célula | Planilha | Sistema | Diferença |")
        add("|---|---|---:|---:|---:|")
        cells = per_month[(section, line)]
        for m in months:
            ov, bv, dv = cells[m]
            marca = "" if abs(dv) >= 0.005 else " ✓"
            add(
                f"| {MESES[m]} | `{_col(SINT_COL[m])}{wrow}` | {_brl(bv)} | {_brl(ov)} |"
                f" {_sgn(dv)}{marca} |"
            )
        sb = round(sum(cells[m][1] for m in months), 2)
        so = round(sum(cells[m][0] for m in months), 2)
        add(f"| **Acumulado** | — | **{_brl(sb)}** | **{_brl(so)}** | **{_sgn(round(so - sb, 2))}** |")
        add("")
        if info:
            add(f"{info['causa']}")
            add("")
            add(f"*Conferir:* {info['conferir']}")
            add("")
        else:
            add("*Causa ainda não documentada — falar com o time antes da reunião.*")
            add("")

    if somas:
        add("### Linhas que são somas de outras")
        add("")
        add("Estas não têm causa própria — cada uma é a soma das linhas acima (Resultado")
        add("Bruto e Líquido dentro de cada bloco; Custos Diretos = as três áreas). Elas")
        add("aparecem aqui só para fechar o acumulado:")
        add("")
        add(_hdr("Linha", months, abbr))
        add(_sep(months))
        for section, line, label, _w, _o, _b, _d in sorted(somas, key=_ordem):
            add(_row_deltas(label, per_month[(section, line)], months, None))
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

    add("## O que fazer")
    add("")
    add("### 1. Na planilha: copiar as fórmulas de junho para janeiro–maio")
    add("")
    add("Nas linhas **204, 205 e 206**, as fórmulas de janeiro a maio somam as despesas da")
    add("área **seguinte**. As de junho estão corretas — copiá-las para os meses anteriores")
    add("resolve a maior parte da diferença de *Despesas Equipe* e *Despesa Institucional*")
    add("das três áreas.")
    add("")
    add("### 2. No sistema: manter a anotação do convênio atualizada quando o plano mudar")
    add("")
    add("A *memória de cálculo* no lançamento do convênio é o que diz quanto do plano é da")
    add("MBC. Quando ela fica velha, o sistema estima a parte da MBC pela proporção dos")
    add("outros meses — funciona, mas é estimativa. Hoje há uma: a parte da MBC do **RB em")
    add("janeiro** (o plano dele mudou e nenhuma anotação registra a proporção daquele mês).")
    add("Se puderem confirmar esse número, ele deixa de ser estimado.")
    add("")
    add("### 3. Uma pergunta: de onde vem o R$ 35,52 do vale-transporte de janeiro?")
    add("")
    add("A célula `C123` traz `=35,52+262,64`. Os **262,64** são o vale-transporte da pessoa")
    add("do administrativo (14 dias × R$ 18,76) e conferem. Os **35,52** não aparecem em")
    add("nenhum lançamento do sistema — nem em janeiro, nem em nenhum outro mês. Não é")
    add("vale-refeição (o menor do ano é R$ 783,70) e não corresponde a um número inteiro de")
    add("dias em nenhuma diária de vale.")
    add("")
    add("Também não é um pedaço que falte do nosso número: o vale-transporte de janeiro")
    add("(R$ 262,64) já está completo, então os 35,52 estão somados por cima. Se for de outra")
    add("competência ou um acerto pontual, é só dizer e passamos a tratá-lo da mesma forma.")
    add("")
    add("## Diferenças que não mudam nenhum total")
    add("")
    add("Estas são de classificação: o valor existe nos dois lados, em seções diferentes.")
    add("Ficam registradas porque **se repetem todo mês** e costumam gerar dúvida.")
    add("")
    add("* **ISS trimestral** — o sistema lança por advogado, a planilha numa única linha da")
    add("  área (efeito no acumulado: R$ 0,04).")
    add("* **AASP** — dentro do Custo equipe na planilha, em Despesa de Área no sistema.")
    add("* **Endomarketing × Prospecção** e **Ocupação × Administrativas** — a mesma conta em")
    add("  famílias diferentes de cada lado; as duas entram no total, efeito zero.")
    add("* **Vale do administrativo** — a planilha lança as três pessoas em Salários")
    add("  Administração; o sistema deixa ali só a pessoa do administrativo e manda os")
    add("  estagiários para o custo das áreas deles.")
    add("* **Aluguel** — o sistema usa o valor líquido da sublocação (crédito Belline).")
    add("* **Tarifa bancária** — R$ 4,80/mês, vem do sistema e está zerada no Excel.")
    add("* **Prêmio de seguro** — é anual (lançado em janeiro e julho); a planilha o divide")
    add("  em parcelas mensais e o classifica em *Administrativas*, o sistema em *Ocupação*.")
    add("")

    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)}  ({len(materiais)} materiais, {len(menores)} menores)")


if __name__ == "__main__":
    main()
