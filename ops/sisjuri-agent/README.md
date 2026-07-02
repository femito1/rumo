# SISJURI extraction agent (runs on MBC-LDESK01)

Pulls the monthly closing data out of the private-VCN Oracle DB and ships it to
the RUMO backend. This is **egress Option A** from `docs/SISJURI_QUERIES.md` §10:
the server (the only host with a route to the DB) POSTs outbound over HTTPS, so
no inbound firewall rule or VPN is needed.

## Files

- `extract.sql` — one read-only query emitting the whole closing extract as a
  single JSON document (Oracle 19c `JSON_OBJECT`/`JSON_ARRAYAGG`). Parameterised
  by `&ANO_MES` / `&D_START` / `&D_END`.
- `run-agent.ps1` — PowerShell wrapper: connects via the existing `sqlplus`,
  runs `extract.sql`, validates the JSON, writes a snapshot, optionally uploads.
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
