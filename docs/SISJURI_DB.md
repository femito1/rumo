# SISJURI Database — direct DB access (discovered 2026-07-01)

> **Audience:** engineers evaluating a DB-backed alternative/audit path to the
> LegalDesk OData API. For the API itself see `docs/LEGALDESK.md`; for current
> status see `PROJECT_STATUS.md`. **Sacred numbers still live in
> `docs/LEGALDESK.md` §4 and win.**
>
> **Secrets:** this file contains **no** credentials. The DB user/password and
> the Windows RDP password used during discovery were shared out-of-band and
> **must be rotated**. Never commit them.

## TL;DR

SISJURI has **no API**, but its data lives in an **Oracle 19c** database that is
reachable — read-only — through the authorized Windows bridge server
`MBC-LDESK01` (the same host that runs the Power BI gateway). The DB contains an
**`LDESK` schema (601 tables)** that is the LegalDesk data RUMO already consumes
via OData, plus an **`SSJR` schema (704 tables)** of SISJURI core data. This is a
viable path to **audit** the sacred numbers, act as a **fallback** source, or
back a future `Source` implementation.

## Access path (authorized — through the server, not direct)

```
SISJURI Oracle 19c
  host 172.16.237.9 : 1521   (private OCI VCN — NOT reachable from the internet)
  SERVICE_NAME cdbp01_pdb1.submbc.vcnmbc.oraclevcn.com
        ^  Oracle 11g client + sqlplus  (System DSN "sisjuri")
        |
  MBC-LDESK01   Windows Server 2012 R2   (RDP; only host with a route to the DB)
        |
        v  Power BI On-Premises Data Gateway (PBIEgwService, running)
   Power BI cloud
```

- The DB host is a **private VCN address**: only `MBC-LDESK01` can reach it, which
  is why all access must go **through the server**.
- Oracle client home: `C:\oracle11\app\product\11.2.0\client_1`
  (`bin\sqlplus.exe`, `bin\tnsping.exe`).
- TNS aliases in `...\network\admin\tnsnames.ora`: `SISJURI` / `CDBP01_PDB1`
  (the 19c PDB, used by the DSN), plus `SISJURI11` / `PROD11` on `172.16.237.31`
  (older Oracle 11 hosts — not used here).

## Credential & privileges (as discovered)

- DB user **`RGN`** — provided out-of-band. **Rotate it.**
- Privileges: `CREATE SESSION` only, **no roles**. Despite that, it has **real
  SELECT** on `LDESK` application tables (confirmed by returning row counts, not
  just catalog visibility). Treat as **read-only**; only ever run `SELECT`.

## Schema inventory (18 owners; application data in bold)

| Owner | Tables | What it is |
| --- | ---: | --- |
| **SSJR** | 704 | SISJURI core (agenda, faturamento, fiscal SPED, SAPC contencioso, DBM CRM, compras) |
| **LDESK** | 601 | **LegalDesk** model (`CAD_*`, `FAT_*`, `JUR_*`, `GERENC_*`, `CONTR_*`) — the RUMO source |
| RCR | 353 | module (TBD) |
| SAPC | 221 | SAP connector / contencioso |
| FINANCE | 89 | financial |
| SYNC | 25 | replication/sync |
| SEGURANCA | 11 | security/users |
| CUSTOM / LDESK_CUSTOM / LIXO | 2 / 1 / 1 | custom / scratch |
| SYS, SYSTEM, MDSYS, XDB, CTXSYS, APEX_220200, FOEX_210100 | — | Oracle internals (ignore) |

## Key billing tables (LDESK) and confirmed shape

Row counts (2026-07-01) and the columns that matter for the monthly closing:

| Table | Rows | Notable columns |
| --- | ---: | --- |
| `LDESK.FAT_FATURA` | 4,249 | `NUMERO`, `SITUACAO`, `DATA_EMISSAO`, `DATA_CANCELAMENTO`, `VALOR_HONORARIOS`, `VALOR_DESCONTO`, `VALOR_DESPESAS`, `VALOR_DESPESAS_TRIB`, `ID_ESCRITORIO`, `ID_PROFISSIONAL_RESP` |
| `LDESK.FAT_FATURA_PROF` | 9,798 | invoice x professional |
| `LDESK.FAT_RATEIOFATURA_PROF` | 19,812 | `ID_FATURA`, `ID_PROFISSIONAL`, `ID_CASO`, `ID_CLIENTE`, **`VALOR_FATURADO`**, **`VALOR_TRABALHADO`**, **`ANO_MES`** (`'YYYY-MM'`), `ID_ESCRITORIO` |
| `LDESK.FAT_TIMESHEET` | 55,925 | timesheets |
| `LDESK.CAD_PROFISSIONAL` | 69 | professionals |

