"""Helpers for working with a competence month (``AnoMes``)."""
from __future__ import annotations

import calendar
from dataclasses import dataclass

_MONTH_NAMES_PT = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]


@dataclass(frozen=True)
class Period:
    """A single competence month, e.g. 2026-05 (May 2026)."""

    year: int
    month: int

    @classmethod
    def parse(cls, ano_mes: str) -> "Period":
        year, month = ano_mes.split("-")
        return cls(int(year), int(month))

    @property
    def ano_mes(self) -> str:
        return f"{self.year:04d}-{self.month:02d}"

    @property
    def month_name_pt(self) -> str:
        return _MONTH_NAMES_PT[self.month - 1]

    @property
    def label(self) -> str:
        return f"{self.month_name_pt} {self.year}"

    @property
    def date_start(self) -> str:
        """First day of the month, ISO date (inclusive lower bound)."""
        return f"{self.year:04d}-{self.month:02d}-01"

    @property
    def date_end(self) -> str:
        """First day of the *next* month, ISO date (exclusive upper bound)."""
        if self.month == 12:
            return f"{self.year + 1:04d}-01-01"
        return f"{self.year:04d}-{self.month + 1:02d}-01"

    @property
    def days_in_month(self) -> int:
        """Number of days in this competence month (28/29/30/31)."""
        return calendar.monthrange(self.year, self.month)[1]

    @property
    def column_letter(self) -> str:
        """Spreadsheet column for this month (C=Jan .. N=Dec)."""
        return chr(ord("C") + self.month - 1)
