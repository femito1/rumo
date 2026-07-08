# SESSION HANDOFF — Vale-ADM is the last open institutional residual (2026-07-08)

> Read in this order: `PROJECT_STATUS.md` → `docs/HANDOFF_DRE_AUTOMATION.md`
> (the durable narrative) → `docs/SISJURI_DB.md` §"Known account facts — CHECK
> THIS BEFORE PROBING" → **this file**. This file is the short-lived "where we
> physically stopped" note; the durable facts already live in the two docs above.

## TL;DR of this session

We closed almost every `Base_Resultado_Mensal` institutional family to the
centavo against the **authoritative `05.2026`** book (boss confirmed `05` is the
most correct). The account→family map is now encoded and tested:

- `backend/app/closing/workbook_layouts.py` — `_CONTA3_TO_SECTION`,
  `_PREFIX_TO_SECTION`, `_030_TO_SECTION`, `is_direct_team`,
  `institutional_030_section`, `section_for(nome_conta_pai, id_conta)`.
- `backend/app/closing/dre.py` — routes `030.*` to Custo equipe except the
  institutional carve-outs (e.g. `030.010.0180` Cursos → Gestão do Conhecimento).
- Locked by `backend/tests/test_workbook_layouts.py` and the updated
  `test_dre_assembler.py::test_institutional_sections_roll_up_by_family`.

**One family does not yet reconcile to the centavo: "Salários Administração"**,
specifically the **Vale Refeição-ADM + Vale Transporte-ADM (Vale-ADM)** portion.
That is the entire remaining task.

## What we proved about Vale-ADM (do NOT re-derive this)

- Vale is NOT in `FINANCE.CONTASPAGAR` by `CPGCHISTORICO` (searched Jan–Mai; only
  incidental reimbursements match).
- Vale IS posted in `FINANCE.LANCAMENTO`. The correct **date axis is `LANDDATA`**
  (competence), not `LANDDATADESP`.
- `FINANCE.LANCAMENTO` does NOT have `ID_GRUPOJURIDICODEST`. The real grouping
  columns are **`SIGLADEST`** (cost-center/professional sigla) and
  **`LANCPROFDEST`**. (Confirmed via `probe_vale_cols.sql` column inventory.)
- Vale postings live in the personal-debit namespace **`500.010.<SIGLA>`** (and a
  few show up on `020.030.0060` / `200.010.0010`), historico contains
  "Vale transporte" / "Refei" / "Transp".

## The exact discrepancy that stopped us

The full reconciliation table (numbers verified this session) lives in
`docs/SISJURI_DB.md` §"Vale Refeição/Transporte source". Reproduced here so the
next agent sees the shape without re-probing:

| month | wb Vale-ADM | MLA+VSR (500.010, `%VALE%`) | +other Vale postings | ties? |
|------:|------------:|----------------------------:|---------------------:|:-----:|
| Jan | 1 127,96 | 1 092,44 | — | ~ (Δ35,52) |
| Feb | 1 351,88 | 1 351,88 (MLA only) | — | **yes** |
| Mar | 3 983,22 | 2 249,32 | 3 335,76 | no |
| Abr | 3 421,36 | 2 230,56 | — | no |
| Mai | 3 326,94 | 1 121,94 | 2 090,04 | no |

Only **Feb** reconstructs cleanly from Vale-labelled postings. Every other month
the workbook Vale-ADM is **larger** than any `%VALE%/%REFEI%/%TRANSP%` posting we
can find on `500.010.*`. So the remainder is almost certainly bundled inside
**non-Vale-labelled** `500.010`/`030.*`/`200.010.*` postings — i.e. a
payroll/benefit allocation the workbook author keys by hand each month. We have
NOT yet proven this is irreducible; the North Star says keep hunting until 100%
proven impossible.

## The single next step (do this first)

