# HANDOFF — Full DRE automation from SISJURI (2026-07-08)

> **Read `PROJECT_STATUS.md` and `docs/SISJURI_QUERIES.md` (§11–§13) first.**
> This handoff is the narrative of *why* we are where we are and *exactly* what
> the next agent should do. It supersedes nothing; it points at the durable docs.

## North star (do not lose this)

Fully automate the monthly closing so the client does the **least manual work
possible**. The workbook (`Fechamento MBC MM.YYYY.xlsx`), the dashboard, and the
Demonstrativo PDF are **development/validation aids only** — ground-truth to
reconcile against. Nothing we ship may assume they arrive each month.

Operating rule: **assume a line is automatable and only accept a manual artifact
once impossibility is 100% proven** with read-only DB probes.

## The decision that governs the next steps

The user chose, on the two open forks:

1. **Institutional total source:** *verify against more months / probe harder*
   before locking it — BUT the governing principle is now explicit:
2. **Per-area allocation:** *probe `DB_RESULTADO_AREA` harder*, **but nonetheless
   we MUST match the workbook logic.**

So the north star for the institutional lines is: **reproduce the workbook's
methodology** (rateio by **custo-equipe share**, already implemented in
`dre.py::despesa_institucional_rateio`), using **DB-sourced inputs**. The DB's
own per-area DRE (`DB_RESULTADO_AREA`, per-capita/peso allocation) is a
*cross-check*, not the target — unless probing proves it equals the dashboard.

## The lesson (what wasted time and what unlocked it)

- **The trap we fell into:** treating "the workbook is wrong" as the escape hatch
  when a DB rollup didn't tie to the centavo. Wrong instinct. The workbook is
  mostly right; small deltas are human hand-keying, which is exactly why we hold
  **two** workbook samples (`02.2026` and `05.2026`) to distinguish a *rule* from
  a *typo*. Always diff a candidate DB rule against BOTH books before concluding.
- **What actually unlocked institutional:** we had never queried the DB's own DRE
  engine. Schema discovery (`probe_schema_inst.sql`) surfaced
  `FINANCE.VW_RESULTADO_MENSAL[CC]`, `LDESK.DB_RESULTADO_AREA`,
  `LDESK.GERENC_LANCAMENTORESUMORATEIO`, `LDESK.DB_VW_DEMONSTRATIVO_RESULTADOS`.
  `VW_RESULTADO_MENSAL` returns the entire DRE by line class (`TIPO`), with
  `TITULO1/2/3` hierarchy, `SETOR` (cost-center) and an `ORCAMENTO` column. Its
  `TIPO='S'` NIVEL-2 titles ARE the workbook's institutional families exactly.
- **Takeaway for future stuck lines:** before hand-deriving from raw
  `LANCAMENTO`/`RESUMO`, check whether LegalDesk already computes the number in a
  `DB_*` / `VW_RESULTADO_*` view. It usually does.

## Current automation status (honest)

| DRE line | Status | DB source | Notes |
|---|---|---|---|
| Receitas | automated (LegalDesk) | honorários + financeira | unchanged |
| Custo equipe (per area) | **PROVEN automatable** | `FINANCE.LANCAMENTO` `030.010.0010` by `COD_ADVG` × `SIGLADEST`→area | §11; ties Σ 172.129,96 Feb; cross-area splits encoded in DB. Wire it. |
| Comissão (per area) | **DONE, shipped** | `020.110.0010` (area) + `030.010.0120` (per-lawyer `LANCPROFDEST`) | §12a; `comissao_deriv.py`, wired in `dre.py`, ties to centavo both months |
| Despesa Institucional TOTAL | **DB-derivable, needs multi-month verify** | `VW_RESULTADO_MENSAL` `TIPO IN ('S','I')` minus Comissões | §13; workbook row-198 drifts ~R$3k (regroup + hand-keyed lines). Verify Jan..Mai vs both books. |
| Despesa Institucional per-area (rateio) | **must match workbook logic** | custo-share rateio (in `dre.py`) on the DB total | §13c; DB_RESULTADO_AREA uses per-capita/peso (different). Keep workbook rule. |
| Despesas Área (direct) | account set DB-correct; per-area split hand-done | area-tagged non-030 `020.030/060/080/090` | Appendix A3: DB per-area ties partially (Arb exact); workbook re-buckets Cont/Econ by hand. Needs workbook area mapping, not DB tag. |
| Orçamento | not in DB | — | `ORCAMENTO` column exists but is 0 for 2026; out of scope |
| area_transfers, distribuicao_extras | manual | — | small, defer |

