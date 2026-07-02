# backend/app/sources/sisjuri_db.py
"""Source backed by the SISJURI Oracle DB, via the on-server extraction agent.

The agent (``ops/sisjuri-agent``) runs read-only SQL on ``MBC-LDESK01`` and emits
a single JSON snapshot per competence month (see ``docs/SISJURI_QUERIES.md``).
This Source consumes that snapshot and adapts it into ``SectionKey``s the
``ClosingProvider`` understands.

Two closing rules confirmed with MBC finance are encoded here:

- **Pro-labore is reported GROSS** (``CPGNVALORBASE``), not the net resumo value.
- **Reserva de bonus = 10% da margem liquida**, a fixed formula (not a DB line).

No live DB connection lives in the backend: egress is the agent's job (it POSTs
the snapshot to ``/api/ingest``). This keeps the private-VCN Oracle credentials
off the VPS.
"""
from __future__ import annotations

from typing import Any

from app.closing.dre import BONUS_RESERVE_RATE, bonus_reserve
from app.closing.period import Period
from app.sources.base import DayRange, SectionData, SectionKey

__all__ = ["SisjuriDbSource", "BONUS_RESERVE_RATE"]


def _round(x: Any) -> float:
    return round(float(x or 0.0), 2)


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

        ``emit_meta=False`` puts the source in *augment* mode: it does not emit
        ``META`` so it can be composed **after** ``LegalDeskSource`` without
        clobbering that source's KPIs.
        """
        return cls(snapshot, emit_meta=emit_meta)

    def supports(self) -> set[SectionKey]:
        keys = {SectionKey.INSTITUCIONAL_ANO, SectionKey.RATEIO_MENSAL}
        if self._emit_meta:
            keys.add(SectionKey.META)
        return keys

    def bonus_reserve(self, net_margin: float) -> float:
        """Reserva de bonus = fixed rate x margem liquida (finance-confirmed)."""
        return bonus_reserve(net_margin)

    # --- expense grouping ----------------------------------------------------
    def _grouped_despesas(self, despesas: list[dict]) -> list[dict[str, Any]]:
        """Group expense accounts by their parent section for a tree table.

        Emits a rich-tab row list: one section subtotal row followed by its
        indented sub-account rows, in stable order.
        """
        by_section: dict[str, list[dict]] = {}
        order: list[str] = []
        for row in despesas:
            pai = row.get("nome_conta_pai") or "Outros"
            if pai not in by_section:
                by_section[pai] = []
                order.append(pai)
            by_section[pai].append(row)

        rows: list[dict[str, Any]] = []
        for pai in order:
            contas = by_section[pai]
            subtotal = _round(sum(float(c.get("total", 0.0)) for c in contas))
            rows.append(
                {
                    "Conta": pai,
                    "Valor": {"value": subtotal, "source": "realizado"},
                    "Lancamentos": sum(int(c.get("n", 0)) for c in contas),
                    "indent": 0,
                    "is_total": True,
                }
            )
            for c in sorted(contas, key=lambda x: str(x.get("id_conta", ""))):
                rows.append(
                    {
                        "Conta": c.get("nome_conta", "?"),
                        "Valor": {"value": _round(c.get("total")), "source": "realizado"},
                        "Lancamentos": int(c.get("n", 0)),
                        "indent": 1,
                        "is_total": False,
                    }
                )
        return rows

    def _rateio_rows(self, rateio_prof: list[dict]) -> list[dict[str, Any]]:
        rows = []
        for r in sorted(
            rateio_prof, key=lambda x: float(x.get("faturado", 0.0)), reverse=True
        ):
            rows.append(
                {
                    "Profissional": r.get("id_profissional", "?"),
                    "Faturado": {"value": _round(r.get("faturado")), "source": "realizado"},
                    "Trabalhado": {"value": _round(r.get("trabalhado")), "source": "realizado"},
                }
            )
        return rows

    def _prolabore_rows(self, prolabore: list[dict]) -> list[dict[str, Any]]:
        rows = []
        for p in prolabore:
            rows.append(
                {
                    "Socio": p.get("sigla", "?"),
                    "Bruto": {"value": _round(p.get("bruto")), "source": "realizado"},
                    "Liquido": {"value": _round(p.get("liquido")), "source": "realizado"},
                }
            )
        return rows

    def _distribuicao_rows(self, distribuicao: list[dict]) -> list[dict[str, Any]]:
        rows = []
        for d in distribuicao or []:
            rows.append(
                {
                    "Socio": d.get("sigla", "?"),
                    "Centro de Custo": d.get("cost_center", ""),
                    "Valor": {"value": _round(d.get("valor")), "source": "realizado"},
                }
            )
        return rows

    def _custo_area_rows(self, custo_area: list[dict]) -> list[dict[str, Any]]:
        rows = []
        for a in custo_area:
            rows.append(
                {
                    "Area": a.get("area", "?"),
                    "Custo de Equipe": {"value": _round(a.get("total")), "source": "realizado"},
                    "Lancamentos": int(a.get("n", 0)),
                }
            )
        return rows

    def fetch(self, period: Period, day_range: DayRange) -> dict[SectionKey, SectionData]:
        snap = self._snapshot
        revenue = snap.get("revenue", {}) or {}
        faturas = snap.get("faturas", {}) or {}
        despesas = snap.get("despesas_conta", []) or []
        prolabore = snap.get("prolabore", []) or []
        distribuicao = snap.get("distribuicao_socio", []) or []
        rateio_prof = snap.get("rateio_prof", []) or []
        custo_area = snap.get("custo_area", []) or []

        kpis = {
            "receita_honorarios": _round(revenue.get("recebimento_bruto")),
            "faturamento_realizado": _round(revenue.get("faturamento_bruto")),
            "faturas_emitidas": int(faturas.get("faturas_emitidas", 0)),
            "recebimento_rows": int(revenue.get("recebimento_rows", 0)),
            "faturamento_rows": int(revenue.get("faturamento_rows", 0)),
        }

        totais_por_tipo: dict[str, float] = {}
        for row in despesas:
            tipo = row.get("tipo_conta", "?")
            totais_por_tipo[tipo] = _round(
                totais_por_tipo.get(tipo, 0.0) + float(row.get("total", 0.0))
            )

        prolabore_bruto_total = _round(sum(float(p.get("bruto", 0.0)) for p in prolabore))
        prolabore_liquido_total = _round(sum(float(p.get("liquido", 0.0)) for p in prolabore))

        out: dict[SectionKey, SectionData] = {}
        if self._emit_meta:
            out[SectionKey.META] = {
                "period": period.ano_mes,
                "period_label": period.label,
                "kpis": kpis,
                "source": self.name,
            }

        out[SectionKey.INSTITUCIONAL_ANO] = {
            "kind": "rich",
            "name": "Institucional - Despesas",
            "columns": ["Conta", "Valor", "Lancamentos"],
            "rows": self._grouped_despesas(despesas),
            "totais_por_tipo": totais_por_tipo,
            "prolabore": self._prolabore_rows(prolabore),
            "prolabore_bruto_total": prolabore_bruto_total,
            "prolabore_liquido_total": prolabore_liquido_total,
            "distribuicao_socio": self._distribuicao_rows(distribuicao),
            "custo_area": custo_area,
            "source": self.name,
        }

        out[SectionKey.RATEIO_MENSAL] = {
            "kind": "rich",
            "name": "Rateio Mensal",
            "columns": ["Area", "Custo de Equipe", "Lancamentos"],
            "rows": self._custo_area_rows(custo_area),
            "rateio_profissional": self._rateio_rows(rateio_prof),
            "source": self.name,
        }
        return out
