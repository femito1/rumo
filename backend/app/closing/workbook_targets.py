# backend/app/closing/workbook_targets.py
"""Load the workbook Realizado targets that gate the hard rule.

The hard rule (``verification.py``) blanks any Realizado cell that diverges from
the workbook by more than R$0,01. The targets come from the AUTHORITATIVE
``Fechamento MBC 05.2026.xlsx`` (05.2026 wins on any conflict), pre-extracted into
``workbook_targets_2026.json`` by ``scripts/build_workbook_targets.py`` so nothing
reads the .xlsx at runtime.

``targets_for(period)`` returns ``{section_key: {line_key: value}}`` for a known
competence month, or ``None`` when we have no workbook for that month (in which
case the hard rule is a no-op and derived values are shown as usual).
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.closing.verification import Targets

_DATA = Path(__file__).with_name("workbook_targets_2026.json")


@lru_cache(maxsize=1)
def _all_targets() -> dict[str, Targets]:
    raw = json.loads(_DATA.read_text(encoding="utf-8"))
    return {str(k): v for k, v in (raw.get("targets") or {}).items()}


def _ano_mes(period: Any) -> str:
    """Accept a ``"YYYY-MM"`` string or any object exposing ``ano_mes``."""
    if isinstance(period, str):
        return period
    return str(getattr(period, "ano_mes", period))


def targets_for(period: Any) -> Targets | None:
    """Return the workbook targets for a competence month, or ``None`` if unknown."""
    return _all_targets().get(_ano_mes(period))