Data characteristics:

- **Single tenant** in this instance: one `ID_ESCRITORIO`
  (`5B041D9E-98E9-68F1-A6E1-8C4DB3FE939A`) owns all rows.
- **Continuous history: 98 competence months, 2018-05 -> 2026-06.**
- `FAT_RATEIOFATURA_PROF` is **clean at the PK level** (raw rows == distinct
  `ID_RATEIOFATURA_PROF`). The duplication warned about in `CLAUDE.md` /
  `docs/LEGALDESK.md` comes from the **API view** `RateioFaturaProfissionalViews`,
  not this base table — querying the DB directly avoids that gotcha.

## Cross-check vs. the sacred numbers (2026-05)

Sacred (from `docs/LEGALDESK.md` §4, locked by `test_legaldesk_source.py`):

- `receita_honorarios` (recebimento_bruto) = **415.927,84**
- `faturamento_realizado` (faturamento_bruto) = **719.988,05**
- `faturas_emitidas` = **53**

DB observations so far:

- `FAT_FATURA` by `DATA_EMISSAO` 2026-05 = **53 invoices** -> **matches** `faturas_emitidas`.
- `FAT_RATEIOFATURA_PROF` 2026-05 = **286 rows** -> **matches** the documented
  rateio row count (and 53 distinct invoices).
- The money headlines (415.927,84 / 719.988,05) come from the OData entities
  `PosicaoFinanceiraResultadoRecebimentoViews` / `...FaturamentoViews`
  (sum of `Valor1` for the `AnoMes`). Mapping these to their underlying
  Oracle view/table is **in progress** (search `all_objects` in `LDESK`/`SSJR`
  for `%POSICAO%` / `%RESULTADO%` / `%RECEB%` / `%FATURAMENTO%`).

## Reliable sqlplus invocation (hard-won)

The RDP console **collapses pasted newlines** and PowerShell **mangles
connect-string arguments** (`@`, parentheses). Two robust patterns:

### A. One-liner (easiest — no base64, no multi-line paste)

Everything on ONE line; SQL line breaks are PowerShell backtick-n; password is
double-double-quoted; `CONNECT` lives inside the SQL file:

