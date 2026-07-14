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

## ⭐ BIGGEST GAP (found 2026-07-14) — per-area **Recebimento** basis. The area tabs are mostly BLANK even for May.

Validated live: with the hard-rule targets applied, the Contencioso/Econômico/Arbitragem
tabs render only Custo equipe + Comissão. **Recebimento, Despesas Equipe, Despesa
Institucional and Resultado Bruto all BLANK** — because the DB per-area recebimento
base does not match the workbook per-area target:

| area | DB base (case→área) | workbook target | gap |
|---|---|---|---|
| Contencioso | 205.157,46 | 240.445,00 | **+35.287,54** |
| Econômico | 162.472,56 | 166.876,00 | +4.403,44 |
| Arbitragem | 48.297,82 | 41.860,00 | −6.437,82 |
| **TOTAL** | **415.927,84** (= sacred) | **449.181,00** | **+33.253** |

The DB base ties to the sacred total (415.927,84); the workbook per-area sums to
**449.181** — 33k MORE than the cash actually received. So the workbook's per-area
Recebimento is a **different allocation** than "cash received per case's área." The
old note "the difference is Resumo_Recebidas manual transfers (no DB rule)" is (a)
too big to be minor reclassifications here, and (b) contrary to the directive —
**it IS in the DB.** The `Resumo_Recebidas` tab is gone from 05.2026; the client now
allocates per-area via the **Demonstrativo Resultado Profissional** (a LegalDesk
report generated FROM the DB — so its allocation logic is reproducible).

**Derivation to find (needs a probe on the RDP box):** reproduce the Demonstrativo's
per-área allocation. Candidates to test against the workbook per-área targets:
- per-área **faturamento** share applied to total recebimento (excluding "Não Alocados");
- a `Demonstrativo`/`VW_RESULTADO*` LegalDesk view that already emits per-área receita
  with the same 449k basis (the extra 33k vs cash suggests it's a competence/accrual
  or faturado-basis allocation, not cash);
- `CAD_CASO.ID_SUBAREAJURIDICA` sub-splits.
This gap **blocks every per-area Resultado Bruto** — highest priority to crack, and it
directly tests the "everything is DB-derivable" thesis on the hardest line.

## The real gaps (not yet DB-derived) — ranked by closeability

### GAP 1 — Per-area **Despesa Institucional** (rateio). CLOSEABLE NOW, no RDP.
- **Today:** populated only inside `if has_ledger` (`dre.py:421`); empty `{}` without
  a workbook ledger → the per-area tabs' "Despesa Institucional" row blanks in the future.
- **Derivation (all inputs already in the snapshot except GAP 2):**
  `desp_inst[area] = (despesas_total − Σ despesas_equipe_area) × (CE[area] / Σ CE)`.
  `despesas_total` and per-area `CE` are already DB-derived. The ONLY missing input
  is per-area Despesas Equipe (GAP 2). The rateio formula already exists
  (`ledger_import.py::despesa_institucional_rateio`) — just needs to run off DB
  inputs instead of the ledger.
- **Action:** once GAP 2 lands, compute this rateio unconditionally (not gated on
  `has_ledger`). If GAP 2's ΣDespesasÁrea is 0, the rateio is simply `despesas × CE-share`.

### GAP 2 — Per-area **Despesas Equipe**. NEEDS ONE PROBE + extract block.
- **Today:** only from imported `ledger` or `manual_actuals` (both empty in prod)
  → blank without a workbook.
- **Derivation (documented in `SISJURI_DB.md`):** `CONTASPAGAR` carries a **`Grupo`**
  column (ECT/EDE/ESP/ADM) already mapped to área — the same grupo dimension used
  for `Grupo='S'` auto-rateio accounts. The current `despesas_liquido` block groups
  by `PCTCNUMEROCONTA` only; it drops the grupo. Add a grupo/área dimension to the
  net-despesa aggregation.
- **Probe first (never push an untested extract):** confirm the CONTASPAGAR column
  name for grupo/área (likely `COD_GRUPO`/`SIGLA` → `CAD_GRUPOJURIDICO`), that área
  despesas (Despesas Área) are separable from institutional overhead, and that they
  tie to the workbook per-area Despesas Equipe (YTD dash: Contencioso 11.996,28).
