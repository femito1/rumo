# backend/app/sources/assembler_source.py
"""Source that emits the assembled DRE views (Orcado x Realizado).

Composed LAST in the provider so it overlays the raw institutional/area tabs
with computed Resultado/Margem/Variacao. It reads the SISJURI snapshot and the
budget directly (not from prior sources) because it needs both together.
"""
from __future__ import annotations

from typing import Any

from app.closing.dre import assemble_dre_sections
from app.closing.period import Period
from app.sources.base import DayRange, SectionData, SectionKey
from app.tenancy.tenant_config import DEFAULT_TENANT, TenantConfig

_VALUE_TO_KEY = {k.value: k for k in SectionKey}


class AssemblerSource:
    name = "assembler"

    def __init__(
        self,
        *,
        snapshot: dict[str, Any] | None,
        budget: dict[str, dict[str, float]] | None,
        budget_annual: dict[str, dict[str, float]] | None = None,
        transfers: list[Any] | None = None,
        targets: dict[str, dict[str, float]] | None = None,
        ytd_recebimento: dict[int, float] | None = None,
        convenio_shares: dict[str, float] | None = None,
        tenant: "TenantConfig | None" = None,
    ) -> None:
        self._snapshot = snapshot
        self._budget = budget
        self._budget_annual = budget_annual
        self._transfers = transfers
        self._targets = targets
        self._ytd_recebimento = ytd_recebimento
        self._convenio_shares = convenio_shares
        #: Per-client accounting shape (áreas, account overrides). None == MBC defaults,
        #: which is what keeps an empty provider_config byte-identical.
        self._tenant = tenant or DEFAULT_TENANT

    def supports(self) -> set[SectionKey]:
        return {
            SectionKey.INSTITUCIONAL,
            SectionKey.CONTENCIOSO,
            SectionKey.ECONOMICO,
            SectionKey.ARBITRAGEM,
            SectionKey.AREAS_SINTETICO,
            SectionKey.AMORTIZACAO,
            SectionKey.BASE_RESULTADO,
            SectionKey.RATEIO_MENSAL,
            SectionKey.DRE_2026,
            SectionKey.INSTITUCIONAL_ANO,
            SectionKey.FLUXO_CONSOLIDADO,
            SectionKey.META_DASHBOARD,
            SectionKey.FATURAS_ANALITICO,
            SectionKey.NACIONAL,
            SectionKey.MOEDAS,
        }

    def fetch(self, period: Period, day_range: DayRange) -> dict[SectionKey, SectionData]:
        sections = assemble_dre_sections(
            snapshot=self._snapshot,
            budget=self._budget,
            budget_annual=self._budget_annual,
            period_label=period.label,
            transfers=self._transfers,
            period_month=period.month,
            targets=self._targets,
            ytd_recebimento=self._ytd_recebimento,
            convenio_shares=self._convenio_shares,
            tenant=self._tenant,
        )
        out: dict[SectionKey, SectionData] = {}
        for value, data in sections.items():
            key = _VALUE_TO_KEY.get(value)
            if key is not None:
                out[key] = data
        return out