```powershell
$s="SET DEFINE OFF`nSET FEEDBACK ON`nWHENEVER SQLERROR CONTINUE`nCONNECT RGN/""<PASSWORD>""@(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=172.16.237.9)(PORT=1521))(CONNECT_DATA=(SERVICE_NAME=cdbp01_pdb1.submbc.vcnmbc.oraclevcn.com)))`n<SQL; statements end with ; and are separated by backtick-n>`nEXIT;";Set-Content C:\temp\q.sql $s -Encoding ASCII;& 'C:\oracle11\app\product\11.2.0\client_1\bin\sqlplus.exe' /nolog '@C:\temp\q.sql' *>&1 | Tee-Object C:\temp\out.txt
```

### B. Base64 delivery (immune to any paste mangling)

Encode a full `.ps1` to base64, then:

```powershell
$b='<BASE64>';[IO.File]::WriteAllText('C:\temp\probe.ps1',[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($b)));powershell -ExecutionPolicy Bypass -File C:\temp\probe.ps1 *>&1 | Tee-Object C:\temp\out.txt
```

Rules that make either work:
- `CONNECT` goes **inside** the `.sql`, password quoted (it contains `@`),
  **inline DESCRIPTOR** (no dependence on `tnsnames.ora` resolution quirks).
- Launch `sqlplus /nolog @file` — no special chars as shell args.
- `SET DEFINE OFF` / `SET SCAN OFF` so `&` is not treated as a substitution prompt.
- `Tee-Object` to a file so output can be retrieved with `Get-Content` if the
  console is hard to copy.

## Why this matters for RUMO

- **Audit**: independently verify the API's sacred numbers against raw DB rows.
- **Fallback / alternative**: a DB-backed `Source` (implementing
  `app/sources/base.py`) could supply the same `SectionKey`s if the API is
  unavailable — without touching the API contract or the SPA.
- **Reach**: `SSJR`/`FINANCE` may expose data the OData API does not.

## Open items

- Map `PosicaoFinanceiraResultado{Recebimento,Faturamento}Views` to their DB
  objects and reconcile the 415.927,84 / 719.988,05 totals.
- Confirm whether other tenants exist on the `SISJURI11` / `PROD11` instances.
- Decide if a `SisjuriDbSource` is worth building (vs. keeping OData primary).

## Full-closing coverage — the FINANCE schema (discovered 2026-07-01)

**Major finding:** the institutional expenses that `docs/LEGALDESK.md` declared
out-of-scope ("TOTVS Backoffice / ~65 manual lines") are **in this same Oracle
DB**, in a dedicated **`FINANCE`** schema that `RGN` can read. This means the DB
can, in principle, source the **entire** monthly closing — revenue *and*
institutional expenses — not just the LegalDesk billing side.

Evidence gathered against the MBC financial exports the client sent
(`reference/workbook/{PLANO CONTAS.XLS.xlsx, Pagtos maio.XLS.xlsx,
lancextrato de contas.xls}`):

| Client sheet | DB object (readable by RGN) | Rows |
| --- | --- | --- |
| `PLANO CONTAS` (chart of accounts, 279 lines) | `FINANCE.PLANOCONTAS` | 278 |
| `Pagtos maio` (payments) | `FINANCE.LANCAMENTO` (financial entries) | 36,093 |
| `lancextrato de contas` (Extrato de Contas ledger, 88 accounts) | built from `FINANCE.LANCAMENTO` + `FINANCE.PLANOCONTAS` | — |
| (payables) | `FINANCE.CONTASPAGAR` | 7,955 |

Also present: `FINANCE.{CONTASRECEBER, EXTRATO, GRUPOPLANOCONTAS,
PLANOCONTACONTABIL}` and many reporting views (`VW_EXTRATO`, `VW_LANCAMENTO`,
`VW_LANCAMENTOCONTABILIDADE`, `VW_RESCENTROCUSTO`, `VW_PLANOCONTASEXTRATO`, ...).
`FINANCE.EXTRATO` is **empty** (0 rows) here — the "Extrato de Contas" report is
derived from `LANCAMENTO`, not from the bank-reconciliation `EXTRATO` table.

### Data model — double-entry

`FINANCE.LANCAMENTO` is a **double-entry** ledger. Each row moves value between
two plano-de-contas accounts:

- `PCTCNUMEROCONTAORG`  — origin account (VARCHAR2, e.g. `200.010.0020`)
- `PCTCNUMEROCONTADEST` — destination account (e.g. `020.010.0010`)
- `LANNVALOR`  — value (NUMBER)
- `LANDDATA`   — entry date (DATE)
- `LANCHISTORICO` — free-text history
- `SIGLAORG` / `SIGLADEST` — professional sigla; `ESCRITORIOORG` / `ESCRITORIODEST`
- `GERADO_LD` — flag: generated by LegalDesk
- NB: `LANCAMENTO.CODIGO` is a currency/real-estimado flag ('R'), **not** the account.

`FINANCE.PLANOCONTAS` key columns:

- `PCTCNUMEROCONTA` — account code (`010.010.0010`) — join key to LANCAMENTO ORG/DEST
- `PCTCTITULO` — account title (e.g. `Aluguel`)
- `PCTCNUMEROCONTAPAI` — parent account (tree)
- `PCTNNIVEL` — level; flags `PCTCFLAGCP/CR/BANCO/RATEIO/...`

### Reproduce the "Extrato de Contas" ledger

Group May-2026 entries by **destination account** joined to the plano de contas:

```sql
SELECT p.PCTCNUMEROCONTA AS conta, p.PCTCTITULO AS titulo,
       COUNT(*) AS n, ROUND(SUM(l.LANNVALOR),2) AS total
  FROM FINANCE.LANCAMENTO l
  JOIN FINANCE.PLANOCONTAS p ON p.PCTCNUMEROCONTA = l.PCTCNUMEROCONTADEST
 WHERE l.LANDDATA >= DATE '2026-05-01' AND l.LANDDATA < DATE '2026-06-01'
 GROUP BY p.PCTCNUMEROCONTA, p.PCTCTITULO
 ORDER BY p.PCTCNUMEROCONTA;
