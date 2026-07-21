# HANDOFF — 2026-07-21: the "lançamentos manuais" claim refuted; ISS decoded; full backfill

> **TL;DR** A pre-meeting re-audit under the directive *"nothing is manually done in the
> workbook — NOTHING"* proved it. Every DRE family the old `NOTA_CLIENTE` called
> "lançamentos manuais não deriváveis" is an ordinary SISJURI posting. The last holdout —
> ISS Trimestral's per-área split — turned out to be DB-derivable via `LANCSOLICITANTE`,
> and now ties the workbook to the centavo. One real bug was found and fixed (ISS was being
> dropped). Backend 241 tests, ruff/mypy clean. A full backfill was run to repopulate all
> snapshots with the corrected extract.

## Read first
- `docs/FINDINGS_2026-07-21-manuais-refutados.md` — the full evidence chain, family by family.
- `docs/SISJURI_DB.md` — the account index (updated: ISS row, Vale correction).
- `docs/NOTA_CLIENTE_meses_em_branco.md` — client-facing explanation (rewritten this session).

## What was proven (each family is system-derived, not hand-entered)

The decisive artifact was the **raw May system export** `reference/workbook/lancextrato de
contas.xls` (an "Extrato de Contas" straight from SISJURI, built on `FINANCE.LANCAMENTO`) —
the actual ledger, not a workbook tab. Cross-checked with `Pagtos maio.XLS.xlsx`
(`FINANCE.CONTASPAGAR`, which carries **Valor Bruto AND Valor Liquido as native columns**).

1. **Vale-ADM** — the transitória `200.010.0010` unfolds the VR/VT Mensal parent into
   per-person destination accounts (`500.010.MLA/.JVO/.VSR` + a `020.030.0060` slice). The
   ADM-vs-área tag *is* the destination account — the prior "the DB doesn't store who is ADM
   vs área" was false (it read `LANCPROFDEST`/`SIGLADEST`, NULL on these rows). May VR+VT =
   3.326,94 = workbook. Client's own action list said it: *"VALE REFEICAO, buscar na conta
   transitória."*
2. **Associações** (`020.060.0020`) — the area split is written in the histórico
   (*"IBRAC … Dividido em Contencioso e Econômico"* posts as two rows 700,09+700,10; AASP
   "AM, DC" → Contencioso; "Canal 100% Arbitragem"). May ties (2.822,06). In **Jan/Feb the
   workbook OMITTED lines** (AASP + Canal) the DB has — so there the DB is *more complete*.
3. **DL extras** — `150.*` + `030.010.0010` by month, already wired: Feb Bônus 101.705,99,
   Jan DL sócios 164.477,34, Mar DL MV 6.627 — all tie.
4. **ISS Trimestral** (`030.010.0160`) — see next section.

## The ISS story (the real work of this session)

**The bug:** ISS jurídico is named just "ISS", so `is_imposto()` matched the "iss" token and
classified it as a tax → dropped it (the DRE Imposto line is a 15%-of-recebimento formula,
not a sum of tax accounts). It's **trimestral** (Jan/Apr/Jul/Oct), so May — the
reconciliation month — was zero and the bug hid for the whole project.

**The mechanism (fully DB-derivable, proven to the centavo):**
- ISS is a flat per-professional rateio of the firm's quarterly ISS (histórico *"rateado
  para N profissionais"*: 14 in Jan, 11 in Apr/Jul), one `FINANCE.LANCAMENTO` posting/unit.
- ⭐ **Each unit's area = its `LANCSOLICITANTE` (requester)'s home area — NOT `LANCPROFDEST`.**
  Discovered by diffing all 70 columns of JGS's two Jan rows (`probe_iss_jgs_allcols`): they
  were identical except `LANCSOLICITANTE` (JGS vs MAM), both `DESNITEM` slices of the same
  payable `18172`. MAM's home is Econômico → that unit lands in Econômico.
- Folded through the standard AM-50/50 rateio, this ties Jan exactly:
  Contencioso **1.719,72** / Econômico **2.101,88** / Arbitragem **1.528,64** (Σ 5.350,24).
- **Why GERENC hid it:** `GERENC_LANCAMENTORESUMO` rolls every ISS posting to the lawyer's
  home group, so both JGS units looked like Arbitragem. The raw `FINANCE.LANCAMENTO` has the
  solicitante. (An earlier verdict in this session called the split "manual" from the GERENC
  view — that was wrong and is retracted in the findings.)

**The fix (committed, `main`):**
- `workbook_layouts.is_imposto` — excludes any `is_direct_team` account (so ISS is never a tax).
- `extract.sql` `custo_equipe_deriv` — ISS added as a 3rd UNION leg, keyed by
  `LANCSOLICITANTE` from `FINANCE.LANCAMENTO` (not GERENC-by-profD).
