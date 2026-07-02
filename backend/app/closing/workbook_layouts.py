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


def section_for(nome_conta_pai: str | None) -> str:
    if not nome_conta_pai:
        return "Despesas Gerais"
    return _PAI_TO_SECTION.get(nome_conta_pai, nome_conta_pai)


def is_indirect(id_conta: str) -> bool:
    """020.* and 040.* families are institutional (indirect) overhead."""
    return id_conta.startswith("020.") or id_conta.startswith("040.")


def is_direct_team(id_conta: str) -> bool:
    """030.* is Custo equipe (direct team cost)."""
    return id_conta.startswith("030.")


def is_imposto(row: dict[str, Any]) -> bool:
    pai = str(row.get("nome_conta_pai", "")).lower()
    nome = str(row.get("nome_conta", "")).lower()
    return "imposto" in pai or "imposto" in nome or "iss" in nome or "inss" in nome


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
    ('Equipe Contencioso', 'Equipe Direito Econômico', 'Arbitragem')."""
    low = (snapshot_area_name or "").lower()
    if area == "Econômico":
        return "econ" in low
    if area == "Contencioso":
        return "conten" in low
    if area == "Arbitragem":
        return "arbitr" in low
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

#: Reserva de bônus = 10% da margem líquida (finance-confirmed, all months).
BONUS_RESERVE_RATE = 0.10
