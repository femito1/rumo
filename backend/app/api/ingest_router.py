# backend/app/api/ingest_router.py
"""Ingest endpoint for the on-server SISJURI agent (egress Option A).

The agent runs on MBC-LDESK01 (the only host with a route to the private-VCN
Oracle DB) and POSTs a per-competence-month JSON snapshot here over HTTPS, with a
shared bearer token. We never open an inbound path to the DB; the server reaches
out to us. Snapshots are persisted via ``SnapshotStore`` for ``SisjuriDbSource``.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException

from app.api.providers import get_settings
from app.api.providers import get_snapshot_store as _get_snapshot_store

router = APIRouter(prefix="/api", tags=["ingest"])

#: Default tenant for agents that don't (yet) send a client_id. The current
#: single-client agent extracts MBC; new tenants pass meta.client_id.
_DEFAULT_CLIENT = "mbc"

#: Extract contract version this backend expects (``meta.extract_version`` in
#: extract.sql). A snapshot below this was produced by an agent whose SQL emitted
#: fields with DIFFERENT meaning, so its numbers are wrong even though the code is
#: right — e.g. v1 folded the lawyers' Vale into ``vale_adm``, which inflated
#: Despesa Institucional and every área's rateio share. Surfaced by the summary
#: endpoint so an operator can see WHICH months still need re-extracting instead
#: of discovering it as a wrong number in a client meeting.
#:
#: v3 (2026-07-30) replaces ``vale_adm`` with the raw per-person ``vale_prof``
#: slices. v2's "exclude 500.010.* twins" rule never fired (0 rows dropped in every
#: month Jan–Jun 2026), so v2 snapshots still carry the estagiários' Vale inside
#: ``vale_adm``. NOTE the lesson: a version bump asserts the CONTRACT changed, not
#: that the logic is right — v2 certified a broken rule. Pair every bump with a test
#: that ties a real month (see test_vale_adm_derives_adm_only_from_per_person_slices).
#:
#: v4 (2026-08-03) widens the três históricos from 60/80 to 300 chars
#: (``despesas_desdobramento``, ``vale_prof``, ``convenio_extra_dl``). Finance writes
#: the arithmetic INTO that text — *"Vale transporte / Calculo: 14 dias x R$ 18,76"* —
#: and the old caps cut it off exactly where the calculation began, which is why the
#: January "35,52" had to be chased through a hand-exported .xls instead of the
#: snapshot. This is a WIDER FIELD, not a re-meaning; the bump exists so the summary
#: endpoint's ``stale`` flag tells the operator WHICH months still hold truncated text.
#: ⚠ It can still move money: ``despesas_liquido.net_by_account`` reclassifies on
#: markers found in that string, so a longer histórico may match where the short one
#: did not. Guarded by
#: ``test_widening_the_historico_must_not_move_copa_to_informatica``, which pins every
#: row that was actually at the cap on a reclass account.
#:
#: v5 was ATTEMPTED 2026-08-04 (``~`` chunk guards to stop a space being lost at a
#: chunk boundary) and REVERTED the same day — it corrupted the live store instead.
#: The box is Oracle **11g**, whose sqlplus rejects ``SET TRIMSPACE`` outright
#: (``SP2-0158``), so that setting was never active and the root-cause theory behind
#: v5 was wrong. Worse, real sqlplus line-wrapping put the ``~`` guards INSIDE the JSON
#: (``"r~ecebimento_rows"``), which the local round-trip test — modelling clean 180-char
#: chunks — never reproduced, so it passed with false confidence. The proper fix needs
#: to be validated against the actual box (probe its wrapping first); until then the
#: whitespace glue is a known, money-neutral cosmetic defect. Do NOT re-bump to 5
#: without that validation. Detail: docs/HANDOFF_v5_reverted_2026-08-04.md.
CURRENT_EXTRACT_VERSION = 4


def _unmapped_lawyers(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    """Siglas with per-lawyer cost but NO ``home_area`` entry, and the money at stake.

    Why this is worth surfacing: per-área Custo equipe is built by folding each lawyer's
    ``custo_equipe_deriv`` rows into their home grupo (``build_area_splits`` falls back to
    ``home_area`` when a lawyer has no ``rateio_grupo``). A sigla in neither map has no
    área to land in, so its cost is silently **dropped from the institucional total AND
    every área** — no error, no divergence between the two, just a smaller number.

    The realistic trigger is an onboarding race: finance posts a new lawyer's
    distribuição/convênio before their grupo is set in ``CAD_PROFISSIONAL``. 2026 already
    saw four joiners and four leavers (VSR in March, AVN in April), so this is not
    hypothetical — it simply has not bitten yet because the grupo has always been set
    first. Empty list = nothing to do.
    """
    home = {
        str(k).strip()
        for k, v in (snapshot.get("home_area") or {}).items()
        if str(v or "").strip()
    }
    by_sigla: dict[str, float] = {}
    for row in snapshot.get("custo_equipe_deriv") or []:
        sigla = str(row.get("sigla") or "").strip()
        if not sigla or sigla in home:
            continue
        try:
            by_sigla[sigla] = round(by_sigla.get(sigla, 0.0) + float(row.get("valor") or 0.0), 2)
        except (TypeError, ValueError):  # pragma: no cover - defensive on raw snapshot
            continue
    return [
        {"sigla": s, "custo_equipe_dropped": v}
        for s, v in sorted(by_sigla.items(), key=lambda kv: -abs(kv[1]))
    ]


def snapshot_extract_version(snapshot: dict[str, Any]) -> int:
    """``meta.extract_version``, defaulting to 1 (pre-versioning snapshots)."""
    meta = snapshot.get("meta") or {}
    try:
        return int(meta.get("extract_version") or 1)
    except (TypeError, ValueError):
        return 1


def get_snapshot_store():
    """Snapshot persistence (Supabase in prod, filesystem for local/USE_FAKE_REPO)."""
    return _get_snapshot_store()


def get_ingest_token() -> str:
    return get_settings().ingest_token


def _require_ingest_token(authorization: str | None, token: str) -> None:
    if not token:
        raise HTTPException(status_code=503, detail="Ingestão não configurada")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Não autenticado")
    if authorization.split(" ", 1)[1] != token:
        raise HTTPException(status_code=401, detail="Token de ingestão inválido")


@router.post("/ingest")
def ingest(
    snapshot: dict[str, Any],
    authorization: str | None = Header(default=None),
    token: str = Depends(get_ingest_token),
    store=Depends(get_snapshot_store),
) -> dict[str, str]:
    _require_ingest_token(authorization, token)

    meta = snapshot.get("meta") or {}
    ano_mes = meta.get("ano_mes")
    if not ano_mes:
        raise HTTPException(status_code=422, detail="Snapshot sem meta.ano_mes")
    client_id = meta.get("client_id") or _DEFAULT_CLIENT

    try:
        store.put(ano_mes, snapshot, client_id=client_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return {"status": "ok", "ano_mes": ano_mes, "client_id": client_id}


@router.post("/ingest/migrate-fs-to-supabase")
def migrate_fs_to_supabase(
    client_id: str = _DEFAULT_CLIENT,
    authorization: str | None = Header(default=None),
    token: str = Depends(get_ingest_token),
) -> dict[str, Any]:
    """One-time migration: copy filesystem snapshots on this host into Supabase.

    Runs where the legacy files live (the VPS), so the 29-month backfill moves to
    the durable store without re-running the agent. Idempotent (upsert). Reads
    both the new ``sisjuri_{client}_{mes}.json`` and legacy ``sisjuri_{mes}.json``
    layouts.
    """
    _require_ingest_token(authorization, token)

    import os
    import re
    from pathlib import Path

    from app.sources.snapshot_store import SnapshotStore
    from app.sources.supabase_snapshot_store import SupabaseSnapshotStore

    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_key:
        raise HTTPException(status_code=503, detail="Supabase não configurado")

    root = Path(os.environ.get("SNAPSHOT_DIR", "data/snapshots"))
    fs = SnapshotStore(root)

    from supabase import create_client

    dest = SupabaseSnapshotStore(
        create_client(settings.supabase_url, settings.supabase_service_key)
    )

    months: set[str] = set()
    pat = re.compile(rf"^sisjuri_(?:{re.escape(client_id)}_)?(\d{{4}}-\d{{2}})\.json$")
    for p in root.glob("sisjuri_*.json"):
        m = pat.match(p.name)
        if m:
            months.add(m.group(1))

    migrated: list[str] = []
    skipped: list[str] = []
    for ano_mes in sorted(months):
        snap = fs.get(ano_mes, client_id=client_id)
        if snap is None:
            skipped.append(ano_mes)
            continue
        dest.put(ano_mes, snap, client_id=client_id)
        migrated.append(ano_mes)

    return {
        "client_id": client_id,
        "migrated": migrated,
        "skipped": skipped,
        "count": len(migrated),
    }


@router.get("/ingest/{ano_mes}/summary")
def ingest_summary(
    ano_mes: str,
    client_id: str = _DEFAULT_CLIENT,
    authorization: str | None = Header(default=None),
    token: str = Depends(get_ingest_token),
    store=Depends(get_snapshot_store),
) -> dict[str, Any]:
    """Token-protected integrity check for a stored snapshot.

    Returns structure/counts/headline values (not the full financial payload) so
    an operator can verify what actually landed after an agent run.
    """
    _require_ingest_token(authorization, token)

    try:
        snapshot = store.get(ano_mes, client_id=client_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Sem snapshot para o mês")

    def _n(key: str) -> int:
        val = snapshot.get(key)
        return len(val) if isinstance(val, list) else 0

    revenue = snapshot.get("revenue") or {}
    version = snapshot_extract_version(snapshot)
    return {
        "ano_mes": ano_mes,
        "meta": snapshot.get("meta"),
        # Is this snapshot's SQL contract current? `stale: true` means re-run the
        # agent for this month — the stored numbers predate a meaning-changing
        # extract fix, so the API will serve them wrongly but without erroring.
        "extract": {
            "version": version,
            "expected": CURRENT_EXTRACT_VERSION,
            "stale": version < CURRENT_EXTRACT_VERSION,
        },
        "top_level_keys": sorted(snapshot.keys()),
        "counts": {
            "rateio_prof": _n("rateio_prof"),
            "despesas_conta": _n("despesas_conta"),
            "custo_area": _n("custo_area"),
            "prolabore": _n("prolabore"),
            "distribuicao_socio": _n("distribuicao_socio"),
        },
        # Lawyers carrying cost that the DRE would DROP because no grupo is recorded
        # for them. Reported here (an operator integrity check) rather than guarded in
        # the money path — the derivation must stay honest about what the DB says.
        "unmapped_lawyers": _unmapped_lawyers(snapshot),
        "revenue": {
            "recebimento_bruto": revenue.get("recebimento_bruto"),
            "faturamento_bruto": revenue.get("faturamento_bruto"),
            "recebimento_rows": revenue.get("recebimento_rows"),
            "faturamento_rows": revenue.get("faturamento_rows"),
        },
        "faturas": snapshot.get("faturas"),
    }
