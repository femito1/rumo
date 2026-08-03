# PROJECT_STATUS.md

> **Living status document. Read this first.**
> Agents and engineers working on this repo should treat this file as the
> single source of truth for *current* state, limitations, and plans.
> Keep it updated at the end of every milestone. When it disagrees with
> older docs, this file wins (except for the sacred LegalDesk numbers, which
> live in `docs/LEGALDESK.md`).

**Last updated:** 2026-08-03
**Product:** RUMO — Plataforma de Fechamento Mensal Multi-Cliente
**Architecture:** `docs/DESIGN.md` · **LegalDesk:** `docs/LEGALDESK.md`

---

## ⭐ 2026-08-03 (latest) — The vale block is fully decomposed; ONE number left open

Tested the theory that the hand-typed vale terms are "a vale-refeição plus a
vale-transporte". **Right for one of them, and it cracked the whole block.**

`backend/scripts/audit_vale_composition.py`:

* **Every vale is N whole days × a per-person daily rate, and the rate is IN the
  histórico** (*"Calculo: 14 dias x R$ 18,76"*). 2026 rates: VR **46,10** for everyone;
  VT **VSR 10,80 · MLA 18,76 · JVO 33,60**. This is the fastest way to sanity-check any
  vale figure.
* **`r123` is now explained in every month.** Fev/Jun = MLA only (ties our rule exactly).
  Abr/Mai = **all three people** (655,36 = 300,16+268,80+86,40; 607,04 =
  262,64+268,80+75,60) — the un-adjusted months, no top-up involved. Mar's `674` = the
  month's three-person VT total **674,12** (the June extrato says *"22 dias = Total:
  674,12"* verbatim). Jan's `262,64` = MLA's VT, 14 days × 18,76.
* **`543,22` is SOLVED — and it is exactly "a VR + a VT"**: a separate estagiária payable
  *outside* the transitória, `020.080.0050` VR **507,10** + `020.080.0060` VT **36,12**,
  her name in the histórico. Only exists in March.

⚠ **A correction that generalises.** My earlier sweep reported 543,22 as "not found
anywhere". Wrong twice over: it is not *stored* but is the **sum of two stored rows**, and
my broad pass tested values and pairwise *differences* — never sums. It was also already
written down in `docs/SISJURI_DB.md`. **Search for compositions, not just values, and grep
the durable docs before declaring something unknown.**

**`35,52` (January) is the only thing left,** and it survives every route: not a whole day
at any rate, absent from all 8 months and both extratos, and the `020.080.*` accounts that
explain March **do not exist in January** (which has exactly four vale lines, none of them
35,52). Weak hint: January paid VR for 18 days against MLA's VT of 14 — four days — and
`35,52 = 4 × 8,88`, but 8,88 is nobody's rate.

**So the client list is down to two items, one of which is a typo-level fix:** update the
two stale SISJURI convênio notes, and tell us where R$35,52 came from.

---

## 2026-08-03 — Dug until the floor: 5 of 6 open questions answered from the DB

Pushed on every remaining "needs a finance ruling" item. **Only two survive, and neither is
a decision** — one is a typo-level fix in SISJURI, the other a single R$35,52 we cannot
find. Three of my own documented claims were wrong and are corrected.

### The convênio was OUR bug, and it was self-detectable

`convenio_memo` carries the Parte MBC as free text, and finance sometimes leaves the
PREVIOUS period's note on the lançamento. EHF's `030.010.0110` posts **2.122,30 in all six
months**; the mar–jun memo cites exactly that, but the **jan/fev memo cites 968,65 — never
posted** — and derives 603,50 from it. Same for RB in February (memo 3.543,45, posted
3.427,58). We were trusting the stale note; the workbook, which keeps the standing Parte
MBC every month, was right.

New guard `dre._memo_describes_this_month`: apply the override only when the memo mentions
the amount actually posted that month. No hardcoded month, no fitting to the workbook.
Closes **90% of January's Econômico gap** (−3.060,10 → +290,15) and **53% of the jan/fev
per-área custo-equipe absolute error**.

⚠ **The remaining residual is deliberate.** Without a valid memo we fall back to the posted
GROSS, because the real Parte MBC exists only in the memo text — `convenio_extra_dl` is
constant year-round and does not reconstruct it (measured). Hardcoding 1.564,10 would be
fitting to the workbook. Closing the last ~558/month needs the note fixed in SISJURI.

⚠ **Accepted trade-off (user decision):** each component is now more correct but the
headline totals look WORSE — Custos Diretos YTD +4.248,95 → +12.021,29, Resultado Bruto
+131,84 → −7.640,50 — because the old Econômico understatement was **cancelling** the
Arbitragem overstatement (Feb: −3.016,26 against +1.911,95). That +131,84 was netting, not
accuracy. The document explains the movement explicitly so nobody is ambushed by it.

### Three corrections to my own documented claims

1. **Arbitragem's +1.911,95 needs no ruling — the workbook contradicts itself.** February
   keeps JGS's Distribuição (r70, 9.379,00) and Pró-labore (r71, 1.621,00) but blanks his
   Convênio (r69). Someone still drawing both is on the payroll, so the plan is a real
   cost, and the DB posts it. From March all three rows blank on both sides and Arbitragem
   ties 0,00. JGS has **no memo in any month** — do not confuse this with the EHF/RB case.
2. **REFUTED: the jan/fev "lançamentos avulsos" ARE in the DB.** `DIFF_JAN_ABR_2026.md` §3
   called r34/r35/r43/r47/r51/r54 *"sem lançamento correspondente"*. Wrong — the DB posts
   ONE distribuição that already includes the Reajuste and the Subsídio. February: BBX,
   IAC, EHF, FSM tie to the centavo, and **ASG closes at R$0,00** (book 9.822,92 across
   five rows vs our 9.822,92). Presentation, not a gap. Only real residual: BMP 50 centavos.
3. **`reconcile_custo_equipe.py` had a private COPY of the override loop** and kept the old
   behaviour after the guard landed, reporting numbers the product no longer produced. It
   now imports `_memo_describes_this_month`.

### What genuinely still needs the client — the whole list

1. **Update two SISJURI notes** (EHF and RB convênio, jan/fev): they describe an older
   plan. Not a decision — with the right text those months close themselves.
2. **The R$35,52** in `C123` (`=35,52+262,64`). Searched every list in every month's
   snapshot: it appears **nowhere**. Genuinely needs finance.

Everything else is closed: the r204/205/206 formula shift (worth fixing in the sheet, but
changes nothing on our side), the JGS convênio, the one-off lines, January's Associações
(AASP 195,40 + Canal de Arbitragem 1.204,47), the Vale-ADM months and the aluguel.

Backend **294** tests, frontend **72**; all gates clean.

---

## 2026-08-03 — Every contributing cause PROVEN, not asserted

The differences document named causes but several were *readings*, not measurements. Each
is now decomposed with a reproducible script, and doing that **found one attribution of
mine that was plainly wrong**.

1. **Custo equipe: all 18 cells close to 0,00** (3 áreas × **6** months — was Jan–Abr
   only). `scripts/reconcile_custo_equipe.py` extended; Mai adds only the lawyer Vale
   (+1.236,90 Contencioso) and Jun is clean.
2. **The r204/205/206 formula shift is now MEASURED** (`scripts/audit_despesas_area.py`):
   recomputing Jan–Mai with June's formula cuts total absolute error **10.216,31 →
   3.494,78 (−66%)** and takes ties from **4/18 to 11/18**. The row labels confirm the
   mechanism directly — Contencioso's formula sums *"Eventos e Happy hour - Direito
   Econômico"*, Econômico's sums *"... - Institucional"*, Arbitragem's sums
   *"... - Contencioso"*. What survives is January, and it is the already-documented
   Associações gap: **1.399,87 = AASP 195,40 + Canal de Arbitragem 1.204,47**, with the
   Canal de Arbitragem being *exactly* Arbitragem's residual.
3. **⚠ CORRECTION — per-área Despesa Institucional was attributed to the WRONG cause.**
   I had it as the r204/205/206 shift. It is not: the rateio is
   `POOL × (área custo share)`, and decomposing the delta into those two factors
   (`scripts/audit_desp_inst_rateio.py`, an identity exact to R$0,01 in all 18 cells)
   shows **the SHARE effect sums to ZERO in every month** — pure redistribution — while
   **100% of the money comes from the POOL** (Jan–Jun −5.811,73). So that line is
   explained by institucional *Despesas Indiretas*, not by anything per-área. **June
   proves the mechanism**: pool differs by exactly R$4,80 (the bank tariff) and the three
   áreas land on 1,72 / 1,84 / 1,24.
4. **Institucional Despesas Indiretas decomposed for all six months** (was Jan–Abr). Mai
   = Vale-ADM −2.280,60 (book types the full 3-person transitória: 2.719,90 + 607,04 =
   3.326,94 vs our 1.046,34) + aluguel Belline +129,17; Jun = the R$4,80 tariff alone.
   Also confirmed the Endomarketing ↔ Inv. Prospecção swap is presentation-only (Jan:
   our 1.317,71 Endomarketing = the book's 1.317,71 Inv. Prospecção, net zero in r198).
5. **Resultado Bruto has no cause of its own** — verified across all 18 cells that
   `ΔRB = Δreceita − Δcusto − Δcomissão − ΔdespEq − ΔdespInst` to within R$0,01.

A methodology note worth keeping: while decomposing Mai/Jun I first got family totals of
−5.178,15 / −1.895,18 against sintetico deltas of −2.151,43 / +4,80. The cause was my own
**truncated family names** ("Inv. Prospecção" vs "Investimentos em Prospecção") silently
matching nothing and contributing zero. With the exact names it ties. A lookup that misses
returns 0,00 and looks like data, not like a bug.

---

## 2026-08-03 — Meeting prep: differences moved to a DOCUMENT; deck numbers fixed

Two deliverables for the next client meeting: (1) every material workbook-vs-system
difference explained clearly, and (2) presentation numbers that can be trusted.

### 1. Differences now live in a document, not in the product

**Client decision: nothing about differences goes in the app.** The in-app "Diferenças
conhecidas" panel is **REMOVED** (`app/closing/notes.py`, `NotesPanel.tsx`, the payload
`notas` key, the row-level `notas` tags and their CSS). Verified not load-bearing for any
number — the two apparent outside references were false positives ("de**notes**" in a
docstring, and `foot="notas emitidas"` meaning invoice count).

Replaced by `docs/DIFERENCAS_ACUMULADO_2026.md`, generated by
`backend/scripts/build_diferencas_doc.py` from live snapshots + the June workbook, with
per-área YTD from the **production** `assemble_dre_sections`. Materiality **R$ 1.000**
("R$ 4,80 does not matter, R$ 1.900 does"); the 8 smaller ones are summed as a named
remainder rather than dropped. One format per entry: *planilha value + cell reference ·
our value · signed delta · cause · where to verify · what we need from finance*.

**10 material differences, all attributed, all in despesa.** Receita (−R$0,60 on 2,1M),
Impostos (−R$0,09) and Amortização (R$0,00) tie; institucional Resultado Bruto differs
**+R$131,84**. Three causes account for essentially everything: the workbook's own
`r204/205/206` one-row formula shift (Jan–Mai, the heaviest), lawyer Vale in Custo equipe,
and the jan/fev convênio memo — the only one still needing a **finance ruling**.
Cross-checked against `reconcile_custo_equipe.py`: Arbitragem's whole YTD delta is Jan–Abr
with 0,00 from Mai/Jun, exactly as the convênio story predicts.

Note the row-level `notas` tags had **never rendered anywhere** (`TabView.tsx` had zero
references) and never reached the acumulado tab (annotated at `:211`, tab inserted at
`:234`, plus a tab-id/section-key mismatch). The column-order guard test was kept and
generalised — that positional-binding trap outlives the notes feature.

### 2. Three presentation defects fixed, all verified against live data

- **The deck had no partial label and the PDF export stripped the one that existed.**
  `.partial-banner` is a sibling of `#presentation-root`, and the print CSS hides
  everything outside that root — so an open month exported as a finished closing, a direct
  violation of the CLAUDE.md rule. The deck now carries `is_partial`/`status_label` from
  the same `_period_payload` helper as the `period` block; the cover swaps its band and
  **every slide footer** carries the marker (each slide is one printed page). Verified by
  rendering the real deck in headless Chrome and grepping the generated PDF.
- **The Despesas card silently understated May by ~R$108k.** `_sum_or_none` summed what
  was present, so with `custo_equipe=211.401,96` and `despesas=None` (blanked by the
  hard rule) the card rendered a confident 211.401,96 labelled "custo equipe +
  institucionais". New `_sum_all_or_none` blanks when any component is withheld. Verified
  live: May → `None`, June → 316.713,20 unchanged. First presentation test on a hard-rule
  month (all others use 2026-02).
