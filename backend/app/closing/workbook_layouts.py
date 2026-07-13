# backend/app/closing/workbook_layouts.py
"""Canonical vocabulary + rollups matching `Copy of Fechamento MBC 02.2026.xlsx`.

The workbook is the source of truth for labels and structure. SISJURI expense
accounts (`despesas_conta`, each with `id_conta`, `nome_conta`, `nome_conta_pai`,
`tipo_conta`) roll up into the workbook's named sections by account-family
prefix:

- ``020.*`` -> Despesas Indiretas (institutional overhead), grouped by
  ``nome_conta_pai`` into the workbook's institutional sections.
- ``030.*`` -> Custo equipe (direct team cost).
- ``040.*`` -> Investimentos (mapped into institutional sections too, e.g.
  Consultoria / Informática).
- Impostos family -> the Impostos block.

Only *structure* lives here; no IO, no math beyond summation helpers.
"""
from __future__ import annotations

import re
from typing import Any

# --- Institucional expense sections, in workbook display order ---------------
# The workbook's Institucional tab (block 3) lists these section subtotals.
INSTITUCIONAL_SECTIONS: tuple[str, ...] = (
    "Ocupação",
    "Telecomunicações",
    "Despesas Gerais",
    "Consultoria",
    "Salários Administração",
    "Administrativas",
    "Investimentos em Prospecção",
    "Endomarketing",
    "Gestão do Conhecimento",
    "Informática",
)

# Map a SISJURI ``nome_conta_pai`` onto a workbook Institucional section.
# Anything unmapped falls back to its own SISJURI parent name (still shown).
_PAI_TO_SECTION: dict[str, str] = {
    "Ocupação": "Ocupação",
    "Telecomunicações": "Telecomunicações",
    "Despesas Gerais": "Despesas Gerais",
    "Serviços de Terceiros": "Consultoria",
    "Consultoria": "Consultoria",
    "Investimentos": "Consultoria",
    "Salários Administração": "Salários Administração",
    "Administrativas": "Administrativas",
    "Investimento em Prospecção": "Investimentos em Prospecção",
    "Investimentos em Prospecção": "Investimentos em Prospecção",
    "Gestão do Conhecimento": "Gestão do Conhecimento",
    "Informática": "Informática",
    "Endomarketing": "Endomarketing",
}


# Account-code-level overrides for the workbook institutional families.
#
# Verified to the centavo against Fechamento MBC 02.2026 and 05.2026 by
# reconciling FINANCE.VW_RESULTADO_MENSAL_DET (see docs/HANDOFF_DRE_AUTOMATION.md,
# Appendix B). These are keyed on the STABLE numeric CONTA3 codes, never on the
# accented ``nome_conta_pai`` text, so they survive label churn.
#
# The workbook re-buckets a handful of leaves away from their SISJURI parent:
#   - "Serviços de Terceiros" (020.040.*) is split across three families.
#   - Seguros (020.060.0040) moves into Ocupação as "Seguro Locação".
#   - Financeiras (020.070.*) fold into Administrativas.
#   - Manutenção e Conservação (020.010.0050) moves into Despesas Gerais.
#   - Marketing/Assessoria (040.010.*) and Investimentos:Consultoria (040.030.*)
#     both land in Consultoria; Biblioteca (040.050.*) is Gestão do Conhecimento.
_CONTA3_TO_SECTION: dict[str, str] = {
    "020.010.0050": "Despesas Gerais",  # Manut. e Conservação -> "Manut. do Escritório"
    "020.030.0150": "Endomarketing",  # Relacionamento Institucional -> "Presentes"
    "020.040.0010": "Informática",  # Serviços de Informática -> "Suporte de Informática"
    "020.040.0030": "Despesas Gerais",  # Terceirização Limpeza -> "Limpeza e Copeira"
    "020.040.0050": "Consultoria",  # Contabilidade
    "020.040.0060": "Informática",  # Servidor Externo -> "Data Center"
    "020.060.0040": "Ocupação",  # Seguros -> "Seguro Locação"
    "020.080.0030": "Despesas Gerais",  # Estacionamento (clientes)
    "020.080.0050": "Salários Administração",  # Vale Refeição - ADM
    "020.080.0060": "Salários Administração",  # Vale Transporte
    "020.090.0040": "Endomarketing",  # Eventos e Happy Hour -> "Eventos Internos" (05 book)
}

# Account-family prefixes that fold into a fixed institutional family regardless
# of their SISJURI parent name.
_PREFIX_TO_SECTION: tuple[tuple[str, str], ...] = (
    ("020.070.", "Administrativas"),  # Financeiras -> Taxas / Despesas Financeiras
    ("040.010.", "Consultoria"),  # Marketing / Assessoria de Imprensa
    ("040.030.", "Consultoria"),  # Investimentos:Consultoria Adm. e Financeira
    ("040.040.", "Informática"),  # Licenças / Micros / Impressoras
    ("040.050.", "Gestão do Conhecimento"),  # Biblioteca
)


def section_for(nome_conta_pai: str | None, id_conta: str | None = None) -> str:
    """Resolve the workbook institutional family for an expense leaf.

    Prefers the verified account-code rules (``id_conta`` = SISJURI CONTA3) and
    only falls back to the parent-name map when no code rule applies.
    """
    if id_conta:
        if id_conta in _CONTA3_TO_SECTION:
            return _CONTA3_TO_SECTION[id_conta]
        for prefix, section in _PREFIX_TO_SECTION:
            if id_conta.startswith(prefix):
                return section
    if not nome_conta_pai:
        return "Despesas Gerais"
    return _PAI_TO_SECTION.get(nome_conta_pai, nome_conta_pai)


