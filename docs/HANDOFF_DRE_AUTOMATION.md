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
| Despesas Área (direct) | open | `VW_RESULTADO_MENSALCC` `TIPO='S'` by `SETOR` | SETOR (ECT/EDE/ESP/ADM) → workbook area needs the same re-bucket as Custo equipe |
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