- `test_custo_equipe_deriv::test_iss_juridico_ties_workbook_via_solicitante` — locks the tie.
- **Verified live:** re-ran Jan; the snapshot now emits `JGS|382.16` + `MAM|382.16` (was a
  single `JGS|764.32`); the backend fold on live data reproduces the workbook exactly.

## Tooling added this session
- `ops/sisjuri-agent/lint_probe.py` — sqlglot (Oracle dialect) linter for probe `.sql`.
  Catches the two failure classes that wasted RDP round-trips: positional `ORDER BY N`
  beyond the SELECT column count (ORA-01785) and `XMLTYPE(<bare alias>)` (ORA-00904).
  **Run it on every new probe before sending:** `python3 lint_probe.py probe_x.sql`.

## Probes committed (audit trail, all read-only, all linted)
`probe_janapr_reconcile`, `probe_unknown_accounts`, `probe_iss_area`, `probe_iss_deep`,
`probe_iss_hist`, `probe_iss_jgs_dup`, `probe_iss_jgs_allcols`, `probe_iss_solicitante`.

## DB blind-spot sweep (result: model is complete)
Reconciled all 66 May ledger accounts + a Jan & Apr full-account census against the
account→family map. Every account maps to a known destination. ISS was the only real gap.
Financial income `010.020.0020` (Rendimentos, 13.744,98) is correctly excluded (the DRE has
no financial-income line — below-the-line investment yield). Seasonal ADM payroll (13º,
rescisões) hasn't posted in 2026 yet but is prefix-swept when it does.

## Current repo state (as of this handoff)
- **Branch:** all work is on `main`, pushed, tree clean. Head = the docs commit
  (`1de987c` at handoff time). ~18 commits this session (`0f7cc4d` → `1de987c`): the ISS
  arc, the probes, `lint_probe.py`, and docs.
- **Backend:** 241 tests pass; `ruff check` + `mypy app` clean. The code changes are just
  two files: `app/closing/workbook_layouts.py` (`is_imposto` guard) and the extract; plus
  two test files. Nothing else in `app/` moved.
