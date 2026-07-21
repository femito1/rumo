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

## Operator actions
1. **Full backfill (done this session / re-run any time):**
   ```powershell
   [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
   $env:SISJURI_PASSWORD = '<RGN password>'
   $env:INGEST_URL       = 'https://rumo-backend.xem1qi.easypanel.host/api/ingest'
   $env:INGEST_TOKEN     = '<INGEST_TOKEN from ingest.local.secrets>'
   powershell -ExecutionPolicy Bypass -File C:\temp\sisjuri\backfill.ps1 -StartMonth 2024-01
   ```
   (Use `-StartMonth 2026-01` to refresh only the validated year.)
2. The daily scheduled task keeps the latest month fresh with the same (self-updating) extract.

## Open / next (decision, not blocked)
- **Un-blank Jan–Apr from the DB.** Now that every family derives, the Jan–Apr cells the
  hard rule blanks can be filled from the DB — accepting that DB Jan/Feb will differ from
  (and improve on) the old hand-entered workbook cells (the AASP/Canal omissions). This is a
  targets change (`build_workbook_targets.py`) + a product/finance decision on whether to
  show DB numbers or keep historical workbook values for those months.
- **Orçamento & Amortização** remain the only manual inputs by design (a plan and a
  depreciation constant, not actuals) — explicitly out of scope for DB derivation.
