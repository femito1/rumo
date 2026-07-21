# HANDOFF — 2026-07-16: per-área DRE automated from the DB (Recebimento + Despesas Equipe + Despesa Institucional), POINT 17 live

> **Read first, in order:** `PROJECT_STATUS.md` §0 (client-confirmed rules — DO NOT
> re-ask), `docs/DB_ONLY_GAP_MAP.md` (the living gap map — this session closed most of
> it), and the recalled memories: `per-area-recebimento-basis-gap`,
> `despesas-area-split-gap`, `gap3-dl-extras-closed`, `point17-live-state-gap`,
> `no-sanity-guard-layer`, `multimonth-despesas-validation`, `workbook-uses-liquido-not-bruto`.
>
> **Product goal (unchanged):** fully replicate the MBC closing workbook purely from
> LegalDesk + SISJURI, with NO monthly manual input except the Orçamento. Directive
> reaffirmed emphatically this session: **NOTHING is hand-split — the SISJURI system
> does every allocation. If a number diverges, find the DB rule; do not conclude "manual
> layer" or "workbook bug" on our own — ask the client (Renata).**

---

## ⭐ DO THIS FIRST — the branch is NOT merged; prod has the data but doesn't render it

This session's **code lives on branch `fix/workbook-free-guards`** (11 commits ahead of
main, backend **235 tests** green, ruff/mypy/tsc clean). The **extract.sql changes were
pushed to `main`** so the daily job emits the new blocks — meaning:

- Production snapshots (Supabase) NOW carry `recebimento_area_prof` + `despesas_equipe_area`
  (verified live for 2026-02 and 2026-05).
- **But the deployed backend builds from `main`, and the `dre.py` code that READS those
  blocks is branch-only.** So the new per-área values are in the data but are NOT yet
  rendered in prod.

**Action:** review + merge `fix/workbook-free-guards` → `main`, then redeploy backend
(`ops/easypanel-deploy.sh backend`, creds in `ops/easypanel.local.secrets`). Snapshots are
read live from Supabase, so no data re-run is needed after the merge — only the code deploy.
Quality gates before merge: `cd backend && ruff check . && mypy app && pytest` (235);
`cd frontend && npm run lint && npm run typecheck && npm run test` (52). Frontend renders
`tab_order` generically — no frontend change was needed this session.

---

## What this session accomplished (all live-validated on real 2026 SISJURI data)

Started from a claim-validation task ("an agent claimed ~95% automation — verify it"). That
was true in code but overstated live; corrected, then drove the per-área tabs from mostly
blank to DB-derived. Highlights:

### 1. ⭐ Per-área RECEBIMENTO — SOLVED + LIVE (the biggest gap)
The area tabs were blank because DB cash-by-case per-área (Σ = sacred 415.927,84) ≠ the
workbook per-área target (Σ 449.181). Probes proved the workbook uses the **Demonstrativo
per-profissional basis**: `LDESK.DB_RESULTADO_PROF.RECEITA_REC` summed by `NOMEGRUPO` (the
sacred cash re-attributed to each lawyer by participation %, rolled to home grupo). Ties the
May book to R$1: Contencioso 240.444,72 / Econômico 166.875,57 / Arbitragem (incl. Equipe
Ambiental) 41.859,35. Grand total over ALL grupos (incl. Não Alocados/Administração, which
the area tabs exclude) = 415.927,84 = sacred. Extract block `recebimento_area_prof`;
`dre.py` prefers it over the legacy cash-by-case `recebimento_area` (fallback kept). **This
also subsumed GAP 4 (`area_transfers`)** — "Resumo_Recebidas" WAS this prof re-split.
Verified live after re-run for both Feb and May.

### 2. Per-área DESPESA INSTITUCIONAL (rateio) — DB-derived, no longer ledger-gated
`dre.py::from_snapshot` now computes `desp_inst[area] = (despesas_total − ΣDespesasÁrea) ×
(CE[area]/ΣCE)` unconditionally (was only inside `if has_ledger`, so it blanked in the
workbook-free path). Ties the May book within ~R$25 once GAP 2 (below) carves out ΣDespesasÁrea.

