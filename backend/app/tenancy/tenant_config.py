# backend/app/tenancy/tenant_config.py
"""What differs between clients.

The closing pipeline was written against MBC's chart of accounts and its three practice
areas. Everything structural (tables, sources, the DRE maths) is already per-client;
these are the last pieces that were literal constants.

**MBC's values are the defaults**, so an empty ``provider_config`` reproduces today's
behaviour exactly — that is what `tests/test_mbc_golden.py` pins, and it is the reason
this is safe to add before a second client actually exists.

Shape in ``clients.provider_config`` (every key optional):

```json
{
  "areas": [
    {"label": "Contencioso", "match": ["conten"]},
    {"label": "Econômico",   "match": ["econô", "econo"]},
    {"label": "Arbitragem",  "match": ["arbitr", "ambient", "compliance"]}
  ],
  "accounts": {"020.060.0040": "Administrativas"},
  "amortizacao_mensal": 8117.0,
  "bonus_reserve_rate": 0.10
}
```

`accounts` is an OVERLAY on the built-in map, not a replacement: a second client shares
most of the SISJURI account tree and only needs to name its exceptions.

⚠ Reading this from ``provider_config`` means the same column holds credentials. Never
serialize the whole config into an API response (`_client_public` omits it).
"""
from __future__ import annotations

from dataclasses import dataclass, field

#: MBC's three cost centres, in workbook order, with the substrings that identify each
#: in a SISJURI grupo name. Client-confirmed 2026-07-10: *Ambiental soma com
#: Arbitragem* (the LegalDesk Demonstrativo lists it separately; the workbook does not).
#: ⚠ Econômico is anchored on 'econô'/'econo', NOT a bare 'econ' — 'equipecontencioso'
#: contains 'econ' when SISJURI drops a space, and three loops in dre.py ADD over every
#: matching área, so an ambiguous name would land the money in two áreas at once.
DEFAULT_AREAS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Contencioso", ("conten",)),
    ("Econômico", ("econô", "econo")),
    ("Arbitragem", ("arbitr", "ambient", "compliance")),
)

#: A grupo name containing this is not an área at all ("Não Alocados" is its own line).
NOT_AN_AREA = ("alocad",)


@dataclass(frozen=True)
class AreaSpec:
    label: str
    match: tuple[str, ...]


@dataclass(frozen=True)
class TenantConfig:
    """Per-client accounting shape. Defaults are MBC's."""

    areas: tuple[AreaSpec, ...] = field(
        default_factory=lambda: tuple(
            AreaSpec(label=lbl, match=m) for lbl, m in DEFAULT_AREAS
        )
    )
    #: CONTA3 → institutional family, layered OVER the built-in map.
    account_overrides: dict[str, str] = field(default_factory=dict)
    amortizacao_mensal: float | None = None
    bonus_reserve_rate: float | None = None

    @property
    def area_labels(self) -> tuple[str, ...]:
        return tuple(a.label for a in self.areas)

    def match_area(self, snapshot_area_name: str, area: str) -> bool:
        """Whether a SISJURI grupo name belongs to ``area``."""
        low = (snapshot_area_name or "").lower()
        if any(tok in low for tok in NOT_AN_AREA):
            return False
        for spec in self.areas:
            if spec.label == area:
                return any(tok in low for tok in spec.match)
        return False

    @classmethod
    def from_provider_config(cls, provider_config: dict | None) -> "TenantConfig":
        cfg = provider_config or {}

        raw_areas = cfg.get("areas")
        if isinstance(raw_areas, list) and raw_areas:
            areas = tuple(
                AreaSpec(
                    label=str(a["label"]),
                    # Default the matcher to the label itself, lowercased — enough for a
                    # client whose grupo names already equal its área labels.
                    match=tuple(str(m).lower() for m in a.get("match") or [str(a["label"]).lower()]),
                )
                for a in raw_areas
                if isinstance(a, dict) and a.get("label")
            )
        else:
            areas = tuple(AreaSpec(label=lbl, match=m) for lbl, m in DEFAULT_AREAS)

        raw_accounts = cfg.get("accounts")
        overrides = (
            {str(k): str(v) for k, v in raw_accounts.items()}
            if isinstance(raw_accounts, dict)
            else {}
        )

        def _num(key: str) -> float | None:
            v = cfg.get(key)
            try:
                return float(v) if v is not None else None
            except (TypeError, ValueError):
                return None

        return cls(
            areas=areas,
            account_overrides=overrides,
            amortizacao_mensal=_num("amortizacao_mensal"),
            bonus_reserve_rate=_num("bonus_reserve_rate"),
        )


#: The default (MBC) configuration, for callers that have no Client in hand.
DEFAULT_TENANT = TenantConfig()