```

This returns all 88 accounts with the right titles (Aluguel, Condomínio, IPTU,
Salários, INSS, FGTS, Distribuição Mensal Fixa, Consultoria, COFINS, per-
professional `500.010.*`, etc.). Spot-check: DEST `020.010.0010 Aluguel` =
**27.477,67**, which matches the genuine Aluguel line in the client's ledger
export. (A naive re-sum of the `.xls` mis-parses because of the report's
blank/merged rows; the DB figure is the clean source of truth.)

### Coverage matrix (workbook tabs -> source)

| Workbook data family | Source | DB objects |
| --- | --- | --- |
| Revenue: honorários / recebimento / faturamento | API today; **also DB** | `LDESK.FAT_FATURA`, `PosicaoFinanceira*` (mapping TBD) |
| Rateio por profissional / por caso | API today; **also DB** | `LDESK.FAT_RATEIOFATURA_PROF` |
| Faturas / centro de custo | API today; **also DB** | `LDESK.FAT_FATURA` (+ rateio caso) |
| **Institutional expenses (aluguel, salários, INSS/FGTS, impostos, distribuições, CAPEX)** | **was MANUAL/TOTVS — now DB** | `FINANCE.LANCAMENTO` + `FINANCE.PLANOCONTAS` |
| Chart of accounts / DRE scaffold | **DB** | `FINANCE.PLANOCONTAS` (278) |
| Payables / receivables | **DB** | `FINANCE.CONTASPAGAR` (7,955), `FINANCE.CONTASRECEBER` |

**Implication:** the `PROJECT_STATUS.md` §5 assumption that institutional
expenses require a future Juritis/TOTVS integration may be **obsolete** — the
data is reachable now via this DB. This warrants revisiting the Juritis plan and
considering a `FinanceDbSource` alongside `LegalDeskSource`.

### Open reconciliation items

- Whether the closing wants **DEST-only**, **ORG-net**, or **cash-account
  (100.*)** views per line (the double-entry means each value appears on both
  sides). Match the workbook's DRE definitions before trusting per-line totals.
- Confirm the ledger's competence vs. cash-date convention (`LANDDATA` vs
  `LANDDATADESP`).

## DRE reconciliation nuance (2026-07-01) — data is present, but 3 transforms apply

Reading the workbook's core DRE tab `Base_Resultado Mensal_V2` against the DB
shows the closing is **not** a raw account dump. Three transforms sit between the
DB ledger and the workbook lines. The DB has all the data; a `FinanceDbSource`
must replicate these:

1. **Competence (accrual) vs cash (payment) basis.** Workbook `Aluguel` Jan =
   `26.384,63` (competence base); the DB/ledger payment is `27.477,67` (cash, with
   monetary correction, competence Abr/2026). So `SUM(LANNVALOR) by LANDDATA month`
   != the workbook line. Competence likely comes from the `Competência: MM/AAAA`
   text in `LANCHISTORICO` (or `LANDDATADESP`), not the payment date `LANDDATA`.
2. **Per-professional x cost-center breakdown.** DRE lines are grouped as
   `Custo equipe - {Contencioso, Econômico, Arbitragem e Compliance}`, then
   `Ocupação`, etc., each split per professional (`... - Convenio Medico`,
   `- Distribuição Mensal`, `- Pro labore`). DB can do this via
   `LANCAMENTO.SIGLADEST` + `PCTCNUMEROCONTADEST` and the `500.010.<SIGLA>`
   accounts, **plus** a professional->cost-center mapping the workbook encodes by hand.
3. **Line taxonomy.** Plano-de-contas accounts must be mapped to the workbook's
   DRE line labels.

**Today these leaf values are hardcoded** in `Base_Resultado Mensal_V2` (the audit
counts 58 hardcoded cells; only subtotals are `SUM()` formulas). That is the
manual step the client's ledger export currently feeds — and the step a DB source
could automate.

**Conclusion:** there is **no missing data source** for the closing — revenue and
all institutional expenses are in the DB. Remaining work to automate is
*modeling* (competence assignment, cost-center map, line taxonomy), not *access*.

## Sacred-number reconciliation — EXACT MATCH (2026-07-01)

The two headline sacred totals were reconciled **to the centavo, including row
counts**, straight from the DB. Source views (behind the OData
`PosicaoFinanceiraResultado*Views`):

- Recebimento: `LDESK.GERENC_VW_POSFIN_RESULTREC`
- Faturamento: `LDESK.GERENC_VW_POSFIN_RESULTFAT`
- Aggregation: `SUM(VALOR1)` filtered by `ANO_MES = 'YYYY-MM'` (note underscore).

| Metric | Sacred (docs/LEGALDESK.md §4) | DB result | Rows |
| --- | --- | --- | --- |
| recebimento_bruto 2026-05 | 415.927,84 | **415.927,84** | 98 (match) |
| faturamento_bruto 2026-05 | 719.988,05 | **719.988,05** | 97 (match) |
| recebimento 2026-01 | 279.821,07 | **279.821,07** | 89 |
| recebimento 2026-02 | 319.233,58 | **319.233,58** | 92 |

Verification query:

```sql
SELECT ROUND(SUM(VALOR1),2) total, COUNT(*) n
  FROM LDESK.GERENC_VW_POSFIN_RESULTREC WHERE ANO_MES = '2026-05';  -- 415927.84 / 98
