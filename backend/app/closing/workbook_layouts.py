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
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # import-cycle-free: tenant_config does not import this module
    from app.tenancy.tenant_config import TenantConfig
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
# reconciling FINANCE.VW_RESULTADO_MENSAL_DET (Appendix B of the pruned
# HANDOFF_DRE_AUTOMATION.md: `git show 118a6c4^:docs/archive/HANDOFF_DRE_AUTOMATION.md`). These are keyed on the STABLE numeric CONTA3 codes, never on the
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
    # Same story: the workbook books Seguro de Resp. Civil in Administrativas (r133,
    # inside r124) while we keep the whole 020.060.0040 in Ocupação as "Seguro
    # Locação". r198 adds r85 AND r124, so the pair nets to zero in the total — the
    # non-zero Jan/Fev residue on this pair comes from the ÁREA Assinaturas/
    # Associações rows the book keeps inside r124, not from the seguro itself.
    "020.060.0040": "Ocupação",  # Seguros -> "Seguro Locação"
    "020.080.0030": "Despesas Gerais",  # Estacionamento (clientes)
    "020.080.0050": "Salários Administração",  # Vale Refeição - ADM
    "020.080.0060": "Salários Administração",  # Vale Transporte
    # 020.090.0040 "Eventos e Happy Hour" is a MIXED account (internal team
    # confraternização + client/área-facing food) and the WORKBOOK ITSELF files it
    # inconsistently: the same confraternização spend lands in r141 (inside the
    # Investimentos-em-Prospecção block) in Jan/Fev and in r166 (Endomarketing) in
    # Mar–Jun. We keep it in Endomarketing for ALL months. That is deliberate and
    # NOT a defect: r198 adds BOTH r137 and r164, so which of the two families holds
    # the line cannot change the institutional total, the rateio pool, or any number
    # the client reads. Verified 2026-07-30 — our Jan 1.171,71 equals her r141 to the
    # centavo; only the family label differs. (scripts/diff_jan_abr.py §3.5)
    "020.090.0040": "Endomarketing",  # Eventos e Happy Hour -> "Eventos Internos" (05 book)
    # 040.030.* ("Investimentos") is a MIXED bucket — mapped per account, NOT by
    # prefix. Only 0010 is consultancy; the other two are office spend the workbook
    # books in Despesas Gerais. Client-confirmed by Renata 2026-07-29:
    #   0020 Móveis e Utensílios -> "Material de Escritório" (June H105 = 468,40, of
    #        which 429,00 is a pressure washer): "sendo um bem de escritório é uma
    #        despesa institucional que seria rateada, não de uma área específica".
    #   0030 Reforma -> "Manutenção do Escritório" ("manutenção de escritório
    #        despesas gerais"). ⚠ OPEN NUANCE, to settle with Adriana: a REFORMA DE
    #        MELHORIA is arguably an investimento, not manutenção ("linhazinha bem
    #        tênue"). Either way it stays inside Despesa Institucional and is
    #        rateized, so only the family label would change — do not move it out of
    #        despesas without a client artifact.
    "040.030.0020": "Despesas Gerais",  # Móveis e Utensílios -> Material de Escritório
    "040.030.0030": "Despesas Gerais",  # Reforma -> Manutenção do Escritório
}

# Account-family prefixes that fold into a fixed institutional family regardless
# of their SISJURI parent name.
_PREFIX_TO_SECTION: tuple[tuple[str, str], ...] = (
    ("020.070.", "Administrativas"),  # Financeiras -> Taxas / Despesas Financeiras
    ("040.010.", "Consultoria"),  # Marketing / Assessoria de Imprensa
    # NOTE 040.030.* is deliberately NOT a blanket prefix: 0020/0030 are overridden
    # per account above, so only 0010 (Consultoria Adm. e Financeira) falls through
    # here. Adding new 040.030.* children? Decide their family explicitly.
    ("040.030.", "Consultoria"),  # Investimentos:Consultoria Adm. e Financeira
    ("040.040.", "Informática"),  # Licenças / Micros / Impressoras
    ("040.050.", "Gestão do Conhecimento"),  # Biblioteca
)


def section_for(
    nome_conta_pai: str | None,
    id_conta: str | None = None,
    tenant: "TenantConfig | None" = None,
) -> str:
    """Resolve the workbook institutional family for an expense leaf.

    Prefers the verified account-code rules (``id_conta`` = SISJURI CONTA3) and
    only falls back to the parent-name map when no code rule applies.

    ``tenant`` supplies per-client overrides, which are checked FIRST and layered over
    the built-in map — a second client shares most of the SISJURI tree and only needs to
    name its exceptions. Omitting it keeps MBC's behaviour exactly.
    """
    if id_conta:
        if tenant is not None and id_conta in tenant.account_overrides:
            return tenant.account_overrides[id_conta]
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


# Accounts the workbook books under Impostos (row 168), not their nominal family.
# FGTS-ADM (020.050.0060) is a payroll charge that the workbook lists in the
# Impostos block, NOT in Salários Administração — verified vs 05.2026 (row 172
# "FGTS 400,00"). INSS-ADM (020.050.0050) already matches by name.
_IMPOSTO_ACCOUNTS: frozenset[str] = frozenset({"020.050.0060"})


def is_imposto(row: dict[str, Any]) -> bool:
    id_conta = str(row.get("id_conta", ""))
    # Comissão accounts contain "iss" inside "comissões"; exclude them explicitly
    # so they are never miscounted as a tax leaf (they are derived separately).
    if is_comissao_account(id_conta):
        return False
    # ISS jurídico (030.010.0160) is named just "ISS" but is TEAM COST in the
    # workbook (per-area "ISS Trimestral"), not a tax. Without this guard the
    # "iss" token below would misclassify it as imposto and drop it entirely (the
    # DRE Imposto line is 15% of recebimento, not a sum of tax accounts). It is
    # trimestral, so May (the reconciliation month) was zero — hence long unseen.
    if is_direct_team(id_conta):
        return False
    if id_conta in _IMPOSTO_ACCOUNTS:
        return True
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

    Must resolve to **exactly one** área. SISJURI emits the same grupo with
    inconsistent spacing (live 2026 snapshots: 'EquipeContencioso',
    'Equipe DireitoEconômico', 'EquipeDireito Econômico', 'EquipeAmbiental'), and
    a missing space splices a false ``"econ"`` out of ``"equipE-CONtencioso"``
    — which made a Contencioso grupo match Econômico too. That is harmless where
    the caller takes the first hit, but ``dre.py`` has three loops that ADD over
    every matching área, so an ambiguous name lands in two áreas at once. Hence
    the Econômico test is anchored on 'econô'/'econo' (the word, not the splice).
    """
    low = (snapshot_area_name or "").lower()
    if "alocad" in low:  # "Não Alocados" — never a workbook area
        return False
    if area == "Econômico":
        # 'econô'/'econo' — NOT a bare 'econ', which 'equipecontencioso' contains.
        return "econô" in low or "econo" in low
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
