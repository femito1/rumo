"""Thin client for the Juritis LegalDesk OData v3 API.

This is the *only* data source for v0. The client deliberately keeps to the
small set of verified behaviours documented in docs/AUTOMATION_BUILD_GUIDE.md:

- HTTP Basic auth, JSON responses, rows under the ``value`` key.
- OData **v3** syntax (no v4, no ``$expand``, no ``$select=*``).
- Always send a large ``$top`` and a ``$filter`` (some views return stale
  paginated data otherwise).
- Money fields arrive as strings; callers cast to float via ``to_float``.
"""
from __future__ import annotations

from typing import Any
from urllib.parse import quote

import requests
from requests.auth import HTTPBasicAuth

from .config import SETTINGS, Settings


def to_float(value: Any) -> float:
    """Cast an API money string (e.g. ``"316807.42"``) to float, safely."""
    if value is None or value == "":
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


class LegalDeskClient:
    def __init__(self, settings: Settings = SETTINGS) -> None:
        self.settings = settings
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(settings.api_user, settings.api_password)
        self.session.headers["Accept"] = "application/json"

    def get(self, entity: str, filter_: str | None = None, top: int | None = None) -> list[dict]:
        top = top or self.settings.default_top
        url = f"{self.settings.api_base}/{entity}?$top={top}"
        if filter_:
            url += "&$filter=" + quote(filter_, safe="=' ()")
        resp = self.session.get(url, timeout=self.settings.request_timeout)
        resp.raise_for_status()
        return resp.json().get("value", [])

    # ----- Verified primitives (see guide §3) ---------------------------------

    def recebimento_rows(self, ano_mes: str) -> list[dict]:
        return self.get(
            "PosicaoFinanceiraResultadoRecebimentoViews",
            f"AnoMes eq '{ano_mes}'",
        )

    def faturamento_rows(self, ano_mes: str) -> list[dict]:
        return self.get(
            "PosicaoFinanceiraResultadoFaturamentoViews",
            f"AnoMes eq '{ano_mes}'",
        )

    def rateio_profissional_rows(self, date_start: str, date_end: str) -> list[dict]:
        f = (
            f"FaturaDataEmissao ge datetimeoffset'{date_start}T00:00:00Z' "
            f"and FaturaDataEmissao lt datetimeoffset'{date_end}T00:00:00Z'"
        )
        return self.get("RateioFaturaProfissionalViews", f)

    def fatura_rows(self, date_start: str, date_end: str) -> list[dict]:
        f = (
            f"DataEmissao ge datetimeoffset'{date_start}T00:00:00Z' "
            f"and DataEmissao lt datetimeoffset'{date_end}T00:00:00Z'"
        )
        return self.get("FaturaViews", f)

    def rateio_caso_rows(self, date_start: str, date_end: str) -> list[dict]:
        f = (
            f"FaturaDataEmissao ge datetimeoffset'{date_start}T00:00:00Z' "
            f"and FaturaDataEmissao lt datetimeoffset'{date_end}T00:00:00Z'"
        )
        return self.get("RateioFaturaCasoViews", f)

    def tributo_percentuais(self, ano_mes: str) -> dict[str, float]:
        """Monthly tax rates (IRPJ, CSLL, PIS, COFINS) as fractions.

        Source: ``TributoViews`` (verified present for 2026). Lets us *estimate*
        tax lines as ``base × rate`` the way the workbook's DRE does, without the
        institutional payroll/expense data this API doesn't expose.
        """
        rows = self.get("TributoViews", f"AnoMes eq '{ano_mes}'", top=50)
        if not rows:
            return {}
        r = rows[0]
        return {
            "irpj": to_float(r.get("PercentualIRPJ")) / 100.0,
            "csll": to_float(r.get("PercentualCSLL")) / 100.0,
            "pis": to_float(r.get("PercentualPIS")) / 100.0,
            "cofins": to_float(r.get("PercentualCOFINS")) / 100.0,
        }