## Key DB facts learned (see §13 for full detail)

- `VW_RESULTADO_MENSAL` `TIPO` map: `E`=Receitas, `C`=Custos c/ Pessoal,
  `S`=Despesas (institucional), `I`=Investimentos, `O`=Obrigações Fiscais,
  `L`=Distribuição de Lucros. Feb 2026: E 319.234,91 / C 215.310,35 /
  S 68.771,58 / I 30.913,70 / O 11.687,83 / L 94.696,15.
- `SETOR` codes are cost-centers **ECT/EDE/ESP/ADM**, NOT the workbook's
  Contencioso/Econômico/Arbitragem. Same re-bucket problem solved for Custo
  equipe applies here — reuse `custo_equipe_deriv`'s home-area mapping.
- `DB_RESULTADO_AREA` is populated every month (Jan..Mai present) with
  CUSTO_DIR/CUSTO_IND/DESP_DIR/DESP_IND/INV per area, but its DESP_IND uses
  **per-capita + peso** weighting → Feb Cont 59.085,78 / Econ 50.519,53 /
  Arb 67.502,34. This does NOT equal the workbook's custo-share rateio.
- `ORCAMENTO` is present but zero for 2026 — no budget in the DB.

## Do next (in order)

1. **Verify the institutional TOTAL rule across all months.** Run
   `probe_resultado_mensal.sql` (already in repo) for Jan..Mai; compute
   `TIPO IN ('S','I')` − Comissões per month; diff against BOTH workbooks'
   row-198. Confirm the delta is small + both-signed (human drift), not a
   systematic rule. If confirmed: the DB total is authoritative.
2. **Probe `DB_RESULTADO_AREA` harder** (new probe) to answer: does its per-area
   split EVER equal the dashboard/workbook per-area? Compare
   `DESP_IND+INV` per area to the workbook's rateio'd Despesa Institucional per
   area for Feb AND May. If it matches on a mapping we missed → use it. If not →
   confirm we keep the workbook's custo-share rateio (`dre.py`) on the DB total.
3. **Add the institutional-total extract block** to `extract.sql`
   (`inst_total_deriv`): one row per competence month with the `S` and `I`
   subtotals and the Comissões subtotal, from `VW_RESULTADO_MENSAL`. Keep it
   additive; do not change the API/SPA contract.
4. **Wire Custo equipe (§11)** — the corrected extract (drop the bad
   `LANCHISTORICO` filter; fold distribuição by `SIGLADEST`→area into
   `custo_equipe_prof`), validate the three area subtotals to the centavo.
5. **Only after live validation:** retire the workbook importer as a data path
   (keep it as an offline validation harness). Then update `PROJECT_STATUS.md`,
   `CLAUDE.md`, delete `ledger_import.py` + `scripts/import_ledger.py` +
   `test_ledger_import.py`.

## Talking to git / running probes from the RDP box (READ CAREFULLY)

This is the single most fragile part of the workflow and it wastes an hour every
time it's rediscovered. The DB is only reachable from **`MBC-LDESK01`** (Windows
Server 2012, **PowerShell 3–4**, Oracle 11g client). We ship probes by pushing a
`.sql` to the **public** GitHub repo (`femito1/rumo`, branch `main`) and pulling
it over HTTPS on the box. The full canonical version lives in
`ops/sisjuri-agent/README.md` §"Ad-hoc probes over RDP" — keep both in sync.