The candidate we did NOT check yet: dump the **full monthly movement of
`500.010.MLA` and `500.010.VSR` (ALL historicos, not just `%VALE%`)** plus the
**`200.010.*` benefits account**, by `LANDDATA`, Jan–Mai. Then in Python search
for the subset of those postings whose monthly sum equals the workbook Vale-ADM
(row 122 Ref + row 123 Transp) for ALL of Jan–Mai in BOTH books. If a stable rule
falls out (e.g. "all MLA+VSR benefit movement", or a specific historico set),
encode it — ideally derived from "ADM = sigla not assigned to a billing area" so
it is future-proof rather than a hardcoded name list.

Probe skeleton already exists — reuse/extend `ops/sisjuri-agent/probe_vale_500.sql`
and `probe_vale_find.sql`. Remember Oracle 11g: **no positional multi-col
`ORDER BY`** — name the expressions (`ORDER BY TO_CHAR(...), col`).

## RDP execution recipe (unchanged, works)

1. Push probe to GitHub `femito1/rumo` main.
2. On the RDP box, fetch **by commit SHA** (CDN caches `main`; SHA never caches):

```powershell
$sha = "<paste full commit sha>"
Remove-Item C:\temp\sisjuri\probe.sql -ErrorAction SilentlyContinue
Invoke-WebRequest -UseBasicParsing "https://raw.githubusercontent.com/femito1/rumo/$sha/ops/sisjuri-agent/probe_vale_500.sql" -OutFile C:\temp\sisjuri\probe.sql
Set-Content C:\temp\sisjuri\q.sql -Encoding ASCII -Value ("CONNECT RGN/""$($env:SISJURI_PASSWORD)""@(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=172.16.237.9)(PORT=1521))(CONNECT_DATA=(SERVICE_NAME=cdbp01_pdb1.submbc.vcnmbc.oraclevcn.com)))`r`n" + (Get-Content C:\temp\sisjuri\probe.sql -Raw))
& 'C:\oracle11\app\product\11.2.0\client_1\bin\sqlplus.exe' -S /nolog '@C:\temp\sisjuri\q.sql' *>&1 | Tee-Object C:\temp\sisjuri\out.txt
```

- Credentials for probes: `U:RGN P:RgN@92Kx7` (env `SISJURI_PASSWORD`).
- Query **year is 2026**. Emit **pipe-delimited** rows with a `#COLS` header and a
  `#END` sentinel — clean CSV avoids the `\Uffffffff` JSON-serialization garbage
  we hit when dumping raw text.

## Quality gates before calling Vale-ADM done

- `cd backend && ruff check . && mypy app && pytest`
- `cd frontend && npm run lint && npm run typecheck && npm run test`
- Vale-ADM reconciles to the centavo against BOTH `02.2026` and `05.2026`
  (`05` wins on any conflict).
- Add the confirmed ADM sigla set / derivation rule to
  `docs/SISJURI_DB.md` §"Known account facts" **in the same commit**.
- Update `PROJECT_STATUS.md` (mark Salários Administração / Vale-ADM automated).

## Still open after Vale-ADM (lower priority, per North Star scope)

- **Distribuição de Lucros extras** and **area_transfers** — user asked to attempt
  these; not started this session. Sources hinted in `docs/SISJURI_QUERIES.md`
  and the DL probes (`probe_dl_extras_clientes.sql`).
- Behaviour when the monthly workbook is absent: the shipped pipeline must not
  depend on it — everything above must run from DB alone.

## Files touched this session (for `git log` orientation)

- `backend/app/closing/workbook_layouts.py`, `backend/app/closing/dre.py`
- `backend/tests/test_workbook_layouts.py`, `backend/tests/test_dre_assembler.py`
- `docs/SISJURI_DB.md` (Known account facts index; Vale correction)
- `ops/sisjuri-agent/probe_inst_csv.sql`, `probe_inst_close.sql`,
  `probe_vale_adm.sql`, `probe_vale_folha.sql`, `probe_vale_500.sql`,
  `probe_vale_lanc.sql`, `probe_vale_cols.sql`, `probe_vale_find.sql`
