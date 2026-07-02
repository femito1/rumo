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
  [string]$OutDir = 'C:\temp\sisjuri'
)

$ErrorActionPreference = 'Stop'
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$agent = Join-Path $scriptDir 'run-agent.ps1'
if (-not (Test-Path $agent)) { throw "run-agent.ps1 not found next to backfill.ps1 ($agent)" }

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
    & $agent -AnoMes $am -OutDir $OutDir
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