### Two hard gotchas (both bite every session)

1. **TLS 1.2 is OFF by default.** `Invoke-WebRequest` to GitHub fails with
   *"The request was aborted: Could not create SSL/TLS secure channel"* until you
   enable it. Run this ONCE per PowerShell window before any pull.
2. **Multi-line / here-string commands are unreliable.** Paste **one command per
   line, no line continuations** (no backtick-newline, no backslash). Build any
   multi-line SQL wrapper with an inline `` `r`n `` inside a single
   `Set-Content`. NEVER paste a `foreach {...}` block or a `$base=...; foreach`
   one-liner — they silently misbehave in the 2012 shell. One URL, one file, one
   run, at a time.

### The fixed recipe (copy ONE line at a time)

Paths: agent dir `C:\temp\sisjuri`; sqlplus at
`C:\oracle11\app\product\11.2.0\client_1\bin\sqlplus.exe`; DB password in
`$env:SISJURI_PASSWORD`; DB user `RGN`; host `172.16.237.9:1521`; service
`cdbp01_pdb1.submbc.vcnmbc.oraclevcn.com`.

```powershell
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$env:SISJURI_PASSWORD = '<RGN password>'
Invoke-WebRequest -UseBasicParsing "https://raw.githubusercontent.com/femito1/rumo/main/ops/sisjuri-agent/probe_NAME.sql" -OutFile C:\temp\sisjuri\probe_NAME.sql
Set-Content C:\temp\sisjuri\q.sql -Encoding ASCII -Value ("CONNECT RGN/""$($env:SISJURI_PASSWORD)""@(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=172.16.237.9)(PORT=1521))(CONNECT_DATA=(SERVICE_NAME=cdbp01_pdb1.submbc.vcnmbc.oraclevcn.com)))`r`n" + (Get-Content C:\temp\sisjuri\probe_NAME.sql -Raw))
& 'C:\oracle11\app\product\11.2.0\client_1\bin\sqlplus.exe' -S /nolog '@C:\temp\sisjuri\q.sql' *>&1 | Tee-Object C:\temp\sisjuri\out_NAME.txt
```

Then paste the contents of `out_NAME.txt` back into chat. Replace `probe_NAME`
throughout with the real filename.

### To ship a NEW probe from the dev machine

```bash
git add ops/sisjuri-agent/probe_NAME.sql
git commit -m "Add probe_NAME: <what it checks>"
git push origin main
```

The repo is public, so the raw URL is live within seconds. No base64, no
clipboard paste, no scp. Pull it on the box with the recipe above.

### Query pitfalls (do not rediscover)

- `FINANCE.LANCAMENTO` has **NO** `ID_GRUPOJURIDICODEST` (→ `ORA-00904`). Area of
  a cash movement is `SIGLADEST` (cost-center) or the destination professional's
  home grupo — not a group column on the row.
- Accents render as `\Uffffffff` in the sqlplus console — **display artifact
  only**; the extract's UTF-8 (`NLS_LANG=.AL32UTF8`) is fine.
- `GERENC_LANCAMENTORESUMO` does not carry every account (Vale `030.010.0100/0220`
  and some personal lines live in the `500.010.<SIGLA>` namespace in `LANCAMENTO`).
- SET DEFINE OFF is baked into extract.sql-style files; probes that use `&ANO_MES`
  substitution should keep it or hard-code the month.

## Files that matter

