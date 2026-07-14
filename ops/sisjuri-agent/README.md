# SISJURI extraction agent (runs on MBC-LDESK01)

Pulls the monthly closing data out of the private-VCN Oracle DB and ships it to
the RUMO backend. This is **egress Option A** from `docs/SISJURI_QUERIES.md` §10:
the server (the only host with a route to the DB) POSTs outbound over HTTPS, so
no inbound firewall rule or VPN is needed.

## Files

- `extract.sql` — one read-only query emitting the whole closing extract as a
  single JSON document (Oracle 19c `JSON_OBJECT`/`JSON_ARRAYAGG`). Parameterised
  by `&ANO_MES` / `&D_START` / `&D_END`.
- `run-agent.ps1` — PowerShell wrapper: **self-updates `extract.sql` from `main`**
  (fail-safe — falls back to the on-disk copy if the pull fails or the payload
  fails a sanity check), connects via the existing `sqlplus`, runs `extract.sql`,
  validates the JSON, writes a snapshot, optionally uploads. The self-update means
  the daily task always runs the committed query — no more manual file copies to
  keep the box in sync (root cause of the 2026-07-14 stale snapshot). Pass
  `-NoSelfUpdate` to force the local copy when testing an uncommitted edit.
- `register-task.ps1` — installs a daily Scheduled Task (run once, elevated).
- `backfill.ps1` — one-shot historical catch-up: loops months from a start
  through the last closed month, calling `run-agent.ps1` for each.

No Python is required on the server; the agent uses the Oracle 11g `sqlplus`
already installed at `C:\oracle11\app\product\11.2.0\client_1\bin`.

## One-time setup on the server

1. Copy the three files to `C:\temp\sisjuri\` (e.g. via RDP clipboard / Notepad).
2. Set machine-level secrets (elevated PowerShell):

   ```powershell
   [Environment]::SetEnvironmentVariable('SISJURI_PASSWORD','<RGN password>','Machine')
   [Environment]::SetEnvironmentVariable('INGEST_TOKEN','<shared token>','Machine')
   [Environment]::SetEnvironmentVariable('INGEST_URL','https://<vps>/api/ingest','Machine')
   ```

3. Install the daily task (elevated):

   ```powershell
   powershell -ExecutionPolicy Bypass -File C:\temp\sisjuri\register-task.ps1
   ```

## Manual runs

```powershell
# snapshot only (no upload) — for testing
$env:SISJURI_PASSWORD='<RGN password>'
powershell -ExecutionPolicy Bypass -File C:\temp\sisjuri\run-agent.ps1 -AnoMes 2026-02

