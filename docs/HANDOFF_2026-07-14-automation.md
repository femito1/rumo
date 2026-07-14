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

## STATE: ~95% automated. May DRE ties end-to-end. One manual file-pull + re-run away
## from Nacional/Moedas going live. Everything committed + pushed to `main`,
## backend **224 tests**, ruff/mypy/tsc clean, prod redeployed.

---

## ⭐ DO THIS FIRST — the one open bottleneck (5 min on the RDP box)

The self-update fix for the daily job (commit 60731b1) lives INSIDE `run-agent.ps1`,
so it only kicks in after the box pulls the NEW `run-agent.ps1` **one time by hand**.
As of the last re-run the box still ran the OLD `run-agent.ps1` + OLD `extract.sql`:
the fresh May snapshot (generated 11:01) has the T5 net blocks but NOT the three new
blocks (`faturas_moeda`, `bonus_equipe_030`, `convenio_extra_dl`). Fix = pull both
files once, then re-run.

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
  | python3 -c "import json,sys; p=json.loads(sys.stdin.read())[0]['payload']; p=json.loads(p) if isinstance(p,str) else p; print('faturas_moeda:', len(p.get('faturas_moeda') or [])); print('bonus_equipe_030:', p.get('bonus_equipe_030')); print('convenio_extra_dl:', len(p.get('convenio_extra_dl') or []))"
```
Expect `faturas_moeda` ~53 rows. Then validate Nacional/Moedas tie (script in §Verify).
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
2. **Wire `convenio_extra_dl` into the DL split** — the block is emitted but not yet
   consumed. Subtract each sigla's extra from that partner's Distribuição de Lucros.
   Depends on RUMO's partner-split of account 150.* / the DL block (POINT 17, their task).
   See `transitoria-desdobramento-mechanism` memory for the mechanism.
3. **Jan–Abr manual layer** — decide with the client: accept the DB number (add per-month
   `despesas` target overrides like the aluguel one) or leave those cells blank. Our
   numbers are DB-correct; the workbook cells carry hand-entry. See
   `multimonth-despesas-validation`.
4. **DL extras (Feb)** — decomposed & proven (Bônus equipe = 101.705,84; DL-excedente-sócios
   folds into 030.010.0010). Wire the partner/MV split when POINT 17 lands. See
   `dl-extras-bonus-rules`.
5. **Multi-month re-validation** after POINT 17 / any target decisions.
6. **Orçamento** — intentionally OUT of scope (client fills the ORÇAMENTO tab; already an
   editable budget in the product via `BudgetEditor`).

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
  `probe_convenio_extra_dl.sql`, `probe_faturas_moeda_validate.sql`.

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