- **K-rounding: disclosed, not "fixed".** ⚠ My first instinct — more decimals — was
  **WRONG**, and I measured it: ~49% of realistic 6-month rows diverge visibly at one
  decimal *and* at two, because rounding a sum can never equal the sum of rounded parts.
  Two decimals made a real live faturamento row *worse*. The deck now states the rounding
  in a `.slide-note` and also explains the two legitimately non-additive tables (margens
  computed on the accumulated base; the three áreas not summing to institucional because
  per-área receita follows each professional's home grupo — the ~7k gap Adriana chased).

**REFUTED and not acted on:** a subagent reported Impostos Orçado showing 452.250 on
slide 5 vs 302.250 summed across the área slides. The live budget has
`institucional.imposto = 100.750,00` = exactly 15% × 671.666,67. It reconciles; that claim
came from a fixture, not production. Check live before planning work around a report.

Backend **293** tests (was 303: −10 note tests, 2 guards merged into 1, +2 new), frontend
**72**. All gates clean.

---

## 2026-08-03 — Custo equipe now closes to 0,00 per person in Jan–Abr

**The Jan–Abr custo-equipe attribution had a hole and it is now closed.** The 2026-07-30
entry below claims "every Jan–Abr difference has a named cause". That was true for
*despesa* (proved structurally — the ten families ARE the components of `r198`) but only
narrative for *custo equipe*: §1–§4 of `docs/DIFF_JAN_ABR_2026.md` showed four causes in
isolation and nothing summed them against the per-área delta. Adding them by hand left a
residual — Econômico Jan/Fev ≈ −3.000 was covered by none of the four.

`backend/scripts/reconcile_custo_equipe.py` closes it: both sides decomposed to
**(pessoa, conta)**, every difference bucketed into a named cause, **residual 0,00 in all
12 cells** (3 áreas × 4 months) to the centavo. Per-person values come from the
PRODUCTION functions called one lawyer at a time, never a re-implementation — a
reconciliation that re-derives the number it checks proves nothing. Gates clean, 303
tests, no app code touched.

Two findings that were in no document:

1. **ISS trimestral (`030.010.0160`) is a PRESENTATION difference.** Posted per lawyer in
   jan/abr (382,16 or 507,14 each); the book types ONE área-level row (r25/r54/r79). Same
   total, cancels at área level (net 0,04 over four months) — but it makes *every* lawyer
   line differ, so a per-person read looks alarming until you net it.
2. **The jan/fev convênio difference is the SISJURI memo itself, not our parse** — the
   largest custo-equipe difference of the quarter (2.962,41/month on Econômico, +1.911,95
   on Arbitragem in February). jan/fev memos state a different plan base and are
   internally consistent at it (EHF `1.795,86-1.192,36 (Parte MBC)=603,50`) while the book
   types March's constant `1.564,10` in all six months. **This is now question #0 for
   finance** — it needs a ruling, not a code change.

⚠ **A fourth trap for the list in §0 below: I misdiagnosed #2 as "our regex takes the last
number in the memo".** It does not — it anchors on `(Parte MBC) =` and matches correctly in
both months. Check whether the SOURCE DATA changed before blaming the parser.

Also corrected while doing this: two of my own bucket labels asserted things I had not
checked. "AASP — livro provisiona, DB não posta" was wrong (AASP *is* in the DB, as
Despesas Área `020.060.*` — a section difference, not a missing value), and the
`Base_Resultado` block totals are `r5=SUM(6:27)` / `r30=SUM(31:57)` / `r60=SUM(61:79)` —
**read the formula, never presume the range**, or excluded rows manufacture a phantom
residual.

---

## 2026-07-30 — Vale-ADM per person; notes panel; Jan–Abr fully attributed

**State: everything from the 2026-07-28 meeting is shipped and live.** All seven 2026
months are on extract v3, the daily agent refreshes the closed *and* the open month
unattended, June still ties the five cells the client validated, and every Jan–Abr
difference now has a named cause. Backend **303** tests, frontend **72**; all gates
clean. Deployed (a push to `main` auto-deploys — see the correction below).

### 0. Read this before touching numbers again — three traps that cost real time today

1. **A version bump is not a correctness check.** `extract_version: 2` certified a
   `vale_adm` rule that **never fired** (`n_rows_dropped = 0` in every month). June
   appeared to tie only because its stored snapshot had been hand-patched; a
   `backfill.ps1` run then overwrote the patch and silently regressed five
   client-validated cells in prod. Assert numbers in tests against fixtures — a
   contract marker only says the *shape* changed.
2. **A family-level difference is NOT automatically a misclassification.** `r198` adds
   *both* halves of Ocupação↔Administrativas and Endomarketing↔Prospecção, so moving a
   leaf between them changes no total. I reported two of these as our bugs before
   checking; they net to zero and the workbook itself switches criterion month to
   month. **Check the total first.**
3. **A matching YTD total can be pure netting.** Econômico "ties" on the per-área YTD
   while having the *largest* gross monthly error of the three (~94% cancels). Always
   decompose to months before declaring an área validated.

### 1. Vale-ADM is derived PER PERSON from the desdobramento

Mechanism (Renata, voice notes 2026-07-30): the VR/VT payable lands as **one lump on
transitória `200.010.0010`** and is then unfolded per person into
`500.010.<SIGLA>` — *"depois ele abre isso dentro do sistema... dizendo pra qual pessoa
é essa despesa."* The ADM share is the slices whose sigla has
`home_area == "Administração"`; **no sigla is hardcoded**, so the number follows
whatever finance records in SISJURI. extract **v3** emits raw `vale_prof` slices (no
policy in SQL); `dre.py` applies the test, and also excludes the ADM person from the
áreas' Custo equipe so the double count closes from both ends.

Ties **Fev 1.351,88** and **Jun 1.333,12** exactly (Base_Resultado r122+r123).
**Mar/Abr/Mai differ by design** — her own un-adjusted months, *"não vale a pena
corrigir, o valor é muito irrisório"* — asserted by a test so nobody fits to them.
Two rejected approaches are documented in `docs/SISJURI_DB.md` so they are not retried.

### 2. PT-BR "Diferenças conhecidas" panel

`app/closing/notes.py` + `NotesPanel.tsx`. A hand-written registry of already-diagnosed
differences, shown next to the number it explains, with a mailto pre-filling client +
competence + note id. Seeded with four (March's un-adjusted Vale, January's 35,52
hand-typed top-up, the Jan–May área formula shift, the recurring 4,80 bank tariff).
**Explains, does not detect** — nothing inspects a value; the no-guard-layer decision
stands. Shown to CLIENT too (they are the ones who ask). Collapsed by default and
renders nothing on a clean month. Fix a cause ⇒ delete the note in the same commit.

### 3. Jan–Abr differences: every delta attributed

`docs/DIFF_JAN_ABR_2026.md`, regenerated by `scripts/build_janabr_diff.py` from live
data — per line, per área, per institutional family, with the components summing
**exactly** to each month's total (no "unexplained" residue).

- **Faturamento, Receita, Impostos and Amortização differ by ZERO in all four months.**
  The sacred LegalDesk revenue is clean; every difference is in *despesa*.
- Dominant cause: **Vale ADM in the un-adjusted months** (Mar −2.199,08 / Abr −2.199,20).
- **Mar Informática −237,60** is exactly `7.744,12 − 7.506,52` on `040.040.0030`: the
  book used **gross**, we use `CPGNVALORLIQUIDO` (the confirmed rule, which ties 10/10
  families in May and all of June). Jan/Mai/Jun tie at 0,00 → our number is right.
- **Mar Gestão do Conhecimento −815,49**: an *Arbitragem* course the book files as
  institutional; being área-specific it belongs in Despesas Área (`030.010.0180`).
- Also identified by the earlier per-line pass: lawyer Vale inside área Custo equipe,
  the Econômico estagiária from March, the Arbitragem convênio that stops in the book
  after January, and 8 one-off typed lines in Jan/Fev.
- **Net effect over four months: Resultado Bruto −702** on 3M+ of faturamento.
- Four open questions for finance are listed at the end of that document.

### 4. Pipeline is self-sustaining

All 7 months extract v3 (`stale=false`). `register-task.ps1` re-registered with
**`-StorePassword`** → `LogonType: Password`, so the daily 06:00 job survives logoff
(the old Interactive default would silently stop on reboot — the 2026-07-14 incident
shape). It now extracts the **last-closed AND the open** month, each in its own
try/catch. Verified unattended, not assumed: June + July regenerated at 10:57:43 /
10:57:45 and June's five validated cells still tie. Note `LastTaskResult 267009` =
`0x00041301` = SCHED_S_TASK_RUNNING is informational, not a failure.

Also fixed today: the agent's `.ps1` files must be **pure ASCII** (PowerShell 3/4 reads
BOM-less UTF-8 as cp1252, so an em-dash's trailing byte becomes a closing quote and the
parse dies with a misleading "Unexpected token"). `ops/sisjuri-agent/lint_ps1.py`
enforces it in CI (`ops-scripts` job).

---

## 2026-07-29 — meeting follow-ups §5.1–§5.5 shipped

**⭐ CORRECTION (2026-07-30): EasyPanel DOES auto-deploy on push to `main`.** Two
places in this file previously said it does not. Measured: `84cda48` pushed at
13:35:46 UTC, backend build `Success` at **13:35:53 UTC** (7s later), frontend at
13:36:06 — with no `ops/easypanel-deploy.sh` invocation. So a push to `main` ships to
prod. Treat every push as a deploy: that is how today's `backfill.ps1` run and the v3
backend landed together without an explicit deploy step. `ops/easypanel-deploy.sh`
remains useful to FORCE a rebuild and to read build logs (`<svc> logs`).

All of HANDOFF_2026-07-29 §5.1–§5.5 implemented, TDD, each verified against the
workbook or live prod. Backend **285** tests, frontend **65**; all gates clean.

**DEPLOY: ✅ BOTH SERVICES LIVE** (`fb0a183`), verified rather than assumed:
- Backend build log `Success` at 17:13:32Z; `/api/health` 200. (Note `/openapi.json`
  could NOT prove this one — the route set didn't change, so the build log is the
  check here. Prod also overrides the seed logins, so an authenticated probe is out.)
- Frontend live bundle went `index-k5sXq9Xg.js` → **`index-D55MiXXw.js`**, and a local
  `VITE_API_URL=<prod> vite build` of this tree produces a **byte-identical** file
  (`cmp` clean). The new strings are confirmed present in the *downloaded* bundle:
  `Mês em aberto · parcial`, `não são um fechamento`, `available_months_detail`,
  `Mês no futuro`, `custo equipe + institucionais`, `stat-row-5`.

✅ **Operator work DONE 2026-07-30:** `backfill.ps1` re-extracted 2026-01..05 and
`run-agent.ps1` pushed 2026-07, so **all seven months are now extract v3**
(`stale=false`) with real per-person `vale_prof` slices. June's hand-patch is removed
and its five client-validated cells still tie from genuine extract output.
✅ **Daily task fixed and PROVEN unattended (2026-07-30).** `register-task.ps1` re-run
with **`-StorePassword`**, so `LogonType: Password` — it now fires whether anyone is
logged on or not (the old default was "only while logged on": a silent stop on reboot or
logoff, the same shape as the 2026-07-14 stale-snapshot incident). Fired manually to
verify rather than waiting for 06:00: both months landed seconds apart
(2026-06 `10:57:43`, 2026-07 `10:57:45`) and June's five client-validated cells still
tie. `LastTaskResult 267009` is **not** an error — `0x00041301` = SCHED_S_TASK_RUNNING,
i.e. still executing when queried.

- **§5.2 — the per-área YTD ~7k gap is a WORKBOOK formula bug, not ours.** See the
  section below; the headline is that `Base_Resultado` r204/205/206 are off by one row
  in Jan–May, and that "Econômico ties" is a netting artifact (94% cancellation), not
  a validated área. Nothing to fix in our derivation. `scripts/audit_area_ytd_formulas.py`
  reproduces it.
- **§5.1 — per-área Orçado Imposto + Amortização now derive** (were blank; Adriana
  14:30). Workbook formulas: `Impostos = área Recebimento Orçado × 15%`,
  `Amortização = inst Amortização Orçado × área ANNUAL custo-equipe share`
  (`Rateio Mensal` M = L/$L$5). Also extended the Orçado tail to Resultado Líquido +
  Reserva. Ties June exactly (37.781,25 / 3.000,63 · 3.042,29 · 2.074,08) against both
  the workbook and the live prod budget. No `AMORTIZACAO_MENSAL` fallback on purpose —
  8.117 is a *realizado* default and would display a budget the client never entered.
- **§5.4 — Faturamento fills every month** in the institucional detail (was competence
  only; 19:49). It is not a DRE row, so `_accumulate_dre_ytd` now also returns
  `{month: revenue.faturamento_bruto}` from each snapshot. All six 2026 months tie the
  book; YTD 3.463.471,84. The competence month still prefers the sacred LegalDesk KPI.
- **§5.3 — Despesas card added to the institucional slide** (29:39/30:01), a 5-up row.
  Total despesa = custo equipe + despesas institucionais (June 316.713,20). Scope held:
  the per-área **monthly** slides keep no despesa line (28:14), asserted by a test.
  Measured in headless Chrome at the real 1056px deck width: 205px cards, no clipping,
  dead space still 15px (the `cca0be9` whitespace fix is not disturbed).