# with upload to the VPS
$env:SISJURI_PASSWORD='...'; $env:INGEST_TOKEN='...'
powershell -ExecutionPolicy Bypass -File C:\temp\sisjuri\run-agent.ps1 -AnoMes 2026-02 -IngestUrl https://<vps>/api/ingest
```

Snapshots are written to `C:\temp\sisjuri\closing_<AnoMes>.json`.

## Ad-hoc probes over RDP (READ THIS FIRST — the well-worn path)

We frequently need to run a one-off read-only `.sql` probe against the DB from
the RDP box `MBC-LDESK01`. The box runs **Windows Server 2012 / PowerShell 3-4**,
which has two hard gotchas that waste time every single session:

1. **TLS 1.2 is OFF by default.** `Invoke-WebRequest` to GitHub fails with
   *"The request was aborted: Could not create SSL/TLS secure channel"* until you
   enable it. You MUST run this once per PowerShell window BEFORE any pull:

   ```powershell
   [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
   ```

2. **Multi-line / here-string commands are unreliable.** Paste **one command per
   line, no line continuations** (no `` ` `` backtick-newline, no `\`). Build any
   multi-line SQL wrapper with an inline `` `r`n `` inside a single `Set-Content`.

### The fixed recipe (copy these one line at a time)

The agent lives at **`C:\temp\sisjuri`**. The Oracle client is at
`C:\oracle11\app\product\11.2.0\client_1\bin\sqlplus.exe`. The DB password is in
`$env:SISJURI_PASSWORD`. Probes are pulled from the **public** GitHub raw URL
`https://raw.githubusercontent.com/femito1/rumo/main/ops/sisjuri-agent/<file>.sql`.

```powershell
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$env:SISJURI_PASSWORD = '<RGN password>'
Invoke-WebRequest -UseBasicParsing "https://raw.githubusercontent.com/femito1/rumo/main/ops/sisjuri-agent/probe_NAME.sql" -OutFile C:\temp\sisjuri\probe_NAME.sql
Set-Content C:\temp\sisjuri\q.sql -Encoding ASCII -Value ("CONNECT RGN/""$($env:SISJURI_PASSWORD)""@(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=172.16.237.9)(PORT=1521))(CONNECT_DATA=(SERVICE_NAME=cdbp01_pdb1.submbc.vcnmbc.oraclevcn.com)))`r`n" + (Get-Content C:\temp\sisjuri\probe_NAME.sql -Raw))
& 'C:\oracle11\app\product\11.2.0\client_1\bin\sqlplus.exe' -S /nolog '@C:\temp\sisjuri\q.sql' *>&1 | Tee-Object C:\temp\sisjuri\out_NAME.txt
```

Replace `probe_NAME` with the actual probe filename; paste the `out_NAME.txt`
contents back. To push a NEW probe first: commit + push to `main` (the repo is
public), then pull it with the URL above — no base64, no clipboard paste.

### Known query pitfalls (do not rediscover these)

- **`FINANCE.LANCAMENTO` has NO `ID_GRUPOJURIDICODEST`.** Area for a cash
  movement is `SIGLADEST` (cost-center) or, better, the destination
  professional's home grupo — not a group column on the row. Probes that select
  `ID_GRUPOJURIDICODEST` fail with `ORA-00904`.
- **DB connection facts:** host `172.16.237.9:1521`, service
  `cdbp01_pdb1.submbc.vcnmbc.oraclevcn.com`, user `RGN`. Only `MBC-LDESK01` can
  route to the private VCN address (see `docs/SISJURI_QUERIES.md` §10).
- **Accents render as `\Uffffffff`** in the sqlplus console; that is a display
  artifact only — the extract's UTF-8 handling (`NLS_LANG=.AL32UTF8`) is fine.
- **`GERENC_LANCAMENTORESUMO` does not carry every account.** Vale
  (`030.010.0100/0220`) and some personal lines are absent; those live in the
  `500.010.<SIGLA>` personal-debit namespace in `FINANCE.LANCAMENTO`.

## Historical backfill (one-shot)

Populate every past month so any competence month shows real data in the UI.
Runs the agent month-by-month from `-StartMonth` to the last closed month:

```powershell
$env:SISJURI_PASSWORD='...'; $env:INGEST_TOKEN='...'
$env:INGEST_URL='https://<vps>/api/ingest'
powershell -ExecutionPolicy Bypass -File C:\temp\sisjuri\backfill.ps1 -StartMonth 2024-01
```

After the catch-up, the daily scheduled task keeps recent months fresh. Verify
a few months landed via the token-protected summary endpoint:

```powershell
$h = @{ Authorization = "Bearer $env:INGEST_TOKEN" }
Invoke-RestMethod -Headers $h "https://<vps>/api/ingest/2024-01/summary" | ConvertTo-Json -Depth 5
```

## Environment / where the secrets live (2026-07-13)

Real secrets are **not** committed. They live in two gitignored files:

- `backend/.env` — full backend config (JWT, Supabase, LegalDesk, INGEST_TOKEN,
  INGEST_URL, SISJURI_DSN/USER). Prod uses `USE_FAKE_REPO=0` → snapshots persist
  to **Supabase** (`sisjuri_snapshots`), not `SNAPSHOT_DIR`.
- `ops/sisjuri-agent/ingest.local.secrets` — the ingest target + token for the
  agent on the RDP box, plus the ready-to-paste session setup.

Ingest endpoint (full): **`http://187.127.29.178:3000/api/ingest`** (the operator
may quote the base `.../:3000/` — always append `/api/ingest`). Token is the
`INGEST_TOKEN`. Verify a landed month with the summary endpoint (§Historical
backfill) using the same token.

Backfill/daily now **fail fast** if `INGEST_URL`/`INGEST_TOKEN` are unset (they no
longer silently produce snapshot-only runs). Pass `-SnapshotOnly` to `backfill.ps1`
if you intentionally want extraction without upload.

## Backend side

`POST /api/ingest` (bearer `INGEST_TOKEN`) stores the snapshot via `SnapshotStore`
(`SNAPSHOT_DIR`). A client whose `provider` is `legaldesk+sisjuri` then has its
institutional expenses served from the DB snapshot (see
`app/closing/provider.py`), augmenting the LegalDesk revenue/billing side.

## Security

- Credentials come only from env vars; never commit them or bake them into the
  task XML. The RGN DB password and the RDP password shared during setup **must
  be rotated**.
- The agent is read-only (`extract.sql` only `SELECT`s).
