"""Thin client for the Juritis LegalDesk OData v3 API.

This is the *only* data source for v0. The client deliberately keeps to the
small set of verified behaviours documented in docs/LEGALDESK.md:

- HTTP Basic auth, JSON responses, rows under the ``value`` key.
- OData **v3** syntax (no v4, no ``$expand``, no ``$select=*``).
- Always send a large ``$top`` and a ``$filter`` (some views return stale
  paginated data otherwise).
- Money fields arrive as strings; callers cast to float via ``to_float``.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import requests
from requests.auth import HTTPBasicAuth


#: Fallback when a client's ``provider_config`` says nothing. MBC's row carries an
#: empty config, so this is still the live path for it.
_DEFAULT_BASE = "https://legaldesk.mbclaw.com.br/API/v1/ODataGERALADV"


@dataclass(frozen=True)
class _LegalDeskSettings:
    api_base: str = _DEFAULT_BASE
    api_user: str = "integracao"
    api_password: str = ""
    request_timeout: int = 120
    default_top: int = 5000

    @classmethod
    def from_env(cls) -> "_LegalDeskSettings":
        """Read the environment NOW.

        ⚠ These used to be dataclass field defaults (``api_base: str =
        os.environ.get(...)``), which Python evaluates once when the class body runs —
        i.e. at import. Combined with the module-level singleton below, that pinned a
        whole process to one LegalDesk tenant and made ``monkeypatch.setenv`` in tests
        silently ineffective. Same call-time shape as ``Settings.from_env``.
        """
        return cls(
            api_base=os.environ.get("LEGALDESK_BASE", _DEFAULT_BASE).rstrip("/"),
            api_user=os.environ.get("LEGALDESK_USER", "integracao"),
            api_password=os.environ.get("LEGALDESK_PASSWORD", ""),
            request_timeout=int(os.environ.get("LEGALDESK_TIMEOUT", "120")),
            default_top=int(os.environ.get("LEGALDESK_TOP", "5000")),
        )

    @classmethod
    def from_provider_config(cls, provider_config: dict | None) -> "_LegalDeskSettings":
        """Per-client credentials from ``clients.provider_config['legaldesk']``.

        Shape (every key optional)::

            {"legaldesk": {"base": ..., "user": ..., "password": ...,
                           "timeout": 120, "top": 5000}}

        Each key falls back to the environment INDIVIDUALLY, so two tenants sharing a
        host can override only user/password without blanking the base URL, and MBC's
        empty config behaves exactly as before.

        ⚠ These are upstream credentials: they must never be serialized into an API
        response (see ``_client_public``) or reach the browser.
        """
        env = cls.from_env()
        cfg = (provider_config or {}).get("legaldesk") or {}
        base = str(cfg.get("base") or env.api_base).rstrip("/")
        return cls(
            api_base=base,
            api_user=str(cfg.get("user") or env.api_user),
            api_password=str(cfg.get("password") or env.api_password),
            request_timeout=int(cfg.get("timeout") or env.request_timeout),
            default_top=int(cfg.get("top") or env.default_top),
        )


def _default_settings() -> "_LegalDeskSettings":
    return _LegalDeskSettings.from_env()


#: Back-compat default for callers that construct a client with no settings.
SETTINGS = _LegalDeskSettings.from_env()


def to_float(value: Any) -> float:
    """Cast an API money string (e.g. ``"316807.42"``) to float, safely."""
    if value is None or value == "":
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


class LegalDeskClient:
    def __init__(self, settings: _LegalDeskSettings | None = None) -> None:
        # Resolved here, not as a default argument: a default would again freeze the
        # environment at import time.
        settings = settings if settings is not None else _LegalDeskSettings.from_env()
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
