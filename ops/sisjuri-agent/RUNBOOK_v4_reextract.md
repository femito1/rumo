# Operator runbook — re-extract to contract **v4** (wider `historico`)

**Why:** `extract.sql` now emits the three `historico` fields at **300 chars** instead of
60/80. Finance writes the arithmetic *into* that text — *"Vale transporte / Calculo: 14
dias x R$ 18,76"* — and the old caps cut it off exactly where the calculation began. That
is why the January `35,52` had to be chased through a hand-exported `.xls` instead of the
snapshot.

**Who runs this:** an operator on **MBC-LDESK01** (there is no route to the box from the
dev machine). Everything below is read-only against Oracle.

**Time:** ~1 minute per month, so ~10 minutes for 2026 plus 2025 if you want it.

---

## 0. Before you start

`git pull` on the box so it has the new `extract.sql`. `run-agent.ps1` self-updates from
`main`, but confirm the SQL really changed:

```powershell
Select-String -Path .\extract.sql -Pattern "extract_version' VALUE 4"
Select-String -Path .\extract.sql -Pattern "DESCHISTORICO,1,300"   # expect 2 hits
Select-String -Path .\extract.sql -Pattern "LANCHISTORICO),1,300"  # expect 1 hit
```

Check what is currently stale (all eight 2026 months should say `v3`):

```
GET <backend>/api/ingest/summary/2026-06     ->  "extract": {"version": 3, "expected": 4, "stale": true}
```

## 1. Re-extract the CLOSED months

```powershell
$env:SISJURI_PASSWORD='...'; $env:INGEST_TOKEN='...'
$env:INGEST_URL='https://<vps>/api/ingest'
powershell -ExecutionPolicy Bypass -File backfill.ps1 -StartMonth 2026-01 -EndMonth 2026-07
```

`backfill.ps1` stops at the last **fully closed** month, so it will not push the current
one — that is intentional.

## 2. Re-extract the OPEN month

```powershell
powershell -ExecutionPolicy Bypass -File run-agent.ps1 -AnoMes 2026-08
```

## 3. Verify — do NOT skip this

**3a. Every month reports v4.** Hit the summary for each and confirm
`"version": 4, "stale": false`. A month still on v3 did not re-extract; re-run it.

**3b. The históricos are actually longer.** The point of the whole exercise. In the
snapshot for any month, a `vale_prof` histórico should now read like
`"Vale transporte\r\n\r\nCalculo: 14 dias x R$ 18,76"` rather than stopping at
`"Vale transporte"`. If they are still short, the box ran an old `extract.sql`.

**3c. ⚠ The reclass accounts have not moved.** This is the one way this change can break
numbers. `despesas_liquido.net_by_account` decides reclassifications by searching the
histórico for markers (`claude`, `software`, `saas`, `licen`, `cloud`), so a **longer**
string can match where the truncated one did not — and money would jump from Material de
Copa (`020.030.0020`) to Informática (`020.040.0010`).

Six rows were sitting at the old 80-char cap on a reclass account. All six are Mercado
Livre copa/limpeza purchases, so **nothing should move**:

| Mês | Valor | Histórico (truncated form) |
|---|---:|---|
| Mar | 202,06 | Mercado Livre - Compra de 100 unidade de bolacha… |
| Mar | 88,99 | Mercado livre- Valor original da compra 383,39… |
| Abr | 132,72 | Mercado Livre - Compra de saleiro e suporte… |
| Abr | 273,11 | Mercado Livre - Compra de papel toalha… |
| Jul | 250,95 | "Mercado Livre - Compora de material de copa… |
| Ago | 142,95 | "Mercado Livre - Compra de material de copa… |

After the re-extract, confirm the June numbers the client validated are unchanged:

* Contencioso Custo equipe **75.424,21** · Econômico **80.536,85** · Arbitragem **54.383,94**
* Contencioso Despesa Institucional **32.564,56** (the workbook types 32.562,84; the
  R$1,72 gap is the bank tariff rateado and is expected — do not "fix" it)
* Institucional Despesas Indiretas **105.932,16**

These are OUR live values, verified 2026-08-03 before the widening. Any movement is caused
by the widening, not by a pre-existing difference.

If any of those move, the widening matched a marker it should not have. Read the new full
histórico for the row that changed and decide deliberately — the guard test
`test_widening_the_historico_must_not_move_copa_to_informatica` pins the intended
behaviour, so run `pytest tests/test_despesas_liquido.py` too.

**3d. Re-run the audits.** They read live snapshots, so they re-verify end to end:

```bash
cd backend
python -m scripts.reconcile_custo_equipe        # expect 0,00 residual in all 18 cells
python -m scripts.audit_vale_composition        # the day-count table + the two typed terms
python -m scripts.build_diferencas_doc          # regenerate the client document
```

## 4. What this may finally answer

The whole reason for v4: with the full text, `35,52` (January, `Base_Resultado` C123) may
turn out to be visible in a histórico that was previously cut off. Check the January
`despesas_desdobramento` and `vale_prof` blocks for any line whose text now mentions it or
a `Calculo:` that produces it.

If it is still absent, that settles it — the number does not exist in SISJURI and only
finance can say where it came from. Either way, update
`docs/DIFERENCAS_ACUMULADO_2026.md` and `PROJECT_STATUS.md` with what the fuller text
showed.

## 5. If something goes wrong

The extract is read-only, so the worst case is a bad snapshot being pushed. Re-running a
month overwrites it, so the fix is always "run that month again". The previous
snapshots are **not** kept, so if you need to compare before/after, save the JSON that
`run-agent.ps1` writes under `C:\temp\sisjuri` before pushing.
