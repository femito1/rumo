# HANDOFF — 2026-07-13 (noite): Despesas decodificada + próximos passos

> Read `PROJECT_STATUS.md` §0 first (client-confirmed rules, DO NOT re-ask), then
> `docs/SISJURI_DB.md` ("Known account facts") and the recalled memories
> (`workbook-uses-liquido-not-bruto`, `transitoria-desdobramento-mechanism`,
> `despesas-gap-is-provisao-smoothing`, `dl-extras-bonus-rules`, `easypanel-redeploy`).
>
> **Goal:** fully replicate the MBC closing workbook from LegalDesk + SISJURI, no
> manual input. Workbook `Fechamento MBC 05.2026.xlsx` is the source of truth; every
> displayed number must tie to it (hard rule blanks anything off by > R$1,00).

## STATE: ~85% automated. The DRE spine ties to the centavo on live May data.

Everything below is committed + pushed to `main`, CI green, **218 backend tests**.

### ✅ Done & live-validated (real May 2026 SISJURI snapshot, ties to workbook)
- Recebimento (sacred LegalDesk) + per-area recebimento (Ambiental→Arb, Não Alocados).
- Custo equipe 3 áreas (74.141,21 / 79.436,24 / 54.383,94); Comissão (EHF→Econ 2.128,06);
  Custos Diretos 210.089,45.
- Imposto 15%, Amortização 8.117, Reserva 10% do líquido.
- Salários Adm 12.344,91 (Vale-ADM from transitória 200.010.0010 + FGTS→Impostos).
- Hard rule tolerance R$1,00 (workbook rounds to whole reais).

### 🟡 Implemented, needs ONE live extract re-run to go live — **THE BOTTLENECK**
**T5 — Despesas Institucional at LÍQUIDO + desdobramento.** Fully decoded and coded;
proven to the centavo (10/10 families, residual R$129,17 = the client's own aluguel
pending). The recipe:
- Despesa = **net** (`CONTASPAGAR.CPGNVALORLIQUIDO`), not gross GERENC.
- Lumps (card/transitória) unfolded via **`CPDESDOBRAMENTO`** (DESCCONTADESTINO,
  DESNVALOR, DESCHISTORICO).
- Aluguel: use GERENC net 24.359,77 (already net of the "Belline" sublet credit
  3.117,90), NOT CONTASPAGAR gross 27.477,67.
- Reclass: "Claude"/software slice out of Material de Copa (020.030.0020) →
  Informática (020.040.0010); Custas (020.030.0140) + Transporte (020.030.0060) OUT
  of row-198; Cursos 030.010.0180 → Gestão do Conhecimento.

Code: `ops/sisjuri-agent/extract.sql` (new `despesas_liquido` + `despesas_desdobramento`
blocks), `backend/app/closing/despesas_liquido.py` (`net_by_account`), `dre.py`
(`from_snapshot` overrides gross→net when blocks present; **no-op until the extract
re-runs** — safe). Locked by `tests/test_despesas_liquido.py` + 2 integration tests.

**NEXT ACTION (do this first):** ask the operator to re-run the May extract on the RDP
box (`MBC-LDESK01`) so the snapshot carries the new blocks:
```powershell
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$env:INGEST_TOKEN = '<in ops/sisjuri-agent/ingest.local.secrets>'
$env:INGEST_URL = 'https://rumo-backend.xem1qi.easypanel.host/api/ingest'
Invoke-WebRequest -UseBasicParsing "https://raw.githubusercontent.com/femito1/rumo/main/ops/sisjuri-agent/extract.sql?nocache=$(Get-Random)" -OutFile C:\temp\sisjuri\extract.sql
powershell -ExecutionPolicy Bypass -File C:\temp\sisjuri\run-agent.ps1 -AnoMes 2026-05 -IngestUrl $env:INGEST_URL
```
Then pull the fresh snapshot from Supabase (recipe below), update
`backend/tests/fixtures/sisjuri_2026_05.json`, and verify end-to-end that institucional
`despesas` ties (~105.640 vs workbook 105.511, i.e. the R$129 aluguel) and that
Resultado Bruto/Líquido/Reserva/margens stop blanking. Redeploy prod
(`ops/easypanel-deploy.sh backend`).

