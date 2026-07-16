# DB-only gap map — the road to zero manual input (2026-07-14)

> **Directive (user, 2026-07-14):** *Nothing is non-DB-derivable. Literally nothing.*
> Every workbook number comes from SISJURI. Hard-to-read numbers are **contas
> transitórias** that must be **desdobrada** into the real accounts. The workbook
> disappears in the future — so each line must stand on its own DB rule, and the
> hard-rule validation (blank if ≠ workbook target) loses its ground truth. This
> file is the exhaustive map of what is NOT yet DB-derived, with the derivation
> path for each. Only the **Orçamento** stays a manual input (a plan, not an actual).

## Headline finding (validated against live Supabase, 2026-07-14)

**MBC already runs DB-only.** Both manual tables are EMPTY in production:
`area_transfers` = 0 rows, `manual_actuals` = 0 rows. Live snapshots carry NO
`ledger` block. So the manual paths below are **dormant escape hatches**, not live
dependencies — the DRE is assembled purely from the SISJURI snapshot today. The
work remaining is to (a) fill the last few genuinely-missing derivations, (b) retire
the dormant override paths so they can't silently mask the DB, and (c) replace the
disappearing-workbook safety net with intrinsic sanity guards.

## What IS DB-derived today (via `extract.sql` → snapshot)

Recebimento, Faturamento (+ sacred lock), per-area Recebimento base, Custo equipe
per area (`custo_equipe_deriv` + `rateio_grupo` + `home_area`), Comissão per area
(`comissao_deriv`), institutional Despesas at líquido (`despesas_liquido` +
`despesas_desdobramento`), Imposto (15% recebimento), Nacional/Moedas
(`faturas_moeda`), convênio-extra (`convenio_extra_dl`), and the bonus/DL blocks
(`bonus_equipe` 150.*, `bonus_equipe_030`, `dl_excedente_socios`, `dl_excedente_mv`)
— the last four pending the POINT 17 re-run (see [[point17-live-state-gap]]).

## ✅ BIGGEST GAP — SOLVED (2026-07-14) — per-area **Recebimento** = DB_RESULTADO_PROF.RECEITA_REC by NOMEGRUPO

The area tabs were mostly blank even for May because the cash-by-case per-área base
(205.157 / 162.473 / 48.298, Σ = sacred 415.928) did not match the workbook per-área
target (240.445 / 166.876 / 41.860, Σ 449.181). **Probes cracked it:** the workbook uses
the **Demonstrativo per-profissional basis** — `LDESK.DB_RESULTADO_PROF.RECEITA_REC`
summed by `NOMEGRUPO` (the sacred cash re-attributed to each lawyer by participation %,
rolled to the home grupo). Ties the authoritative May book to R$1:

| grupo | RECEITA_REC | workbook | Δ |
|---|---|---|---|
| Equipe Contencioso | 240.444,72 | 240.445 | 0,28 |
| Equipe Direito Econômico | 166.875,57 | 166.876 | 0,43 |
| Arbitragem + Equipe Ambiental | 41.997,50 − 138,15 = 41.859,35 | 41.860 | 0,65 |

Grand total over ALL grupos (incl. "Não Alocados" −33.251,80, "Administração") =
**415.927,84 = sacred cash** — confirming RECEITA_REC is the cash, re-split by prof.

**Shipped (branch `fix/workbook-free-guards`):** extract block `recebimento_area_prof`
(the validated query) + `dre.py` prefers it over the legacy cash-by-case
`recebimento_area`, folding "Equipe Ambiental"→Arbitragem and excluding "Não Alocados"/
"Administração" (so the three areas do NOT sum to sacred — the workbook omits them too).
Test `test_recebimento_area_prof_is_preferred_and_ties_may_workbook`. **Not live until a
re-run** populates the block (live falls back to cash-by-case, no regression). This also
subsumes GAP 4 (area_transfers): the "Resumo_Recebidas" reclassification WAS the
prof-participation re-split, now DB-derived.