def is_indirect(id_conta: str) -> bool:
    """020.* and 040.* families are institutional (indirect) overhead."""
    return id_conta.startswith("020.") or id_conta.startswith("040.")


# A few 030.* accounts are NOT team cost in the workbook: it lifts them into an
# institutional family. Verified vs 05.2026 (HANDOFF Appendix B): "Cursos /
# Treinamento Jurídico" (030.010.0180) feeds "Gestão do Conhecimento" (row 158),
# matching Mar 1.094,49 / Mai 1.600 to the centavo.
_030_TO_SECTION: dict[str, str] = {
    "030.010.0180": "Gestão do Conhecimento",  # Cursos / Treinamento Jurídico
}


def is_direct_team(id_conta: str) -> bool:
    """030.* is Custo equipe (direct team cost), except the institutional carve-outs."""
    return id_conta.startswith("030.") and id_conta not in _030_TO_SECTION


def institutional_030_section(id_conta: str) -> str | None:
    """Return the institutional family for a 030.* carve-out, else None."""
    return _030_TO_SECTION.get(id_conta)


# Comissão accounts (Participação Externa/Interna). These are derived per-area
# separately (``comissao_deriv``); they are NOT institutional expenses and must not
# be classified as team cost, imposto or a despesas-section leaf.
_COMISSAO_ACCOUNTS: frozenset[str] = frozenset(
    {"020.110.0010", "030.010.0120", "030.010.0080"}
)


def is_comissao_account(id_conta: str) -> bool:
    """True for a Comissão (Participação) account, handled by ``comissao_deriv``."""
    return id_conta in _COMISSAO_ACCOUNTS


def is_imposto(row: dict[str, Any]) -> bool:
    # Comissão accounts contain "iss" inside "comissões"; exclude them explicitly
    # so they are never miscounted as a tax leaf (they are derived separately).
    if is_comissao_account(str(row.get("id_conta", ""))):
        return False
    pai = str(row.get("nome_conta_pai", "")).lower()
    nome = str(row.get("nome_conta", "")).lower()
    # Match "iss"/"inss" only as whole words (or hyphenated), never as a substring
    # of "comissões". "imposto" anywhere still counts.
    if "imposto" in pai or "imposto" in nome:
        return True
    tokens = re.split(r"[^a-zà-ú]+", nome)
    return any(t in ("iss", "inss") for t in tokens)


# --- The three cost-center areas, workbook labels + snapshot-name matching ----
AREAS: tuple[str, ...] = ("Contencioso", "Econômico", "Arbitragem")

#: Workbook area-tab line labels (Orçado | Realizado | %).
AREA_LINES: tuple[str, ...] = (
    "Recebimento",
    "Custo equipe",
    "Comissão",
    "Despesas Equipe",
    "Despesa Institucional",
    "Resultado Bruto",
)


def match_area(snapshot_area_name: str, area: str) -> bool:
    """Snapshot area names differ from workbook labels
    ('Equipe Contencioso', 'Equipe Direito Econômico', 'Arbitragem').

    Client-confirmed (2026-07-10): **Ambiental soma com Arbitragem** — they are
    the same workbook area ('Arbitragem e Compliance'). The LegalDesk Demonstrativo
    lists 'Equipe Ambiental' separately, but it folds into Arbitragem here.
    'Não Alocados' is NOT an area and must never match one (it is its own line).
    """
    low = (snapshot_area_name or "").lower()
    if "alocad" in low:  # "Não Alocados" — never a workbook area
        return False
    if area == "Econômico":
        return "econ" in low
    if area == "Contencioso":
        return "conten" in low
    if area == "Arbitragem":
        return "arbitr" in low or "ambient" in low or "compliance" in low
    return False


# --- Institucional DRE block lines (block 1), workbook labels ----------------
# Orçado | Realizado | % (of Recebimento). Base is RECEBIMENTO, not faturamento.
INSTITUCIONAL_DRE_LINES: tuple[tuple[str, bool], ...] = (
    ("Recebimento", False),
    ("Custo equipe", False),
    ("Despesas", False),
    ("Resultado Bruto", True),
    ("Imposto", False),
    ("Amortização", False),
    ("Resultado Liquido", True),
)

#: Fixed monthly institutional amortization installment (workbook 'Amortização').
AMORTIZACAO_MENSAL = 8117.0

#: Reserva de bônus = 10% do Resultado Líquido (client-confirmed 2026-07-10).
BONUS_RESERVE_RATE = 0.10

#: Imposto do DRE = 15% do Recebimento (client-confirmed 2026-07-10). This is a
#: rate on gross receipts, NOT the sum of the ledger tax accounts (050.010.* /
#: the 168-Impostos razão block). Verified to the centavo vs the official
#: dashboard: Feb 0.15*319233.58 = 47885.04; May 0.15*415928 = 62389.20.
IMPOSTO_RATE = 0.15


def imposto_sobre_recebimento(recebimento: float) -> float:
    """DRE tax line = 15% of Recebimento (gross receipts)."""
    return round(recebimento * IMPOSTO_RATE, 2)