### 🔴 Not yet automated (each has a known path, none are mysteries)
1. **DL extras** (DL excedente sócios / MV / Repasse Cacione): no DB rule found; happens
   ~1×/year in February. Validate against a February snapshot. Partner-split out of
   150.* is RUMO's task (POINT 17). Bônus equipe (150.*) block already runs (null in May).
2. **Convênio extra per lawyer** (upgrade/dependentes): booked to `500.010.<SIGLA>`,
   **deducted from that lawyer's DL** (not an office expense). Mechanism known (transcript);
   3 lawyers (RB/AM/DC). Wire it into the DL block. See `transitoria-desdobramento-mechanism`.
3. **Abas Nacional / Moedas** (per-invoice faturamento lists, 16 cols): need a new extract
   block from FAT_FATURA / POSFIN_RESULTFAT with Cliente/NF/Moeda/dates. T8.
4. **Backfill Jan–Abr 2026** with the corrected + net extract (RDP re-run per month), then
   validate each month ties. T7.
5. **Multi-month validation:** everything proven on May; Feb (bônus/DL) + others need live
   checks.

## How to work (well-worn paths)

- **DB probes / extract re-run over RDP:** the operator is on `MBC-LDESK01`. Give them
  copy-paste PowerShell one-liners with the password inlined (it's in
  `ops/sisjuri-agent/ingest.local.secrets`: RGN pw `RgN@92Kx7`; DB host 172.16.237.9:1521,
  service cdbp01_pdb1.submbc.vcnmbc.oraclevcn.com). Recipe: pull probe from the public raw
  GitHub URL, wrap with CONNECT, run via `sqlplus -S /nolog`. See
  `ops/sisjuri-agent/README.md` "Ad-hoc probes over RDP". Always start a new PS window with
  `[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12`.
- **Pull a fresh Supabase snapshot** (creds in `backend/.env`):
  `curl -H "apikey: $SUPABASE_SERVICE_KEY" -H "Authorization: Bearer $SUPABASE_SERVICE_KEY" "$SUPABASE_URL/rest/v1/sisjuri_snapshots?client_id=eq.mbc&ano_mes=eq.2026-05&select=payload"`
- **Redeploy prod:** `ops/easypanel-deploy.sh backend|frontend` (creds in
  `ops/easypanel.local.secrets`; see `easypanel-redeploy` memory).
- **Offline reference files** the client gave (in `reference/workbook/`, gitignored, not in
  repo): `Pagtos maio.XLS.xlsx` (= CONTASPAGAR detail w/ Valor Bruto/**Líquido**/Grupo/
  ORIENTAÇÃO — the raw material; mine with openpyxl), `lancextrato de contas.xls` (full May
  razão, per-account, via xlrd), `Fechamento MBC 05.2026.xlsx` (workbook target), the
  meeting `Transcript` (.docx; unzip word/document.xml). These are dev aids only — never a
  monthly input.
- **Quality gates:** `cd backend && ruff check . && mypy app && pytest`;
  `cd frontend && npm run lint && npm run typecheck && npm run test`.

## Key numbers to reconcile against (May 2026, workbook)
Recebimento 415.927,84 · Custos Diretos 210.089,46 · Despesas Indiretas 105.511,43 ·
Resultado Bruto 100.327,11 · Imposto 62.389,20 · Amortização 8.117 · Resultado Líquido
29.820,91 · Reserva 2.982,09. Per-family despesas (row-198) and the full recipe are in the
`workbook-uses-liquido-not-bruto` memory.
