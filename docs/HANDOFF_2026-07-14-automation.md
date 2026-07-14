# HANDOFF — 2026-07-14 (evening): despesas live, backfill validated, DL/convênio + Nacional/Moedas automated

> **Read first, in order:** `PROJECT_STATUS.md` §0 (client-confirmed rules — DO NOT
> re-ask), `docs/SISJURI_DB.md` §"Known account facts — CHECK THIS BEFORE PROBING",
> and the recalled memories: `workbook-uses-liquido-not-bruto`,
> `transitoria-desdobramento-mechanism`, `dl-extras-bonus-rules`,
> `daily-job-selfupdate-and-backfill-scope`, `multimonth-despesas-validation`,
> `easypanel-redeploy`.
>
> **Product goal:** fully replicate the MBC closing workbook from LegalDesk + SISJURI
> with NO monthly manual input, EXCEPT the Orçamento (client fills the ORÇAMENTO tab).
> The `Fechamento MBC 05.2026.xlsx` workbook is the source of truth; every displayed
> number must tie to it (hard rule: blank a Realizado cell that diverges > R$1,00).

---

## STATE: ~95% automated *in code* for May. May DRE ties end-to-end from the LIVE
## snapshot; Nacional/Moedas + convênio-extra already live. Everything committed +
## pushed to `main`, backend **228 tests**, ruff/mypy/tsc clean, prod live.

> **⚠ CORRECTION (independent validation, 2026-07-14 end of day).** Two things in the
> sections below are now STALE — read this first:
> 1. **The "one file-pull bottleneck" below is ALREADY RESOLVED.** A re-run after this
>    doc was written populated `faturas_moeda` (45–59 rows/mo), `convenio_extra_dl`
>    (DC/RB/EHF) and `bonus_equipe_030` (Feb 7.009,84) across all live snapshots.
>    Nacional/Moedas tie EXACTLY live (708.659,18 + 11.328,87 = 719.988,05 sacred).
> 2. **A NEW bottleneck replaced it.** The POINT 17 fix (commit `a0537b4`, 16:55)
>    repointed the `150.%` bonus block to `FINANCE.LANCAMENTO` + sócio exclusion —
>    but it landed AFTER the last re-run. So in the live snapshots RIGHT NOW:
>    `bonus_equipe`(150.*), `dl_excedente_socios`, `dl_excedente_mv` are all **None**.
>    The code + 17 tests pass, but Feb's 101.705,84 bonus and the sócio split do NOT
>    render in prod until **another re-run of the corrected `extract.sql`**. "POINT
>    17 done" is true in code, not yet live.
>
> Net: run the recipe below ONE more time (with the current `extract.sql`) and the
> POINT 17 blocks go live. Everything else validated green.

---

## ⭐ DO THIS FIRST — re-run the corrected extract (5 min on the RDP box)

The self-update fix for the daily job (commit 60731b1) lives INSIDE `run-agent.ps1`,
so it only kicks in after the box pulls the NEW `run-agent.ps1` **one time by hand**.
The `faturas_moeda`/`bonus_equipe_030`/`convenio_extra_dl` blocks are ALREADY live
(a prior re-run picked them up), but the **POINT 17 correction to the `150.%` block
is not** — it needs one more re-run with the current `extract.sql` to populate
`bonus_equipe`(150.*), `dl_excedente_socios`, `dl_excedente_mv`. Pull both files
once (idempotent — safe even if already current), then re-run Feb + May.

