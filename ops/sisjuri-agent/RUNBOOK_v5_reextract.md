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

## 0. FIRST — copy the new `run-agent.ps1` onto the box

**This is the urgent half and it is not optional.** The box self-updates `extract.sql` from
`main` but **nobody updates `run-agent.ps1`**, and the fix spans both files. A v5
`extract.sql` in a pre-v5 wrapper produces JSON with a `~` at every 180-char boundary and
fails to parse — which hits the **daily 06:00 task**, not just manual runs. The
self-update's sanity gate does NOT catch it (v5 still contains `JSON_OBJECT` and
`'despesas_liquido'`).

Per README §1 you MUST enable TLS 1.2 first, and per §2 paste **one command per line, no
backtick line continuations**:

```powershell
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
Invoke-WebRequest -UseBasicParsing "https://raw.githubusercontent.com/femito1/rumo/main/ops/sisjuri-agent/run-agent.ps1" -OutFile C:\temp\sisjuri\run-agent.ps1
Invoke-WebRequest -UseBasicParsing "https://raw.githubusercontent.com/femito1/rumo/main/ops/sisjuri-agent/backfill.ps1" -OutFile C:\temp\sisjuri\backfill.ps1
```

Confirm the guard-strip landed — expect **one** match:

```powershell
Select-String -Path C:\temp\sisjuri\run-agent.ps1 -Pattern 'Length - 2'
```

`extract.sql` needs no copying: `run-agent.ps1` pulls it from `main` on the next run. So it
will still read `VALUE 4` on disk at this point — that is expected, not a problem. After
the first run of step 1 you can confirm it moved:

```powershell
Select-String -Path C:\temp\sisjuri\extract.sql -Pattern 'VALUE 5'
Select-String -Path C:\temp\sisjuri\extract.sql -Pattern 'DBMS_LOB.SUBSTR'
```

Check what is currently stale (all 2026 months should say `v4`):

```
GET <backend>/api/ingest/summary/2026-06   ->  "extract": {"version": 4, "expected": 5, "stale": true}
```

## 1. Re-extract the CLOSED months

```powershell
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$env:SISJURI_PASSWORD = 'RgN@92Kx7'
$env:INGEST_TOKEN = 'OxlcIEMB_PcpmCaxKcEcJwNXmyiYB5F9l3JUnjktfAoKSxor5s6hRJ2Et9R_Hr5s'
$env:INGEST_URL = 'https://rumo-backend.xem1qi.easypanel.host/api/ingest'
powershell -ExecutionPolicy Bypass -File C:\temp\sisjuri\backfill.ps1 -StartMonth 2026-01 -EndMonth 2026-07
```

(`run-agent.ps1` sets TLS 1.2 itself, but the window may also need it for the self-update
if you changed the protocol earlier in the session — setting it costs nothing.)

`backfill.ps1` stops at the last **fully closed** month, so it will not push the current
one — intentional. It prints the resolved range (`[backfill] months 2026-01 .. 2026-07
inclusive.`) — **read that line and count the months it actually pushes.** On 2026-08-03 it
silently pushed only Jan–Jun (loop bounds kept the current time-of-day); fixed, but verify.

## 2. Re-extract the OPEN month

```powershell
powershell -ExecutionPolicy Bypass -File C:\temp\sisjuri\run-agent.ps1 -AnoMes 2026-08
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
parse with a `~` visibly at a boundary, the box's `run-agent.ps1` is pre-v5 — redo step 0
(the `Invoke-WebRequest` copy) and re-run. Save the JSON `run-agent.ps1` writes under `C:\temp\sisjuri` before pushing if
you want a before/after.