The old cash-by-case note ("difference = Resumo_Recebidas manual transfers, no DB rule")
was wrong: it IS in the DB, exactly as the directive said.

## The real gaps (not yet DB-derived) — ranked by closeability

### GAP 1 — Per-area **Despesa Institucional** (rateio). STRUCTURE DONE, ties pending GAP 2.
- **Done (commit on `fix/workbook-free-guards`):** the rateio now runs off DB inputs
  unconditionally (no longer gated on `has_ledger`); the per-area row renders instead
  of blanking. `dre.py::from_snapshot` fills `area_desp_inst` via
  `desp_inst[area] = (despesas_total − Σ despesas_equipe_area) × (CE[area] / Σ CE)`.
- **⚠ Does NOT yet tie to the workbook.** Validated against the ONE authoritative book
  (May 2026, `test_area_despesa_institucional_ties_may_workbook`, currently **xfail**):
  ours overshoots each area by ~1.5–2.3k (Contencioso 37.662 vs wb 35.555 etc.).
  Root cause: the workbook subtracts per-area **Despesas Equipe** (~5.78k for May)
  from the pool BEFORE rateio; our `Σ despesas_equipe_area` is 0 because GAP 2 isn't
  extracted yet. Conservation (Σ areas == total) is a tautology and proves nothing here.
- **Action:** land GAP 2 → the xfail flips to pass and the row ties to the centavo.

### GAP 2 — Per-area **Despesas Equipe** (~5.78k/mo). PROBED 4×; DB does NOT cleanly tie.
- **Today:** only from imported `ledger` or `manual_actuals` (both empty in prod)
  → blank without a workbook.
- **Finding (4 probes, 2026-07-14 — see memory `despesas-area-split-gap`):** CONTASPAGAR
  has NO área column, only a SPARSE `SIGLA` cost-center (ECT=Contencioso/EDE=Econômico/
  ESP=Arbitragem) on some lines; CPDESDOBRAMENTO slices carry `DESCSETOR` (same codes) +
  `DESCPROFISSIONAL` (EMPTY on every slice). Combined SIGLA+DESCSETOR rollup for May:
  ECT 995,03 / EDE 2.204,82 / ESP 1.272,47 vs targets 2.276,22 / 2.300,10 / 1.204,47 —
  **does NOT tie.** AASP "AM, DC" (217,40) is booked fully ECT in the DB but the workbook
  splits it ÷2 by professional (AM=Econ, DC=Conten) — a HAND layer the DB doesn't carry
  (DESCPROFISSIONAL empty). Only Arbitragem = 1 clean account (020.060.0020 Patrocínio).
- **Untried leads:** (a) competência/accrual basis — test DB_RESULTADO_PROF
  `DESPESAS_INCORRIDAS_REC` / `DESPESAS_CUSTO_REC` per grupo vs these targets (the workbook
  may accrue, not pay-month); (b) a Demonstrativo per-prof despesa line that already applies
  the ÷2. This is the SMALLEST line on the board — weigh RDP round-trips vs value.
- **Blocks:** GAP 1's May-workbook tie (its xfail). Until GAP 2 lands, per-area Despesa
  Institucional overshoots by the ΣDespesasÁrea (~5.78k).

### GAP 3 — `dl_extraordinaria` + `repasse_cacione`. ✅ CLOSED (confirmed no-op, 2026-07-14).
- **Probed all history 2024-01 → 2026-06** (`probe_dl_extraordinaria_cacione.sql`):
  - **Extraordinária** occurs exactly ONCE: 2024-05 "Distribuição extraordinária êxito
    WM referente a fatura 2945" (a one-off success fee, `030.010.0010` + `150.010.0010`
    per lawyer). NOT present in any 2026 month → correctly blank in the 05.2026 book.
  - **Cacione** appears NOWHERE (the only `%CACIONE%` hits were false matches on
    "manifesta**ção**"). No such repasse exists in the data window.
- **Conclusion:** both lines are correctly always-blank in the current data; nothing to
  wire. If a future month books an Extraordinária (like the 2024 WM êxito), the histórico
  pattern is known — add it then. Do NOT invent a value when absent.