### 3. Per-área DESPESAS EQUIPE (GAP 2) — DB-derived by cost-center
"Despesas Área" = the Grupo='S' auto-rateio families (Associações 020.060.*, Viagens/
Prospecção 020.090.*, Cursos 030.010.0180, ...), attributed to área by each line's
**cost-center**: `SIGLA` on a direct CONTASPAGAR line, `DESCSETOR` on a CPDESDOBRAMENTO
slice, where **ECT=Contencioso, EDE=Econômico, ESP=Arbitragem** (documented in SISJURI_DB).
`RATNCODIG` is null on these — NOT the key. Extract block `despesas_equipe_area`; `dre.py`
maps cc→area into `area_despesas_equipe`. Live May: ECT 917,49 / EDE 3.804,82 / ESP 1.272,47
(Σ 5.994,78). **⚠ OPEN with Renata** — see the divergence section below.

### 4. GAP 3 (DL Extraordinária + Repasse Cacione) — CLOSED as confirmed no-op
Probed all history 2024-01→2026-06: Extraordinária occurs ONCE (2024-05 êxito WM fatura
2945), never in 2026; Cacione appears nowhere. Both lines are correctly always-blank in the
current data — nothing to wire. Pattern is known if a future month books one.

### 5. POINT 17 (sócio/employee bonus split) — CONFIRMED LIVE via a Feb re-run
Feb snapshot now has `bonus_equipe`(150.*) = 94.696,15 + `bonus_equipe_030`(JGS) = 7.009,84
→ Base_Resultado "Bônus equipe" = 101.705,99 vs workbook 101.705,84 (Δ 0,15, ties). The
DL-excedente split (`dl_excedente_socios`/`mv`) posts Jan/Mar, correctly None in Feb.

### 6. bonus_reserve floored at zero
`bonus_reserve()` now returns `max(líquido,0) × 10%` — a loss month (e.g. June) was rendering
a negative reserve. Plain correctness fix (NOT the seed of a guard framework — see below).

### 7. Cross-check discipline (caught a mistake — MINE, not the code's)
On the May self-audit, the live EDE Despesas Equipe was 3.804,82 but my test hardcoded
3.658,82 — my earlier HAND-SUM had missed a R$146 slice (pão de queijo/reunião cliente WM,
DESCSETOR=EDE). The extract was right. **Lesson: quote composed totals from a query, never
from mental arithmetic. Trust the extract over hand-sums.**

---

## 🔴 Open items (each with its exact state)

### A. [BLOCKER-ish] Merge `fix/workbook-free-guards` → main + redeploy backend
See "DO THIS FIRST". Until merged, prod shows the OLD per-área behavior despite the data
being present. No data re-run needed post-merge.

### B. [AWAITING RENATA] Despesas Área per-área allocation (GAP 2 divergence)
Message drafted and SENT (awaiting reply): `reference/msg_renata_despesas_area.md` (plain
text, every ref has aba+cell). The DB (by cost-center) and the workbook subtotals disagree
on the per-área split of Despesas Área, by three describable items in May:
- Viagens 1.358,72 (cell G156, LABELED "Viagens - Direito Econômico"): DB→Econômico (SIGLA
  EDE, paid by RB whose home is Econômico); the workbook SUBTOTAL formula sums it into
  Contencioso (a 1-row offset between labels and formula refs, present for Viagens/Eventos/
  Material/Patrocínio/Refeições/Cursos but NOT Associações/Assinaturas).
- Assento R$68 (G154, Viagens-Arbitragem): DB→Arbitragem; no workbook subtotal references it.
- Pão de queijo R$146 (020.090.0040, DESCSETOR=EDE): DB→Econômico; not in the workbook May subtotals.
So May Σ: workbook 5.780,79 vs DB 5.994,78. **Do NOT decide who's right — Renata's answer
tells us whether to allocate by label/cost-center (what the DB does) or by another rule.**
When she answers: if label/cost-center → the wiring is already correct; else adjust the
cc→area mapping (or the family/exclusion set) in the extract block + `dre.py`.

### C. [OPEN — needs a DB rule, NOT "manual layer"] Jan/Feb/Mar institutional despesa classification
Only MAY ties the institutional despesa total to the centavo. Feb DB despesas = 97.545,98 vs
workbook target 95.047,39 (**+2.498,59**); custos diretos −2.516,76 (they nearly cancel →
net ~R$18 on Resultado). Jan +2.531,57, Mar −683,51. `multimonth-despesas-validation` frames
these as a Vale-ADM / Associações-÷2÷3 / Eventos-HH classification difference. **Per the
directive, treat this as "a DB rule we haven't found yet," not a settled hand-layer.** It is
the SAME family of question as B (per-área/family classification splits) and overlaps
`reference/PERGUNTAS_REUNIAO_FINANCEIRO.md`. Candidate next step: extend the Renata thread
(or a probe) to nail the Vale-ADM transitória total and the Associações/Cursos area splits
per month. May is the proof the recipe is correct when the workbook isn't differently classified.

