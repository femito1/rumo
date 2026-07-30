<#
.SYNOPSIS
  One-shot operator script for the 2026-07-29 follow-ups. Run on MBC-LDESK01.

.DESCRIPTION
  Everything the box needs after the §5.1–§5.5 deploy, in the right order:

    1. Refresh the agent files from `main` (register-task.ps1 changed today and
       does NOT self-update the way extract.sql does).
    2. Extract + push the CURRENT (open) month — prod has no snapshot for it at
       all, so the new "mês em aberto" partial view renders empty until this runs.
    3. Re-extract Jan → last-closed month. Jan–May still serve extract v1
       (pre-f5fe22c, i.e. the vale_adm double count and the Assinatura reclass are
       missing), and this also replaces June's hand-patched snapshot with genuine
       extract output — a free check on the numbers the client validated.
    4. Re-register the daily task so it extracts the last-closed month AND the
       current one (it only ever did AddMonths(-1)).
    5. Verify every month via the token-protected summary endpoint and print a
       table: any row with stale=True still needs attention.
    6. Run probe_vale_twin_allmonths.sql and save the output for review.

  SECRETS ARE NEVER PASTED OR PRINTED. They are read from the box's own
  environment (Process → User → Machine scope). Anything missing is asked for
  once via a masked prompt and then persisted at User scope so the daily task
  inherits it.

  Safe to re-run: every step is idempotent (the task register is -Force, and
  snapshots upsert by (client_id, ano_mes)).

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File C:\temp\sisjuri\run-followups.ps1
#>
[CmdletBinding()]
param(
  [string]$AgentDir   = 'C:\temp\sisjuri',
  [string]$StartMonth = '2026-01',
  [string]$Branch     = 'main',
  # Skip flags, for re-runs where one step already succeeded.
  [switch]$SkipFetch,
  [switch]$SkipOpenMonth,
  [switch]$SkipBackfill,
  [switch]$SkipTask,
  [switch]$SkipProbe
)

$ErrorActionPreference = 'Stop'
$RAW = "https://raw.githubusercontent.com/femito1/rumo/$Branch/ops/sisjuri-agent"

function Section($n, $t) { Write-Output ""; Write-Output ("=" * 72); Write-Output "  STEP $n — $t"; Write-Output ("=" * 72) }

# Windows Server 2012 defaults to TLS 1.0, which GitHub refuses. Without this
# every Invoke-WebRequest below dies with "Could not create SSL/TLS secure channel".
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

if (-not (Test-Path $AgentDir)) { New-Item -ItemType Directory -Path $AgentDir -Force | Out-Null }

# ── Secrets: resolve from the box, prompt only for what is genuinely absent ────
function Resolve-Secret($name, $prompt, $persist) {
  $v = [Environment]::GetEnvironmentVariable($name, 'Process')
  if (-not $v) { $v = [Environment]::GetEnvironmentVariable($name, 'User') }
  if (-not $v) { $v = [Environment]::GetEnvironmentVariable($name, 'Machine') }
  if (-not $v) {
    Write-Output ""
    Write-Output "  $name is not set on this machine."
    $sec = Read-Host -Prompt "  $prompt" -AsSecureString
    $v = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
           [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec))
    if (-not $v) { throw "$name is required." }
    if ($persist) {
      [Environment]::SetEnvironmentVariable($name, $v, 'User')
      Write-Output "  -> saved at User scope (the daily task will inherit it)."
    }
  }
  Set-Item -Path "env:$name" -Value $v
  return $v
}

Write-Output "RUMO SISJURI follow-ups — $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
Write-Output "agent dir: $AgentDir   source: $Branch"

