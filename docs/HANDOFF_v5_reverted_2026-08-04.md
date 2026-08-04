# Handoff — the v5 chunk-guard fix was WRONG and is reverted (2026-08-04)

> Read this before touching `extract.sql`, `run-agent.ps1`, or the whitespace-glue defect.
> It is the record of a fix that passed its local test, shipped, and corrupted the live
> store — and of exactly why, so the next attempt does not repeat it.

## What the defect actually is (still true, still unfixed)

The agent drops a space ~6 times per month, in every 2026 month (62 total): `"Despesas
Gerais"` arrives as `"DespesasGerais"`. It is **transport, not SISJURI** — the same sigla's
home grupo comes back spelled differently in months extracted 40 seconds apart, and master
data cannot vary by month. It is **money-neutral** (repairing every glued string and
re-running `assemble_dre_sections` across all months moves 0 values, 0 reclassifications);
its only bite is that `workbook_layouts.section_for` is an exact dict lookup, so a glued
`nome_conta_pai` could open a duplicate expense family. `match_area` already guards the one
place that would double-count. **This is a cosmetic defect and it is fine to leave it.**

## What I shipped, and the two things that were wrong

"v5" wrapped every emitted chunk in `~` guards in `extract.sql` and stripped them in
`run-agent.ps1`. It had a local round-trip test that **passed** — and was wrong on both the
premise and the mechanism:

1. **False premise.** I blamed `SET TRIMSPACE ON` trimming a boundary space. This box is
   Oracle **11g**, and its sqlplus rejects that SET outright — the run log shows
   `SP2-0158: unknown SET option "TRIMSPACE"`. It was never active. So whatever eats the
   space, it is not TRIMSPACE, and I never actually identified the real mechanism.

2. **The local test modelled the wrong thing.** `test_extract_chunk_transport.py` emitted
   clean 180-char chunks and reassembled them. Real sqlplus **wraps a long `DBMS_OUTPUT`
   line at `LINESIZE`**, so one guarded chunk prints as several physical lines. My strip
   removed a `~` only when a line had one at *both* ends — a wrapped chunk's leading `~`
   had no trailing partner, so it survived *into the JSON*: `"r~ecebimento_rows"`. The test
   never wrapped, so it never saw this. **A green test on a model the box does not match is
   worse than no test — it gave false confidence.**

## The damage, and the current state

The v4→v5 backfill ran on the box before I caught it. Result in the live store (checked
2026-08-04): **Jan, Mar, Abr, Mai, Jun, Jul are corrupted v5** — each has exactly 2 leaked
`~`, one always breaking the `recebimento_rows` key (`"r~ecebimento_rows"`), one in a text
value. **Feb and Aug are clean v4** (Feb's v5 attempt failed to parse and was rejected, so
the prior v4 survived; Aug had not been re-run).

**Nothing is on fire.** The corrupted months still assemble correctly — June's
client-validated per-área cells (75.424,21 / 80.536,85 / 54.383,94), recebimento, custo and
despesas are all intact. The leaked `~` sits in a diagnostic row-count key and two text
fragments that no money path reads. The live site is not showing wrong numbers.

Reverted in the repo (this commit): `extract.sql`, `run-agent.ps1`, and
`CURRENT_EXTRACT_VERSION` are back to **v4**; the two v5 tests and `RUNBOOK_v5_reextract.md`
are deleted. What was KEPT because it is independent of v5 and correct: the refreshed v4
fixtures, the 14 explained assertion updates, the widened vale day-count test, the promoted
per-área custo / desp-inst identity tests, and `scripts/dump_fixture.py`.

## Recovery — clean the store when convenient (NOT urgent)

`main` is v4 again, so a plain re-run overwrites every month with clean v4 from the DB. The
box self-updates `extract.sql` from `main`, so no file copy is needed this time — but per
the README rules, TLS 1.2 first and one command per line:

```powershell
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$env:SISJURI_PASSWORD = 'RgN@92Kx7'
$env:INGEST_TOKEN = 'OxlcIEMB_PcpmCaxKcEcJwNXmyiYB5F9l3JUnjktfAoKSxor5s6hRJ2Et9R_Hr5s'
$env:INGEST_URL = 'https://rumo-backend.xem1qi.easypanel.host/api/ingest'
powershell -ExecutionPolicy Bypass -File C:\temp\sisjuri\backfill.ps1 -StartMonth 2026-01 -EndMonth 2026-07
powershell -ExecutionPolicy Bypass -File C:\temp\sisjuri\run-agent.ps1 -AnoMes 2026-08
```

⚠ Also re-copy `run-agent.ps1` from `main` first if the box still has the v5 wrapper on
disk (the one with the guard-strip) — the reverted v4 `extract.sql` emits no guards, so the
v4 wrapper is what you want:

```powershell
Invoke-WebRequest -UseBasicParsing "https://raw.githubusercontent.com/femito1/rumo/main/ops/sisjuri-agent/run-agent.ps1" -OutFile C:\temp\sisjuri\run-agent.ps1
```

Verify no month has a `~` in a key afterward: `GET /api/ingest/2026-06/summary` should show
`version: 4`, and the June cells above must be unchanged.

## If anyone re-attempts the space fix

Do NOT start from a local model. First probe how THIS box's sqlplus wraps a long
`DBMS_OUTPUT.PUT_LINE` at `LINESIZE 200` — emit a known 500-char line with sentinels at
positions 179/180/181/199/200/201 and read back exactly where it breaks and whether it
trims. Only then design a reassembly, and validate it against real box output pasted back,
never against a clean-chunk simulation. The cheaper path may be to raise `LINESIZE` and
drop the chunking entirely, or to base64 the CLOB so whitespace cannot be touched — both
sidestep the wrapping question instead of guessing at it.