On `MBC-LDESK01`, a fresh PowerShell window, one line at a time:
```powershell
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$env:SISJURI_PASSWORD = 'RgN@92Kx7'
$env:INGEST_TOKEN = 'OxlcIEMB_PcpmCaxKcEcJwNXmyiYB5F9l3JUnjktfAoKSxor5s6hRJ2Et9R_Hr5s'
$env:INGEST_URL = 'https://rumo-backend.xem1qi.easypanel.host/api/ingest'
Invoke-WebRequest -UseBasicParsing "https://raw.githubusercontent.com/femito1/rumo/main/ops/sisjuri-agent/run-agent.ps1?nocache=$(Get-Random)" -OutFile C:\temp\sisjuri\run-agent.ps1
Invoke-WebRequest -UseBasicParsing "https://raw.githubusercontent.com/femito1/rumo/main/ops/sisjuri-agent/extract.sql?nocache=$(Get-Random)" -OutFile C:\temp\sisjuri\extract.sql
powershell -ExecutionPolicy Bypass -File C:\temp\sisjuri\run-agent.ps1 -AnoMes 2026-05 -IngestUrl $env:INGEST_URL
```
**Verify it worked:** the run should print `[agent] extract.sql self-updated from main`
near the top, and the snapshot should be LARGER than 35.8 KB (it now carries ~53
invoice rows). Then confirm from the dev box:
```bash
cd backend && set -a && source .env && set +a
curl -s -H "apikey: $SUPABASE_SERVICE_KEY" -H "Authorization: Bearer $SUPABASE_SERVICE_KEY" \
  "$SUPABASE_URL/rest/v1/sisjuri_snapshots?client_id=eq.mbc&ano_mes=eq.2026-05&select=payload" \
  | python3 -c "import json,sys; p=json.loads(sys.stdin.read())[0]['payload']; p=json.loads(p) if isinstance(p,str) else p; print('faturas_moeda:', len(p.get('faturas_moeda') or [])); print('bonus_equipe(150.*):', p.get('bonus_equipe')); print('bonus_equipe_030:', p.get('bonus_equipe_030')); print('dl_excedente_socios:', p.get('dl_excedente_socios')); print('dl_excedente_mv:', p.get('dl_excedente_mv')); print('convenio_extra_dl:', len(p.get('convenio_extra_dl') or []))"
```
Expect `faturas_moeda` ~53 rows (May), and — the POINT 17 acceptance test — **Feb**
`bonus_equipe`(150.*) = **94696.15** (currently None → proves the re-run picked up the
corrected block) and `dl_excedente_socios`/`dl_excedente_mv` populated. Then validate
Nacional/Moedas tie (script in §Verify).
Optionally re-run `backfill.ps1 -StartMonth 2026-01` so Jan–Abr carry the new blocks too.

After this ONE manual pull, the daily 06:00 task is self-maintaining forever (it
self-updates `extract.sql` each run) — no more hand-copying files to the box.

---

## What was accomplished this session (all live-validated on real 2026 SISJURI data)

### 1. T5 despesas at LÍQUIDO — LIVE for May
Re-ran the extract; the fresh snapshot's `despesas_liquido` + `despesas_desdobramento`
blocks reproduce the recipe to the centavo (aluguel 24.359,77, contabilidade 8.042,94,
licenças 7.239,10, cursos 1.600, Claude→Informática, Custas/Transporte excluded).
**Despesas = 105.640,60.** The pure module `app/closing/despesas_liquido.py::net_by_account`
+ the `dre.py::from_snapshot` override are unchanged from 2026-07-13; this session just
made them live and proved the LIVE extract matches the hand-proven recipe.

### 2. Daily-job staleness — ROOT-CAUSED & FIXED
The daily task ran a pre-T5 `extract.sql` for a full day because the box's copy is
hand-maintained and nothing pulled `main`. `run-agent.ps1` now self-updates `extract.sql`
from `main` before each run — sanity-checked (must contain `JSON_OBJECT` + `'despesas_liquido'`
+ >4KB) and fail-safe (WARN + fall back to local copy on any error, so the job never stops).
`-NoSelfUpdate` forces the on-disk copy for testing. **Caveat: needs the one-time manual
pull above to take effect** (the logic lives in the file being updated).

### 3. Renata's aluguel–Belline authorization — May tail UN-BLANKED
Renata (2026-07-14): "assume the DB is correct for the aluguel–Belline numbers (ONLY
those)." Our GERENC-net aluguel (net of the Belline sublet credit) is authoritative; the
workbook typed a value R$129,17 lower. `scripts/build_workbook_targets.py::
_apply_aluguel_override` bumps the `despesas` target for Apr+May by +129,17 and propagates
through the tail (bruto/líquido −129,17; reserva = 10% of corrected líquido). **May now
renders the full institucional tail** (despesas 105.640,60, bruto 100.197,94, líquido
29.691,74, reserva 2.969,17, both margins) instead of blanking. Scoped to aluguel only.

