# backend/app/closing/notes.py
"""Known-discrepancy notes, in PT-BR, shown next to the number they explain.

The client kept re-discovering the same handful of differences in meetings and
asking why our figure and their spreadsheet disagree. This registry writes each
one down once, in Portuguese, and the payload carries it to the row it concerns so
the answer sits where the question gets asked — plus who to contact.

**This is NOT a validation layer.** Nothing here inspects a value, compares
anything, or decides a number is wrong. That was explicitly rejected ("derive
numbers correctly from the DB, don't police them after the fact"). A note is a
*committed human explanation* of something we already diagnosed and understood; if
we ever fix the underlying cause, we delete the note in the same commit.

Adding a note: append to ``NOTES``, name the months and the exact
``section``/``lines`` it belongs to, write PT-BR copy a finance reader would
understand without the codebase, and cite the evidence (workbook cell, probe,
commit) in ``origem`` so the next agent can re-verify instead of trusting us.
"""
from __future__ import annotations

from dataclasses import dataclass

#: Who the client should contact. Kept here (not in env) so the copy is reviewable
#: in diffs; it is a public support address, not a secret.
CONTATO = "Fernando Rimoli — fernando@bia4u.com.br"

#: ``severidade`` drives only the badge colour/tone in the UI:
#: ``info``    — expected and explained; no action needed (the common case).
#: ``atencao`` — the client may want to change something on their side.
_SEVERIDADES = ("info", "atencao")


@dataclass(frozen=True)
class Note:
    """One explained discrepancy.

    ``months``  — competence months it applies to (``"2026-03"``), or ``("*",)``
                  for a structural fact that recurs every month.
    ``section`` — canonical section key (``institucional``, ``contencioso``, …)
                  or ``None`` when the note is about the closing as a whole.
    ``lines``   — canonical line keys inside that section (``despesas``,
                  ``despesa_institucional``, …). Empty = the whole section.
    ``origem``  — where to re-verify this (workbook cell, probe, commit). NOT
                  shown to the client; it is for whoever maintains the note.
    """

    id: str
    titulo: str
    detalhe: str
    months: tuple[str, ...]
    section: str | None = None
    lines: tuple[str, ...] = ()
    severidade: str = "info"
    origem: str = ""
    #: Optional: what the client would have to do to make the numbers agree.
    acao: str | None = None

    def applies_to(self, ano_mes: str) -> bool:
        return "*" in self.months or ano_mes in self.months

    def applies_to_row(self, ano_mes: str, section: str, line: str) -> bool:
        """Row-level match, used to badge one cell.

        ``section=None`` means "about the closing as a whole" and therefore matches
        NO row: it belongs in the month's notes panel, not stuck onto an arbitrary
        line. Attaching it to every row would badge the entire sheet.
        """
        if self.section is None or not self.applies_to(ano_mes):
            return False
        if self.section != section:
            return False
        # No lines named ⇒ the note belongs to the whole section.
        return not self.lines or line in self.lines

    def to_payload(self) -> dict[str, object]:
        """Client-facing shape. ``origem`` is deliberately withheld — it cites
        internal commits/probes and would only confuse a finance reader."""
        return {
            "id": self.id,
            "titulo": self.titulo,
            "detalhe": self.detalhe,
            "severidade": self.severidade,
            "acao": self.acao,
            "contato": CONTATO,
        }


