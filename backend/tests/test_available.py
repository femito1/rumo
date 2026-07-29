# backend/tests/test_available.py
from datetime import date
from app.closing.available import available_months, is_closeable

def test_past_month_is_closeable():
    assert is_closeable("2026-05", today=date(2026, 6, 21)) is True

def test_current_month_not_closeable():
    assert is_closeable("2026-06", today=date(2026, 6, 21)) is False

def test_future_month_not_closeable():
    assert is_closeable("2026-12", today=date(2026, 6, 21)) is False

def test_available_months_descending_and_bounded():
    months = available_months(today=date(2026, 6, 21), back=3)
    assert months == ["2026-05", "2026-04", "2026-03"]


# ── Open-month (partial) view ────────────────────────────────────────────────
# Client asked for the in-progress month (2026-07-28, 6:45 — Adriana: *"Por que ele
# não é online? ... Não é um fechamento mensal, mas para a gente aproveitar muito
# mais as informações"*). The extract already runs daily at 06:00, so this is a
# display rule. ``is_closeable`` keeps its exact old meaning — a partial month must
# never be presentable AS a closing — and a separate predicate gates viewing.


def test_current_month_is_viewable_even_though_not_closeable():
    from app.closing.available import is_viewable

    assert is_viewable("2026-06", today=date(2026, 6, 21)) is True
    # ...while still NOT closeable. The two concepts must stay distinct.
    assert is_closeable("2026-06", today=date(2026, 6, 21)) is False


def test_future_month_is_never_viewable():
    from app.closing.available import is_viewable

    assert is_viewable("2026-07", today=date(2026, 6, 21)) is False
    assert is_viewable("2027-01", today=date(2026, 6, 21)) is False


def test_is_partial_is_true_only_for_the_open_current_month():
    from app.closing.available import is_partial

    assert is_partial("2026-06", today=date(2026, 6, 21)) is True
    assert is_partial("2026-05", today=date(2026, 6, 21)) is False


def test_available_months_includes_the_open_month_first():
    # The picker must offer the in-progress month, newest first, and it must be
    # explicitly flagged so the UI can label it rather than pass it off as closed.
    from app.closing.available import available_months_detail

    detail = available_months_detail(today=date(2026, 6, 21), back=3)
    assert [d["ano_mes"] for d in detail] == ["2026-06", "2026-05", "2026-04"]
    assert detail[0]["is_partial"] is True
    assert all(d["is_partial"] is False for d in detail[1:])


def test_available_months_stays_closed_only_for_back_compat():
    # The old list-of-strings helper must NOT start emitting the open month: the
    # comparison harness and the closing gate both rely on it meaning "closed".
    assert available_months(today=date(2026, 6, 21), back=2) == ["2026-05", "2026-04"]