- **Bonus:** the probe's block #C dumped the full `030.010.0010` DL vocabulary and
  **confirmed POINT 17's split live** — `"DL excedente <SIGLA> - Reserva <month>"` (Jan:
  DC/RB 46.843,20 + AM 70.790,94 = 164.477,34; Mar: MV 6.627) + `"Bônus JGS"` 7.009,84.

### GAP 4 — `area_transfers` (Resumo_Recebidas cross-area reclassification). LIKELY DERIVABLE.
- **Today:** empty in prod (0 rows). A delta overlay on per-area recebimento; never
  changes the sacred total. Genuinely finance-entered historically, but the
  Demonstrativo per-profissional (LegalDesk) already reclassifies Ambiental→Arbitragem
  automatically, and the per-area base ties to the centavo without transfers for
  Jan/Feb.
- **Action:** verify whether ANY month actually needs a transfer once the per-case
  → área mapping is authoritative. If the DB per-área split already matches the
  workbook per-área recebimento every month, transfers are redundant → delete the path.

### GAP 5 — Dormant manual OVERRIDES that would mask the DB if ever set. RETIRE.
- `distribuicao_extras.*` explicit values, `custo_equipe_overrides`,
  `manual_actuals.{comissao,despesas_equipe,despesa_institucional}`, and the `ledger`
  block. All empty/absent in prod today but out-rank the DB when present.
- **Action:** once each DB derivation is proven, REMOVE the override path entirely
  (preferred). The `distribuicao_extras` divergence flag already shipped (item 2) is a
  transitional visibility aid, not a permanent guard — retire the override once GAP 3
  (dl_extraordinaria / repasse_cacione) is DB-derived.

## Workbook-free validation — NO runtime guard layer (user decision, 2026-07-14)

The user rejected building an intrinsic "sanity guard" / invariant layer as useless
(see memory `no-sanity-guard-layer`). **Do not propose or build one.** The goal is to
DERIVE each number correctly from the DB, not to police numbers after the fact. When a
number looks wrong, find and fix the DB derivation.
- The one shipped correctness fix — `bonus_reserve` floored at zero — stays as a plain
  fix (a reserve can't be negative), NOT the seed of a guard framework.
- Keep the Jan–May 2026 workbook figures as permanent **regression-test locks** (May is
  the ONE authoritative book — the Feb layout was superseded). Ground truth we already
  captured; used in tests, not as a runtime gate.

## Suggested order of work
0. **⭐ BIGGEST GAP probe — per-area Recebimento basis (449k allocation).** Crack the
   Demonstrativo Resultado Profissional's per-área allocation from the DB. Unblocks
   every per-area Resultado Bruto. RDP probe. Largest blank surface + sharpest test of
   the DB-only thesis.
1. **GAP 2 probe** (per-area Despesas Equipe via CONTASPAGAR grupo) — unblocks GAP 1
   (flips its May-workbook xfail to pass) AND fills the per-area Despesas Equipe row.
2. Wire GAP 2 into `from_snapshot`; GAP 1 then ties to the May book to the centavo.
3. **GAP 3 probe** (dl_extraordinaria / repasse_cacione histórico).
4. **GAP 4** decision (are transfers ever needed?) — likely subsumed by the BIGGEST GAP fix.
5. **GAP 5** retire the dormant overrides once their DB derivations are proven.
6. POINT 17 re-run (separate, RDP-blocked) — see [[point17-live-state-gap]].

NO sanity-guard layer (user decision — memory `no-sanity-guard-layer`). Validation =
regression-test locks against the Jan–May figures, not a runtime gate.

**Note on RDP dependency:** items 0/1/3 need a probe run on `MBC-LDESK01` (the operator;
I can't reach the box). Prep the probe SQL so it's ready the moment the operator is
available. Two probes are now committed & ready: `probe_recebimento_area_basis.sql`
(GAP 0) and `probe_despesas_equipe_area.sql` (GAP 2).
