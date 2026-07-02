<#
.SYNOPSIS
  Registers a daily Windows Scheduled Task that runs the SISJURI agent for the
  most-recently-closed competence month and uploads the snapshot to the VPS.

.DESCRIPTION
  Run ONCE (elevated) on MBC-LDESK01 to install the task. Secrets are read from
  MACHINE-level environment variables so they are not baked into the task XML:
    - SISJURI_PASSWORD : Oracle RGN password
    - INGEST_TOKEN     : shared bearer token for POST /api/ingest
    - INGEST_URL       : e.g. https://<vps>/api/ingest
  Set them first (elevated), e.g.:
    [Environment]::SetEnvironmentVariable('SISJURI_PASSWORD','...', 'Machine')
    [Environment]::SetEnvironmentVariable('INGEST_TOKEN','...', 'Machine')
    [Environment]::SetEnvironmentVariable('INGEST_URL','https://.../api/ingest','Machine')

.NOTES
  The agent computes the previous month at run time (see -PrevMonth handling in
  run-agent.ps1 invocation below), so the task needs no date parameter.
#>
[CmdletBinding()]
param(
  [string]$TaskName  = 'RUMO-SISJURI-Agent',
  [string]$AgentDir  = 'C:\temp\sisjuri',
  [string]$RunAt     = '06:00'   # daily, local time
)

$ErrorActionPreference = 'Stop'

$runAgent = Join-Path $AgentDir 'run-agent.ps1'
if (-not (Test-Path $runAgent)) { throw "run-agent.ps1 not found at $runAgent" }

# The task computes last-closed month at runtime and passes it to the agent.
# Single-line -Command; the agent reads secrets from Machine env vars.
$command = "`$m=(Get-Date).AddMonths(-1); `$am=('{0:0000}-{1:00}' -f `$m.Year,`$m.Month); & '$runAgent' -AnoMes `$am -IngestUrl `$env:INGEST_URL"

$action = New-ScheduledTaskAction -Execute 'powershell.exe' `
  -Argument "-NoProfile -ExecutionPolicy Bypass -Command `"$command`""

$trigger = New-ScheduledTaskTrigger -Daily -At $RunAt

# Run as SYSTEM so it works with no interactive login; highest privileges for the
# Oracle client. Machine env vars are visible to SYSTEM.
$principal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
$settings  = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd `
  -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
  -Principal $principal -Settings $settings -Force | Out-Null

Write-Output "Registered scheduled task '$TaskName' (daily at $RunAt, runs as SYSTEM)."
Write-Output "Test it now with:  Start-ScheduledTask -TaskName '$TaskName'"
Write-Output "Inspect result:    Get-ScheduledTaskInfo -TaskName '$TaskName'"
