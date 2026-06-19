"""Central configuration for the MBC closing automation.

Credentials are read from the environment so they never get hard-coded into a
committed file or shipped to the browser. For local/dev convenience we fall
back to the integration credentials documented in the build guide, but in a
production deployment these MUST come from a secret manager / env vars only.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


API_BASE_DEFAULT = "https://legaldesk.mbclaw.com.br/API/v1/ODataGERALADV"


@dataclass(frozen=True)
class Settings:
    api_base: str
    api_user: str
    api_password: str
    request_timeout: int
    default_top: int

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            api_base=os.environ.get("MBC_API_BASE", API_BASE_DEFAULT).rstrip("/"),
            api_user=os.environ.get("MBC_API_USER", "integracao"),
            api_password=os.environ.get("MBC_API_PASSWORD", "RumoTech1!"),
            request_timeout=int(os.environ.get("MBC_API_TIMEOUT", "120")),
            default_top=int(os.environ.get("MBC_API_TOP", "5000")),
        )


SETTINGS = Settings.from_env()
