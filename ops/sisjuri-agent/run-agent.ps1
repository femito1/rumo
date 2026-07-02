<#
.SYNOPSIS
  SISJURI closing extraction agent (runs on MBC-LDESK01).
  Runs extract.sql for a competence month, writes a JSON snapshot, and
  optionally POSTs it to the RUMO backend ingest endpoint over HTTPS (TLS 1.2).

.NOTES
  - No Python required; uses the Oracle 11g sqlplus already on the box.
  - Credentials come from ENV or params; never hard-code them in this file.
  - Read-only: extract.sql only SELECTs.

.EXAMPLE
  # dry run (snapshot only, no upload):
  powershell -ExecutionPolicy Bypass -File run-agent.ps1 -AnoMes 2026-02

  # with upload:
  $env:SISJURI_PASSWORD='...'; $env:INGEST_TOKEN='...'
  powershell -ExecutionPolicy Bypass -File run-agent.ps1 -AnoMes 2026-02 -IngestUrl https://<vps>/api/ingest
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][ValidatePattern('^\d{4}-\d{2}$')][string]$AnoMes,
  [string]$SqlplusPath = 'C:\oracle11\app\product\11.2.0\client_1\bin\sqlplus.exe',
  [string]$DbHost      = '172.16.237.9',
  [int]   $DbPort      = 1521,
  [string]$DbService   = 'cdbp01_pdb1.submbc.vcnmbc.oraclevcn.com',
  [string]$DbUser      = $(if($env:SISJURI_USER){$env:SISJURI_USER}else{'RGN'}),
  [string]$DbPassword  = $env:SISJURI_PASSWORD,
  [string]$IngestUrl   = $env:INGEST_URL,
  [string]$IngestToken = $env:INGEST_TOKEN,
  [string]$OutDir      = 'C:\temp\sisjuri'
)

$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# Force Oracle client + console to UTF-8 so accented account names survive.
$env:NLS_LANG = '.AL32UTF8'
[Console]::OutputEncoding = [Text.Encoding]::UTF8

if (-not $DbPassword) { throw "DB password not set. Set `$env:SISJURI_PASSWORD or pass -DbPassword." }

# Derive date bounds from the competence month.
$y = [int]$AnoMes.Substring(0,4); $m = [int]$AnoMes.Substring(5,2)
$dStart = ('{0:0000}-{1:00}-01' -f $y, $m)
$next   = (Get-Date -Year $y -Month $m -Day 1).AddMonths(1)
$dEnd   = ('{0:0000}-{1:00}-01' -f $next.Year, $next.Month)

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$extractSql = Join-Path $scriptDir 'extract.sql'
if (-not (Test-Path $extractSql)) { throw "extract.sql not found next to run-agent.ps1 ($extractSql)" }

# Build a wrapper .sql that CONNECTs (password quoted, inline descriptor) and
# DEFINEs the parameters, then @-includes extract.sql. This mirrors the proven
# paste-safe invocation from docs/SISJURI_DB.md.
$connect = "CONNECT $DbUser/""$DbPassword""@(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=$DbHost)(PORT=$DbPort))(CONNECT_DATA=(SERVICE_NAME=$DbService)))"
$wrapper = @(
  'SET DEFINE OFF',
  $connect,
  'SET DEFINE ON',
  "DEFINE ANO_MES=$AnoMes",
  "DEFINE D_START=$dStart",
  "DEFINE D_END=$dEnd",
  "@`"$extractSql`""
) -join "`n"
$wrapperPath = Join-Path $OutDir 'run.sql'
Set-Content -Path $wrapperPath -Value $wrapper -Encoding ASCII

Write-Output "[agent] extracting $AnoMes ($dStart .. $dEnd) ..."
$raw = & $SqlplusPath -S /nolog "@$wrapperPath" 2>&1 | Out-String

# sqlplus may print a leading/trailing blank line; isolate the JSON object.
$startIdx = $raw.IndexOf('{')
$endIdx   = $raw.LastIndexOf('}')
if ($startIdx -lt 0 -or $endIdx -le $startIdx) {
  $errPath = Join-Path $OutDir "error_$AnoMes.txt"
  Set-Content -Path $errPath -Value $raw -Encoding UTF8
  throw "No JSON found in sqlplus output. Raw saved to $errPath"
}
$json = $raw.Substring($startIdx, $endIdx - $startIdx + 1)

# Validate it parses.
try { $obj = $json | ConvertFrom-Json } catch { throw "sqlplus returned invalid JSON: $_" }

$snapshot = Join-Path $OutDir "closing_$AnoMes.json"
Set-Content -Path $snapshot -Value $json -Encoding UTF8
Write-Output "[agent] snapshot written: $snapshot ($([math]::Round(($json.Length/1kb),1)) KB)"
Write-Output ("[agent] revenue.recebimento_bruto = {0}" -f $obj.revenue.recebimento_bruto)
Write-Output ("[agent] despesas_conta rows = {0}" -f ($obj.despesas_conta | Measure-Object).Count)

if ($IngestUrl) {
  if (-not $IngestToken) { throw "IngestUrl set but INGEST_TOKEN missing." }
  Write-Output "[agent] uploading to $IngestUrl ..."
  $headers = @{ Authorization = "Bearer $IngestToken"; 'Content-Type' = 'application/json' }
  $resp = Invoke-WebRequest -UseBasicParsing -Uri $IngestUrl -Method POST -Headers $headers -Body $json -TimeoutSec 60
  Write-Output "[agent] ingest response: $($resp.StatusCode)"
} else {
  Write-Output "[agent] no -IngestUrl; snapshot-only run (no upload)."
}
Write-Output "[agent] done."
