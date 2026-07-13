# backend/tests/test_verification.py
"""Hard-rule tolerance: absorb the workbook's whole-real rounding, still catch bugs.

Client-confirmed 2026-07-13: the workbook rounds many cells to whole reais while our
DB derivation carries centavos, so an exact R$0,01 match is impossible. The tolerance
is R$1,00 — large enough for whole-real rounding + small DRE-chain compounding, far
below any real derivation bug.
"""
import pytest

from app.closing.verification import MATCH_TOLERANCE, matches_target, verified_value


def test_tolerance_is_one_real():
    assert MATCH_TOLERANCE == pytest.approx(1.00)


def test_may_recebimento_rounding_is_tolerated():
    # Workbook types 415928 (whole reais); sacred LegalDesk = 415927.84 (R$0,16 gap).
    assert matches_target(415927.84, 415928.0) is True
    assert verified_value(415927.84, "institucional", "recebimento",
                          {"institucional": {"recebimento": 415928.0}}) == 415927.84


def test_may_imposto_rounding_is_tolerated():
    # 15% of the precise recebimento (62389.18) vs the workbook echo (62389.20).
    assert matches_target(62389.18, 62389.20) is True


def test_real_bug_still_blanks():
    # A genuine derivation error is orders of magnitude beyond R$1 and must blank.
    assert matches_target(98140.47, 79436.24) is False
    assert verified_value(98140.47, "economico", "custo_equipe",
                          {"economico": {"custo_equipe": 79436.24}}) is None


def test_just_over_a_real_blanks():
    # The boundary: 1,50 off is beyond tolerance (a real bug is much larger, but we
    # keep the gate tight enough that a > R$1 discrepancy is never silently shown).
    assert matches_target(100.0, 101.50) is False


def test_within_a_real_is_kept():
    assert matches_target(100.0, 100.99) is True


def test_no_target_shows_value():
    assert matches_target(123.45, None) is True
    assert verified_value(123.45, "s", "k", None) == 123.45


def test_none_value_never_satisfies_a_target():
    assert matches_target(None, 100.0) is False