- **§5.5 — OPEN-MONTH partial view** (client asked at 6:45). `is_closeable` keeps its
  exact old meaning; new `is_viewable` / `is_partial` / `available_months_detail` gate
  *display*. Only future months 422 now. The payload carries
  `period.is_partial|is_closing|status_label`, and a partial is labelled everywhere
  (eyebrow, banner for both roles, dotted picker cell) — it must never read as a
  fechamento. Landing month stays the latest **closed** one. `CLAUDE.md` updated in the
  same commit so convention and code agree. Two real bugs fixed while wiring it: the
  YTD accumulator and the Meta dashboard both gate on `is_closeable`, so the open month
  was excluded from **its own** YTD ("Acumulado Jan → Julho" would have stopped at June).
  **⚠ Operator action:** the daily Scheduled Task only ever extracted `AddMonths(-1)`,
  so the open month would have rendered permanently EMPTY (prod has snapshots for
  Jan–Jun only; there is no 2026-07). `register-task.ps1` now runs the last-closed month
  **and** the current month (open month second, each in its own try/catch, so a partial
  failure can't block the closing). **Re-run `register-task.ps1` on MBC-LDESK01** — an
  already-registered task keeps its old single-month command line.

**Still open:** §5.6 (map, don't fix, the Jan–Abr diffs — now known to be largely the
workbook's own formula bug; **re-extract first**, Jan–May still serve extract v1) and
§5.7 (logo + palette, then per-user logins — blocked on Adriana sending the assets).

---

## 2026-07-29 — the per-área YTD ~7k gap is a WORKBOOK formula bug

HANDOFF §5.2 ("Contencioso + Arbitragem differ ~7k, Econômico ties"). Both the user
and Adriana suspected a cross-área leak on our side — *"pode ser de lá, veio para cá"*.
**There is a cross-área leak, and it is in the workbook's own Jan–May formulas.**
Proven against `Fechamento MBC 06.2026.xlsx` + the live snapshots; reproduce with
`cd backend && python -m scripts.audit_area_ytd_formulas`.

1. **The leak hypothesis is refuted for our code, by its own signature.** If a slice
   were misrouted *between* áreas, Σ(3 áreas) would still tie while the parts moved.
   It doesn't: Σ itself differs per month, in **both directions** (custo equipe Jan
   −3.156,84 … Mar +3.652,42). So nothing is being moved from one área to another
   on our side. `accumulate_ytd` is also exonerated — the workbook's own YTD is a
   plain sum of its monthly columns (`AB = C+G+K+O+S+W`), verified for all 9 cells,
   so a YTD gap can only be the per-month gaps.
2. **`Base_Resultado Mensal_V2` r204/205/206 are off by one row in Jan–May.** For
   five families (Eventos e Happy hour, Material Gráfico, Patrocínio, Refeições,
   Viagens) each área reads the label one line **below** its own — the block is
   ordered Arbitragem / Contencioso / Econômico / Institucional per family:
   Contencioso reads *Direito Econômico*, Econômico reads *Institucional*,
   Arbitragem reads *Contencioso*. Net: the five **Arbitragem** rows
   (r138/142/146/150/154) are dropped and the five **Institucional** rows
   (r141/145/149/153/157) are counted. **June's formulas were repaired** — which is
   precisely why June ties us to the centavo and Jan–May do not. It also perturbs
   `r207 = r198 − r203` → per-área Despesa Institucional rateio.
3. **⚠ "Econômico ties" is an artifact of netting, not a validated área.** Per month
   Econômico has the *largest* gross error of the three (Σ|monthly Δ| = 15.426) but
   ~94% cancels between over/under statements, so its YTD looks clean. Contencioso
   cancels 74%, Arbitragem only 34% — that is the whole reason those two show a
   residue. **Never read a matching YTD total as evidence an área is right.**
4. **Fixed a real latent cross-área bug found on the way** (`match_area`): SISJURI
   emits whitespace-variant grupo names, and `EquipeContencioso` spliced a false
   `"econ"` out of `"equipE-CONtencioso"` → matched Contencioso **and** Econômico.
   Harmless where the caller takes the first hit, but `dre.py` has three loops that
   ADD over every match, so an ambiguous name double-counts into two áreas. Econômico
   is now anchored on `econô`/`econo`; pinned by a test. Not currently firing on live
   data (those blocks carry canonical names) — this closes it before it does.

**Nothing to "fix" in our derivation. The Jan–Abr diff (§5.6) is a question for
Renata about her formulas**, not a convergence target. Jan–May are also still
extract v1 (stale) — re-run `backfill.ps1` before quoting residual magnitudes.

Backend **272** tests; ruff + mypy clean.

---

## 2026-07-29 — June validation: custo-equipe fix, deck, re-theme

Client meeting validating June numbers. Delivered:

1. **Per-área Custo equipe fixed — ties the June workbook to the centavo.** June was
   rendering MAY's numbers (Contencioso 74.141,21, Total 207.961,39). Root cause: the
   `030.010.*` per-lawyer components are identical month-to-month, so the only mover is
   **lawyer Vale (refeição/transporte)** — which the old `FIX 1` dropped. Client ruled
   **"always include Vale"**; `dre.py` now folds `custo_equipe_area` into the derivation.
   June: Contencioso 75.424,21 / Econômico 80.536,85 / Total **210.345,00** (workbook to
   the centavo). May re-baselined (+1.236,90 / +75,60) via a generator override. Also
   resolves the "Rateio total ≠ Areas Sintetico custo equipe" report. See
   [[vale-in-custo-equipe-and-despinst-gap]].
2. **Presentation is now a full slide-by-slide deck** mirroring the monthly PPTX
   (`reference/workbook/MBC Resultado Jan a Mai 2026.pdf`): capa, índice, institucional
   (mês + monthly detail), YTD×Meta + **Atingimento da Meta** bars, análise YTD with
   status dots, per-área (mês/YTD/DRE), reserva matrix. `app/closing/presentation.py` is
   a pure projection; renders for both roles (CLIENT sees only it) and exports to PDF.
3. **Light re-theme to the PPTX palette** — white bg, black/gray, orange accent; green/red
   reserved for numbers. **All negatives red** app-wide; positives green on result rows.
4. **Areas Sintetico blocks expand/collapse** by section header, like Base_Resultado.

**OPEN (needs a client rule, not a code bug):** per-área **Despesa Institucional** is
over-rateized — we split 100% of the institucional pool by custo share, but the workbook
holds ~R$18.939 back as institutional-only and splits the remainder on a *different* ratio.
Client's cited 32.563 matches neither workbook realizado (30.609,71) nor orçado (33.821,38).
Ask Renata for the hold-back rule before touching it.

Backend 265 tests, frontend 60; ruff + mypy + lint clean. June snapshot added as a fixture.

---

## 2026-07-28 — cumulative is a TAB; 7 defects in the checkpoint fixed

Review of the checkpoint commit (`8941598`) against the full transcript. **Six of the
seven action points held up**; #1 (cumulative) was the wrong *shape* and broken in five
ways. Backend **263** tests, frontend **59**; ruff/mypy/eslint/tsc clean; `npm run build` OK.

- **⭐ The cumulative is now a TAB, not a render mode** (client ruling, overriding the
  transcript's "botãozinho" at 17:10). Rationale that makes it the *more* faithful
  reading: the workbook's cumulative view **is not a sheet or a mode** — it is the
  right-hand column group of `Areas Sintetico atualizado` (06.2026 cols Z..AE) over the
  *same* 44 stacked rows (institucional + 3 áreas). So it is ONE additive tab
  (`ACUMULADO_TAB`, ordered right after `areas_sintetico`), built from the per-month
  assemblies. Purely additive → no existing tab changes shape. **Removed:** the toolbar
  toggle, `?mode=`, `ClosingMode`, `build_closing(mode=…)`, the mode filter chip, the
  dead `.mode-toggle` CSS. A stale `?mode=…` URL still returns 200 (verified live).
- **Columns tie to the workbook to the centavo** (validated by folding the six 2026
  months): `Linha | Orçado YTD | Realizado YTD | Variação | Desvio % | Orçado Anual |
  Falta p/ meta` = workbook `A | AA | AB | AC | AD | Z | AE`. Receita YTD 2.130.830,87 ·
  Orçado YTD 4.030.000,02 · Variação −1.899.169,15 · Desvio 0,5287 · Res.Bruto YTD
  253.819,11 — all exact. **Names are corrected, values verbatim:** the sheet's own
  headers mislead (its "Orçado YTG" holds the *annual* budget; its "Variação Mensal"
  holds a *ratio*), so shipping them literally would mean two near-duplicate headers.
- **D1 — repeated line keys collapsed (corrupted the cumulative).** `accumulate_ytd`
  accumulated into a flat `{key: total}`, but `areas_sintetico` stacks four blocks that
  all repeat `recebimento`/`resultado_bruto`/… → **every block showed the sum of all
  four** (1000/500/300/200 all rendered 2000). Now keyed by `(block, line, occurrence)`,
  partitioning at `kind == "header"`. Verified live: 735.161,42 / 338.360,20 / 280.099,27
  / 116.701,95, Σáreas = institucional exactly.
- **D2 — non-DRE sections force-fitted and destroyed.** It rewrote *every* `rich`
  section: `rateio_mensal`/`amortizacao`/`meta_dashboard`/`nacional` came out as `{}`
  rows; `base_resultado` (`Linha, Valor` — no Realizado) and `dre_2026` (12 month
  columns) came out all-null. Now an explicit `_YTD_SECTIONS` allowlist.
- **D3 — "Meta anual R$ NaN" (user-reported).** `assemble_meta` returns `meta_anual` as a
  *sourced cell*; `_build_presentation` passed the dict to `formatBRL`. New `_num()`
  unwrap on every presentation field (`atingimento_mes` is a bare float — left alone).
- **D4 — the presentation silently emptied in acumulado mode.** It was built from the
  *overlaid* `tabs`, so `_row_value(…, "Realizado")` missed the YTD columns → all áreas,
  `meta_anual` and the monthly series went null. `_build_presentation` now takes
  `sections` (keyed by `SectionKey`), so no future overlay can re-break it.
- **D5 — header rows broke the positional-column contract.** Headers passed through as
  `dict(tmpl)`, keeping the *monthly* keys — and `TabView.rowKeys` samples **`rows[0]`
  only**, which in `areas_sintetico` *is* a header. Every value row resolved `undefined`
  → "ainda não temos", and the last column rendered the literal string `recebimento`.
  `richToAoA` in `exportClosing.ts` had the same bug, so exports were corrupt too. All
  rows (headers included) now emit the 7 display keys first.
- **D6 — `Orçado YTG` matched no workbook column.** It computed `annual − Orçado YTD`;
  the workbook's real year-to-go is `AE = Z − AB` = **annual − Realizado**. Now
  `Falta p/ meta`, locked to workbook `AE3` (8.060.000,04 − 3.463.471,64 = 4.596.528,40).
- **D7 — `transfers` never threaded into the YTD path**, so per-área Recebimento YTD
  wouldn't equal the sum of the monthly tabs. Now fetched per month.
- **Decision: no hard rule in the cumulative** (`targets=None`). A YTD *sum* can't be
  blanked per-cell without poisoning the whole line, and the client chose "segue com o
  sistema" for every month but the 2026-05 reconciliation.
- Accumulation is **skipped for CLIENT** (no detail tabs anyway), and a failure now omits
  the tab rather than rendering an empty one.
- **Not a defect, noted:** 2027 budget entry (transcript 20:14) works per-`ano` in
  `BudgetEditor`, but `available_months` spans 24 months *back* only — 2027 becomes
  reachable in Jan 2027. Out of scope.

**DEPLOY: ✅ BOTH SERVICES LIVE** (`13b12e7`).

- ✅ **Backend live and verified.** Proven, not inferred: **`/openapi.json` is PUBLIC**
  (200, no auth) and reflects the *deployed* route signatures — the `mode` Query param is
  gone from `/api/clients/{client_id}/closing`. Use this as the backend deploy check from
  now on (it supersedes the old "backend = indirect only" note).
- ✅ **Frontend live and verified.** Live bundle went `index-BSDA_8fR.js` (pre-`8941598`)
  → **`index-Cl_KK7s7.js`**, byte-identical to a local clean Docker build of the same
  tree. Confirmed in the shipped JS: `mode-toggle` and the `Período` group are **absent**
  (toggle gone), presentation strings present. So the July checkpoint UI *and* the
  cumulative tab are now both shipped.
- **The frontend had been failing to deploy since `8941598` — two real host-side bugs,
  now both fixed.** My first pass misdiagnosed this as "Docker disk pressure, needs
  operator action"; that was wrong. Root causes, from the actual build log:
  1. **`build: null`** on the frontend service — no build configuration at all (backend
     had `{"type":"dockerfile","file":"Dockerfile"}`). Fixed via
     `services/app/updateBuild`; both services now match.
  2. **Poisoned buildkit cache** — `failed to commit <id> … snapshot <id> does not
     exist: not found`, with every earlier step `CACHED`.
     `dockerBuilders/stopDockerBuilder` does *not* clear it. Two fixes:
     `services/app/updateSourceGithub` to force a fresh archive (the checkout was stale —
     the build was transferring the **336B old Dockerfile** while `main` had 968B), and
     `frontend/Dockerfile` now consumes the `GIT_SHA` build-arg EasyPanel already passes,
     above `RUN npm run build`, so the layer's cache key changes per commit. **Keep that
     ARG where it is.**
- **⭐ The panel API is oRPC at `/api/rpc/<ns>/<proc>`** (POST-only, `{"json":…}`-wrapped)
  — **not** tRPC at `/api/trpc`, which the deploy script had used. `/api/trpc` answers
  *everything* with a generic `{"error":"Bad Request"}`, valid procs included, which is
  what produced the earlier false conclusions that "only POST mutations work" and "the
  panel exposes no build logs". **Build logs are available**:
  `actions/listActions` → `actions/getAction` → `.log`. Full recipe + proc table in
  `ops/README.md`.
- `ops/easypanel-deploy.sh` rewritten onto the working API, plus a new
  **`ops/easypanel-deploy.sh <svc> logs`** subcommand (prints the last build log; also
  dumped automatically on a failed deploy). Also fixed: it **exited 0 on the FAILED path**
  (grep status consumed by the `if`) so `$?` was untrustworthy, and a naive
  `grep KEY= | cut` was pulling a comment line into the API key — the deploy "worked" only
  because that variable was unused on the success path.

---

## 2026-07-28 (later) — checkpoint action points implemented (deploy pending)

Implemented every action point from the 2026-07 client checkpoint
(`reference/meeting_transcript.MD`). Backend **253** tests, frontend **55**;
ruff/mypy/eslint/tsc clean; `npm run build` OK. **One deploy at the end** (see below).

- **#4 Per-área Orçado bug FIXED (proven to the centavo, May+June).** The Orçado column
  showed zero per-área Despesa Equipe/Institucional → wrong per-área Orçado Resultado Bruto
  (Adriana/Renata caught it live). Real formula: DespEq = typed per-área budget (Orçamento
  2026 rows 192/193/194); Despesa Institucional = "Despesa para ratear" pool (row 196) ×
  área **annual** custo-equipe rateio share (share = área annual custo budget ÷ Σ). New
  budget line key `despesa_para_ratear` (`budget/models.py`); importer reads the Orçamento
  sheet (`workbook_import.parse_orcamento_area_budget` + `scripts/import_budget`); rewrote
  `dre._per_area_orcado` (threads `budget_annual` via provider→AssemblerSource). **Persisted
  to prod Supabase (13 budget rows).** Ties June Conten 138.696,64 / Econ 136.199,31 / Arb
  91.470,78. Locked by tests.
- **Jan–Abr un-blanked ("segue com o sistema").** Hard rule now applies ONLY to 2026-05
  (`provider._HARD_RULE_MONTHS`); earlier months render raw DB numbers (the old hand-entered
  workbook cells omitted real lines — DB is more complete). `targets_for` unchanged (raw
  lookup kept for the comparison harness); gate is in the provider.
- **#1 YTD / acumulado view.** First shipped as a `mensal↔acumulado` toggle; **superseded
  the same day by the "Acumulado" TAB** — see the review section at the top of this file.
  New `snapshots_by_year` on both snapshot stores + `closing.ytd_accumulate.accumulate_ytd`
  survive; the toggle, the `?mode=` param and `build_closing(mode=…)` are gone.
- **Per-área reserva computed** (feeds YTD + presentation). `_area_rows` extended past
  Resultado Bruto to Imposto (15%×receb) / Amortização (área custo share) / Resultado Líquido
  / Reserva (signed 10%). Ties June per-área; Σareas vs institucional differ only by the
  "Não Alocados" recebimento (same as the client's PPTX).
- **#3 Tab cleanup + server-side role boundary.** `TAB_ORDER`-filtered KEEP set
  (base_resultado, areas_sintetico, dre_2026, orcamento_2026, rateio_mensal, amortizacao);
  removed Institucional/áreas/Meta/Nacional/Moedas/Faturas Analítico from the rail
  (institucional still ASSEMBLED so KPIs lift). **CLIENT sees ONLY the presentation panel**
  — detail `tabs`/`tab_order` withheld server-side in `build_closing(role=...)`, not hidden.
- **#2 Presentation panel + PDF.** Server assembles a `presentation` payload (headline +
  per-área cards + monthly recebimento series) from the existing sections — no new endpoint.
  New `PresentationPanel.tsx` (reuses KpiCard/tokens/format); ADMIN gets an "Apresentação"
  tab + detail tabs, CLIENT gets only the panel. PDF via `window.print()` + a scoped
  `@media print` light theme (`exportPresentation.ts`) — **zero new deps**, one slide/page.
- **#5 Equipe splits highlighted.** Per-professional drill-down rows were muted gray; now
  full-contrast text + `--api` left-accent + faint tint (`index.css .cell-indent`).

**⚠ DEPLOY (single, at end): backend + frontend both need a prod redeploy** via
`ops/easypanel-deploy.sh`. (⚠ CORRECTED 2026-07-30: EasyPanel DOES auto-deploy on push — see the top of this file. This note was wrong.) The budget rows are already live
in Supabase; the signed reserva + all the above render only after redeploy.

---

## 2026-07-28 — June book validates (untuned month); reserva de bônus is SIGNED

The June docs landed (`Fechamento MBC 06.2026.xlsx`, `lancextrato de contas junho.pdf`,
`MBC_JanJun_2026.pptx`). June is the strongest possible test: **no targets exist for
2026-06** (`targets_for("2026-06")` is `None`), so the hard rule masks nothing — the site
renders raw DB. Validated our live June snapshot (fresh, daily job 06:01) via
`assemble_dre_sections(targets=None)` against all three artifacts.

- **Headline lines tie to the centavo across workbook + raw ledger + PPTX:** Faturamento
  1.090.965, Recebimento **265.018,56** (ledger "TOTAL DE ENTRADA" 265.018,57; PPTX
  265.019), Res.Bruto −51.694 (wb −51.689), Res.Líquido −99.564 (wb −99.559), Imposto
  39.752,78 (15%), Amortização 8.117. June was a **loss month** (recebimento fell to 265K).
- **All residuals identified and net to zero:** (1) Vale/VR-VT ±2.383,60 — June wb moved
  VR/VT into per-área Custo Equipe; we keep it in Salários-ADM (dre.py "FIX 1", by design);
  net-zero on institucional. (2) Software-license ±10.340 reclass Informática↔Administrativas
  (net R$4,80). (3) Per-área Resultado Bruto (−3.068/−3.680/+6.743, Σ −5,22) = the same
  net-zero Despesas-Área cost-center allocation Renata ruled on. These are **classification
  choices, not correctness wins** — where the DB and the book bucket differently, the
  workbook is the reference (§0).
- **⭐ Reserva de bônus is SIGNED — removed the zero-floor (real fix).** Earlier code floored
  `bonus_reserve` at zero ("can't reserve a negative bonus"). The June book **refutes** that:
  wb reserva = **−9.955,93** (signed 10% × negative líquido), and the client's own PPTX
  (slide 13) states the model verbatim — *"Positivo = acúmulo de provisão; Negativo =
  consumo"* — accumulating the SIGNED monthly values to its printed YTD (−11,5K). The floor
  was our own invented assumption, made before we had this book. `dre.py::bonus_reserve` now
  returns `resultado_liquido * 0.10` (signed); June renders −9.956,44 (ties within R$0,51
  rounding); May profit month unaffected (2.969,16). Test flipped
  (`test_bonus_reserve_is_signed_for_a_loss_month`). Also un-blanks Jan/Feb/Apr reserva cells
  whose *targets* were already signed negatives (verification uses sign-correct abs-diff).
  Reinforces the "no sanity-guard layer" directive — don't clamp DB outputs on invented
  "business sense". Backend **242** tests, ruff/mypy clean; frontend unchanged (`formatBRL`
  already renders negatives). **⚠ Not yet redeployed to prod** — the signed reserva needs a
  backend redeploy (`ops/easypanel-deploy.sh backend`) to render live.

---

## 2026-07-21 (later) — confirmation sweep + DL-extras dash + prod redeploy

A full-state confirmation sweep of the ISS/backfill handoff, plus two fixes.

- **Gates re-verified:** backend now **242** (was 241; +1 test below), mypy clean,
  frontend **53** (was 52), eslint/tsc clean. **Fixed a real defect the handoff
  mislabeled "ruff clean":** two committed `E702` (semicolons) in
  `test_custo_equipe_deriv.py:172` — `ruff check` had been failing (exit 1).
- **Snapshots re-confirmed live** via `/api/ingest/<m>/summary`: Jan/May stamped
  `2026-07-21 08:4x` (backfill), June `06:00` (daily), all carry
  `custo_equipe_deriv`; sacred recebimento intact (Jan 279.821,07 / May 415.927,84).
  Feb carries `bonus_equipe`, `dl_excedente_socios/mv`, `convenio_extra_dl`.
- **DEPLOY (was the #1 unconfirmed item): backend + frontend REDEPLOYED from
  `main` (390832a)** via `ops/easypanel-deploy.sh` (both returned `ok`). This lands
  the `is_imposto` ISS guard (`b850300`, which post-dated the last 07-16 deploy) and
  the dash change below. NOTE the deployed SHA still can't be read back — the
  EasyPanel API here only exposes POST mutations (deploy/restart); GET query procs
  return `Method Not Supported`/`Not found`, and the closing endpoint needs
  prod-overridden login. Verified indirectly (frontend bundle-hash change; backend
  health). The ISS guard is **not** load-bearing for May (ISS is trimestral →
  May=0) and per-área ISS renders via `custo_equipe_deriv` (never consults
  `is_imposto`); it matters for **Jan** per-área Custo equipe (~5.350).
- **DL-extras absent lines now render "—", not "ainda não temos"** (`390832a`).
  The five "Distribuição de Lucros extras" lines (Bônus equipe, DL excedente
  sócios/MV, DL Extraordinária, Repasse Cacione) are event-driven; an absent line
  is correct-by-design, not pending data. Backend `row()` gained `empty_dash`;
  the frontend `RichRowsTable` honors a row-level `empty_dash` → `NA_LABEL` ("—"),
  distinct from the pending `MISSING_LABEL`. Locked by 1 backend + 1 frontend test.

---

## ⭐ 2026-07-21 — "lançamentos manuais" REFUTED; ISS decoded; full backfill

(Detailed handoff + per-family findings docs consolidated away 2026-07-28; the durable
account facts live in the `docs/SISJURI_DB.md` account index, the client-facing summary in
`docs/NOTA_CLIENTE.md`.)

- **Every DRE family is DB-derived** — the old "lançamentos manuais não deriváveis"
  claim is refuted (proven against the raw `lancextrato de contas.xls` / `Pagtos maio`
  system exports): Vale-ADM (transitória desdobramento → `500.010.<SIGLA>`),
  Associações (split in the histórico; Jan/Feb the *workbook* omitted AASP/Canal —
  DB is more complete), DL extras (150.*/030.010.0010, tie), and ISS Trimestral.
- **ISS Trimestral (`030.010.0160`) BUG FIXED.** It was named just "ISS" → `is_imposto`
  dropped it (DRE Imposto line is 15%×receb, not a sum of tax accounts); trimestral, so
  May (reconciliation month) was zero and it hid the whole project. **Rule (proven to the
  centavo):** each ISS unit's area = its **`LANCSOLICITANTE`** home area (not profD),
  folded through the AM 50/50 rateio → Jan Conten 1.719,72 / Econ 2.101,88 / Arb 1.528,64.
  Fix: `workbook_layouts.is_imposto` excludes any `is_direct_team` account; extract keys
  ISS by `LANCSOLICITANTE` in `custo_equipe_deriv`. Locked by 2 tests. Backend **241**.
- **Full backfill run** (2024-01 → 2026-05, snapshots stamped 2026-07-21 ~08:4x). June is
  the daily task's (06:00), also fresh. All snapshots carry the corrected `custo_equipe_deriv`.
- **⚠ DEPLOY:** the extract half is live (backfill); the **backend `is_imposto` code needs a
  manual prod redeploy** (`ops/easypanel-deploy.sh backend`) — ⚠ CORRECTED 2026-07-30: EasyPanel DOES auto-deploy on push
  on push. Until then the deployed `dre.py` may still drop ISS. Verify per the handoff playbook.
- **Tooling:** `ops/sisjuri-agent/lint_probe.py` (sqlglot, oracle) — lint every probe before
  the RDP round-trip (catches ORA-01785 positional ORDER BY + ORA-00904 XMLTYPE-on-alias).
- **#1 open (decision, not blocked):** un-blank Jan–Abr from the DB (targets change in
  `build_workbook_targets.py` + finance decision: DB numbers vs historical workbook cells).
  **RESOLVED 2026-07-28** — client chose "segue com o sistema"; hard rule now applies to
  2026-05 only (see the top checkpoint section).
- Superseded handoffs removed 2026-07-28 (were under `docs/archive/`).

## 2026-07-16 — per-área DRE is LIVE in prod (branch merged + deployed)

`fix/workbook-free-guards` was merged to `main` (merge commit `d056713`) and the
backend redeployed via `ops/easypanel-deploy.sh backend`. **Verified live** against
the prod closing endpoint (`/api/clients/mbc/closing?month=2026-05`): the per-área
tabs now render the DB-derived values that were blank before —
Contencioso recebimento **240.444,72** / desp.equipe **917,49**, Econômico
**166.875,57** / **3.804,82**, Arbitragem **41.859,35** / **1.272,47**; Institucional
ties to the centavo (receb 415.927,84, líquido 29.691,61, reserva 2.969,16). This
**closes handoff item A** (the former #1 blocker).

**Remaining "ainda não temos" on live May, and why (all EXPECTED, not regressions):**
- **Per-área `resultado_bruto` (3 cells)** — gated by the hard rule because the
  derived value diverges from the workbook target by the ~R$1.359 Despesas-Área
  split (Viagens G156 label-vs-subtotal offset). **This is the ONLY thing waiting on
  Renata** (handoff item B; question sent 2026-07-16 in the WhatsApp thread).
- **`base_resultado` DL-extras (6 lines: Bônus equipe / DL excedente / Cacione)** —
  correctly blank in May (bonus is a Feb event, DL excedente posts Jan/Mar,
  Extraordinária is a 2024 one-off, Cacione never occurs). Not a bug.
- **`dre_2026` / annual budget rows** — budget-source tab, populated only when the
  Orçamento is imported for the client.
- **Jan/Feb/Mar institutional classification (item C)** — earlier months still gate
  `custo_equipe`/`despesas`; May (the authoritative book) is clean.

## 2026-07-17 — per-área Orçado derived + amortização default (Orçado blanks cleared)

Two commits (main, backend deployed + verified live) addressing the "ainda não temos"
spread in the **Orçado** column:
- `e59dd5a` — **per-área Orçado is now derived from the institucional budget** (the workbook
  doesn't type a per-área budget; it derives it by formula). New `_per_area_orcado(budget)`:
  Recebimento = inst budget × 37,5/37,5/25 (ties workbook to the centavo); Custo/DespEq =
  pass-through; Despesa Institucional = pool × custo-equipe share (pool = OUR inst despesas
  budget − Σ per-área DespEq — DB-derivable, not the workbook's account subset); Resultado
  Bruto derived. Fills all 3 area tabs + areas_sintetico Orçado. Comissão/DespEq Orçado stay
  blank where no budget exists (correct).
- `d9d84dc` — **amortização Orçado defaults to the worksheet constant** (8.117/mês, 97.404/ano)
  in `institucional_ano` (was hard-coded None) and `dre_2026` (row was missing). Manual
  override already exists via BudgetEditor.
- **Key reframing:** almost every remaining "ainda não temos" is an **unentered BUDGET cell**
  (per-account Orçado — workbook budgets at family level; per-área Comissão/DespEq — no budget),
  NOT a missing actual. The Realizado side is complete (May ties, June 0-blank). Backend 239 tests.

## 2026-07-16 (later) — item B CLOSED (Renata's Despesas Área ruling)

Commit `824b1ca` (main, backend deployed). Renata confirmed Despesas Área is allocated
by each line's label/cost-center area (Viagens-Econômico → Econômico, assento →
Arbitragem); the workbook subtotal formula's 1-row offset was a spreadsheet mistake. The
DB already allocated this way, so only the workbook per-área `resultado_bruto` TARGETS
(extracted from the buggy formula) were wrong and were blanking our correct values.
Corrected the three **May** targets via `_apply_despesas_area_override` in
`build_workbook_targets.py` (Contencioso 129.860,86 / Econômico 43.444,15 / Arbitragem
−39.855,42), mirroring the aluguel-override precedent. Scoped to May only. All 6 per-área
`resultado_bruto` cells now render live. **This was the last thing waiting on Renata.**
Remaining per-área blanks are Jan–Apr only, gated by the separate item-C classification
gap. Backend 235 tests.

## 2026-07-16 (later) — Meta dashboard fills full YTD

Commit `adf728b` (main, backend deployed + verified live). The Meta 2026 tab showed
realized Recebimento only for the competence month; now it fills **every closed month**
of the competence year. New `recebimento_by_year(year, *, client_id)` on both snapshot
stores (Supabase = one projected jsonb query; fs = per-month loop); the provider gathers
the map, filters to `is_closeable` months, threads `ytd_recebimento` through
AssemblerSource → assemble_dre_sections → assemble_meta. Total row fixed for YTD (Σ /
meta_anual / falta). Live 2026: Jan–Jun filled, Jul–Dec blank, Total 2.130.830,27,
%Meta 0,2644. Goal column stays budget-derived (BudgetEditor already provides the manual
goal input). Backend 234 tests.

## 2026-07-16 (later) — cleanup: manual editor removed + fluxo/total-row fixes

Commit `d8e8f6b` (main, deployed backend + frontend), in response to a user review of
the live UI:
- **Removed the manual "Lançamentos por área" editor entirely.** Comissão / Despesas
  Equipe / Despesa Institucional are all SISJURI-derived now, so hand-entry was
  vestigial. Backend (`manual_router`, `manual/models`, `manual/repository`, provider
  wiring, `AssemblerSource.manual`, `_area_rows`/`assemble_dre_sections` `man` params,
  `manual_actuals` DDL) + frontend (`ManualActualsEditor`, `useManualActuals`,
  WorkspacePage) + tests. **`area_transfers` (Resumo_Recebidas) is separate and kept.**
- **`fluxo_consolidado` now DB-derived** (was manual-only, blanked 9 cells on live May;
  now Recebimento/Despesas/Margem all fill from the same basis as the area DRE tabs).
- **Total/header rows no longer show "ainda não temos"** in structurally-empty text
  cells (the Moedas/Nacional Total-row placeholder bug). Frontend `TabView`.
- Tests: backend **227**, frontend **51**; ruff/mypy/eslint/tsc clean.

---

## 0. Client-confirmed business rules (DO NOT re-ask — 2026-07-10)

These were confirmed directly by the client (RUMO/MBC finance) and are now
canonical. An agent must NOT ask the user about these again.

> **Product endgame (confirmed 2026-07-13):** the site must **fully replicate the
> workbook** — every tab, faithful to the layout — not just the DRE/KPIs. The
> workbook (`Fechamento MBC 05.2026.xlsx`) is the source of truth; every displayed
> number must tie to it (hard rule: blank if it doesn't match). Data comes only
> from LegalDesk (revenue) + the SISJURI Oracle DB (costs/expenses); no Juritis API.

> **2026-07-10 follow-up meeting + source deep-dive:** the client was UNHAPPY with
> the current site numbers. `docs/MEETING_2026-07-10.md` is now the authoritative
> spec for the DRE fixes (all reconciled to the centavo against the May dashboard):
> **Imposto = 15% do Recebimento** (maio 62.389,20, não 7.510); **Amortização
> 8.117/mês**; **Resultado Líquido = Bruto − Imposto − Amortização** (maio 29.821);
> **Reserva de bônus = 10% do líquido**; **Custo direto = Custo equipe + Participação
> + Comissão**; **Recebimento por área** vem do Demonstrativo LegalDesk (Ambiental
> soma em Arbitragem, + linha "Não Alocados"); **Vale-ADM** está em `200.010.0010`
> (transitória, por histórico VR/VT); rateio institucional usa só despesas de EQUIPE.
> Também: **remover "Faturas emitidas"** do produto.
>
> **IMPLEMENTADO (2026-07-10):** (1) Imposto = 15% do recebimento
> (`workbook_layouts.imposto_sobre_recebimento`; deixou de somar o razão) — fev
> 47.885,04 / mai 62.389,20, bate com o dashboard; cadeia líquido/reserva
> corrigida por consequência. (2) **Regra dura** `app/closing/verification.py`:
> célula Realizado que divergir do alvo do workbook além de R$ 0,01 fica em branco
> ("ainda não temos"); overlay `targets` passa por `assemble_dre_sections`.
> (3) Recebimento por área agora funde **Ambiental→Arbitragem** e exclui
> **"Não Alocados"** (`match_area`). (4) **Custos Diretos = Custo equipe +
> Participação/Comissão** (`RealizadoInputs.custos_diretos`; Institucional
> Resultado Bruto passa a subtrair comissão) — fev 218.453,74. (5) KPI "Faturas
> emitidas" removido. Backend **179 testes**, frontend **49**; ruff/mypy/eslint/tsc
> limpos.
>
> **REGRA DURA LIGADA (2026-07-10):** targets extraídos do workbook autoritativo
> (`scripts/build_workbook_targets.py` → `app/closing/workbook_targets_2026.json`),
> carregados por `app/closing/workbook_targets.py` e passados via `provider.py` →
> `AssemblerSource` → `assemble_dre_sections(targets=...)`. Meses sem workbook =
> no-op. Números/layout documentados em `docs/SISJURI_DB.md` ("Workbook targets")
> e `docs/MEETING_2026-07-10.md` §VI. Backend **183 testes**, frontend **49**.
> PENDENTE: custo equipe por área do SISJURI (Econômico mai alvo 79.436,24) e
> rateio institucional só de EQUIPE — para as células saírem do branco e exibirem
> o valor; DL extras; Vale-ADM (200.010.0010).
>
> **IMPLEMENTADO (2026-07-13) — pontos da reunião 10JUL2026:**
> - **PONTO 12 — Amortização manual por ANO.** A amortização deixou de ser só a
>   constante `AMORTIZACAO_MENSAL=8117`. O usuário informa UM valor anual (linha
>   `amortizacao` do orçamento, já editável no `BudgetEditor` com preview `/mês`);
>   a linha mensal do DRE = anual/12. `RealizadoInputs.from_snapshot` recebe
>   `amortizacao_mensal` (do orçamento) e cai no default 8.117 quando ausente/zero.
>   Regra dura do workbook intacta (alvo 8.117 em todos os meses do book).
> - **PONTO 13 — Orçamento Despesa por equipe.** `despesas_equipe` virou linha
>   orçável; `BudgetEditor` ganhou uma seção "Orçamento Despesa por equipe"
>   (Contencioso/Econômico/Arbitragem). Armazenado por `(área, line_key)` no
>   plumbing de orçamento existente; flui para a coluna Orçado de cada aba de área
>   (`_area_rows` já lia `orc.get(DESPESAS_EQUIPE)`).
> - **PONTO 16 — Bônus equipe da conta 150.000.0000.** `_base_resultado_rows` lê
>   uma chave de snapshot `bonus_equipe` (Σ da conta 150.* — bloco novo no
>   `extract.sql`), preenchendo a linha "Bônus equipe" do bloco "Distribuição de
>   Lucros extras"; um `distribuicao_extras.bonus_equipe` explícito ainda vence.
>   Em branco ("ainda não temos") quando ausente — robusto ao split de sócios
>   (PONTO 17, tarefa do RUMO) chegar depois. Conta documentada em `SISJURI_DB.md`.
> - **PONTO 18 — Drill-down por profissional.** Na aba Base_Resultado, as seções
>   "Custo equipe - {área}" agora são clicáveis: expandem para as linhas por
>   profissional daquela área (recolhidas por padrão). Drill-down genérico no
>   `RichTabView` (chaveado nos grupos `custo_*`).
>
> Backend **192 testes**, frontend **52**; ruff/mypy/eslint/tsc limpos.
>
> **IMPLEMENTADO (2026-07-13, tarde) — validação com dados SISJURI ao vivo (maio):**
> Sessão dedicada com o operador rodando probes/extract no RDP `MBC-LDESK01`. Tudo
> commitado e no `main`; extract re-rodado ao vivo (HTTP 200, snapshot fresco no
> Supabase). Contra o snapshot REAL de maio, batem ao centavo com o workbook:
> - **T1 — Custo equipe por área** (2 correções): Vale (`custo_equipe_area`,
>   `500.010.<SIGLA>`) NÃO entra no custo direto; convênio (`030.010.0110`) usa a
>   "Parte MBC" de `convenio_memo`. Contencioso **74.141,21** · Econômico
>   **79.436,24** · Arbitragem **54.383,94**; Σ 207.961,39.
> - **T2 — Comissão** (bug null resolvido): a linha `030.010.0120` tem
>   `LANCAMENTO.LANCPROFDEST` NULL (sigla só no histórico); o extract passou a ler
>   `CONTASPAGAR.COD_ADVG`. Ao vivo: EHF 2.128,06 → Econômico. Custos Diretos
>   **210.089,45** (wb 210.089,46). Comissão derivada agora aparece nas abas de área
>   mesmo sem ledger (`has_comissao_deriv`).
> - **Regra dura: tolerância R$0,01 → R$1,00.** O workbook arredonda para reais
>   inteiros (mai Recebimento 415.928 vs sacred 415.927,84); a tolerância antiga
>   zerava toda a cauda institucional. Drift máx. em células deriváveis = R$0,16.
> - **T4 — Vale-ADM** de `200.010.0010` (transitória, histórico "VR/VT Mensal", ao
>   vivo 3.326,94) + FGTS-ADM (`020.050.0060`) reclassificado p/ Impostos →
>   **Salários Administração 12.344,91** (bate exato).
> - **Bug de rótulo:** `030.010.0120` "com**iss**ões" era classificado como imposto
>   (substring "iss"); `is_comissao_account` + match por palavra inteira corrigem.
> - **T3/T6 — Bônus equipe (150.*) / DL extras:** bloco roda ao vivo (null em maio, correto —
>   150.* só posta ~1×/ano em fev); linhas em branco quando ausentes.
> - **Contas Transitórias (correção do cliente):** é uma CLASSE de contas
>   (`200.010.0010/.0020/.0030/.0050/.0060`, `200.020.0030`, `300.010.*`), não um hub.
>   O sistema **desdobra** cada uma nas contas de despesa via o campo `ORIENTAÇÃO`
>   do LANCAMENTO/CONTASPAGAR. Documentado em `SISJURI_DB.md`.
> Backend **208 testes**, frontend **52**; ruff/mypy limpos. CI: uma falha do
> frontend foi blip de infra do GitHub ("Failed to resolve action download") — não
> do nosso código; backend verde em todos os commits.
>
> **IMPLEMENTADO (2026-07-13, noite) — DESPESAS INSTITUCIONAL DECODIFICADA (T5):**
> A reunião com o financeiro (Renata) + probes fecharam o mistério das despesas. A
> regra, provada ao centavo contra o workbook (**10/10 famílias**, resíduo total
> **R$129,17** = pendência do próprio cliente com a Malu, não nossa):
> - **Despesa = LÍQUIDO, não bruto.** O workbook lança o valor líquido (net do
>   imposto retido de terceiros) dos prestadores; o `GERENC` dá o bruto. Fonte do
>   líquido = **`FINANCE.CONTASPAGAR.CPGNVALORLIQUIDO`**. Ex.: Contabilidade Ozai
>   bruto 8.570 → líquido **8.042,94** (bate exato); Suporte Totvs bruto 3.108,97 →
>   líquido **2.917,77**; Terceirização Limpeza **3.346,68**.
> - **Desdobramento de lumps** (cartão de crédito Itaú 32.408, plano de saúde 31.882,
>   transitórias) → tabela **`FINANCE.CPDESDOBRAMENTO`** (`DESCCONTADESTINO`,
>   `DESNVALOR`, `DESCHISTORICO`), 1 linha por fatia desdobrada.
> - **Aluguel líquido de sublocação:** bruto 27.477,67 − crédito Belline 3.117,90 =
>   **24.359,77** (já é o valor da conta `020.010.0010` no GERENC — usar esse, não o
>   bruto do CONTASPAGAR). Workbook tem 24.230,60 → os **R$129,17** que a Renata vai
>   conferir com a Malu (provável defasagem da planilha).
> - **Reclassificações** (confirmadas pelo cliente): "Contratação do Claude" 2.166,53
>   é licença de software → Informática (não Material de Copa); Custas (`020.030.0140`)
>   e Transporte e Frete (`020.030.0060`) saem do row-198; Cursos `030.010.0180` →
>   Gestão do Conhecimento.
> - **Implementação:** `extract.sql` ganhou blocos aditivos `despesas_liquido`
>   (CONTASPAGAR net por conta) + `despesas_desdobramento` (CPDESDOBRAMENTO). Módulo
>   puro `app/closing/despesas_liquido.py::net_by_account` aplica a receita.
>   `dre.py::from_snapshot` sobrepõe o bruto de cada conta institucional pelo líquido
>   quando os blocos existem (no-op caso contrário — seguro até o re-run). Locked por
>   `tests/test_despesas_liquido.py` + 2 testes de integração.
> - **PENDENTE (o gargalo):** rodar o `extract.sql` atualizado no RDP para maio (e
>   demais meses) popular os blocos; então a linha Despesas fecha e **Resultado
>   Bruto/Líquido/Reserva/margens deixam de ficar em branco**. (Handoff detalhado
>   removido em 2026-07-28; regra provada vive em `docs/SISJURI_DB.md`.)
>
> Backend **218 testes**, frontend **52**; ruff/mypy limpos.
>
> **IMPLEMENTADO (2026-07-14) — despesas ao vivo, backfill validado, DL/convênio
> provados, Nacional/Moedas automatizadas:** sessão com o operador no RDP.
> - **T5 despesas ao vivo:** re-rodado o extract (net blocks `despesas_liquido` +
>   `despesas_desdobramento`) para mai; snapshot fresco no Supabase reproduz a receita
>   ao centavo (aluguel 24.359,77, contabilidade 8.042,94, licenças 7.239,10 etc.).
>   Despesas mai = **105.640,60**.
> - **Gargalo do daily job RESOLVIDO:** o `extract.sql` da box ficara defasado um dia
>   inteiro (rodava a versão pré-T5). `run-agent.ps1` agora **auto-atualiza o
>   extract.sql do `main`** a cada run (sanity-checked + fail-safe → nunca para).
> - **Autorização da Renata (aluguel–Belline é DB-autoritativo, só ele):** override
>   dos alvos abr+mai (+129,17 em despesas, propagado ao bruto/líquido/reserva). **Mai
>   agora renderiza a cauda inteira** (bruto 100.197,94, líquido 29.691,74, reserva
>   2.969,17) — deixou de ficar em branco.
> - **Backfill jan–mai + validação multi-mês:** só **mai bate ao centavo**; jan/fev/mar
>   divergem no **layer manual do cliente** (Vale-ADM batido à mão, splits de Associações
>   ÷2/÷3) — NÃO é bug de DB; documentado. Nossos números são discutivelmente *mais*
>   corretos que as células antigas do workbook.
> - **DL/convênio provados ao vivo:** convênio extra por advogado deduzido da DL
>   (DC 3.796,78 / RB 5.151,75 / EHF 1.398,01, em `500.010.<SIGLA>`); **Bônus equipe**
>   fev = 94.696,15 (`150.010.0010`) + 7.009,84 JGS (`030.010.0010`) = 101.705,84 (bate
>   o workbook). Blocos aditivos `convenio_extra_dl` + `bonus_equipe_030` no extract;
>   `bonus_equipe` no dre.py agora soma os dois.
> - **T8 — abas Nacional/Moedas AUTOMATIZADAS:** fonte `LDESK.DB_VW_FATURASEMI_REC`
>   **validada ao centavo** (Σ `VALOR_HONORARIOS_NAC` mai = 719.988,05 = sacred, split
>   R$ 708.659,18 + US$ 11.328,87). Bloco `faturas_moeda` (GROUP BY NUMERO, per-fatura)
>   + `SectionKey.NACIONAL/MOEDAS` + `assemble_faturas_moeda`. Falta só um re-run p/ o
>   snapshot carregar o bloco e as abas irem ao ar.
> - **PENDENTE:** re-run final (self-update pega o `faturas_moeda`); **POINT 17 —
>   automatizar o split sócio/funcionário do bônus NÓS (não é tarefa do RUMO —
>   decisão do usuário 2026-07-14):** probe `probe_socio_split.sql` (commitada, não
>   rodada) procura flag estrutural de sócio no DB; a sigla já vem no histórico do
>   150.* e as siglas vistas são todas funcionárias → 150.* pode já excluir sócios.
>   Depois: wire do `convenio_extra_dl` no split de DL. jan–abr = layer manual
>   (esperar cliente / aceitar número do DB). **Só o Orçamento fica fora.**
> Backend **224 testes**, frontend **52**; ruff/mypy/tsc limpos.
>
> **VALIDAÇÃO INDEPENDENTE (2026-07-14, fim de dia) — estado ao vivo corrigido:**
> Auditoria contra o Supabase ao vivo + testes + prod (não só os docs). O que
> **confere ao vivo**: gates verdes (backend **228** testes — não 224, agora são
> *mais* —, ruff/mypy limpos; frontend **52**, lint/tsc limpos); números sagrados
> travados; **maio fecha ponta a ponta a partir do snapshot REAL** (bruto 100.197,79,
> líquido 29.691,61, reserva 2.969,16 — dentro da tolerância R$1); **Nacional/Moedas
> batem EXATO ao vivo** (708.659,18 + 11.328,87 = 719.988,05 sagrado); `faturas_moeda`
> (45–59 linhas/mês), `convenio_extra_dl` (DC 3.796,78 / RB 5.151,75 / EHF 1.398,01)
> e `bonus_equipe_030` (fev 7.009,84) **já estão nos snapshots** — o "gargalo do
> file-pull" do handoff de 16:04 **já foi resolvido** por um re-run posterior.
> - **⚠ NOVO GARGALO (não sinalizado no handoff):** a correção do PONTO 17 (commit
>   `a0537b4`, 16:55 — repontou o bloco `150.%` para `FINANCE.LANCAMENTO` + exclusão
>   de sócio via `CAD_PROFISSIONAL.SOCIO`) entrou **DEPOIS** do último re-run. Logo,
>   nos snapshots ao vivo hoje: `bonus_equipe`(150.*) = **None** em TODOS os meses,
>   e `dl_excedente_socios` / `dl_excedente_mv` = **None**. O código + 17 testes
>   passam, mas **o número não aparece em produção até um NOVO re-run** do
>   `extract.sql` corrigido. A afirmação "PONTO 17 feito" é verdade *em código*, não
>   *ao vivo*. O bônus de fev 101.705,84 NÃO é reproduzível do snapshot atual (só a
>   parte JGS 7.009,84 está lá).
> - **Correção de rótulo:** "~95% automatizado" descreve a *capacidade do código* para
>   *maio*, não o estado ao vivo de todos os meses. Falta 1 re-run para o bônus/split
>   de sócio de fato renderizarem; jan–abr seguem no layer manual do cliente.
> Backend **228 testes**, frontend **52**; ruff/mypy/tsc limpos; prod no ar
> (`/api/health` → 200, frontend → 200).

- **No Juritis/TOTVS API exists — and none is planned.** The *only* non-LegalDesk
  data path is the **direct SISJURI Oracle DB** (read-only, via `MBC-LDESK01`).
  Section 5's "when the Juritis API arrives" is therefore moot; the `JuritisSource`
  placeholder will never be filled by an API. Treat the DB as the permanent source.
- **Authoritative reference workbook = `Fechamento MBC 05.2026.xlsx`.** On any
  conflict between books, 05.2026 wins. Its structure is the target layout.
- **A lawyer who works in two areas is ALWAYS split 50/50** (divide em 2) between
  the two areas — for custo de equipe and comissão. This is a fixed rule, never
  case-by-case. (This is the "Aurélio ÷2 / Beatriz" pattern.)
- **The workbook figure is the number of record.** Finance does not, and will not,
  reconcile against the DB. When our DB-derived number and the workbook disagree,
  the **workbook is the target** and any residual is ours to explain via the DB —
  never something to raise with finance as a DB question. Finance are not DB users.


## 1. What this is

A production-grade, multi-tenant SaaS turning the old single-tenant MBC
monthly-closing script into a web product sold to **RUMO**:

- **RUMO** logs in as **ADMIN** and sees **all clients**, drilling into any
  client's monthly closing.
- Each **client** (e.g. MBC) logs in as **CLIENT** and sees **only their own**.
- Competence month is chosen **in the UI** (replacing the old CLI `--month`),
  with an optional **day-range refinement** for date-driven tabs.

Stack: **FastAPI** (Python) backend + **React + TypeScript (Vite)** SPA.
Credentials and the LegalDesk password stay server-side; the browser only
talks to our authenticated backend.

---

## 2. Current status (built vs stubbed)

### Built and tested
- Backend scaffold, `/api/health`, env-driven `Settings` (no hard-coded secrets).
- Verified MBC data logic ported into `backend/app/` (period, builder, layouts,
  LegalDesk client) behind the new Source/Provider seams — behavior preserved.
- Auth: argon2 password hashing, JWT issue/verify, `POST /api/auth/login`,
  `GET /api/auth/me`.
- Tenancy: `User`/`Client` models, `Role` enum, `can_access_client`; server-side
  guards (`require_user`, `require_admin`, `require_client_access`).
- Repository abstraction: `Repository` protocol, in-memory `FakeRepository`
  (tests), `SupabaseRepository` (prod) + `app/db/schema.sql`.
- Data layer: `SectionKey` (15 sections), `DayRange`, `Source` protocol,
  `ClosingProvider` (ordered sources, later-overrides-earlier merge).
- Sources: `LegalDeskSource` (wraps verified builder; locked by recorded
  fixture), `FixtureSource` (demo client), `JuritisSource` (placeholder).
- API: `/api/clients` (admin list), `/api/clients/{id}` (tenancy-guarded),
  `/api/clients/{id}/closing?month=&from=&to=` (month validation + day-range).
- Idempotent Supabase seed script (`backend/scripts/seed.py`).
- Frontend: typed API client + `ApiError`, auth store with silent session
  restore, route guards (`RequireAuth`/`RequireAdmin`), design tokens +
  primitives, `MonthPicker` + `DayRangeFilter`, `LoginPage`, `ClientsPage`,
  `WorkspacePage`, `TabView` (rich + grid), app shell. All PT-BR, dark fintech.
  Tables have **sticky column headers** (`thead` pinned inside the scroll body);
  rich tabs (Meta, Base_Resultado, Resumo Recebidas, Faturas Centro Custo) render
  their real structure and fill not-yet-available cells with **"ainda não temos"**
  instead of a placeholder paragraph.
- **`.xlsx` export:** `lib/exportClosing.ts` turns a `ClosingPayload` into a
  multi-sheet workbook (one sheet per tab). WorkspacePage exposes "Exportar tudo"
  (all sheets) and "Exportar esta página" (current tab only). Uses SheetJS
  (patched CDN build `xlsx-0.20.3`, **0 npm audit vulns**), lazy-imported so it
  ships as a separate chunk and stays out of the initial bundle.
- CI: GitHub Actions running ruff + mypy + pytest (backend) and eslint + tsc +
  vitest (frontend) on push/PR.
- Docker: `backend/Dockerfile`, `frontend/Dockerfile` + `nginx.conf`,
  `docker-compose.yml`. **Smoke-tested:** `docker compose build` builds both
  images; backend container boots and serves `/api/health` → 200.

### Stubbed / placeholder (intentional)
- **`JuritisSource`** — documented placeholder, NOT wired. `supports()` returns
  empty; `fetch()` raises `NotImplementedError`. See §5 for the migration paths.
- **`FixtureSource`** — minimal deterministic demo data; exists only to showcase
  the admin multi-client view. Not real client data.

### Workbook-faithful DRE rework (2026-07-02)
The closing tabs now mirror `Copy of Fechamento MBC 02.2026.xlsx` in vocabulary
and structure (base = **Recebimento**, not Faturamento):
- `app/closing/workbook_layouts.py` — canonical section vocabulary + account-
  family rollups (`020./040.*` → institutional sections by `nome_conta_pai`,
  `030.*` → Custo equipe, Impostos → Impostos).
- `app/closing/dre.py` rebuilt: **Institucional** (DRE block + section-by-section
  expense breakdown with sub-accounts, % of Recebimento), **area tabs**
  (Recebimento/Custo equipe/Comissão/Despesas Equipe/Despesa Institucional/
  Resultado Bruto), **Base_Resultado Mensal** (hierarchical: per-lawyer custo
  equipe grouped by area + institutional sections/sub-accounts + Impostos).
- `app/closing/secondary_tabs.py` — **Amortização** real fixed schedule (8 × 2022
  originations, 60 parcelas each = R$ 8.117,32/mês) + **Rateio Mensal** per-area
  shares.
- `ops/sisjuri-agent/extract.sql` extended with `custo_equipe_prof` (per-lawyer ×
  account 030.*, area via professional→grupo). **Needs a re-backfill** to
  populate historical months (existing snapshots lack this key; Base_Resultado
  per-lawyer rows show only for months re-run with the new extract).

### Per-area Recebimento — RULE CONFIRMED, now auto-derived (2026-07-03)
Per-area **Recebimento** *is* derivable from SISJURI after all (the earlier
2026-07-02 note below is superseded). The receipt view splits by **case → área
jurídica**: `GERENC_VW_POSFIN_RESULTREC` (via `ID_CASO`) → `CAD_CASO.
ID_AREAJURIDICA` → `CAD_AREAJURIDICA.NOME`, summing `VALOR1`. Verified to the
centavo vs the workbook base numbers for Jan & Fev 2026. See
`docs/SISJURI_QUERIES.md` §9 (2026-07-03) for the query + table.

Built on top of that:
- **`extract.sql`** emits `recebimento_area` (this split), `faturamento_area`
  (same split on the faturamento view) and `faturas_analitico` (per-CASE
  faturamento detail from `GERENC_VW_POSFIN_RESULTFAT`). All 29 months
  (2024-01 → last closed) backfilled to Supabase (2026-07-03). The agent emits
  the JSON in DBMS_OUTPUT chunks so it never hits sqlplus's 32767 LINESIZE
  ceiling (see `run-agent.ps1`/`extract.sql`).
- **`dre.py`** `RealizadoInputs.area_recebimento` parses `recebimento_area` and
  folds names onto the three areas; area tabs' Recebimento is SISJURI-derived
  and **no longer hand-fillable** (with `Resumo_Recebidas` transfers applied
  upstream). Manual per-area recebimento is rejected by the API and ignored by
  the assembler.
- **`Resumo_Recebidas` transfers** modeled as `area_transfers` (origem→destino
  deltas, net 0) overlaid on the base — new `app/manual/transfers.py` +
  `area_transfers` table. These small cross-area reclassifications are still
  finance-entered (no DB rule), but the *base* is now automatic.
- **Distribuição de Lucros extras** block surfaced in `base_resultado` (Bônus
  equipe, DL Extraordinária, DL excedente sócios/MV, Repasse Cacione), values
  from optional snapshot `distribuicao_extras`, blank otherwise.
- **Budget granularity:** `BudgetEntry.monthly_amounts` (optional 12-value array)
  → workbook per-month Orçado; `monthly_budget(entries, month=...)` selects it;
  `budgets.monthly_amounts` jsonb column + API accepts/returns it. On a
  legacy/canonical key collision the entry with monthly detail wins (so an
  imported granular budget is never shadowed by an old annual seed).
- **Budget import from workbook:** `app/budget/workbook_import.py` +
  `scripts/import_budget.py` parse the `DRE 2026` sheet (per-area Custo equipe,
  institucional Recebimento/Despesas/Imposto/Amortização/Reserva) into
  `BudgetEntry`s with 12-month detail, upserted on (client,ano,area,line) so the
  **manual budget API still works** (imported lines refresh in place, manual
  lines under other keys are preserved). MBC 2026 imported (2026-07-03); the 4
  legacy annual-only seed rows were removed.
- **Meta dashboard:** new `meta_dashboard` tab (annual goal 8.060.000, monthly
  goal, this-month attainment, 12-month table) via `assemble_meta`.

Still manual (no verified DB rule): the `area_transfers` and
`distribuicao_extras`.

### Per-area Custo equipe — automation frontier (2026-07-07)

> **Direction correction.** The end goal is **full automation**: the client
> should do the *least* manual work possible. The workbook / dashboard /
> Demonstrativo are **development aids only** (ground-truth to validate against),
> **not** monthly inputs — nothing we ship may assume they arrive each month.
> Per the operating rule, we **assume automation is possible and only accept a
> manual artifact once impossibility is 100% proven.**
>
> The **workbook importer below mirrors the monthly workbook**, so it does NOT
> reduce their manual work and is **not** the automation path. It is retained
> only as an **offline validation harness** (it ties to the dashboard to the
> centavo) and a temporary fallback.
>
> **PROVEN full-automatable (2026-07-07 probe).** The read-only probe
> (`ops/sisjuri-agent/probe_distribuicao_area.sql`, results in
> `docs/SISJURI_QUERIES.md` §11) confirmed per-area Custo equipe is **fully
> derivable from SISJURI with no monthly manual input**: `FINANCE.LANCAMENTO`
> books Distribuição Mensal Fixa (`030.010.0010`) per **lawyer (`COD_ADVG`) ×
> area (`SIGLADEST` cost-center)**, ties to the centavo (Σ 172.129,96 Feb), and
> **encodes cross-area splits in the DB** (Beatriz BBX split 518,40 Contencioso /
> 7.537,40 Econômico — the "Aurelio ÷2" pattern, but booked at payment time). So
> a **future lawyer's split flows through automatically**. Next: wire the
> corrected extract (drop the bad `LANCHISTORICO` filter; fold distribuição by
> `SIGLADEST`→area into `custo_equipe_prof`), validate the three area subtotals
> to the centavo, then **remove the workbook importer** as a data path.

#### Validation harness / temporary fallback: workbook ledger importer
A **second workbook
sample** (`Fechamento MBC 05.2026.xlsx`, alongside the earlier `02.2026`)
confirmed the `Base_Resultado Mensal_V2` **structure is stable across months** —
every section header (`Custo equipe - {area}`, `Participação/comissão`,
`Repasse`, `Despesas Área`, `Despesas Institucional`, `Total saídas`) matches;
only per-lawyer rows churn as staff change, and each still follows the
`{Nome} - {TipoConta}` convention. The `05.2026` edition even formalized the
rateio into a named block (`Despesa para ratear` / `Equipe` / `Comissão` /
`CHECK`, rows 207-214), confirming the rule is deliberate.

- **`app/closing/ledger_import.py`** — pure, label-driven parser. Locates section
  anchors by column-A label (robust to row insertion) and reads their **cached
  values** (never the formulas — sidesteps the manual `=12500-C8`, `=3182.83/2`
  per-lawyer splits, which Excel has already resolved into the subtotal). Emits
  per-area `custo_equipe`, `comissao` (Participação+Repasse), `despesas_equipe`
  (Despesas Área). Derives per-area **Despesa Institucional** via the workbook
  rateio: `desp_inst[area] = (DespInstTotal − ΣDespesasÁrea) × (CE[area]/ΣCE)`.
- **`scripts/import_ledger.py`** — reads the workbook `Base_Resultado` sheet and
  merges a `ledger` block into each competence month's snapshot
  (read-modify-write, preserving all SISJURI data). Imports every month present
  in the sheet (columns C..N).
- **`dre.py` wired**: `RealizadoInputs.from_snapshot` reads the `ledger` block;
  when present it **overrides** the SISJURI `custo_area` per-area Custo equipe
  (the two do NOT reconcile — SISJURI is a raw DB aggregation, the ledger is the
  hand-maintained figure the client dashboard uses) and drives Comissão /
  Despesas Equipe / the derived Despesa Institucional. `_area_rows` prefers the
  ledger; manual entry remains the fallback for months with no ledger.
- **Parity: verified to the centavo** against the client dashboard `MBC Resultado
  Jan a Mai 2026.pdf` (YTD Jan–Mai): Contencioso Custo equipe 372.279,42 (dash
  372,3K), Despesas Equipe 11.996,28 (12,0K), Despesa Institucional 170.869,75
  (170,9K); Econômico/Arbitragem Custo equipe 389.116,53 / 282.414,08 (389,1K /
  282,4K). Institucional Faturamento/Receita still tie to the sacred numbers.
- **Institutional row-198 map SOLVED (account-keyed).** `probe_inst_csv.sql`
  dumped `FINANCE.VW_RESULTADO_MENSAL_DET` as CONTA3-keyed rows; reconciled to the
  centavo against Fechamento MBC 02.2026 + 05.2026. Workbook "Despesas
  Institucional" (row 198) = sum of 10 families (Ocupação, Telecom, Despesas
  Gerais, Consultoria, Salários Adm, Administrativas, Invest. Prospecção, Gestão
  do Conhecimento, Endomarketing, Informática); Impostos + Distribuição de Lucros
  + area lines are excluded. The verified account→family overrides now live in
  `workbook_layouts.py::section_for(nome_pai, id_conta)` (keyed on stable CONTA3
  codes, e.g. Contabilidade 020.040.0050→Consultoria, Seguros 020.060.0040→
  Ocupação). Locked by `tests/test_workbook_layouts.py`. The residual ≈5–7k
  workbook drift is line-attributed to a manual annualization layer
  (Administrativas/Gestão/Endomkt) that is NOT in the DB month. These become optional manual
  inputs now that the workbook is going away.

**Demonstrativo Resultado Profissional** (`..._AR_20260623_....pdf`): the
LegalDesk report the client now uses to allocate per-area recebimento — it
replaced the workbook's `Resumo_Recebidas` + `FATURAS Analitico` tabs (both
absent from `05.2026`). Per client direction it is used as **cross-validation**
of our already-verified SISJURI-derived per-area recebimento, not (yet) wired as
an ingestion source.

### Operator steps to finish the deploy
1. Apply the new DDL in Supabase (`area_transfers` table + `budgets.
   monthly_amounts` column + earlier `manual_actuals` — see `app/db/schema.sql`).
2. Update the on-server `extract.sql` and **re-run the backfill** so snapshots
   carry `recebimento_area`, `faturamento_area`, `faturas_analitico`
   (see "When to re-run the backfill" below).
3. Optionally verify `FAT_FATURA` columns with `probe_faturas_analitico.sql`
   before trusting `faturas_analitico`.
4. **Import the per-area ledger** so area tabs match the dashboard:
   `python -m scripts.import_ledger --workbook "reference/workbook/Fechamento MBC 05.2026.xlsx"
   --client mbc --ano 2026` (idempotent; merges a `ledger` block into each
   month's snapshot). Re-run whenever a new monthly workbook arrives.

### Test counts (as of last update)
- Backend: **224 passing** (`cd backend && pytest`). +6 on 2026-07-14: bonus_equipe
  from 030.010.0010 (2), Nacional/Moedas tabs (4), SectionKey count. Earlier +26 on 2026-07-13:
  live SISJURI validation — custo equipe 2 fixes, comissão null fix + area-tab
  display, R$1 tolerance (8 verification tests), Vale-ADM + FGTS reclass,
  comissão/imposto label fix, margin-blanking, and **T5 despesas at líquido +
  desdobramento** (`test_despesas_liquido.py` + 2 integration tests).
- Frontend: **52 passing** (`cd frontend && npm run test`).

### Production (EasyPanel + Supabase) — live 2026-06-22
- **Frontend:** https://rumo-frontend.xem1qi.easypanel.host
- **Backend API:** https://rumo-backend.xem1qi.easypanel.host (`/api/health` → 200)
- **Supabase:** project `skrwptamwbhwaiwwhrqj` — `schema.sql` applied, seed run (`mbc` + `demo` clients, three users).
- **EasyPanel:** project `rumo`, services `backend` + `frontend` (GitHub `femito1/rumo` @ `main`, Dockerfiles in `backend/` + `frontend/`).
- **Auth:** production uses Supabase (`USE_FAKE_REPO=0`). Dev zero-setup toggle still available locally.
- Env templates: `backend/.env.production.example`, `frontend/.env.production.example`.

---

## 3. Architecture at a glance

```
rumo/
├── backend/            FastAPI service (Python)
│   ├── app/
│   │   ├── main.py         app + CORS + router wiring + /api/health
│   │   ├── config.py       env-driven Settings.from_env()
│   │   ├── auth/           passwords (argon2), tokens (JWT)
│   │   ├── tenancy/        User/Client models, Repository, SupabaseRepository
│   │   ├── db/             schema.sql (clients + users)
│   │   ├── sources/        base (SectionKey/DayRange/Source), legaldesk,
│   │   │                   fixture, juritis (placeholder), legaldesk_client
│   │   ├── closing/        period, builder, layouts, available, provider
│   │   └── api/            deps, providers, auth_router, clients_router,
│   │                       closing_router
│   ├── tests/          pytest (unit + API + recorded-fixture integration)
│   ├── scripts/seed.py idempotent Supabase seeding
│   └── Dockerfile, pyproject.toml
├── frontend/           React + TS + Vite SPA
│   └── src/{app,features/{auth,clients,closing},lib,components,styles}
│       + Dockerfile, nginx.conf
├── .github/workflows/ci.yml
├── docker-compose.yml
├── PROJECT_STATUS.md   (this file)
├── CLAUDE.md           agent operating guide
├── docs/               LEGALDESK.md, DESIGN.md
└── reference/workbook/ ground-truth xlsx + Postman (not runtime)
```

Data flow: `provider`/`provider_config` on a client → ordered `Source`s →
`ClosingProvider.build_closing(period, day_range)` → provider-agnostic
`ClosingPayload` → SPA renders it regardless of upstream source.

---

## 4. Verified facts preserved (SACRED — never silently regress)

Source of truth: `docs/LEGALDESK.md`. Locked by backend tests
against the recorded fixture `backend/tests/fixtures/legaldesk_2026_05.json`:

- `recebimento_bruto('2026-05')` ≈ **415.927,84** (98 rows)
- `faturamento_bruto('2026-05')` ≈ **719.988,05** (97 rows)
- **53** distinct invoices in May 2026
- Historicals: jan/2026 = **279.821,07** · fev/2026 = **319.233,58**
- `RateioFaturaProfissionalViews` rows are **duplicated** — de-dup by
  `(FaturaNumero, ProfissionalSigla)`.
- Workbook year is **2026** (not 2025). OData **v3** syntax.

If a change moves any of these numbers, it is a bug until proven otherwise.

---

## 5. Juritis-readiness (the defining constraint)

> **UPDATE 2026-07-01 — may be partly obsolete.** The institutional expenses this
> section assumes live only in TOTVS Backoffice were found in the **SISJURI Oracle
> DB** (`FINANCE` schema), readable today via the bridge server. See
> `docs/SISJURI_DB.md` §"Full-closing coverage". A `FinanceDbSource` could supply
> the expense side without waiting for the Juritis API. Revisit the paths below
> in light of that. Reconciliation of exact per-line DRE definitions is still open.

> **SUPERSEDED (2026-07-10, client-confirmed): there is NO Juritis/TOTVS API and
> none is planned.** The only non-LegalDesk source is the SISJURI Oracle DB (see
> §0 and §6b). The `JuritisSource` placeholder stays as a generic seam but will
> never be backed by an API. The paths below are kept for historical context only.

The Juritis / TOTVS Backoffice API ~~is coming but its shape is **unknown**~~. The
data layer is built so integrating it is a localized change, never a frontend or
contract rewrite. When access arrives, pick one path:

1. **Additive** — add `JuritisSource` supplying the institutional-expense
   SectionKeys; merge fills previously-MANUAL lines. LegalDesk untouched.
2. **Partial override** — Juritis supplies some sections LegalDesk also did;
   `merge_policy` sets per-section precedence (later source wins).
3. **Full replacement** — a client's provider lists `[JuritisSource]` instead
   of `[LegalDeskSource]`. LegalDesk stays for clients still on it.

In all three, the API contract and the SPA are unchanged: cells just carry a
different `origin` tag (`juritis` instead of `manual`).

---

## 6. Known limitations / tech debt

Non-blocking items found during review. Fix opportunistically; add new ones here.

- **Login timing oracle (low):** login compares password only when the user
  exists, so response timing can hint whether an email is registered. Acceptable
  for a small known user set; mitigate later with a constant-time dummy verify.
- **`DayRange` calendar validation gap (low):** `DayRange.within` trusts the
  caller's day bounds; it does not reject impossible days (e.g. day 31 in a
  30-day month) beyond basic ISO formatting. The closing endpoint clamps to the
  month, so impact is limited, but explicit validation would be cleaner.
- **`FixtureSource` is not representative:** demo numbers are arbitrary; do not
  use them to reason about real behavior or in screenshots shown to clients.
- **JWT secret length warning in tests:** test secrets are short and trigger a
  PyJWT `InsecureKeyLengthWarning`. Production secret comes from env and must be
  ≥ 32 bytes.
- **`docker compose up` needs `backend/.env`:** compose references
  `env_file: ./backend/.env`. Copy `backend/.env.example` → `backend/.env`
  before `up`. The `.env` is gitignored and must never be committed.

## 6b. SISJURI direct DB access (discovered 2026-07-01)

An **Oracle 19c** database behind SISJURI is reachable **read-only** through the
authorized Windows bridge server `MBC-LDESK01` (the Power BI gateway host). It
contains the **`LDESK`** schema (601 tables) — the same LegalDesk data RUMO pulls
via OData — and **`SSJR`** (704 tables) of SISJURI core data. Confirmed: real
`SELECT` on `LDESK` billing tables, 98 months of history (2018-05 → 2026-06),
53 May-2026 invoices matching the sacred `faturas_emitidas`. This opens an
**audit / fallback / alternative-`Source`** path to the API. Details, schema map,
and the (hard-won) `sqlplus`-over-RDP invocation recipe live in
`docs/SISJURI_DB.md`; the implementation-ready SQL per DRE line and the egress
options live in `docs/SISJURI_QUERIES.md`. The DB and RDP credentials used during
discovery were shared out-of-band and **must be rotated**; never commit them.

**Now partially wired (2026-07-02).** Full closing proven sourceable from the DB
via three objects + one fixed formula: revenue (`GERENC_VW_POSFIN_RESULT*`),
expenses gross/competence (`GERENC_LANCAMENTORESUMO`), pró-labore gross
(`CONTASPAGAR.CPGNVALORBASE`), and reserva de bônus = 10% da margem líquida
(finance-confirmed). Built so far:

- **On-server agent** `ops/sisjuri-agent/{extract.sql, run-agent.ps1}` — pure
  PowerShell + the existing `sqlplus` (no Python on the box), emits one JSON
  snapshot per competence month, TLS-1.2 outbound POST. Verified on the server:
  `closing_2026-02.json` (recebimento 319.233,58; 30 expense accounts).
- **Egress = Option A** (server pushes to VPS): `POST /api/ingest` (bearer-token,
  `INGEST_TOKEN`) stores snapshots via the snapshot store.
- **Snapshots persist in Supabase (2026-07-03).** `sisjuri_snapshots`
  (`client_id, ano_mes, payload jsonb`, PK `(client_id, ano_mes)`) is now the
  durable, multi-tenant source of truth — the whole financial dataset lives in
  Postgres alongside `budgets`/`manual_actuals`, not on the VPS disk.
  `SupabaseSnapshotStore` is selected in prod; the filesystem `SnapshotStore`
  (`SNAPSHOT_DIR`) remains the `USE_FAKE_REPO`/local-dev fallback and gained
  client scoping (with a legacy clientless-filename read fallback). `client_id`
  flows through `/api/ingest` (`meta.client_id`, default `"mbc"`) and the closing
  read path (`client.id`). The agent stamps `meta.client_id`. A one-time
  token-protected `POST /api/ingest/migrate-fs-to-supabase` copied the existing
  30 months (2024-01 → 2026-06) into Supabase; verified the closing endpoint now
  reads from Supabase with the sacred numbers intact.
- **`app/sources/sisjuri_db.py`** (`SisjuriDbSource`) consumes a snapshot and
  emits `SectionKey`s, encoding the pró-labore-gross and bonus-reserve rules.
  Tested against a recorded fixture (`tests/fixtures/sisjuri_2026_02.json`).
- **`ClosingProvider`** now has a `legaldesk+sisjuri` mode: composes
  `LegalDeskSource` (KPIs) with `SisjuriDbSource` in augment mode (institucional),
  preserving the sacred numbers.
- **LIVE on EasyPanel (2026-07-02):** `POST /api/ingest` is deployed and verified
  end-to-end — 401 without/with-wrong token, 422 on missing `meta.ano_mes`, 200 on
  the real Feb-2026 snapshot, persisted to a named volume `sisjuri-snapshots` →
  `/data/snapshots` (survives redeploys). **Root-cause fix:** the `backend` service
  was building via **Nixpacks** (wrong start cmd `python -m rumo-backend` → boot
  crash / 502); switched `build.type` to **`dockerfile`** so it uses the tested
  `backend/Dockerfile` (`uvicorn app.main:app`). `INGEST_TOKEN` is set in the
  EasyPanel backend env (not committed).
- **SCHEDULED & LIVE (2026-07-02):** `RUMO-SISJURI-Agent` runs daily at 06:00 on
  MBC-LDESK01 for the previous full month, extracts, and pushes to the VPS.
  Verified `LastTaskResult=0` (2026-06 snapshot uploaded). Constraints found on
  that box: `bia4u` is **not** a local admin, so env vars are **User-scope** and
  the task **runs as `bia4u`** (not SYSTEM). "Run whether logged on or not"
  needed the *Log on as a batch job* right, which an admin granted to `bia4u`
  (error `2147943785` until then). `register-task.ps1` now has `-StorePassword`
  (run-as-user) and `-AsSystem` modes.
- **Agent upload:** must send the body as **UTF-8 bytes** with an explicit
  charset (fixed in `run-agent.ps1`); a plain string body 400s on FastAPI,
  especially with accented account names.
- **Still TODO:** rotate the DB/RDP credentials that were shared in chat.

---

## 6c. Workbook mirror + manual budget (2026-07-02)

The deployed closing page now mirrors the MBC workbook DRE structure and adds a
manually-entered Orçado (budget) for Orçado × Realizado variance. Built:

- **DRE engine `app/closing/dre.py`** — a canonical DRE line-key registry
  (`faturamento`, `custos_diretos`, `despesas_indiretas`, `resultado_bruto`,
  `margem_bruta`, `impostos`, `amortizacao`, `resultado_liquido`,
  `margem_liquida`, `reserva_bonus`) shared by the SISJURI source, the budget
  domain and the frontend. `assemble_dre_sections` computes the **Institucional**
  block plus three area blocks (Contencioso/Economico/Arbitragem) and
  `areas_sintetico`, each row carrying `orcado | realizado | variacao | desvio%`.
  It **recomputes** from clean sources (not the workbook cells, which have
  `#REF!`s). Reserva de bônus = 10% da margem líquida; amortização = fixed
  monthly institutional installment.
- **`SisjuriDbSource` expanded** — emits rich, grouped expense detail
  (`INSTITUCIONAL_ANO`, section subtotal + indented sub-accounts) plus
  `RATEIO_MENSAL` (per-area team cost + per-lawyer rateio), prolabore (gross/net)
  and distribuição tables. The assembled DRE owns `INSTITUCIONAL`.
- **Budget domain `app/budget/`** — `budgets` Supabase table
  (`client_id, ano, area, line_key, annual_amount`; DDL in `app/db/schema.sql`),
  `BudgetRepository` (supabase + in-memory seeded), annual granularity split
  evenly to monthly. `BudgetSource` emits the `ORCAMENTO_2026` reference tab.
- **Budget API** — `GET/PUT /api/clients/{id}/budget?ano=YYYY`, guarded by
  `require_client_access` (ADMIN + that client's CLIENT may edit). Validates
  area/line keys. Seeded placeholder budget (Meta 8.060.000/ano) for MBC 2026.
- **Provider composition** — `legaldesk+sisjuri` now composes
  LegalDesk → SisjuriDb → Budget → **Assembler** (last, overrides). Headline KPIs
  (`resultado_bruto`, `margem_bruta`, `resultado_liquido`, `margem_liquida`,
  `reserva_bonus`) are lifted from the assembled DRE into the `kpis` map. When no
  snapshot exists the DRE still renders with `snapshot_missing: true`.
- **Frontend** — new KPI cards (with `formatPercent`/`formatNumber` and a
  `KpiCard format` prop); `RichTabView` renders DRE percent columns, section/total
  rows and indented sub-accounts; a PT-BR **missing-data banner**
  ("Dados institucionais ainda não importados para este mês") on institucional/DRE
  tabs; a **budget editor** panel (`BudgetEditor` + `useBudget` hook in its own
  module) for ADMIN and CLIENT. Spinner already existed. New rich tabs export via
  the existing `exportClosing.ts` automatically.
- **Backfill** — `ops/sisjuri-agent/backfill.ps1` loops 2024-01 → last closed
  month calling `run-agent.ps1` per month (one-shot catch-up; the daily task
  keeps recent months fresh). Documented in the agent README.
- **MBC provider** — the fixture/demo MBC client is now `legaldesk+sisjuri`. The
  **prod `clients.provider` for MBC must be set to `legaldesk+sisjuri`** for this
  to show live.

**Tests:** backend 95 passing (new: DRE assembler math/variance/margins,
BudgetSource, budget repo/API auth boundary, provider composition with all four
sources, snapshot_missing flag; sacred-number lock still green). Frontend 44
passing (new: `formatPercent`/`formatNumber`, DRE percent + grouped/indent
rendering + banner, BudgetEditor). Backend `ruff`+`mypy` clean; frontend
`lint`+`typecheck` clean.

**Operator TODO before this is fully live:**
1. Apply the `budgets` DDL (`backend/app/db/schema.sql`) to Supabase.
2. Set MBC's `clients.provider = 'legaldesk+sisjuri'` in Supabase.
3. Deploy backend+frontend (GitHub → EasyPanel, Dockerfile build).
4. Run `backfill.ps1` once on MBC-LDESK01, then verify a few months via
   `GET /api/ingest/{ano_mes}/summary`.

---

## 7. Future plans / phases (out of v1, noted not precluded)

- Implement `JuritisSource` once the API is available (see §5).
- Evolution API (WhatsApp) closing notifications.
- Password-reset emails; self-serve client onboarding UI.
- Per-request audit logging for ADMIN cross-client access.

---

## 8. Run / test / deploy

See `README.md`. Quality gates: backend `ruff` + `mypy` + `pytest`; frontend `lint` +
`typecheck` + `vitest`. Update this file when status changes.

---

## 9. Conventions (enforced)

- **TDD:** a failing test precedes every new function/endpoint.
- **Secrets:** never committed or shipped; always from env / `.env.example`.
- **Sacred numbers:** the verified LegalDesk totals (§4) must not regress.
- **UI is PT-BR**, money formatted as `R$ 415.927,84`.
- **New data sources** implement the `Source` protocol and emit `SectionKey`s;
  they never touch the API contract or the SPA.
- **Tenancy boundary is server-side.** Hiding a frontend button is never the
  security boundary; `require_client_access` is.
- Conventional, focused commits.