- `ops/sisjuri-agent/extract.sql` — the monthly extract (add `inst_total_deriv`).
- `ops/sisjuri-agent/README.md` — canonical RDP recipe (keep in sync with above).
- `ops/sisjuri-agent/probe_resultado_mensal.sql` — the institutional-total probe.
- `ops/sisjuri-agent/probe_rateio_applied.sql` — DB_RESULTADO_AREA / RATEIO probe.
- `docs/SISJURI_QUERIES.md` §11 (Custo equipe), §12 (Comissão), §13 (DRE engine).
- `backend/app/closing/comissao_deriv.py` + `custo_equipe_deriv.py` — deriv logic.
- `backend/app/closing/dre.py` — assembly; `despesa_institucional_rateio` is the
  custo-share rule we must keep.
- Validation workbooks: `reference/workbook/Copy of Fechamento MBC 02.2026.xlsx`
  and `reference/workbook/Fechamento MBC 05.2026.xlsx` (use BOTH).

---

## Appendix A — concrete probe evidence (do not re-run to rediscover)

These are the real numbers from the probe transcript. Keep them; they are the
baseline the next agent validates against.

### A1. Institutional total: DB `020+040 − comissão` vs workbook (row 198)

| Month | DB `020+040−com` | Workbook row-198 | Δ (DB−WB) |
|---|---|---|---|
| Jan | 104.765,06 | 100.181,41 | +4.583,65 |
| Feb | 98.185,28 | 95.047,39 | +3.137,89 |
| Mar | 100.981,35 | 101.968,90 | −987,55 |
| Apr | 110.214,88 | 110.156,11 | +58,77 |
| Mai | 105.784,26 | 105.511,43 | +272,83 |

Deltas are small and **both-signed** → workbook manual drift, not a rule. Note
`020.*`==`TIPO_CONTA='D'` exactly every month; `040.*`==`TIPO_CONTA='I'`.
`VW_RESULTADO_MENSAL` gives the same pool cleanly as `TIPO='S'` (=`020` minus
comissão minus the area-tagged that move to Despesas Área) + `TIPO='I'` (=`040`).

### A2. Workbook row 198 is a hand-maintained regroup (authoritative-side proof)

Row 198 formula = `C85+C92+C95+C110+C116+C124+C137+C158+C164+C180` — ten family
subtotals, NOT "all 020+040". The workbook families do **not** equal DB account
groups: workbook "Consultoria" 22.509,85 vs DB `040.030 Consultoria` 14.705,80;
workbook "Informática" 17.620,95 vs DB `040.040` 8.756. It moves Seguros into
Ocupação, splits Serviços de Terceiros across Consultoria/Informática, and
carries lines with **no DB row** (Seguro Locação 183, Camera Ed. Lacerda). The
regroup nets ~0 within families; the residual per-month Δ is hand-keying.

### A3. Despesas Área: account SET is DB-correct, per-area SPLIT is hand-done

Excluding `030.*` (Custo equipe), Administração and comissão, the area-tagged
non-030 lines (`probe_inst_final` §2) give:

| Month | DB Cont | DB Econ | DB Arb |
|---|---|---|---|
| Feb | 2.346,72 | 2.129,32 | 2.633,69 |
| Mar | 2.346,72 | 2.672,54 | 3.711,92 |
| Apr | 2.602,58 | 2.231,52 | 4.849,55 |
| Mai | 995,03 | 2.204,82 | 1.272,47 |

