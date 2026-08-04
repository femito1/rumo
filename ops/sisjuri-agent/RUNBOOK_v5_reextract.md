# Operator runbook — re-extract to contract **v5** (chunk-guard, no lost spaces)

> ⏳ **DEFERRED, not urgent (decided 2026-08-04).** The fix is in `main` and the code
> expects v5, so every 2026 month reads `stale: true` until this runs. That is fine: the
> bug it fixes **moves no money** (verified — repairing every corrupted string across all
> eight months changes 0 values), so there is no rush. Run this the next time a re-extract
> happens anyway, or whenever convenient. Until then the `stale` flag is doing its job.
>
> ⚠ The daily 06:00 task self-updates `extract.sql` from `main`, so the OPEN month
> (August) will quietly re-extract on v5 by itself. Expect a mixed store — August on v5,
> the closed months still on v4 — and do NOT read that as "fixed everywhere".

**Why:** before v5, `extract.sql` emitted the JSON in 180-char chunks and sqlplus trimmed a
blank sitting at a chunk edge (`SET TRIMSPACE ON`). Because `run-agent.ps1` reassembles by
deleting the line breaks, a trimmed edge space **glued two words together** — `"Despesas
Gerais"` arriving as `"DespesasGerais"`, ~6 times per month in every month of 2026 (62
across the eight). v5 wraps each chunk in `~` guards so the trim can only ever eat a guard,
which `run-agent.ps1` then strips. Text fidelity only — no field changes meaning.

**Who runs this:** an operator on **MBC-LDESK01** (there is no route to the box from the
dev machine). Everything below is read-only against Oracle.

**Time:** ~1 minute per month, so ~10 minutes for 2026.

---

## 0. Before you start

`git pull` on the box so it has the new `extract.sql`. `run-agent.ps1` self-updates from
`main`, but confirm the SQL and the reassembly really changed:

```powershell
Select-String -Path .\extract.sql   -Pattern "extract_version' VALUE 5"
Select-String -Path .\extract.sql   -Pattern "'~' \|\| DBMS_LOB.SUBSTR"       # expect 1 hit
Select-String -Path .\run-agent.ps1 -Pattern "Substring\(1, \`$t.Length - 2\)" # expect 1 hit
```

If `run-agent.ps1` on the box does NOT have the guard-strip, STOP — a v5 `extract.sql` with
a pre-v5 `run-agent.ps1` produces JSON with a `~` at every 180-char boundary and it will
fail to parse. Both must be from the same commit. (The self-update pulls `extract.sql` only,
not `run-agent.ps1`, so `git pull` the script too.)

Check what is currently stale (all 2026 months should say `v4`):

```
GET <backend>/api/ingest/summary/2026-06   ->  "extract": {"version": 4, "expected": 5, "stale": true}
```

## 1. Re-extract the CLOSED months

```powershell
$env:SISJURI_PASSWORD = 'RgN@92Kx7'
$env:INGEST_TOKEN     = 'OxlcIEMB_PcpmCaxKcEcJwNXmyiYB5F9l3JUnjktfAoKSxor5s6hRJ2Et9R_Hr5s'
$env:INGEST_URL       = 'https://rumo-backend.xem1qi.easypanel.host/api/ingest'
powershell -ExecutionPolicy Bypass -File backfill.ps1 -StartMonth 2026-01 -EndMonth 2026-07
```

`backfill.ps1` stops at the last **fully closed** month, so it will not push the current
one — intentional. It prints the resolved range (`[backfill] months 2026-01 .. 2026-07
inclusive.`) — **read that line and count the months it actually pushes.** On 2026-08-03 it
silently pushed only Jan–Jun (loop bounds kept the current time-of-day); fixed, but verify.

## 2. Re-extract the OPEN month

```powershell
powershell -ExecutionPolicy Bypass -File run-agent.ps1 -AnoMes 2026-08
```

## 3. Verify — do NOT skip this

**3a. Every month reports v5.** Hit the summary for each and confirm
`"version": 5, "stale": false`. A month still on v4 did not re-extract; re-run it.

**3b. The spaces are back.** This is the whole point. In any snapshot, the SISJURI grupo
should read `"Equipe Direito Econômico"` (with both spaces), and no account name should be
glued. The dev-side tests turn GREEN automatically once these fixtures are refreshed — see
step 4.

**3c. ⚠ No number moved.** The fix only restores spaces, so nothing should change. Confirm
the June cells the client validated are unchanged:

* Contencioso Custo equipe **75.424,21** · Econômico **80.536,85** · Arbitragem **54.383,94**
* Institucional Despesas Indiretas **105.932,16**

Any movement means a restored space changed a lookup (a reclass marker, a `section_for`
family). Read the row that changed and decide deliberately.

**3d. Re-run the audits.** They read live snapshots, so they re-verify end to end:

```bash
cd backend
python -m scripts.reconcile_custo_equipe        # expect 0,00 residual in all 18 cells
python -m scripts.build_diferencas_doc          # regenerate the client document (should not move)
```

## 4. On the dev side, after the operator confirms v5

Refresh the committed fixtures from the now-clean store and let the guard tests flip:

```bash
cd backend
python -m scripts.dump_fixture --all-2026
pytest tests/test_snapshot_text_integrity.py    # the two xfail tests must now XPASS
```

When they xpass, remove the `xfail` markers and the `KNOWN_GLUED_UNTIL_V5` list in
`tests/test_snapshot_text_integrity.py` — the invariant is then enforced going forward.
Update `PROJECT_STATUS.md`: the v5 re-extract moved from *pending* to *done*.

## 5. If something goes wrong

The extract is read-only, so the worst case is a bad snapshot being pushed. Re-running a
month overwrites it, so the fix is always "run that month again". If the JSON fails to
parse with a `~` visibly at a boundary, the box's `run-agent.ps1` is pre-v5 — `git pull`
and re-run. Save the JSON `run-agent.ps1` writes under `C:\temp\sisjuri` before pushing if
you want a before/after.
