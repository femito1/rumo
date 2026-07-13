<#
.SYNOPSIS
  Registers a daily Windows Scheduled Task that runs the SISJURI agent for the
  most-recently-closed competence month and uploads the snapshot to the VPS.

.DESCRIPTION
  Two modes, chosen by which account can install/run the task:

  1) -RunAsUser (DEFAULT): run as the CURRENT interactive user (e.g. bia4u).
     No admin required. The task inherits that user's USER-level env vars, so
     set these once (User scope) before running the agent:
       [Environment]::SetEnvironmentVariable('SISJURI_PASSWORD','...','User')
       [Environment]::SetEnvironmentVariable('INGEST_TOKEN','...','User')
       [Environment]::SetEnvironmentVariable('INGEST_URL','https://.../api/ingest','User')
     To run "whether logged on or not", pass -StorePassword; you'll be prompted
     for the account password (stored by Task Scheduler, not by this script).

  2) -AsSystem: run as SYSTEM (needs an elevated/admin install). Secrets must be
     MACHINE-level env vars in that case.

.NOTES
  The task computes last-closed month at runtime; no date parameter needed.
#>
[CmdletBinding()]
param(
  [string]$TaskName  = 'RUMO-SISJURI-Agent',
  [string]$AgentDir  = 'C:\temp\sisjuri',
  [string]$RunAt     = '06:00',   # daily, local time
  [switch]$AsSystem,              # run as SYSTEM (needs admin + Machine env)
  [switch]$StorePassword          # run whether logged on or not (prompts for pw)
)

$ErrorActionPreference = 'Stop'

$runAgent = Join-Path $AgentDir 'run-agent.ps1'
if (-not (Test-Path $runAgent)) { throw "run-agent.ps1 not found at $runAgent" }

# Validate the upload target is configured for the scope the task will run under
# (SYSTEM -> Machine env; interactive/stored -> the resolved env below). Without a
# reachable INGEST_URL the daily task would extract a snapshot but never upload it.
$envScope = if ($AsSystem) { 'Machine' } else { 'User' }
$ingestUrl = [Environment]::GetEnvironmentVariable('INGEST_URL', $envScope)
if (-not $ingestUrl) { $ingestUrl = $env:INGEST_URL }
if (-not $ingestUrl) {
  throw "INGEST_URL is not set in $envScope scope (nor the current session). Set it before registering, e.g.: [Environment]::SetEnvironmentVariable('INGEST_URL','https://<vps>/api/ingest','$envScope')  — otherwise the daily task extracts but never uploads."
}

# The task computes last-closed month at runtime and passes it to the agent.
# We pass -IngestUrl EXPLICITLY (baked from the validated value) so the upload
# never silently depends on the task account's env scope; the token/client id are
# still read from env by run-agent.ps1 at run time (they must exist in $envScope).
$command = "`$m=(Get-Date).AddMonths(-1); `$am=('{0:0000}-{1:00}' -f `$m.Year,`$m.Month); & '$runAgent' -AnoMes `$am -IngestUrl '$ingestUrl'"

$action = New-ScheduledTaskAction -Execute 'powershell.exe' `
  -Argument "-NoProfile -ExecutionPolicy Bypass -Command `"$command`""
$trigger  = New-ScheduledTaskTrigger -Daily -At $RunAt
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd `
  -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

if ($AsSystem) {
  # SYSTEM: no interactive login needed; requires elevated install + Machine env.
  $principal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
  Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
    -Principal $principal -Settings $settings -Force | Out-Null
  Write-Output "Registered '$TaskName' (daily $RunAt, runs as SYSTEM, Machine env)."
}
elseif ($StorePassword) {
  # Run whether logged on or not: Task Scheduler stores the account password.
  $user = "$env:USERDOMAIN\$env:USERNAME"
  $cred = Get-Credential -UserName $user -Message "Windows password for $user (stored by Task Scheduler so the task runs when logged off)"
  Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
    -Settings $settings -User $cred.UserName `
    -Password $cred.GetNetworkCredential().Password -RunLevel Limited -Force | Out-Null
  Write-Output "Registered '$TaskName' (daily $RunAt, runs as $user whether logged on or not)."
}
else {
  # Run only when the current user is logged on (no stored password).
  $principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited
  Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
    -Principal $principal -Settings $settings -Force | Out-Null
  Write-Output "Registered '$TaskName' (daily $RunAt, runs as $env:USERNAME only while logged on)."
}

Write-Output "Test it now with:  Start-ScheduledTask -TaskName '$TaskName'"
Write-Output "Inspect result:    Get-ScheduledTaskInfo -TaskName '$TaskName'"