SELECT ROUND(SUM(VALOR1),2) total, COUNT(*) n
  FROM LDESK.GERENC_VW_POSFIN_RESULTFAT WHERE ANO_MES = '2026-05';  -- 719988.05 / 97
```

Related views also present (same `GERENC_VW_POSFIN_*` family): `_FATURA`,
`_COBRANCA`, `_ADIANTAMENTO`, `_DESPINC`, `_PENDENCIA`, `_RESUMODESP`,
`_RESUMOPROF`, plus base table `LDESK.GERENC_POSICAOFINANCEIRA`.

### Bottom line

Every input to the monthly closing is present in the DB and, where a locked
figure exists, **reconciles exactly**:

- Headline recebimento/faturamento — exact (this section).
- 53 distinct invoices (May 2026) — matched (`LDESK.FAT_FATURA`).
- 286 rateio-por-profissional rows — matched (`LDESK.FAT_RATEIOFATURA_PROF`).
- Full institutional-expense ledger (88 accounts) — present
  (`FINANCE.LANCAMENTO` + `FINANCE.PLANOCONTAS`); Aluguel line exact.

Remaining work to automate is **modeling** (competence assignment, cost-center
map, DRE line taxonomy — see previous section), **not data access**. A
`FinanceDbSource` / `SisjuriDbSource` reading these objects can supply the entire
closing.

## Algorithmic proof: DB values -> workbook DRE lines (2026-07-01)

We reproduced individual workbook DRE lines algorithmically from raw
`FINANCE.LANCAMENTO` rows. This proves the closing is *computable* from the DB,
not merely that the data exists.

### The professional/cost-center dimensions

- `COD_ADVG` = the **individual professional** sigla (`AM`, `DC`, `BBX`, `IAC`, ...).
- `SIGLADEST` = the **cost-center group** (`ECT`=Contencioso, `EDE`=Econômico,
  `ESP`=Arbitragem/Compliance).
- `PCTCNUMEROCONTADEST` = plano-de-contas account (e.g. `030.010.0010`
  Distribuição, `030.010.0130` Pró-labore).
- `LANCHISTORICO` = free text that distinguishes sub-types (e.g.
  "Distribuição Fixa Líquida Mensal" vs "DL excedente ... Reserva").

### Associates — exact, direct formula

`workbook line = SUM(LANNVALOR)` grouped by `COD_ADVG` (+ `SIGLADEST`) on account
`030.010.0010`, for the month. Verified exact for January 2026:

| Prof (COD_ADVG) | Group | DB total | Workbook "Distribuição Mensal Fixa" |
| --- | --- | --- | --- |
| BBX | EDE | 7.019 | 7.019 ✓ |
| BMP | EDE | 7.003 | 7.003 ✓ |
| ASG | EDE | 3.579 | 3.579 ✓ |
| IAC | ECT | 14.039 | 14.039 ✓ |
| FSM | ESP | 11.799 | 11.799 ✓ |
| EMC | ESP | 4.699 | 4.699 ✓ |
| MV  | ESP | 23.379 | 23.379 ✓ |

(8 associate lines matched to the centavo.)

### Partners (sócios) — decomposition rule, also exact

Partner rows on `030.010.0010` carry **two sub-types** distinguished by
`LANCHISTORICO`, and the fixed part is **split evenly across the partner's
cost-centers**. Example — AM (Aurelio), January 2026:

| Account | Group | Value | Histórico | Maps to workbook |
| --- | --- | --- | --- | --- |
| 030.010.0010 | EDE | 23.379 | "Distribuição Fixa Líquida Mensal" | **Distribuição Fixa**: 23.379 / 2 groups = **11.689,5** per group ✓ (workbook r7 Contencioso = r38 Econômico = 11.689,5) |
| 030.010.0010 | ECT | 70.790,94 | "DL excedente ... Reserva" | profit/reserve line (NOT the fixed-distribution row — correctly excluded) |
| 030.010.0130 | — | 1.442,69 | "Pró labore mês atual" | Pró-labore line |

So the rule is: **filter by account + histórico sub-type, then split the fixed
distribution across the professional's cost-centers.** That reproduces the
workbook's separate Distribuição / Pró-labore / Excedente lines exactly.

### What this proves

- Revenue KPIs: exact (`GERENC_VW_POSFIN_RESULT*`).
- Per-professional expense/distribution lines: reproduced exactly from
  `FINANCE.LANCAMENTO` (associates directly; partners via the account +
  histórico + cost-center-split rule).
- Therefore the **entire DRE is derivable from the DB**. The only "logic" needed
  is the taxonomy: (account, histórico sub-type) -> workbook line, plus the
  partner fixed-distribution split and competence-month assignment. This is
  exactly what a `FinanceDbSource` would encode.

### Caveat / next validation

- Formalize the (account, histórico) -> line map for all ~65 expense lines
  (some sub-types are identified by free-text histórico; confirm whether a
  structured column/flag exists to avoid text matching).
- Confirm competence-month rule per line (payment date vs a competence tag).

## BREAKTHROUGH — `GERENC_LANCAMENTORESUMO` is the gross competence expense ledger (2026-07-01)

Earlier sections reconstructed expenses from `FINANCE.LANCAMENTO` (the **cash**,
**net** double-entry ledger) and hit a gross-vs-net gap on personnel lines. That
gap is now resolved: the workbook's expense side is built from a **different,
cleaner object** — the pre-aggregated LegalDesk management ledger.

### The table

`LDESK.GERENC_LANCAMENTORESUMO` — **11,803 rows**, one row per
`(ANO_MES, ID_CONTA, ID_PROFISSIONAL, ...)`. Key columns:

- `ANO_MES` (`'YYYY-MM'`) — **competence month** (accrual, not cash date)
- `ID_CONTA` / `NOME_CONTA` — DRE account (e.g. `030.010.0010 Distribuição Mensal Fixa`)
- `ID_CONTA_PAI` / `NOME_CONTA_PAI` — parent account (`030.010.0000 Custos com Pessoal Técnico`)
- `TIPO_CONTA` — `D` (despesa/institucional), `C` (custo pessoal), `I` (investimento)
- `VALOR` — **GROSS** amount (NUMBER) — this is the workbook figure, not the net cash figure
- `ID_GRUPOJURIDICO` — cost-center/area (join `LDESK.CAD_GRUPOJURIDICO.NOME`)
- `ID_PROFISSIONAL` — professional (populated for most accounts; **NULL for the
  distribution account 030.010.0010**, where the total is stored at account level)
- `ORIGEM` — all `'F'` in this data

### Why this is the right source

- **Gross, not net.** `VALOR = 23379` for Distribuição Mensal Fixa exactly equals
  the workbook's gross figure (e.g. Daniel Costa Caselta = 23.379; Martim Della
  Valle = 23.379; João Gabriel = 9.379). No gross-up derivation needed for the
  account-level DRE lines. (`FINANCE.LANCAMENTO` stores the *net/liquida* payment
  and would require adding back withholding — avoid it for the DRE.)
- **Competence-dated.** `ANO_MES` is the accrual month, matching the workbook's
  competence basis directly — no `LANCHISTORICO` date-parsing needed.
- **Account tree baked in.** `ID_CONTA` + `ID_CONTA_PAI` + `TIPO_CONTA` give the
  DRE line taxonomy for free.

### Feb-2026 account roll-up (verified against the workbook)

`SELECT ID_CONTA, TIPO_CONTA, SUM(VALOR) FROM LDESK.GERENC_LANCAMENTORESUMO
WHERE ANO_MES='2026-02' GROUP BY ...` returns 30 accounts in three families:

| Family | TIPO | Feb-2026 total | Meaning |
| --- | --- | ---: | --- |
| `020.*` | D | 68.771,58 | institutional/admin (Aluguel 21.707,78, Contabilidade 7.804,05, Associações 7.109,73, ...) |
| `030.*` | C | 215.310,35 | personnel (Distribuição 172.129,96, Convênio 19.177,71, Pró-labore 17.312,28, INSS-Jur 3.890,40, Bolsa 2.800) |
| `040.*` | I | 30.913,70 | investments (Consultoria 14.705,80, Licenças 16.207,90) |
| **Total** | | **314.995,63** | vs workbook "Total saídas" 318.368,21 |

Individual account lines match the workbook's realized figures (Aluguel,
Condomínio, IPTU, Contabilidade, Consultoria, Licenças, etc.).

### The complete DRE assembles from TWO DB sources

| DRE side | DB source | Grain | Status |
| --- | --- | --- | --- |
| **Revenue** (recebimento / faturamento) | `LDESK.GERENC_VW_POSFIN_RESULTREC` / `_RESULTFAT` | `ANO_MES`, `SUM(VALOR1)` | **EXACT to the centavo** (415.927,84 / 719.988,05) |
| **Expenses** (institutional + personnel + investments) | `LDESK.GERENC_LANCAMENTORESUMO` | `ANO_MES` x `ID_CONTA` (gross, competence) | account-level **matches**; grand total within ~0,3% (gaps below) |

This is far simpler than the `FINANCE.LANCAMENTO` reconstruction: two
management-ledger objects, both keyed by `ANO_MES`, both already gross/competence.

### Two remaining, well-bounded gaps (Feb-2026 total diff ≈ 3.372,58)

1. **Pró-labore net vs gross.** The resumo stores pró-labore **net**
   (`030.010.0130` = 1.442,69 per professional, 12 people = 17.312,28); the
   workbook shows **gross 1.621** per person. Per-person diff 178,31 = INSS/IRRF
   withholding. Options: (a) add back withholding, (b) accept the resumo net if
   the closing definition allows, or (c) source gross from the folha. For the
   *account-level DRE* the resumo value is internally consistent; the 1.621 is a
   per-person supporting-detail figure.
2. **"Distribuição de Lucros extras" / "Bônus equipe" (Feb 101.705,84).** This
   line is **NOT** in `GERENC_LANCAMENTORESUMO` (no bônus/lucros account; value
   not found). In the workbook DRE it aligns with **"Reserva bônus" = 10% of
   Resultado Líquido** — i.e. a **formula-derived appropriation of profit**, not a
   booked cost. Treat as a computed line (result x reserve %), confirm the exact
   rule with finance, rather than sourcing it.

Also: the **per-partner distribution split** (who gets which slice of the
172.129,96) is not in the resumo (`ID_PROFISSIONAL` is NULL on `030.010.0010`).
The **account total is exact**; the per-partner detail, if the closing needs it,
comes from `FINANCE.LANCAMENTO` (net, by `COD_ADVG`) — but the DRE headline does
not require it.

### Honest bottom line (supersedes the optimistic "everything, zero gaps")

- **Revenue:** 100% in the DB, exact.
- **Expenses (institutional + personnel + investments), account-level, gross,
  competence, monthly:** in ONE table (`GERENC_LANCAMENTORESUMO`), account lines
  match the workbook.
- **Genuinely not sourced from these tables:** (a) the pró-labore net->gross
  add-back (small, = withholding), and (b) the profit-bonus/lucros-extras line
  (appears formula-derived: 10% reserve on net result). Both are **bounded and
  explainable**, not "missing data across dozens of manual lines."

So: automation is viable end-to-end. The closing = revenue views + expense resumo
+ two small rules (pró-labore gross-up if required; bonus-reserve formula). That
is a defensible, precise claim to take to the boss — materially stronger than the
prior "reconstruct from the cash ledger" plan.

## Lacunas resolvidas — respostas do financeiro MBC (2026-07-02)

As duas pendências abertas na seção anterior foram **fechadas** com as respostas do
financeiro da MBC e uma verificação no banco.

### Lacuna 1 (pró-labore bruto x líquido) — RESOLVIDA, e no banco

Financeiro: *"lançamos o bruto já para contemplar o valor com INSS... tem a
possibilidade de pegar em detalhes do lançamento, no campo valor base"*.

Confirmado no banco: o bruto está em **`FINANCE.CONTASPAGAR.CPGNVALORBASE`**.
Para os 12 pró-labores de fev/2026 (conta `030.010.0130`, histórico
"Pró labore mês atual"):

- `CPGNVALORBASE`     = **1.621,00**  ← BRUTO (valor da planilha)
- `CPGNVALORLIQUIDO`  = **1.442,69**  ← líquido (o que aparecia no resumo)

Ou seja, **não precisa de folha nem de parametrização manual**: o bruto já existe
no banco. Regra: para pró-labore (e provavelmente outras linhas de pessoal com
retenção), usar `CPGNVALORBASE` de `CONTASPAGAR`, não o `VALOR` líquido do resumo.
Chaves úteis em `CONTASPAGAR`: `COD_ADVG` (profissional), `PCTCNUMEROCONTA`
(conta), `CPGCHISTORICO` (histórico), `CPGDVECTO` (vencimento/competência),
`CPGDDATADESP` (data despesa), `CPGNVALORBRUTO`/`CPGNVALORBASE`/`CPGNVALORLIQUIDO`.
(Obs.: neste dado `CPGNVALORBRUTO` repetiu o líquido; o campo correto para o bruto
"de folha" é **`CPGNVALORBASE`**.)

### Lacuna 2 (bônus / distribuição de lucros extras) — RESOLVIDA como fórmula fixa

Financeiro: *"distribuição de lucros e reserva de bônus são coisas diferentes... a
reserva de bônus vamos demonstrar sendo 10% da margem líquida... a fórmula é fixa
para todos os meses"*.

Portanto:
- **Reserva de bônus = 10% da margem líquida** — **fórmula fixa, todos os meses**.
  É um **cálculo derivado do resultado**, não um lançamento a buscar no banco.
- **Distribuição de lucros** é **outra coisa** (não confundir com a reserva de
  bônus). Tratar separadamente; confirmar a origem/definição da distribuição de
  lucros quando essa linha precisar ser reproduzida.

### Situação final da cobertura

Com isto, o fechamento é **totalmente automatizável a partir do banco** + uma
fórmula fixa:

| DRE | Fonte | Observação |
| --- | --- | --- |
| Receita (recebimento/faturamento) | `LDESK.GERENC_VW_POSFIN_RESULTREC/FAT` | exato ao centavo |
| Despesas por conta (bruto, competência) | `LDESK.GERENC_LANCAMENTORESUMO` | linhas por conta batem |
| Pró-labore **bruto** (e retenções de pessoal) | `FINANCE.CONTASPAGAR.CPGNVALORBASE` | bruto 1.621 confirmado |
| Reserva de bônus | **fórmula fixa** = 10% da margem líquida | não é lançamento |
| Distribuição de lucros | a confirmar (é diferente da reserva de bônus) | fora da reserva de bônus |

Não há mais lacuna de **acesso a dados**. O que resta é modelagem: taxonomia
conta→linha do DRE, escolha de `CPGNVALORBASE` (bruto) vs resumo (líquido) nas
linhas de pessoal, e aplicar a fórmula fixa da reserva de bônus.
