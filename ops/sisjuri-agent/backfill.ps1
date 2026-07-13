<#
.SYNOPSIS
  Backfill historical SISJURI snapshots (runs on MBC-LDESK01).
  Loops competence months from -StartMonth through the last CLOSED month
  (the month before the current one), invoking run-agent.ps1 for each so a
  snapshot is extracted and pushed to the RUMO backend.

.NOTES
  - One-shot catch-up. After this, the daily scheduled task keeps recent
    months fresh (see register-task.ps1).
  - Requires the same env as run-agent.ps1: SISJURI_PASSWORD, INGEST_URL,
    INGEST_TOKEN.
  - Read-only against the DB.

.EXAMPLE
  $env:SISJURI_PASSWORD='...'; $env:INGEST_TOKEN='...'
  $env:INGEST_URL='https://<vps>/api/ingest'
  powershell -ExecutionPolicy Bypass -File backfill.ps1 -StartMonth 2024-01
#>
[CmdletBinding()]
param(
  [ValidatePattern('^\d{4}-\d{2}$')][string]$StartMonth = '2024-01',
  # Optional explicit end (inclusive). Defaults to the last fully-closed month.
  [ValidatePattern('^\d{4}-\d{2}$')][string]$EndMonth,
  [int]$SleepSeconds = 3,
  [string]$OutDir = 'C:\temp\sisjuri',
  # Upload target. Default from env; pass -SnapshotOnly to skip upload on purpose.
  [string]$IngestUrl   = $env:INGEST_URL,
  [string]$IngestToken = $env:INGEST_TOKEN,
  [string]$ClientId    = $(if($env:CLIENT_ID){$env:CLIENT_ID}else{'mbc'}),
  [switch]$SnapshotOnly
)

$ErrorActionPreference = 'Stop'
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$agent = Join-Path $scriptDir 'run-agent.ps1'
if (-not (Test-Path $agent)) { throw "run-agent.ps1 not found next to backfill.ps1 ($agent)" }

# Fail fast if we intend to upload but the target/token are missing. Without this
# the loop would silently produce snapshot files that never reach the backend
# (run-agent only uploads when -IngestUrl is present).
if (-not $SnapshotOnly) {
  if (-not $IngestUrl)   { throw "INGEST_URL not set. Set `$env:INGEST_URL / pass -IngestUrl, or pass -SnapshotOnly to intentionally skip upload." }
  if (-not $IngestToken) { throw "INGEST_TOKEN not set. Set `$env:INGEST_TOKEN / pass -IngestToken, or pass -SnapshotOnly." }
  Write-Output "[backfill] uploading each month to $IngestUrl (client '$ClientId')."
} else {
  Write-Output "[backfill] SnapshotOnly: extracting to $OutDir, NOT uploading."
}

# Compute the inclusive end month: default = month before the current one.
if ($EndMonth) {
  $ey = [int]$EndMonth.Substring(0,4); $em = [int]$EndMonth.Substring(5,2)
  $end = Get-Date -Year $ey -Month $em -Day 1
} else {
  $end = (Get-Date -Day 1).AddMonths(-1)
}

$sy = [int]$StartMonth.Substring(0,4); $sm = [int]$StartMonth.Substring(5,2)
$cur = Get-Date -Year $sy -Month $sm -Day 1

$done = 0; $failed = @()
while ($cur -le $end) {
  $am = ('{0:0000}-{1:00}' -f $cur.Year, $cur.Month)
  Write-Output "==== [backfill] $am ===="
  try {
    if ($SnapshotOnly) {
      & $agent -AnoMes $am -OutDir $OutDir
    } else {
      & $agent -AnoMes $am -OutDir $OutDir -IngestUrl $IngestUrl -IngestToken $IngestToken -ClientId $ClientId
    }
    $done++
  } catch {
    Write-Warning "[backfill] $am FAILED: $_"
    $failed += $am
  }
  Start-Sleep -Seconds $SleepSeconds
  $cur = $cur.AddMonths(1)
}

Write-Output "[backfill] complete: $done month(s) pushed."
if ($failed.Count -gt 0) {
  Write-Warning ("[backfill] {0} month(s) failed: {1}" -f $failed.Count, ($failed -join ', '))
}