Workbook Feb Despesas Área = Cont 2.129,32 / Econ 3.296,07 / Arb 2.633,69. Arb
ties; Cont/Econ are **re-bucketed by hand** (workbook moves Feb "Eventos e Happy
Hour" 1.166,75 from Administração into Econômico; DB-Cont 2.346,72 ≠ WB-Cont).
Only families `020.030 / 020.060 / 020.080 / 020.090` (+`020.110` comissão) ever
carry a DRE-area tag — that IS the Despesas Área candidate set. So this is the
**same "workbook re-buckets area" pattern as Custo equipe**, not a missing
number. To match the workbook we need the workbook's area mapping, not the DB tag.

### A4. Unexplored schema angles (for the "probe DB_RESULTADO_AREA harder" task)

- `GERENC_LANCAMENTORESUMO` exposes **`NOMESUBAREA` / `ID_SUBAREAJURIDICA`** (a
  subarea dimension) and `TIPO_DASHBOARD` — never queried. The subarea may hold
  the workbook's finer area split.
- `FINANCE.PLANOCONTAS` has **`PCTCFLAGRATEIO`, `CRITERIORATEIO`, `RATNCODIG`,
  `RATCCODIG`** (per-account rateio config) and `PCTCFLAGSETOR` — may encode how
  each account is allocated to areas.
- `LDESK.GERENC_VW_PERC_GRUPOJURIDICO` has `ID_GRUPOJURIDICO`, `PERC_GRUPO`,
  period columns — **candidate for the Associações `/3`-style area split rule**.
  Unprobed.
- `LDESK.DB_RESULTADO_AREA` area names are **Ambiental / Arbitragem MV /
  Contencioso / Direito Econômico** (NOT the workbook's Cont/Econ/Arb labels) and
  it splits indirect cost into `DESP_INDIRETA_PERCAPITA` + `DESP_INDIRETA_PESO`
  (headcount/effort weighting). Feb per-area DESP_IND+INV: Cont 59.085,78 / Econ
  50.519,53 / Arb 67.502,34 — a *different methodology* from the workbook's
  custo-share. `DESP_DIRETA` is 0 in `GERENC_LANCAMENTORESUMORATEIO` for the DRE
  areas, so it does NOT hand you Despesas Área directly.
- `FINANCE.VW_RESULTADO_MENSAL_DET` is line-level (`LANNCODIG`) with the same
  `TITULO1/2/3 + SETOR + ORCAMENTO` — use it to see which raw lançamentos land in
  each `SETOR`, to crack the SETOR(ECT/EDE/ESP/ADM)→workbook-area mapping.

### A5. Custo equipe override map (the small irreducible manual bit)

Custo equipe is DB-derivable to the centavo in unit test, EXCEPT a tiny set-once
override map (read from raw memos; not in any DB column):
- EHF / RB convênio: 1.564,10 / 2.526,09
- AM / DC AASP: 54,35/mo
- JGS cap: 11.000
**Not yet validated on live Supabase data** — the Jan–May backfill stalled after
the Vale fix (`030.010.0100/0220` absent from resumo; read `500.010.<SIGLA>` in
`LANCAMENTO`). Confirm live before retiring the importer.

## Appendix B — Institutional row-198 SOLVED (account-keyed, 2026-07-08)

`probe_inst_csv.sql` dumped `FINANCE.VW_RESULTADO_MENSAL_DET` (TIPO S+I) as clean
pipe-delimited rows keyed on the **numeric account codes** `CONTA2/CONTA3`
(accent-free; the `\Uffffffff` in titles is a console artifact only). This let us
reconcile the workbook institutional block to the DB *losslessly* for Feb and May.

### The structural fact (verified to the centavo, both months)

Workbook **row 198 "Despesas Institucional"** = the sum of exactly these ten
family header rows — and **nothing else**:

    85 Ocupação · 92 Telecomunicações · 95 Despesas Gerais · 110 Consultoria ·
    116 Salários Administração · 124 Administrativas · 137 Investimentos em
    Prospecção · 158 Gestão do Conhecimento · 164 Endomarketing · 180 Informática

Explicitly **excluded** from row 198: 168 Impostos, 191 Distribuição de Lucros,
82 Despesas para Clientes, and all "Despesas Área" (rows 204-207). Impostos and
the area lines are *pulled out* of the raw account tree into their own blocks.

### The account → workbook-family map (stable CONTA3 keys)

    020.010.*  Ocupação            (Aluguel/Condomínio/Energia/IPTU)
       └ 020.010.0050 Manut. e Conservação → Despesas Gerais ("Manut. do Escritório")
    020.020.*  Telecomunicações
    020.030.*  Despesas Gerais
    020.040.0010 Serviços de Informática → Informática ("Suporte de Informática")
    020.040.0030 Terceirização Limpeza  → Despesas Gerais ("Limpeza e Copeira")
    020.040.0050 Contabilidade          → Consultoria
    020.040.0060 Servidor Externo       → Informática ("Data Center")
    020.050.*  Salários Administração
       └ 020.050.0050/0060/0070/0160 (INSS/FGTS/IR/e-Social) → Impostos (row168, OUT)
    020.060.0040 Seguros → Ocupação ("Seguro Locação")
    020.060.0010/0020 Assinaturas/Associações → Despesas Área (rows 204-206, OUT)
    020.060.*  (rest)  Administrativas
    020.070.*  Financeiras → Administrativas ("Taxas / Despesas Financeiras")
    020.080.0030 Estacionamento → Despesas Área ; 020.080.* (Vale Ref/Transp) → Salários Adm
    020.090.*  Investimentos em Prospecção  (area-tagged parts → Despesas Área)
    020.110.*  Comissões (leaves the institutional pool → Comissão block)
    040.010.*  Marketing/Assessoria → Consultoria ("Consultoria em Marketing")
    040.030.*  Investimentos:Consultoria → Consultoria ("Consultoria Adm. e Financeira")
    040.040.*  Informática (Licenças, Micros, Impressoras)
    040.050.*  Biblioteca → Gestão do Conhecimento

### Correction (2026-07-08, later): the families ARE fully DB-derived

An earlier draft of this appendix concluded that Administrativas / Gestão /
Endomarketing were an "irreducible manual layer". **That was wrong.** Reading the
*formulas* in the authoritative **05.2026** workbook (the boss confirmed 05 is the
correct book; 02 uses an older, less-correct layout) shows every one of those cells
is plain arithmetic on SISJURI leaf values:

- **Administrativas → Associações** (05 book, May): `=(1400.19/2)+217.40`,
  `=(1400.19/2)`, `=1204.47`. Those constants are the DB `020.060.0020` Associações
  leaves by area (ECT 917.49, EDE 700.10, ESP 1204.47); the `/2` just re-splits one
  DB posting across two area rows. Family total = the DB Associações sum, **identical**.
  So Associações **stay inside the institutional Administrativas family** — they are
  NOT removed to Despesas Área. (The area block rows 204-206 *also* reference the same
  per-area sub-rows; a line can be both in the family total and surfaced per area.)
- **Endomarketing** (05 book, May): `Eventos Internos =59.98+146` = DB
  `020.090.0040` Eventos e Happy Hour (ADM 59.98 + EDE 146); `Presentes =215` = DB
  `020.030.0150` Relacionamento Institucional. Both real DB leaves.
- **Salários Adm** = Convênio (020.050.0110) + Salário (020.050.0010) + Férias
  (020.050.0020) + **Vale Refeição (020.080.0050) + Vale Transporte (020.080.0060)**.
  The Vale lines live under `Benefícios` and are pulled into Salários Adm.

### Corrected map deltas (vs the first draft)

- `020.060.0010/0020` Assinaturas/Associações → **Administrativas** (stay in), NOT
  Despesas Área.
- `020.090.0040` Eventos e Happy Hour → Investimentos em Prospecção (DB TITULO2 /
  02-book placement; the 05 book labels it Endomarketing "Eventos Internos" — the
  choice does not move row 198, since both are institutional families).
- `020.030.0150` Relacionamento Institucional → Endomarketing ("Presentes").

### Remaining residuals — all point at real SISJURI data, not hand-keying

After the corrections, the row-198 net residual is small (Feb +159.80) and fully
line-attributed to DB data the `VW_RESULTADO_MENSAL_DET` **TIPO S+I slice did not
surface for that month**:

- **Salários Adm Feb −1 351.88** = Vale Refeição 1 014.20 + Vale Transporte 337.68.
  Present in DB `Benefícios 020.080.*` (they show in Mar) but absent from the Feb
  S/I slice — a TIPO/timing filter, recoverable.
- **Gestão May +1 600** = a Cursos/Treinamento posting whose account code we have not
  yet captured (workbook cell is a typed constant, but the money is a real lançamento).
- **Despesas Gerais Feb +667.62** = Terceirização Limpeza area split (3 630.03 vs
  3 049.23 = 580.80) + Manutenção reclass (48.40) + Custas 38.42.
- **Informática Feb +626.95** = one Licença line (040.040.0030) the author excluded;
  plus a within-family Totvs/Licenças reshuffle that nets to zero.

`probe_inst_close.sql` (pushed) pulls the raw `GERENC_LANCAMENTORESUMO` postings for
`020.080.*` (Vale), Cursos/Treinamento (Gestão), `020.040.0030` (Limpeza area split)
and `040.040.*` (Licença detail) across Jan..Mai to close every one of these to the
centavo. **Nothing here is manual — it is all in SISJURI.**

### Shipped map (encoded)

`workbook_layouts.py::section_for(nome_pai, id_conta)` carries the verified CONTA3
rules; locked by `tests/test_workbook_layouts.py`. Row 198 = the 10 institutional
families (Impostos + Comissão pulled out; area lines surfaced per-area but kept in
the family totals). Authoritative book = **05.2026**.

## Appendix C — closing the last residuals (2026-07-08, probes inst_close + vale)

Two probes (`probe_inst_close.sql`, `probe_vale_adm.sql`) resolved 3 of the 4 open
residuals against the authoritative **05.2026** book:

- **Gestão do Conhecimento** = Biblioteca (`040.050.*`) + **`030.010.0180` Cursos /
  Treinamento Jurídico** — a `030.*` account the workbook lifts OUT of Custo Equipe.
  Ties Mar (1.094,49) and May (1.600). Encoded as a `030.*` carve-out in
  `workbook_layouts.py` (`_030_TO_SECTION`). **Nuance:** Apr DB = 1.650 (Contencioso
  1.450 + Administração 200); the workbook takes only the **area-tagged 1.450** and
  drops the 200 ADM slice. Current code routes the whole account → Gestão (Apr would
  read 1.650). If Apr parity matters, restrict the carve-out to area-tagged postings.
- **Terceirização Limpeza** (`020.040.0030`) posts with **no area** — the Feb
  580,80 gap vs the workbook "Limpeza e Copeira" is a within-family author reclass,
  not an area split; it does not move row 198 (stays in Despesas Gerais).
- **Licenças** (`040.040.0030`) is a single Administrativa account; the Feb 626,95
  is a within-Informática Totvs/Licenças reshuffle that nets to zero at family level.

### The one genuinely non-ledger line: Vale-ADM

The accounting ledger (`GERENC_LANCAMENTORESUMO`) has **no ADM Vale account**. The
full `020.050.*` Salários Administração list is: Salários, Férias, INSS-ADM, FGTS,
IR-ADM, Convênio Médico-ADM, e-Social — **no Vale**. A name search for `%VALE%`
across all prefixes returns only the tiny area-tagged `020.080.*` staff vale.

Yet the workbook's Salários Administração residual is **exactly** the Vale
(Refeição+Transporte): Feb 1.351,88, May 3.326,94 (proven: wb row 116 − DB
[Salários+Férias+Convênio] = wb Vale total, to the centavo). So Vale-ADM is real
and monthly but lives outside the summarised ledger — most likely in
`FINANCE.CONTASPAGAR` (folha/payroll postings, keyed by `CPGCHISTORICO`), the same
place the gross pró-labore/convênio detail lives (see SISJURI_DB.md Lacuna 1).
`probe_vale_folha.sql` (pushed) hunts it there by history text. If it is a folha-only
figure with no ledger account, Vale-ADM becomes the single **optional manual input**
for Salários Administração — everything else in row 198 is DB-derived and ties.
