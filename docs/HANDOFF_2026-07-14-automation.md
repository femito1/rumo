# HANDOFF — 2026-07-14: despesas live, backfill validated, DL/convênio + Nacional/Moedas automated

> Read `PROJECT_STATUS.md` §0 (client-confirmed rules, DO NOT re-ask), then
> `docs/SISJURI_DB.md` ("Known account facts") and the recalled memories
> (`workbook-uses-liquido-not-bruto`, `transitoria-desdobramento-mechanism`,
> `dl-extras-bonus-rules`, `daily-job-selfupdate-and-backfill-scope`,
> `multimonth-despesas-validation`, `easypanel-redeploy`).
>
> **Goal:** fully replicate the MBC closing workbook from LegalDesk + SISJURI, no
> manual input, apart from the Orçamento. The 05.2026 workbook is the source of truth.

## STATE: ~95% automated. May DRE ties end-to-end; only Orçamento + the client's
## own manual layer remain outside the DB.

Everything below is committed + pushed to `main`, backend **224 tests**, ruff/mypy/tsc clean.

### ✅ Done & live-validated (real 2026 SISJURI snapshots)
- **T5 despesas at LÍQUIDO** live for May: `despesas_liquido` + `despesas_desdobramento`
  blocks in the fresh snapshot reproduce the recipe to the centavo. Despesas = 105.640,60.
- **May renders the full institucional tail** (bruto 100.197,94, líquido 29.691,74,
  reserva 2.969,17) after the client-authorized aluguel–Belline target override (Renata:
  "the DB is correct for aluguel–Belline, only those"). See `build_workbook_targets.py::
  _apply_aluguel_override` (Apr+May, +129,17 propagated through the tail).
- **Daily job can no longer go stale:** `run-agent.ps1` self-updates `extract.sql` from
  `main` each run (sanity-checked, fail-safe). Root cause of the 2026-07-14 stale snapshot.
- **DL/convênio proven to the centavo** (blocks emitted, ready): convênio extra per lawyer
  deducted from DL (DC 3.796,78 / RB 5.151,75 / EHF 1.398,01, `500.010.<SIGLA>`); Bônus
  equipe Feb = 94.696,15 (`150.010.0010`) + 7.009,84 JGS (`030.010.0010`) = 101.705,84.
  `dre.py` now sums `bonus_equipe` + `bonus_equipe_030`.
- **T8 Nacional/Moedas** validated to the centavo (`DB_VW_FATURASEMI_REC` Σ = sacred
  719.988,05, split R$ 708.659,18 + US$ 11.328,87) and fully wired: `faturas_moeda` extract
  block (GROUP BY NUMERO), `SectionKey.NACIONAL/MOEDAS`, `assemble_faturas_moeda`, TAB_ORDER.

### 🟡 One re-run from live — the only bottleneck
**Nacional/Moedas need one extract re-run** so the snapshot carries the new `faturas_moeda`
block (also picks up `bonus_equipe_030` + `convenio_extra_dl`). The extract on `main` has
them; `run-agent.ps1` self-updates, so it's just:
```powershell
$env:SISJURI_PASSWORD='RgN@92Kx7'
$env:INGEST_TOKEN='<ops/sisjuri-agent/ingest.local.secrets>'
$env:INGEST_URL='https://rumo-backend.xem1qi.easypanel.host/api/ingest'
powershell -ExecutionPolicy Bypass -File C:\temp\sisjuri\run-agent.ps1 -AnoMes 2026-05 -IngestUrl $env:INGEST_URL
```
(The daily 06:00 task will do this automatically tomorrow.) Then verify Nacional/Moedas
totals tie via the closing endpoint. Optionally re-backfill Jan–Abr for the same blocks.

### 🔴 Remaining (each has a known path)
1. **`convenio_extra_dl` wiring into the DL split** — the block is emitted; subtract each
   sigla's extra from that partner's DL. Depends on RUMO's partner-split (POINT 17).
2. **Jan–Abr manual layer** — those months diverge from the workbook only on the client's
   hand-entered cells (Vale-ADM, Associações ÷2/÷3). NOT a DB bug; our numbers are arguably
   more correct. They blank under the hard rule until the client accepts the DB value or we
   add per-month targets. See `multimonth-despesas-validation` memory.
3. **DL extras (Feb)** — decomposed & proven (see `dl-extras-bonus-rules`); wire the
   partner/MV split when POINT 17 lands.
4. **Orçamento** — explicitly out of scope (client fills the ORÇAMENTO tab; already an
   editable budget in the product).

## How to work (well-worn paths)
- **DB probes / extract re-run over RDP** (`MBC-LDESK01`): copy-paste PowerShell one-liners.
  Always start a new PS window with `[Net.ServicePointManager]::SecurityProtocol =
  [Net.SecurityProtocolType]::Tls12`. Pull probes from the public raw GitHub URL with a
  `?nocache=$(Get-Random)`. RGN pw `RgN@92Kx7`; DB `172.16.237.9:1521` /
  `cdbp01_pdb1.submbc.vcnmbc.oraclevcn.com`. See `ops/sisjuri-agent/README.md`.
- **Pull a fresh Supabase snapshot** (creds in `backend/.env`):
  `curl -H "apikey: $SUPABASE_SERVICE_KEY" -H "Authorization: Bearer $SUPABASE_SERVICE_KEY" "$SUPABASE_URL/rest/v1/sisjuri_snapshots?client_id=eq.mbc&ano_mes=eq.2026-05&select=payload"`
- **Redeploy prod:** `ops/easypanel-deploy.sh backend|frontend`.
- **Quality gates:** `cd backend && ruff check . && mypy app && pytest`;
  `cd frontend && npm run lint && npm run typecheck && npm run test`.

## Key numbers (May 2026, workbook)
Recebimento 415.927,84 · Custos Diretos 210.089,46 · Despesas Indiretas (DB) 105.640,60
(wb typed 105.511,43; +129,17 = aluguel, DB-authoritative per Renata) · Resultado Bruto
100.197,94 · Imposto 62.389,20 · Amortização 8.117 · Resultado Líquido 29.691,74 ·
Reserva 2.969,17 · Faturamento 719.988,05 (Nacional 708.659,18 + Moedas US$→R$ 11.328,87).