### D. [decision] Convert Jan–May workbook targets to test locks vs runtime gate
The hard rule (`app/closing/verification.py`) blanks a Realizado cell that diverges from a
workbook target by > R$1. It returns the derived value unchanged when NO target exists (so
future workbook-free months render). Targets exist only for 2026-01..05. Endgame decision
still open: keep the Jan–May figures as permanent regression-test locks (recommended) and
stop using them as the runtime gate. **NO intrinsic "sanity guard" layer** — the user
explicitly rejected it (`no-sanity-guard-layer`); derive correctly, don't police.

---

## State of the data (live Supabase, verified this session)
- **2026-05** (authoritative book): Institucional DRE ties to the centavo (receb 415.927,84,
  custo 210.089,45, despesas 105.640,60, bruto 100.197,79, imposto 62.389,18, líquido
  29.691,61, reserva 2.969,16). Per-área recebimento + custo equipe tie exactly.
  `recebimento_area_prof` (6 rows), `despesas_equipe_area` (ECT 917,49/EDE 3.804,82/ESP
  1.272,47) present.
- **2026-02**: recebimento + imposto tie; POINT 17 bonus ties (101.705,99); institutional
  despesa off +2.498,59 (item C). New blocks present.
- **2026-01/03/04/06**: carry the new blocks after prior re-runs; Jan/Mar have the item-C
  classification diffs; loss months render reserva 0 (fixed).

## Files touched this session
- Branch `fix/workbook-free-guards` (code, NOT on main yet): `backend/app/closing/dre.py`
  (recebimento_area_prof preference, despesas_equipe_area wiring, unconditional
  desp_inst rateio, bonus_reserve floor, distribuicao_extras override flag),
  `backend/tests/test_dre_assembler.py` (+ new tests), `docs/DB_ONLY_GAP_MAP.md`.
- On `main` (data path): `ops/sisjuri-agent/extract.sql` (blocks `recebimento_area_prof`,
  `despesas_equipe_area`), plus probes `probe_recebimento_area_{basis,prof}.sql`,
  `probe_despesas_{equipe_area_v2,area_lines,area_setor,area_key}.sql`,
  `probe_dl_extraordinaria_cacione.sql`.
- `reference/msg_renata_despesas_area.md` (sent), memories listed at top.
- Uncommitted: `docs/SISJURI_DB.md` (was modified before this session started — leave for
  the owner; not ours to commit).

## Well-worn paths / how to work
- **DB probes / extract re-run over RDP** (`MBC-LDESK01`, PS 3-4): fresh window, TLS 1.2
  first, pull from `raw.githubusercontent.com/femito1/rumo/main/...?nocache=$(Get-Random)`,
  wrap with CONNECT, run `sqlplus -S /nolog`. Full recipe in `ops/sisjuri-agent/README.md`
  "Ad-hoc probes over RDP". RGN pw in `ops/sisjuri-agent/ingest.local.secrets` (gitignored).
  ⚠ SQL gotcha that bit me 3×: when the SELECT list is ONE concatenated column, use
  `ORDER BY 1` or none — NEVER `ORDER BY 2` (ORA-01785). Verify column names against a
  schema dump first.
- **Extract re-run** (self-updating): pull `run-agent.ps1` + `extract.sql`, then
  `run-agent.ps1 -AnoMes YYYY-MM -IngestUrl $env:INGEST_URL`. Expect `ingest response: 200`.
- **Read a live snapshot** (dev box): curl the `sisjuri_snapshots` REST endpoint with the
  Supabase service key from `backend/.env`. Parse `payload` (may be JSON string).
- **Cross-check a DRE**: `assemble_dre_sections(snapshot=snap, targets=...)` and compare to
  the workbook via openpyxl (`reference/workbook/Fechamento MBC 05.2026.xlsx`, May = col G).
  ALWAYS pull composed totals from a query, not by hand.
- **NEVER push an untested extract.sql** — a bad column breaks the whole daily extract
  (`WHENEVER SQLERROR EXIT FAILURE`). Validate with a standalone probe first.

## Suggested next moves
1. Merge the branch + redeploy (item A) — unlocks everything already built in prod.
2. Act on Renata's Despesas Área answer (item B).
3. Fold item C into the Renata thread / a targeted probe (Vale-ADM + Associações/Cursos
   per-month area splits) — it's the last classification gap; May proves the recipe.
4. Decide targets-as-test-locks (item D).
