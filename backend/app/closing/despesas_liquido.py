# backend/app/closing/despesas_liquido.py
"""Institutional despesas at LÍQUIDO (net of retained 3rd-party tax) — the basis the
workbook uses.

Client-confirmed (2026-07-13) + proven to the centavo against Fechamento MBC 05.2026
(10/10 families tie; residual R$129,17 is the client's own aluguel pending): the
workbook books the **líquido** value for service-provider expenses (net of retained
IRRF/ISS/INSS/PIS/COFINS/CSLL), while ``GERENC_LANCAMENTORESUMO`` gives the **gross**.

Sources (emitted by the extract):
* ``despesas_liquido`` — ``FINANCE.CONTASPAGAR.CPGNVALORLIQUIDO`` per conta (direct
  020.*/040.* payments + the 030.010.0180 Cursos carve-out).
* ``despesas_desdobramento`` — ``FINANCE.CPDESDOBRAMENTO`` slices (DESCCONTADESTINO,
  DESNVALOR, DESCHISTORICO): the card/transitória lumps unfolded into real accounts.

A few workbook reclassifications (from the ledger, confirmed by the client) are applied
by ``id_conta`` + histórico so families tie exactly:
* Aluguel (020.010.0010): use the GERENC net value (already net of the sublocação
  credit, e.g. "Recebimento Belline"), NOT the CONTASPAGAR gross — handled by the
  caller which keeps the GERENC aluguel figure.
* A software line booked to Material de Copa (020.030.0020) whose histórico names a
  software/SaaS (e.g. "Claude") moves to Informática (020.040.0010 family).
* Custas (020.030.0140) and Transporte e Frete (020.030.0060) are NOT institutional
  Despesas Gerais leaves in the workbook (they go to Despesas para Clientes / out of
  row-198) — excluded here.

Pure module: it takes the already-extracted rows, so it is unit-testable without a DB.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence

#: Accounts excluded from institutional despesas (workbook books them elsewhere).
#: Custas -> Despesas para Clientes; Transporte e Frete -> not in row-198 May.
EXCLUDED_ACCOUNTS: frozenset[str] = frozenset({"020.030.0140", "020.030.0060"})

#: Software/SaaS histórico markers that move a Material-de-Copa (020.030.0020) slice
#: into the Informática family (workbook reclass — e.g. the "Claude" subscription).
_SOFTWARE_MARKERS: tuple[str, ...] = ("claude", "software", "saas", "licen", "cloud")

#: Where a reclassified software slice lands (Serviços de Informática leaf).
INFORMATICA_ACCOUNT = "020.040.0010"
MATERIAL_COPA_ACCOUNT = "020.030.0020"


def net_by_account(
    despesas_liquido: Sequence[Mapping[str, object]],
    despesas_desdobramento: Sequence[Mapping[str, object]],
    *,
    aluguel_gerenco_net: float | None = None,
) -> dict[str, float]:
    """Return ``{id_conta -> net despesa}`` combining direct líquido + desdobramento,
    with the workbook reclassifications applied.

    ``aluguel_gerenco_net`` (optional): the GERENC net aluguel figure (already net of
    the sublocação credit). When given it OVERRIDES the CONTASPAGAR gross for
    020.010.0010, so Ocupação ties instead of showing the pre-credit rent.
    """
    net: dict[str, float] = {}

    def add(conta: str, valor: float) -> None:
        if conta in EXCLUDED_ACCOUNTS:
            return
        net[conta] = round(net.get(conta, 0.0) + valor, 2)

    for row in despesas_liquido:
        conta = str(row.get("id_conta") or "")
        if not conta:
            continue
        valor = float(row.get("liquido") or 0.0)  # type: ignore[arg-type]
        add(conta, valor)

    for row in despesas_desdobramento:
        conta = str(row.get("id_conta") or "")
        if not conta:
            continue
        valor = float(row.get("valor") or 0.0)  # type: ignore[arg-type]
        hist = str(row.get("historico") or "").lower()
        # Reclass: a software/SaaS slice booked to Material de Copa -> Informática.
        if conta == MATERIAL_COPA_ACCOUNT and any(m in hist for m in _SOFTWARE_MARKERS):
            add(INFORMATICA_ACCOUNT, valor)
            continue
        add(conta, valor)

    if aluguel_gerenco_net is not None:
        # The GERENC "Aluguel" account is already net of the sublet credit; use it.
        net["020.010.0010"] = round(float(aluguel_gerenco_net), 2)

    return {k: v for k, v in net.items() if v}
