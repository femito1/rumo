# backend/app/sources/base.py
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Protocol
from app.closing.period import Period

class SectionKey(str, Enum):
    META = "meta"
    BASE_RESULTADO = "base_resultado"
    AREAS_SINTETICO = "areas_sintetico"
    RESUMO_RECEBIDAS = "resumo_recebidas"
    FATURAS_CENTRO_CUSTO = "faturas_centro_custo"
    DRE_2026 = "dre_2026"
    ORCAMENTO_2026 = "orcamento_2026"
    INSTITUCIONAL = "institucional"
    INSTITUCIONAL_ANO = "institucional_ano"
    CONTENCIOSO = "contencioso"
    ECONOMICO = "economico"
    ARBITRAGEM = "arbitragem"
    RATEIO_MENSAL = "rateio_mensal"
    FLUXO_CONSOLIDADO = "fluxo_consolidado"
    AMORTIZACAO = "amortizacao"

@dataclass(frozen=True)
class DayRange:
    start: str          # ISO date inclusive lower bound
    end: str            # ISO date exclusive upper bound
    is_full_month: bool

    @classmethod
    def full_month(cls, period: Period) -> "DayRange":
        return cls(start=period.date_start, end=period.date_end, is_full_month=True)

    @classmethod
    def within(cls, period: Period, *, from_day: int, to_day: int) -> "DayRange":
        start = f"{period.year:04d}-{period.month:02d}-{from_day:02d}"
        end_day = to_day + 1
        end = f"{period.year:04d}-{period.month:02d}-{end_day:02d}"
        return cls(start=start, end=end, is_full_month=False)

# SectionData is the raw per-section structure a Source emits (shape defined per section).
SectionData = dict

class Source(Protocol):
    name: str
    def supports(self) -> set[SectionKey]: ...
    def fetch(self, period: Period, day_range: DayRange) -> dict[SectionKey, SectionData]: ...
