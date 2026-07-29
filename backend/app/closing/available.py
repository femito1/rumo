# backend/app/closing/available.py
"""Which competence months the product will serve, and in what mode.

Two DISTINCT questions, deliberately kept apart:

* :func:`is_closeable` — "is this month finished?" A month is closeable only once
  it has fully elapsed. This is what a *fechamento* (monthly closing) requires,
  and it is what the YTD accumulator and the workbook-comparison harness mean.
  **Its meaning has never changed.**
* :func:`is_viewable` — "may we render this month at all?" Since the 2026-07-28
  client meeting this also admits the **in-progress** month, shown as an explicit
  partial (Adriana, 6:45: *"Por que ele não é online? ... Não é um fechamento
  mensal, mas para a gente aproveitar muito mais as informações"*). The SISJURI
  extract already runs daily at 06:00, so this is a display rule, not new data.

A partial month must NEVER be presented as a closing, so nothing here widens
``is_closeable``; callers that mean "closed" keep calling it and keep the old
behaviour. :func:`is_partial` is the flag the API and UI use to label the view.
"""
from __future__ import annotations

from datetime import date
from typing import TypedDict


def is_closeable(ano_mes: str, *, today: date | None = None) -> bool:
    """True iff the month has fully elapsed (a real monthly closing).

    Unchanged semantics — the open month is deliberately excluded. Use
    :func:`is_viewable` to decide whether a month may be *displayed*.
    """
    today = today or date.today()
    year, month = (int(x) for x in ano_mes.split("-"))
    # closeable iff the month ended strictly before the first day of the current month
    return (year, month) < (today.year, today.month)


def is_viewable(ano_mes: str, *, today: date | None = None) -> bool:
    """True iff the month may be rendered: any closed month, plus the CURRENT
    (in-progress) month, which renders as an explicit partial. Future months are
    never viewable — there is nothing to show."""
    today = today or date.today()
    year, month = (int(x) for x in ano_mes.split("-"))
    return (year, month) <= (today.year, today.month)


def is_partial(ano_mes: str, *, today: date | None = None) -> bool:
    """True iff this month is viewable but NOT closed — i.e. the open current
    month, whose figures are a month-to-date snapshot, not a closing."""
    return is_viewable(ano_mes, today=today) and not is_closeable(ano_mes, today=today)


def available_months(*, today: date | None = None, back: int = 24) -> list[str]:
    """CLOSED months, newest first.

    Deliberately excludes the open month: the closing gate, the YTD accumulator
    and the workbook-comparison harness all read this as "months that are done".
    Use :func:`available_months_detail` for the picker, which also offers the open
    month with an explicit flag.
    """
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


class MonthOption(TypedDict):
    ano_mes: str
    is_partial: bool


def available_months_detail(
    *, today: date | None = None, back: int = 24
) -> list[MonthOption]:
    """Selectable months for the UI, newest first, each flagged closed/partial.

    The open current month leads the list so "acompanhar o mês corrente" is one
    click, and carries ``is_partial: True`` so the UI labels it as a month in
    progress instead of passing it off as a closing.

    ``back`` bounds the WHOLE list (the open month included), so the number of
    selectable months does not silently grow by one.
    """
    today = today or date.today()
    open_month = f"{today.year:04d}-{today.month:02d}"
    out: list[MonthOption] = [{"ano_mes": open_month, "is_partial": True}]
    for m in available_months(today=today, back=max(back - 1, 0)):
        out.append({"ano_mes": m, "is_partial": False})
    return out