- **Then:** emit `despesas_equipe_area` (area × net) and read it in
  `RealizadoInputs.from_snapshot` unconditionally.

### GAP 3 — `dl_extraordinaria` + `repasse_cacione` (Base_Resultado only). NEEDS PROBE.
- **Today:** the only two `distribuicao_extras` lines with NO DB emission and no
  writer — always blank. Base_Resultado "Distribuição de Lucros extras" block only;
  does NOT feed any DRE total.
- **Derivation hypothesis:** like the other DL lines, these are LANCAMENTO postings
  on a `030.010.*` / DL account keyed by histórico ("Extraordinária", "Cacione"/
  "Repasse"). Same pattern already cracked for bonus/excedente.
- **Probe:** hunt `030.010.*` (and DL-excedente 0010) histórico for "extraordinár"
  and "cacione"/"repasse"; confirm the account + sign; tie to a month where the
  workbook shows a value.

### GAP 4 — `area_transfers` (Resumo_Recebidas cross-area reclassification). LIKELY DERIVABLE.
- **Today:** empty in prod (0 rows). A delta overlay on per-area recebimento; never
  changes the sacred total. Genuinely finance-entered historically, but the
  Demonstrativo per-profissional (LegalDesk) already reclassifies Ambiental→Arbitragem
  automatically, and the per-area base ties to the centavo without transfers for
  Jan/Feb.
- **Action:** verify whether ANY month actually needs a transfer once the per-case
  → área mapping is authoritative. If the DB per-área split already matches the
  workbook per-área recebimento every month, transfers are redundant → delete the path.

### GAP 5 — Dormant manual OVERRIDES that would mask the DB if ever set. RETIRE / GUARD.
- `distribuicao_extras.*` explicit values, `custo_equipe_overrides`,
  `manual_actuals.{comissao,despesas_equipe,despesa_institucional}`, and the `ledger`
  block. All empty/absent in prod today but out-rank the DB when present.
- **Risk in a workbook-free world:** a stale manual value silently overriding a
  correct DB derivation, with no workbook to catch it.
- **Action:** decide per path — either remove the override entirely (preferred once
  the DB derivation is proven), or keep it but log/flag when a manual value diverges
  from the DB-derived value so an override is never silent.

## The safety-net replacement (workbook-free validation)

The hard rule (`verification.py`) returns the derived value unchanged when no target
exists — so future months don't blank, but nothing catches a bad derivation. Replace
target-matching with **intrinsic invariants** that need no workbook:
- reserva_bonus ≥ 0 (DONE — `bonus_reserve` floored at zero, 2026-07-14).
- recebimento ≈ Σ per-area recebimento (conservation).
- faturamento ≈ sacred LegalDesk faturamento (already locked for the KPI; extend to Nacional+Moedas Σ).
- margins within [−1, 1]; custos ≥ 0; imposto == 15% × recebimento exactly.
- Keep the workbook targets we HAVE (Jan–May 2026) as permanent **regression locks**
  in tests — they're ground truth we already captured; they just stop being the
  runtime gate.

## Suggested order of work
0. **⭐ BIGGEST GAP probe — per-area Recebimento basis (449k allocation).** Crack the
   Demonstrativo Resultado Profissional's per-área allocation from the DB. Unblocks
   every per-area Resultado Bruto. RDP probe. Do this FIRST — it's the largest blank
   surface and the sharpest test of the DB-only thesis.
1. **GAP 2 probe** (per-area Despesas Equipe via CONTASPAGAR grupo) — unblocks GAP 1 too.
2. Wire GAP 1 rateio unconditionally off DB inputs; add tests vs May.
3. **GAP 3 probe** (dl_extraordinaria / repasse_cacione histórico).
4. **GAP 4** decision (are transfers ever needed?) — likely subsumed by the BIGGEST GAP fix.
5. **GAP 5** retire/guard the dormant overrides.
6. Build the intrinsic sanity-guard layer; convert Jan–May targets to test locks.
7. POINT 17 re-run (separate, RDP-blocked) — see [[point17-live-state-gap]].

**Note on RDP dependency:** items 0/1/3 need a probe run on `MBC-LDESK01` (the operator;
I can't reach the box). Items 2/5/6 and the frontend override retirement are pure code,
closeable now. Prep the probe SQL so it's ready the moment the operator is available.