### 4. Backfill Jan–Mai + multi-month validation
All of Jan–Mai re-extracted with the net blocks (ingest 200 each). Ran the DRE per month
vs the workbook per-family truth: **only MAY ties to the centavo**. Jan +2.531, Feb +2.498,
Mar −684 — and these are the client's HAND-ENTERED manual layer (Vale-ADM summed by hand,
Associações ÷2/÷3 splits, Eventos/HH classification flip), NOT DB bugs. Details in the
`multimonth-despesas-validation` memory. Implication: our DB numbers are arguably *more*
correct than the old months' workbook cells; those cells blank under the hard rule until
the client accepts the DB value or we add per-month targets.

### 5. DL / convênio — PROVEN to the centavo, blocks emitted
- **Convênio extra per lawyer** (deducted from that partner's DL, NOT an office expense):
  constant Jan–Mai on `500.010.<SIGLA>` — **DC 3.796,78 / RB 5.151,75 / EHF 1.398,01**
  (Aurélio/AM's extra is inside his 030.010.0110 base). Extract block `convenio_extra_dl`.
- **Bônus equipe** (POINT 16): proven vs Feb — 94.696,15 (`150.010.0010`) + 7.009,84 JGS
  (`030.010.0010`) = **101.705,84**, ties the workbook `D192` exactly. Extract block
  `bonus_equipe_030`; `dre.py` now sums `bonus_equipe` + `bonus_equipe_030`.

### 6. T8 — Nacional/Moedas per-invoice tabs — AUTOMATED
Source `LDESK.DB_VW_FATURASEMI_REC` **validated to the centavo**: Σ `VALOR_HONORARIOS_NAC`
for May emission = 719.988,05 = the sacred `faturamento_bruto('2026-05')` EXACTLY, splitting
R$ 708.659,18 (72) + US$ 11.328,87 (3). The view is per-invoice-LINE (75 rows for ~53
invoices — e.g. invoice 4143 = 6 lines of 678), so the extract `GROUP BY NUMERO` to the
per-invoice grain (the sacred cross-check proves the lines are real, not a join fan-out).
Wired: `faturas_moeda` extract block, `SectionKey.NACIONAL/MOEDAS`,
`secondary_tabs.py::assemble_faturas_moeda` (splits Nacional = moeda==moeda_nac vs Moedas),
`assemble_dre_sections`, assembler `supports()`, `TAB_ORDER`. Frontend renders `tab_order`
generically — no frontend change needed. +4 tests in `tests/test_faturas_moeda.py`.

---

## 🔴 Remaining work (each has a known path — none are mysteries)

1. **[BOTTLENECK] The one manual pull + re-run above** so `faturas_moeda` /
   `bonus_equipe_030` / `convenio_extra_dl` land in the snapshot and go live. Nothing
   ships these blocks until a re-run with the new files.
2. **[NEXT — automate POINT 17 ourselves] Split sócio vs employee bonus from the DB.**
   See the dedicated section below. This unblocks both the "Bônus equipe" vs "DL
   excedente sócios" lines AND wiring `convenio_extra_dl` into each partner's DL. Do
   NOT treat the partner split as RUMO's task — derive it from the DB.
3. **Jan–Abr manual layer** — decide with the client: accept the DB number (add per-month
   `despesas` target overrides like the aluguel one) or leave those cells blank. Our
   numbers are DB-correct; the workbook cells carry hand-entry. See
   `multimonth-despesas-validation`.
4. **DL extras (Feb)** — decomposed & proven (Bônus equipe = 101.705,84; DL-excedente-sócios
   folds into 030.010.0010). Finish the partner/MV split via §POINT 17 below (NOT waiting
   on RUMO). See `dl-extras-bonus-rules`.
5. **Multi-month re-validation** after the POINT 17 split / any target decisions.
6. **Orçamento** — intentionally OUT of scope (client fills the ORÇAMENTO tab; already an
   editable budget in the product via `BudgetEditor`).

---

## ⭐ NEXT SUBSTANTIVE TASK — automate POINT 17 (sócio/employee bonus split) ourselves

**The user explicitly overrode the meeting note here (2026-07-14):** POINT 17 was written
as "tarefa da RUMO" (have RUMO book the partners' bonus to a separate accounting account),
but that pushes a manual chart-of-accounts dependency onto the client — contrary to the
operating rule (assume automation until impossibility is *proven*). We cracked harder
splits than this (desdobramento, convênio-extra, Vale-ADM). **Derive the split from the DB.**

**Why this is very likely DB-derivable (evidence already in hand):** the Feb probe
(`probe_dl_extras_clientes`) showed the `150.010.0010` bonus lines carry the **sigla in the
histórico** — `"Bônus FSM referente a 2025 (22,20%)"`, `"Bônus EHF ..."`, etc. — the exact
same pattern we already exploit elsewhere. So the split is really "classify each sigla as
sócio vs employee," not "separate the accounts." Notably, the siglas that appeared in Feb's
150.* (FSM, EHF, BMP, IAC, BBX, ASG) are all **employees** — the 4 partners (Ricardo,
Aurélio=AM, Daniel=DC, Martim=MV) did NOT appear, which hints 150.* may ALREADY be
employees-only (their excedente posting to `030.010.0010` instead). The probe confirms this.

**The probe is written, committed, and pushed:** `ops/sisjuri-agent/probe_socio_split.sql`.
Run it on the RDP box (standard recipe — TLS 1.2, pull with `?nocache=`, wrap with CONNECT,
`sqlplus -S /nolog`, paste back `out_socio.txt`). It hunts, in priority order:
- **#A/#B/#B2** — a STRUCTURAL sócio flag (a `tipo`/`categoria`/`cargo`/`sócio` column on
  `CAD_PROFISSIONAL`, or a dedicated Sócios table/object). **Best outcome** → classify by a
  DB field, zero hardcoding (which is exactly what the meeting note said to avoid).
- **#C/#C2** — full `CAD_PROFISSIONAL` rows for AM/DC/MV/RB vs employees, to spot which
  column value separates partners.
- **#D** — every 150.* bonus line for 2026 w/ histórico + `LANCPROFDEST`: shows which siglas
  are actually in 150.* (if partners are absent, "Bônus equipe" is already correct and
  POINT 17 collapses to a confirmation).
- **#E** — where the partners' DL-excedente posts (`030.010.0010` "excedente/reserva").
- **#F** — the grupo list, in case a "Sócios" grupo exists to key on.

**Decision tree after the probe:**
- If #A/#B finds a structural flag → wire the split by that field (ideal).
- Else if #D shows 150.* excludes partners → `bonus_equipe` is already employees-only; just
  document it and drop the RUMO dependency. The partners' bonus is the `030.010.0010`
  excedente (block #E) → feeds "DL excedente sócios" (still needs the per-partner/MV split).
- Only if NEITHER works (no flag AND partners mixed into 150.* with no separable signal)
  is a small hardcoded sócio-sigla set `{AM, DC, MV, <Ricardo>}` justified — and even then
  it's OUR code, not a client task. Confirm Ricardo's sigla from #C first.

**Then:** wire the classification into the `extract.sql` bonus blocks + `dre.py`
(`bonus_equipe` = employees only; a new `dl_excedente_socios` derived from #E), add tests,
and — importantly — **update this file, `PROJECT_STATUS.md`, `docs/SISJURI_DB.md`
(the `150.%` row still says "serão separados pelo RUMO"), and `dl-extras-bonus-rules` /
`multimonth-despesas-validation` memories** to reflect that POINT 17 is automated by us.
Once the partner split exists, wire `convenio_extra_dl` (DC/RB/EHF) to deduct from each
partner's DL line.

---

## Verify (dev box) — prove May renders + Nacional/Moedas tie

```bash
cd backend && set -a && source .env && set +a
python3 - <<'PY'
import json, os, urllib.request
from app.closing.dre import assemble_dre_sections
# Pull the live May snapshot straight from Supabase (self-contained).
url = f"{os.environ['SUPABASE_URL']}/rest/v1/sisjuri_snapshots?client_id=eq.mbc&ano_mes=eq.2026-05&select=payload"
k = os.environ['SUPABASE_SERVICE_KEY']
req = urllib.request.Request(url, headers={'apikey': k, 'Authorization': f'Bearer {k}'})
p = json.loads(urllib.request.urlopen(req, timeout=30).read())[0]['payload']
snap = json.loads(p) if isinstance(p, str) else p
targets = json.load(open('app/closing/workbook_targets_2026.json'))['targets']['2026-05']
sec = assemble_dre_sections(snapshot=snap, budget=None, period_label='Maio 2026', targets=targets)
for r in sec['institucional']['rows'][:10]:
    print(r['key'], '->', r['Realizado']['value'])
for key in ('nacional', 'moedas'):  # only populated after the re-run adds faturas_moeda
    tot = next((r for r in sec.get(key, {}).get('rows', []) if r.get('kind') == 'total'), None)
    print(key, 'total honorarios (R$):', tot and tot['Honorários (R$)']['value'])
PY
```
Expected once the block is present: Nacional total ≈ 708.659,18, Moedas ≈ 11.328,87,
sum = sacred 719.988,05.

---

## Well-worn paths / how to work

- **DB probes / extract re-run over RDP** (`MBC-LDESK01`, Windows Server 2012, PS 3-4):
  copy-paste PowerShell one-liners. ALWAYS start a new PS window with
  `[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12`. Pull
  probes/scripts from the public raw GitHub URL with `?nocache=$(Get-Random)` (the CDN
  caches). Wrap a probe with `CONNECT RGN/"<pw>"@(DESCRIPTION=...HOST=172.16.237.9...PORT=1521
  ...SERVICE_NAME=cdbp01_pdb1.submbc.vcnmbc.oraclevcn.com)` then run via `sqlplus -S /nolog`.
  Full recipe in `ops/sisjuri-agent/README.md` "Ad-hoc probes over RDP". RGN pw `RgN@92Kx7`
  (in `ops/sisjuri-agent/ingest.local.secrets`, gitignored — ROTATE these creds someday).
- **⚠ NEVER push an untested `extract.sql`.** A bad column breaks the WHOLE daily extract
  (`WHENEVER SQLERROR EXIT FAILURE`) and the box now self-updates from `main`. Validate any
  new SELECT with a standalone probe FIRST (see `probe_faturas_moeda_validate.sql` as the
  template — it caught the per-invoice-line grain before it shipped).
- **Pull a fresh Supabase snapshot** (creds in `backend/.env`): curl the
  `sisjuri_snapshots` REST endpoint (see §DO THIS FIRST).
- **Redeploy prod:** `ops/easypanel-deploy.sh backend|frontend` (creds in
  `ops/easypanel.local.secrets`). Verify `/api/health` → 200. Snapshots are read LIVE from
  Supabase, so a data re-run needs NO redeploy; only CODE changes do.
- **Quality gates:** `cd backend && ruff check . && mypy app && pytest` (224);
  `cd frontend && npm run lint && npm run typecheck && npm run test` (52).
- **New probes committed this session** (pushable, on `main`): `probe_nacional_moedas.sql`,
  `probe_convenio_extra_dl.sql`, `probe_faturas_moeda_validate.sql`,
  `probe_socio_split.sql` (POINT 17 — NOT yet run; see §NEXT SUBSTANTIVE TASK).

## Files touched this session (all on `main`)
- `ops/sisjuri-agent/run-agent.ps1` — self-update extract.sql (fail-safe).
- `ops/sisjuri-agent/extract.sql` — +`bonus_equipe_030`, `convenio_extra_dl`, `faturas_moeda`.
- `ops/sisjuri-agent/{probe_nacional_moedas,probe_convenio_extra_dl,probe_faturas_moeda_validate}.sql`.
- `backend/scripts/build_workbook_targets.py` + `app/closing/workbook_targets_2026.json` — aluguel override.
- `backend/app/closing/dre.py` — bonus_equipe merge + Nacional/Moedas wiring.
- `backend/app/closing/secondary_tabs.py` — `assemble_faturas_moeda`.
- `backend/app/closing/tab_layouts.py`, `app/sources/base.py`, `app/sources/assembler_source.py` — new tabs.
- `backend/tests/{test_faturas_moeda,test_dre_assembler,test_workbook_targets,test_sources_base}.py`.
- `docs/SISJURI_DB.md` — new account/source facts; `PROJECT_STATUS.md`, `CLAUDE.md` — status.

## Key numbers (May 2026)
Recebimento 415.927,84 · Custos Diretos 210.089,46 · Despesas Indiretas (DB) 105.640,60
(wb typed 105.511,43; +129,17 = aluguel, DB-authoritative per Renata) · Resultado Bruto
100.197,94 · Imposto 62.389,20 · Amortização 8.117 · Resultado Líquido 29.691,74 · Reserva
2.969,17 · Faturamento 719.988,05 (Nacional 708.659,18 + Moedas US$→R$ 11.328,87).