$ingestUrl = [Environment]::GetEnvironmentVariable('INGEST_URL', 'Process')
if (-not $ingestUrl) { $ingestUrl = [Environment]::GetEnvironmentVariable('INGEST_URL', 'User') }
if (-not $ingestUrl) { $ingestUrl = [Environment]::GetEnvironmentVariable('INGEST_URL', 'Machine') }
if (-not $ingestUrl) {
  # Not a secret — the public backend endpoint. Set it so register-task.ps1 (which
  # validates the target scope) and the agent both find it.
  $ingestUrl = 'https://rumo-backend.xem1qi.easypanel.host/api/ingest'
  [Environment]::SetEnvironmentVariable('INGEST_URL', $ingestUrl, 'User')
  Write-Output "INGEST_URL was unset; defaulted to $ingestUrl (saved at User scope)."
}
$env:INGEST_URL = $ingestUrl
if (-not $env:CLIENT_ID) { $env:CLIENT_ID = 'mbc' }

$null = Resolve-Secret 'SISJURI_PASSWORD' 'Oracle RGN password' $true
$null = Resolve-Secret 'INGEST_TOKEN'     'Backend INGEST_TOKEN' $true

# ── 1. Refresh agent files from main ──────────────────────────────────────────
if (-not $SkipFetch) {
  Section 1 'Refresh agent files from main'
  foreach ($f in @('run-agent.ps1','register-task.ps1','backfill.ps1','extract.sql','probe_vale_twin_allmonths.sql')) {
    $dest = Join-Path $AgentDir $f
    try {
      Invoke-WebRequest -UseBasicParsing -Uri "$RAW/$f" -OutFile "$dest.new" -TimeoutSec 60
      $len = (Get-Item "$dest.new").Length
      if ($len -lt 200) { throw "downloaded $f is only $len bytes" }
      Move-Item "$dest.new" $dest -Force
      Write-Output ("  ok  {0,-34} {1,7:N0} bytes" -f $f, $len)
    } catch {
      Remove-Item "$dest.new" -ErrorAction SilentlyContinue
      if (Test-Path $dest) { Write-Warning "  could not refresh $f ($($_.Exception.Message)); keeping local copy." }
      else { throw "could not download $f and no local copy exists: $($_.Exception.Message)" }
    }
  }
}

$agent = Join-Path $AgentDir 'run-agent.ps1'

# Month arithmetic: open = current month, lastClosed = the one before it.
$now        = Get-Date
$openMonth  = '{0:0000}-{1:00}' -f $now.Year, $now.Month
$prev       = (Get-Date -Year $now.Year -Month $now.Month -Day 1).AddMonths(-1)
$lastClosed = '{0:0000}-{1:00}' -f $prev.Year, $prev.Month

# ── 2. The open month (unblocks the new partial view) ─────────────────────────
if (-not $SkipOpenMonth) {
  Section 2 "Extract + push the OPEN month ($openMonth)"
  Write-Output "  Until this lands, the 'mes em aberto' view has nothing to show."
  & $agent -AnoMes $openMonth -IngestUrl $env:INGEST_URL
}

# ── 3. Re-extract the closed months (Jan → last closed) ──────────────────────
if (-not $SkipBackfill) {
  Section 3 "Re-extract $StartMonth .. $lastClosed (clears extract v1)"
  Write-Output "  NOTE: this also replaces June's HAND-PATCHED snapshot with real"
  Write-Output "  extract output. June's numbers were validated by the client, so if"
  Write-Output "  the June figures move at all, report it before anyone reuses them."
  & (Join-Path $AgentDir 'backfill.ps1') -StartMonth $StartMonth -EndMonth $lastClosed -OutDir $AgentDir
}

# ── 4. Re-register the daily task (now two months per run) ───────────────────
if (-not $SkipTask) {
  Section 4 'Re-register the daily task (last-closed AND current month)'
  & (Join-Path $AgentDir 'register-task.ps1') -AgentDir $AgentDir
  $task = Get-ScheduledTask | Where-Object { $_.TaskName -like '*SISJURI*' } | Select-Object -First 1
  if ($task) {
    $args_ = $task.Actions[0].Arguments
    Write-Output ""
    Write-Output "  task: $($task.TaskName)"
    if ($args_ -match 'AddMonths\(-1\),\(Get-Date\)') {
      Write-Output "  ok  two-month command line is installed."
    } else {
      Write-Warning "  the task does NOT look like the two-month version. Arguments:"
      Write-Output "  $args_"
    }
  } else {
    Write-Warning "  no scheduled task matching *SISJURI* found — check register-task output above."
  }
}

