# backend/app/closing/available.py
from __future__ import annotations
from datetime import date

def is_closeable(ano_mes: str, *, today: date | None = None) -> bool:
    today = today or date.today()
    year, month = (int(x) for x in ano_mes.split("-"))
    # closeable iff the month ended strictly before the first day of the current month
    return (year, month) < (today.year, today.month)

def available_months(*, today: date | None = None, back: int = 24) -> list[str]:
    today = today or date.today()
    y, m = today.year, today.month
    out: list[str] = []
    for _ in range(back):
        m -= 1
        if m == 0:
            m = 12
            y -= 1
        out.append(f"{y:04d}-{m:02d}")
    return out
