# backend/app/sources/sisjuri_db.py
"""Source backed by the SISJURI Oracle DB, via the on-server extraction agent.

The agent (``ops/sisjuri-agent``) runs read-only SQL on ``MBC-LDESK01`` and emits
a single JSON snapshot per competence month (see ``docs/SISJURI_QUERIES.md``).
This Source consumes that snapshot and adapts it into ``SectionKey``s the
``ClosingProvider`` understands — mirroring ``LegalDeskSource.from_recorded_payload``.

Two closing rules confirmed with MBC finance are encoded here:

- **Pró-labore is reported GROSS** (``CPGNVALORBASE``), not the net resumo value.
- **Reserva de bônus = 10% da margem líquida**, a fixed formula (not a DB line).

No live DB connection lives in the backend: egress is the agent's job (it POSTs
the snapshot to ``/api/ingest``, or a snapshot is loaded directly). This keeps the
private-VCN Oracle credentials off the VPS.
"""
from __future__ import annotations

from typing import Any

from app.sources.base import DayRange, SectionData, SectionKey
from app.closing.period import Period

#: Fixed appropriation rate for the bonus reserve (finance-confirmed, all months).
BONUS_RESERVE_RATE = 0.10


class SisjuriDbSource:
    """Adapts an agent JSON snapshot into closing sections."""

    name = "sisjuri_db"

    def __init__(self, snapshot: dict[str, Any], *, emit_meta: bool = True) -> None:
        self._snapshot = snapshot
        self._emit_meta = emit_meta

    @classmethod
    def from_snapshot(
        cls, snapshot: dict[str, Any], *, emit_meta: bool = True
    ) -> "SisjuriDbSource":
        """Build from a raw agent snapshot.

        ``emit_meta=False`` puts the source in *augment* mode: it emits only
        ``INSTITUCIONAL`` so it can be composed **after** another source (e.g.
        ``LegalDeskSource``) without clobbering that source's ``META``/KPIs.
        """
        return cls(snapshot, emit_meta=emit_meta)

    def supports(self) -> set[SectionKey]:
        # Revenue KPIs ride on META; expense detail populates INSTITUCIONAL.
        keys = {SectionKey.INSTITUCIONAL}
        if self._emit_meta:
            keys.add(SectionKey.META)
        return keys

    def bonus_reserve(self, net_margin: float) -> float:
        """Reserva de bônus = fixed rate × margem líquida (finance-confirmed)."""
        return round(net_margin * BONUS_RESERVE_RATE, 2)

    def fetch(self, period: Period, day_range: DayRange) -> dict[SectionKey, SectionData]:
        snap = self._snapshot
        revenue = snap.get("revenue", {})
        faturas = snap.get("faturas", {})
        despesas = snap.get("despesas_conta", []) or []
        prolabore = snap.get("prolabore", []) or []

        kpis = {
            "receita_honorarios": revenue.get("recebimento_bruto", 0.0),
            "faturamento_realizado": revenue.get("faturamento_bruto", 0.0),
            "faturas_emitidas": faturas.get("faturas_emitidas", 0),
            "recebimento_rows": revenue.get("recebimento_rows", 0),
            "faturamento_rows": revenue.get("faturamento_rows", 0),
        }

        totais_por_tipo: dict[str, float] = {}
        for row in despesas:
            tipo = row.get("tipo_conta", "?")
            totais_por_tipo[tipo] = round(
                totais_por_tipo.get(tipo, 0.0) + float(row.get("total", 0.0)), 2
            )

        prolabore_bruto_total = round(
            sum(float(p.get("bruto", 0.0)) for p in prolabore), 2
        )
        prolabore_liquido_total = round(
            sum(float(p.get("liquido", 0.0)) for p in prolabore), 2
        )

        out: dict[SectionKey, SectionData] = {}
        if self._emit_meta:
            out[SectionKey.META] = {
                "period": period.ano_mes,
                "period_label": period.label,
                "kpis": kpis,
                "source": self.name,
            }
        out[SectionKey.INSTITUCIONAL] = {
            "contas": despesas,
            "totais_por_tipo": totais_por_tipo,
            "custo_area": snap.get("custo_area", []) or [],
            "prolabore": prolabore,
            "prolabore_bruto_total": prolabore_bruto_total,
            "prolabore_liquido_total": prolabore_liquido_total,
        }
        return out