# ── 5. Verify every month via the summary endpoint ───────────────────────────
Section 5 'Verify snapshots (stale=True means still on the old extract)'
$base = $env:INGEST_URL -replace '/api/ingest$', ''
$hdr  = @{ Authorization = "Bearer $($env:INGEST_TOKEN)" }
$rows = @()
$m = Get-Date -Year ([int]$StartMonth.Substring(0,4)) -Month ([int]$StartMonth.Substring(5,2)) -Day 1
$stop = Get-Date -Year $now.Year -Month $now.Month -Day 1
while ($m -le $stop) {
  $am = '{0:0000}-{1:00}' -f $m.Year, $m.Month
  try {
    $r = Invoke-RestMethod -Headers $hdr -Uri "$base/api/ingest/$am/summary" -TimeoutSec 45
    $rows += New-Object PSObject -Property @{
      Month = $am; Version = $r.extract.version; Expected = $r.extract.expected
      Stale = $r.extract.stale; Generated = $r.meta.generated_at
    }
  } catch {
    $rows += New-Object PSObject -Property @{
      Month = $am; Version = '-'; Expected = '-'; Stale = 'ERROR'; Generated = $_.Exception.Message
    }
  }
  $m = $m.AddMonths(1)
}
$rows | Format-Table Month, Version, Expected, Stale, Generated -AutoSize
$bad = @($rows | Where-Object { "$($_.Stale)" -ne 'False' })
if ($bad.Count -eq 0) { Write-Output "  ok  every month is on the current extract contract." }
else { Write-Warning ("  {0} month(s) still need attention: {1}" -f $bad.Count, (($bad | ForEach-Object { $_.Month }) -join ', ')) }

# ── 6. Vale twin probe (read-only diagnostic) ────────────────────────────────
if (-not $SkipProbe) {
  Section 6 'probe_vale_twin_allmonths.sql (read-only)'
  $probe = Join-Path $AgentDir 'probe_vale_twin_allmonths.sql'
  $qs    = Join-Path $AgentDir 'q_followups.sql'
  $out   = Join-Path $AgentDir 'out_vale_twin.txt'
  $conn  = 'CONNECT RGN/"' + $env:SISJURI_PASSWORD + '"@(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=172.16.237.9)(PORT=1521))(CONNECT_DATA=(SERVICE_NAME=cdbp01_pdb1.submbc.vcnmbc.oraclevcn.com)))'
  Set-Content -Path $qs -Encoding ASCII -Value ($conn + "`r`n" + (Get-Content $probe -Raw))
  $sqlplus = 'C:\oracle11\app\product\11.2.0\client_1\bin\sqlplus.exe'
  if (Test-Path $sqlplus) {
    # try/finally: $qs embeds the DB password, so it must be deleted even if
    # sqlplus throws (a bare Remove-Item after the call would leak it on failure).
    try   { & $sqlplus -S /nolog "@$qs" *>&1 | Tee-Object $out }
    finally { Remove-Item $qs -Force -ErrorAction SilentlyContinue }
    Write-Output ""
    Write-Output "  saved to $out"
    Write-Output "  Block C should match the workbook's typed Vale-ADM:"
    Write-Output "    Jan 1.127,96 | Fev 1.351,88 | Mar 3.983,22 | Abr 3.421,36 | Mai 3.326,94 | Jun 1.333,12"
    Write-Output "  A month that does NOT tie is a question for Renata, not a formula to guess."
  } else {
    Remove-Item $qs -Force -ErrorAction SilentlyContinue
    Write-Warning "  sqlplus not found at $sqlplus — skipped."
  }
}

Write-Output ""
Write-Output ("=" * 72)
Write-Output "  DONE. Paste the STEP 5 table (and STEP 6 output) back for review."
Write-Output ("=" * 72)