- **Snapshots (Supabase, prod):** backfilled 2026-07-21 ~08:42–08:45 for **2024-01 →
  2026-05** (verified: every month's `meta.generated_at` is `2026-07-21T08:4x`). **2026-06
  is stamped `06:00`** — that is the *daily scheduled task*, NOT the backfill (backfill
  stops at the last CLOSED month = May), so June is fresh too and this is expected, not a
  miss. All snapshots carry `custo_equipe_deriv` (now with the solicitante-keyed ISS).
- **`fix/workbook-free-guards` branch still exists** locally/remote — it was merged long ago
  (`d056713`, per PROJECT_STATUS §top); it is stale and can be deleted. Not used this session.

## ⚠ DEPLOY STATUS — VERIFY BEFORE TRUSTING LIVE NUMBERS
The ISS fix has **two halves** and only one is auto-live:
- **Snapshots** (extract change) — LIVE: the backfill repopulated them with solicitante-keyed ISS.
- **Backend code** (`is_imposto` guard in `workbook_layouts.py`) — **needs a manual prod
  redeploy.** EasyPanel does NOT auto-deploy on push to `main`. Until the backend is
  redeployed, the *deployed* `dre.py` path may still classify ISS as imposto and drop it —
  so the fresh snapshot's ISS would NOT render in the live closing. **I could not confirm the
  deployed code version** (the closing endpoint needs login auth; `/api/health` only returns
  `{"status":"ok"}`). **Next agent: redeploy and verify (below).**

```bash
# from the repo root, after confirming main is pushed:
ops/easypanel-deploy.sh backend        # rebuild+deploy backend from main
# (creds in ops/easypanel.local.secrets, gitignored)
```

## How to validate EVERYTHING (next-agent playbook)
1. **Gates:** `cd backend && ruff check . && mypy app && pytest` → expect 241 pass. The ISS
   tie is locked by `test_custo_equipe_deriv::test_iss_juridico_ties_workbook_via_solicitante`
   and `test_workbook_layouts::test_iss_juridico_is_team_cost_not_imposto`.
2. **Reproduce the ISS finding offline (no DB needed):** the raw ledger is committed —
   `reference/workbook/lancextrato de contas.xls` (May) + `Pagtos maio.XLS.xlsx`. Parse with
   openpyxl/xlrd (pandas NOT installed). The `probe_iss_*.sql` outputs are quoted verbatim in
   `docs/FINDINGS_2026-07-21-manuais-refutados.md` — re-derive Jan Conten 1.719,72 / Econ
   2.101,88 / Arb 1.528,64 from the solicitante+rateio rule.
3. **Re-run any probe live (RDP `MBC-LDESK01`):** lint first (`python3 ops/sisjuri-agent/
   lint_probe.py probe_x.sql`), then pull by **commit SHA** (not `/main/` — CDN caches ~5min)
   and run via the recipe in `ops/sisjuri-agent/README.md`. All probes are read-only.
4. **Confirm snapshots landed:** `GET /api/ingest/<ano_mes>/summary` with the bearer
   `INGEST_TOKEN` — check `meta.generated_at` and that `custo_equipe_deriv` is in
   `top_level_keys`. For ISS specifically, pull the local `closing_<m>.json` on the box and
   grep `custo_equipe_deriv` for `030.010.0160` — a quarter month (Jan/Apr/Jul) should show
   one row per solicitante (Jan: 14 rows incl. `JGS|382.16` **and** `MAM|382.16`).
5. **Confirm live rendering (after redeploy):** log into the prod frontend / hit the
   authenticated closing endpoint for `2026-01`; per-área Custo equipe should include ISS
   (Jan is ~5.350 higher than a no-ISS derivation). If it doesn't, the backend wasn't
   redeployed (step "DEPLOY STATUS").

## Operator actions
1. **Full backfill (DONE 2026-07-21; re-run any time):**
   ```powershell
   [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
   $env:SISJURI_PASSWORD = '<RGN password>'
   $env:INGEST_URL       = 'https://rumo-backend.xem1qi.easypanel.host/api/ingest'
   $env:INGEST_TOKEN     = '<INGEST_TOKEN from ingest.local.secrets>'
   powershell -ExecutionPolicy Bypass -File C:\temp\sisjuri\backfill.ps1 -StartMonth 2024-01
   ```
   (Use `-StartMonth 2026-01` to refresh only the validated year.)
2. **Redeploy the backend** so the deployed code has the `is_imposto` fix (see DEPLOY STATUS).
3. The daily scheduled task keeps the latest month fresh with the same (self-updating) extract.

## May proof-of-match artifact (client-facing, built this session)
For the finance meeting: a **3-way** comparison proving our DB reproduces the client's May book.
- `docs/NOTA_MAIO_2026.md` — baby-clear PT-BR explainer with per-line tables + Renata's
  confirmations. Core message: May ties to the centavo except the aluguel-Belline **+129,17**
  (bruto 27.477,67 − Belline credit 3.117,90 = 24.359,77; Renata: use DB); per-area RB diffs are
  the Despesas-Área label regrouping (net-zero across areas, Renata-confirmed). Jan–Apr note: DB
  is **additive** (finds real lines the old planilha omitted, e.g. Jan Associações +AASP +Canal).
- `reference/comparativo/Comparativo_MBC_Maio_2026.xlsx` — color-coded (green=tie, amber=DB
  more correct, grey=regroup/rounding), institucional + 3 areas.
- **Regenerate:** `cd backend && python -m scripts.build_may_comparison` (committed, ruff-clean,
  self-asserts sacred 415.927,84 + live RL 29.691,61). The three legs are: raw `.xlsx` cell
  (leg "Planilha"), `targets_for("2026-05")` (leg "Alvo" — the workbook target the hard rule
  checks, with the aluguel override baked in), and `assemble_dre_sections(targets=None)` (leg
  "Sistema" — pure DB). ⚠ The script rebuilds the May snapshot from `_MAY_OVERRIDES` (values
  captured off the live box 2026-07-21) because the test fixture `sisjuri_2026_05.json` is STALE
  (lacks líquido/desdobramento/prof blocks → false +2.854 gap). To refresh: replace
  `_MAY_OVERRIDES` with a fresh `closing_2026-05.json`'s blocks. "targets"/"Alvo" is transitional
  scaffolding — a workbook-derived safety net the hard rule checks against; it disappears in the
  workbook-free endgame (the DB is the source of truth, not the target).

## Open / next (decision, not blocked)
- **Un-blank Jan–Apr from the DB.** Now that every family derives, the Jan–Apr cells the
  hard rule blanks can be filled from the DB — accepting that DB Jan/Feb will differ from
  (and improve on) the old hand-entered workbook cells (the AASP/Canal omissions). This is a
  targets change (`build_workbook_targets.py`) + a product/finance decision on whether to
  show DB numbers or keep historical workbook values for those months.
- **Orçamento & Amortização** remain the only manual inputs by design (a plan and a
  depreciation constant, not actuals) — explicitly out of scope for DB derivation.