#: The registry. Ordered — the UI lists notes in this order, so keep the most
#: consequential first within a month.
NOTES: tuple[Note, ...] = (
    Note(
        id="vale-adm-meses-nao-ajustados",
        titulo="Vale ADM de março, abril e maio: lançamento não ajustado na planilha",
        detalhe=(
            "O vale-refeição e o vale-transporte são pagos num lançamento único numa "
            "conta transitória e depois abertos por pessoa dentro do sistema. Aqui nós "
            "usamos essa abertura e consideramos como despesa administrativa apenas a "
            "parte da pessoa do administrativo — os dois estagiários entram no custo "
            "de equipe das suas áreas. Em março, abril e maio a planilha lançou o valor "
            "cheio da transitória (as três pessoas) em Salários Administração; em "
            "janeiro, fevereiro e junho lançou só a parte do administrativo, e nesses "
            "meses os números batem exatamente. A diferença é conhecida e foi "
            "considerada irrelevante pelo financeiro, por isso não foi corrigida."
        ),
        months=("2026-03", "2026-04", "2026-05"),
        section="institucional",
        lines=("despesas",),
        severidade="info",
        acao=(
            "Nenhuma ação necessária. Se quiser alinhar a planilha, o critério é "
            "lançar em Salários Administração só o vale da pessoa do administrativo."
        ),
        origem=(
            "Renata, áudios 2026-07-30 ('não vale a pena corrigir, o valor é muito "
            "irrisório'); Base_Resultado Mensal_V2 r122+r123 vs probe_vale_desdobramento; "
            "derivação em dre.py (vale_prof × home_area)."
        ),
    ),
    Note(
        id="vale-adm-janeiro-ajuste-manual",
        titulo="Vale ADM de janeiro: diferença de R$ 35,52 digitada na planilha",
        detalhe=(
            "Em janeiro a planilha traz o vale-transporte como uma soma manual "
            "(35,52 + 262,64 = 298,16). Os 262,64 correspondem ao lançamento do "
            "sistema; os 35,52 não têm lançamento correspondente na competência, "
            "então não conseguimos reproduzi-los a partir do sistema. Por isso o "
            "nosso Vale ADM de janeiro fica R$ 35,52 abaixo do da planilha."
        ),
        months=("2026-01",),
        section="institucional",
        lines=("despesas",),
        severidade="info",
        acao=(
            "Se os 35,52 forem de outra competência ou de um acerto, é só nos dizer "
            "de onde vêm que passamos a tratá-los da mesma forma."
        ),
        origem=(
            "Base_Resultado Mensal_V2 C123 = '=35.52+262.64'; probe_vale_desdobramento "
            "bloco B (jan: JVO 829,80+168,00 / MLA 262,64+829,80 — nenhum lançamento de "
            "35,52). NB: a soma manual NÃO é 'VR+VT na mesma linha' — em março o "
            "equivalente (E123 = 543,22+674) soma DUAS contas a pagar distintas, uma "
            "delas cobrindo VT e VR juntos para uma pessoa ('Pagamento de benefícios VT "
            "e VR ... para o estagiária do concorrencial')."
        ),
    ),
    Note(
        id="despesas-area-formula-deslocada",
        titulo="Despesas por área de janeiro a maio: fórmula da planilha deslocada uma linha",
        detalhe=(
            "Nas linhas de Despesas Equipe por área da planilha (Base_Resultado, "
            "linhas 204, 205 e 206), as fórmulas de janeiro a maio somam a linha de "
            "baixo em cinco famílias de despesa: Eventos e Happy Hour, Material "
            "Gráfico, Patrocínio, Refeições e Viagens. Como o bloco está ordenado "
            "Arbitragem / Contencioso / Direito Econômico / Institucional, cada área "
            "acaba recebendo a despesa da área seguinte: o Contencioso soma a do "
            "Direito Econômico, o Direito Econômico soma a do Institucional, e a "
            "Arbitragem soma a do Contencioso. As cinco linhas da Arbitragem ficam de "
            "fora e as cinco do Institucional entram no lugar. As fórmulas de junho já "
            "estão corretas — é por isso que junho fecha exatamente com o nosso número. "
            "Isso também afeta o rateio da despesa institucional por área nesses meses."
        ),
        months=("2026-01", "2026-02", "2026-03", "2026-04", "2026-05"),
        section=None,  # affects the per-área tabs and the institutional pool alike
        severidade="atencao",
        acao=(
            "Vale conferir as fórmulas das linhas 204, 205 e 206 de janeiro a maio na "
            "planilha e copiá-las de junho, que já está correto."
        ),
        origem=(
            "scripts/audit_area_ytd_formulas.py; Base_Resultado r204/205/206 (Jan–Mai "
            "somam r140/144/148/152/156 em vez de r139/143/147/151/155); commit e249c45."
        ),
    ),
    Note(
        id="tarifa-bancaria-zerada-no-excel",
        titulo="Tarifas bancárias: nós puxamos do sistema, a planilha zera",
        detalhe=(
            "As tarifas bancárias aparecem no nosso número porque vêm direto do "
            "sistema, e no Excel do financeiro elas ficam zeradas. Isso produz uma "
            "diferença pequena e recorrente nas despesas administrativas (em junho, "
            "R$ 4,80) e, por consequência, cerca de 10% disso na reserva de bônus."
        ),
        months=("*",),
        section="institucional",
        lines=("despesas",),
        severidade="info",
        acao="Nenhuma. Diferença já conferida e aceita pelo financeiro.",
        origem=(
            "Adriana, reunião 2026-07-28 12:33 ('é a taxa bancária, a gente está zerado "
            "no Excel'); conta 020.070.0030."
        ),
    ),
)


def notes_for(ano_mes: str) -> list[Note]:
    """Every note that applies to this competence month, in registry order."""
    return [n for n in NOTES if n.applies_to(ano_mes)]


def notes_for_row(ano_mes: str, *, section: str, line: str) -> list[Note]:
    """Notes attached to one specific cell, so the UI can badge it in place."""
    return [n for n in NOTES if n.applies_to_row(ano_mes, section, line)]


def notes_payload(ano_mes: str) -> list[dict[str, object]]:
    """The month's notes as plain data for the closing payload."""
    return [n.to_payload() for n in notes_for(ano_mes)]
