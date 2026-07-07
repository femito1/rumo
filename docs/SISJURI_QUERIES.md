# SISJURI closing automation — query spec (2026-07-02)

> Companion to `docs/SISJURI_DB.md`. This file is the **implementation-ready SQL**
> for a future `SisjuriDbSource` / `FinanceDbSource`. Every query is
> **parameterised by competence month** (`:ano_mes`, format `'YYYY-MM'`) and, where
> relevant, by date bounds (`:d_start` inclusive, `:d_end` exclusive, ISO dates).
> All queries are **read-only** (`SELECT`). Numbers verified against Feb/May 2026.
>
> **Sacred numbers still live in `docs/LEGALDESK.md` §4 and win.** These queries
> reproduce them; they do not redefine them.

## Conventions

- `:ano_mes`  — competence month string, e.g. `'2026-02'`.
- `:d_start` / `:d_end` — `DATE '2026-02-01'` and `DATE '2026-03-01'` (exclusive).
- Money is Oracle `NUMBER`; round with `ROUND(x,2)` at the edge only.
- Schemas: `LDESK` (LegalDesk mgmt), `FINANCE` (contas a pagar / ledger).
- One tenant in this instance (`ID_ESCRITORIO = 5B041D9E-98E9-68F1-A6E1-8C4DB3FE939A`);
  add an escritório filter if that ever changes.

---

## 1. Revenue KPIs — recebimento / faturamento (EXACT, sacred)

Headline recebimento_bruto and faturamento_bruto. Verified to the centavo
(415.927,84 / 719.988,05 for 2026-05).

```sql
-- Recebimento bruto (headline "receita_honorarios")
SELECT ROUND(SUM(VALOR1), 2) AS recebimento_bruto, COUNT(*) AS n
  FROM LDESK.GERENC_VW_POSFIN_RESULTREC
 WHERE ANO_MES = :ano_mes;

-- Faturamento bruto (headline "faturamento_realizado")
SELECT ROUND(SUM(VALOR1), 2) AS faturamento_bruto, COUNT(*) AS n
  FROM LDESK.GERENC_VW_POSFIN_RESULTFAT
 WHERE ANO_MES = :ano_mes;
```

Related views in the same family (available if needed): `_FATURA`, `_COBRANCA`,
`_ADIANTAMENTO`, `_DESPINC`, `_PENDENCIA`, `_RESUMODESP`, `_RESUMOPROF`.

---

## 2. Invoices emitted (count + detail)

```sql
-- faturas_emitidas count (53 for 2026-05). NB: the sacred count includes
-- invoices later cancelled -> do NOT filter DATA_CANCELAMENTO here.
-- (Verified: without filter = 53 = sacred; WITH `DATA_CANCELAMENTO IS NULL` = 50.)
SELECT COUNT(*) AS faturas_emitidas
  FROM LDESK.FAT_FATURA
 WHERE DATA_EMISSAO >= :d_start AND DATA_EMISSAO < :d_end;

-- invoice detail (headline table rows)
SELECT NUMERO, SITUACAO, DATA_EMISSAO,
       VALOR_HONORARIOS, VALOR_DESCONTO, VALOR_DESPESAS, VALOR_DESPESAS_TRIB,
       ID_PROFISSIONAL_RESP
  FROM LDESK.FAT_FATURA
 WHERE DATA_EMISSAO >= :d_start AND DATA_EMISSAO < :d_end
 ORDER BY DATA_EMISSAO, NUMERO;
```

---

## 3. Rateio por profissional / por caso

```sql
-- rateio por profissional (competence month; 286 rows for 2026-05)
SELECT ID_FATURA, ID_PROFISSIONAL, ID_CASO, ID_CLIENTE,
       VALOR_FATURADO, VALOR_TRABALHADO, ANO_MES
  FROM LDESK.FAT_RATEIOFATURA_PROF
 WHERE ANO_MES = :ano_mes;

-- aggregated per professional
SELECT ID_PROFISSIONAL,
       ROUND(SUM(VALOR_FATURADO), 2)  AS faturado,
       ROUND(SUM(VALOR_TRABALHADO), 2) AS trabalhado
  FROM LDESK.FAT_RATEIOFATURA_PROF
 WHERE ANO_MES = :ano_mes
 GROUP BY ID_PROFISSIONAL
 ORDER BY faturado DESC;
```

> NB: query the **base table** `FAT_RATEIOFATURA_PROF` (clean at PK level). The
> API view `RateioFaturaProfissionalViews` is the one that duplicates rows.

---

## 4. Expenses — the DRE cost side (gross, competence, per account)

This is the core expense query. `GERENC_LANCAMENTORESUMO` is already **gross** and
**by competence month** (`ANO_MES`). Three account families:
`020.*` = D (institucional), `030.*` = C (pessoal), `040.*` = I (investimentos).

```sql
-- All DRE expense lines for the month, by account (Feb-2026 verified)
SELECT r.ID_CONTA,
       MAX(r.NOME_CONTA)      AS nome_conta,
       MAX(r.NOME_CONTA_PAI)  AS nome_conta_pai,
       r.TIPO_CONTA,
       ROUND(SUM(r.VALOR), 2) AS total,
       COUNT(*)               AS n
  FROM LDESK.GERENC_LANCAMENTORESUMO r
 WHERE r.ANO_MES = :ano_mes
 GROUP BY r.ID_CONTA, r.TIPO_CONTA
 ORDER BY r.ID_CONTA;

-- Grand totals by family (D / C / I)
SELECT r.TIPO_CONTA, ROUND(SUM(r.VALOR), 2) AS total
  FROM LDESK.GERENC_LANCAMENTORESUMO r
 WHERE r.ANO_MES = :ano_mes
 GROUP BY r.TIPO_CONTA
 ORDER BY r.TIPO_CONTA;
```

### 4a. Expenses rolled up by cost-center (area)

For the "Custo equipe - {Contencioso, Econômico, Arbitragem}" DRE grouping.
Join `ID_GRUPOJURIDICO` to its name.

```sql
SELECT g.NOME                    AS area,
       ROUND(SUM(r.VALOR), 2)    AS total,
       COUNT(*)                  AS n
  FROM LDESK.GERENC_LANCAMENTORESUMO r
  LEFT JOIN LDESK.CAD_GRUPOJURIDICO g
         ON g.ID_GRUPOJURIDICO = r.ID_GRUPOJURIDICO
 WHERE r.ANO_MES = :ano_mes
   AND r.ID_CONTA LIKE '030.%'
 GROUP BY g.NOME
 ORDER BY total DESC;
```

### 4b. Per-professional detail (where present)

`ID_PROFISSIONAL` is populated for most personnel accounts (join to
`CAD_PROFISSIONAL.SIGLA`), but is **NULL on `030.010.0010` Distribuição Mensal
Fixa** (stored at account level only — see §6 for the per-partner split).

```sql
SELECT NVL(p.SIGLA, r.ID_PROFISSIONAL) AS sigla,
       r.ID_CONTA, MAX(r.NOME_CONTA)   AS nome_conta,
       ROUND(SUM(r.VALOR), 2)          AS valor
  FROM LDESK.GERENC_LANCAMENTORESUMO r
  LEFT JOIN LDESK.CAD_PROFISSIONAL p
         ON p.ID_PROFISSIONAL = r.ID_PROFISSIONAL
 WHERE r.ANO_MES = :ano_mes
   AND r.ID_CONTA LIKE '030.%'
 GROUP BY NVL(p.SIGLA, r.ID_PROFISSIONAL), r.ID_CONTA
 ORDER BY r.ID_CONTA, sigla;
```

---

## 5. Pró-labore (and personnel lines) — GROSS via CONTASPAGAR

The resumo (§4) stores pró-labore **net** (1.442,69). The workbook wants **gross**
(1.621). The gross lives in **`FINANCE.CONTASPAGAR.CPGNVALORBASE`** (confirmed by
finance: "valor base"). Use this whenever a personnel line must be gross.

```sql
-- Pró-labore GROSS per professional (Feb-2026: 12 x 1.621 verified)
SELECT cp.COD_ADVG                      AS sigla,
       ROUND(cp.CPGNVALORBASE, 2)       AS bruto,      -- 1621.00  <- workbook value
       ROUND(cp.CPGNVALORLIQUIDO, 2)    AS liquido,    -- 1442.69
       cp.CPGCHISTORICO                 AS historico
  FROM FINANCE.CONTASPAGAR cp
 WHERE cp.PCTCNUMEROCONTA = '030.010.0130'             -- Pró-Labores
   AND cp.CPGDVECTO >= :d_start AND cp.CPGDVECTO < :d_end
 ORDER BY sigla;

-- Pró-labore GROSS total for the month
SELECT ROUND(SUM(CPGNVALORBASE), 2)     AS prolabore_bruto,
       ROUND(SUM(CPGNVALORLIQUIDO), 2)  AS prolabore_liquido,
       COUNT(*)                         AS n
  FROM FINANCE.CONTASPAGAR
 WHERE PCTCNUMEROCONTA = '030.010.0130'
   AND CPGDVECTO >= :d_start AND CPGDVECTO < :d_end;
```

Useful `CONTASPAGAR` columns: `COD_ADVG` (professional sigla),
`PCTCNUMEROCONTA` (account), `CPGCHISTORICO` (history text),
`CPGDVECTO` (due/competence date), `CPGDDATADESP` (expense date),
`CPGDDATAPAGTO` (payment date), `CPGNVALORBASE` (**gross**),
`CPGNVALORLIQUIDO` (net), `CPGNVALORBRUTO` (here mirrors net — do NOT rely on it),
`GERADO_LD` (generated by LegalDesk).

> Decision rule for the source: for personnel accounts where the closing reports
> **gross** (pró-labore, and any line with withholding), read `CPGNVALORBASE` from
> `CONTASPAGAR`; for everything else use the resumo (§4). Confirm the exact set of
> "report gross" accounts with finance as we template more months.

---

## 6. Per-partner distribution split (optional detail)

The DRE headline only needs the **account total** of Distribuição Mensal Fixa
(`030.010.0010`), which §4 gives exactly. If per-partner detail is needed, the
split comes from the **cash ledger** `FINANCE.LANCAMENTO` (net), keyed by
`COD_ADVG`, filtered by the fixed-distribution histórico and split across the
partner's cost-centers.

```sql
-- Per-professional fixed distribution (net), from the cash ledger
SELECT l.COD_ADVG                       AS sigla,
       l.SIGLADEST                      AS cost_center,
       ROUND(SUM(l.LANNVALOR), 2)       AS valor,
       COUNT(*)                         AS n
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST = '030.010.0010'
   AND l.LANCHISTORICO LIKE 'Distribui%Fixa%'   -- fixed-distribution sub-type
   AND l.LANDDATA >= :d_start AND l.LANDDATA < :d_end
 GROUP BY l.COD_ADVG, l.SIGLADEST
 ORDER BY l.COD_ADVG, l.SIGLADEST;
```

> If gross per-partner distribution is ever required, source it from
> `CONTASPAGAR.CPGNVALORBASE` filtered on `PCTCNUMEROCONTA = '030.010.0010'`,
> the same way pró-labore is handled in §5.

---

## 7. Reserva de bônus — FORMULA (not sourced)

Finance: **reserva de bônus = 10% da margem líquida**, fixed for all months, and
is **different** from "distribuição de lucros". This is a computed line, not a DB
lookup:

```
reserva_bonus = 0.10 * margem_liquida_do_mes
```

where `margem_liquida` is the DRE's net result for the month (revenue − expenses −
taxes − amortização), computed from §1 + §4 (+ §5 gross adjustments). Encode as a
constant `BONUS_RESERVE_RATE = 0.10`. Confirm the exact base (margem líquida
definition, rounding) against one closed month before locking.

> "Distribuição de lucros" is a separate line; its source/definition is still to
> be confirmed with finance (do not conflate with the bonus reserve).

---

## 8. Reference / lookup queries (dimensions)

```sql
-- Professionals: GUID -> sigla (and ID_PESSOA for full name if needed)
SELECT ID_PROFISSIONAL, SIGLA, ID_PESSOA, SOCIO, DATA_ENTRADA, DATA_SAIDA
  FROM LDESK.CAD_PROFISSIONAL;

-- Cost-center (area) names
SELECT ID_GRUPOJURIDICO, NOME FROM LDESK.CAD_GRUPOJURIDICO;

-- Chart of accounts (DRE scaffold / line taxonomy)
SELECT PCTCNUMEROCONTA, PCTCTITULO, PCTCNUMEROCONTAPAI, PCTNNIVEL
  FROM FINANCE.PLANOCONTAS
 ORDER BY PCTCNUMEROCONTA;

-- Available competence months present in the expense resumo
SELECT DISTINCT ANO_MES FROM LDESK.GERENC_LANCAMENTORESUMO ORDER BY ANO_MES;
```

---

## 9. Assembly summary (what feeds each DRE block)

| DRE block | Query | Source object | Grain |
| --- | --- | --- | --- |
| Recebimento / Faturamento | §1 | `GERENC_VW_POSFIN_RESULTREC/FAT` | month, exact |
| Faturas emitidas | §2 | `FAT_FATURA` | month |
| Rateio prof/caso | §3 | `FAT_RATEIOFATURA_PROF` | month |
| Despesas por conta (020/030/040) | §4 | `GERENC_LANCAMENTORESUMO` | month x conta, gross |
| Custo equipe por área | §4a | resumo + `CAD_GRUPOJURIDICO` | month x área |
| Pró-labore / pessoal **bruto** | §5 | `CONTASPAGAR.CPGNVALORBASE` | month x prof |
| Distribuição por sócio (detalhe) | §6 | `LANCAMENTO` (net) | month x prof x CC |
| Reserva de bônus | §7 | **fórmula** 10% margem líquida | computed |

All month-parameterised → **works for any competence month** (expense resumo
present 2018-06 → 2026-06, 97 months; billing/revenue history is longer). No
hardcoded month anywhere.

### Validation log (2026-07-02)

- §1 recebimento/faturamento 2026-05 = 415.927,84 / 719.988,05 — exact ✓
- §2 faturas 2026-05 = **53** (no cancellation filter) ✓
- §4 Feb-2026 account roll-up matches workbook lines ✓
- §4a area roll-up (Econômico 94.571,59 / Arbitragem 70.796,83 / Contencioso
  49.941,93) — join to `CAD_GRUPOJURIDICO` works ✓
- §5 pró-labore gross `CPGNVALORBASE` = 1.621 x 12 ✓
- §8 resumo months 2018-06 → 2026-06 (97) ✓

### Probe findings (2026-07-02) — per-area recebimento & per-lawyer

- `GERENC_VW_POSFIN_RESULTREC` has **`ID_PROFISSIONAL`** and **`ID_CASO`** but
  **no group/area column**; area must be derived via professional→grupo.
- `CAD_PROFISSIONAL.ID_GRUPOJURIDICO` **exists** → prof→area join is valid.
- **Per-area recebimento is NOT directly available.** `FAT_RATEIOFATURA_PROF`
  aggregated by area (via prof→grupo) is **faturamento-basis** and includes a
  large **"Não Alocados"** bucket (Feb: Contencioso faturado 342.576 / Econ
  341.642 / Arbitragem 85.618 / Não Alocados 274.888). It does **not** equal the
  workbook's per-area *Recebimento* (Feb ~138.600 / 120.362 / 86.846). The
  workbook allocates **received cash** to areas by a rule we must confirm with
  finance (candidate: apply each area's faturado *share*, excluding Não
  Alocados, to the month's total recebimento). Until confirmed, area
  Recebimento realizado stays blank; the DRE structure is faithful regardless.
- **Per-lawyer 030.\* detail** via resumo→`CAD_PROFISSIONAL.SIGLA` returns only
  INSS-Jurídico (324,20), Convênio, and Pró-Labores (net 1.442,69) per person;
  `030.010.0010 Distribuição Mensal Fixa` is a lump (Feb 172.129,96, NULL prof).
  The workbook's per-lawyer salary/distribution rows come from the §6
  `FINANCE.LANCAMENTO` per-partner split, not from the resumo.

### Probe findings (2026-07-03) — per-area recebimento RULE CONFIRMED ✅

The per-area *Recebimento* split **is** derivable, and it is NOT via the
professional. The receipt view splits by **case → área jurídica**:

- `GERENC_VW_POSFIN_RESULTREC.ID_PROFISSIONAL` is entirely unmapped for receipts
  (all rows `(sem area)`), so prof→grupo does **not** work here.
- `CAD_CASO` carries **`ID_AREAJURIDICA`** (+ `ID_SUBAREAJURIDICA`); a dedicated
  `CAD_AREAJURIDICA` table holds the name (`NOME`, e.g. "Direito Econômico",
  "Arbitragem MV", "Contencioso", "Ambiental").
- Rule (verified to the centavo, Jan & Fev 2026):

  ```sql
  SELECT NVL(a.NOME,'(sem area)') area, ROUND(SUM(r.VALOR1),2) total
    FROM LDESK.GERENC_VW_POSFIN_RESULTREC r
    LEFT JOIN LDESK.CAD_CASO c ON c.ID_CASO = r.ID_CASO
    LEFT JOIN LDESK.CAD_AREAJURIDICA a ON a.ID_AREAJURIDICA = c.ID_AREAJURIDICA
   WHERE r.ANO_MES = :ano_mes GROUP BY a.NOME;
  ```

  | area | Jan | Fev |
  |---|---|---|
  | Contencioso | 57.490,92 | 133.202,74 |
  | Direito Econômico | 105.768,64 | 117.626,71 |
  | Arbitragem MV | 116.561,51 | 68.404,13 |
  | Ambiental | 0 | 0 |

  These are the workbook's per-area **base** numbers (57.491 / 105.769 / 116.562,
  etc.). The workbook's final `Receita` per area = this base **+** the small
  cross-area reclassifications in `Resumo_Recebidas` (net 0 across areas). Those
  transfers are genuinely manual (no DB rule) and modeled as `area_transfers`
  (origem→destino deltas) overlaid on the base.
- Name mapping: `Direito Econômico`→Econômico, `Arbitragem MV`→Arbitragem
  (handled by `workbook_layouts.match_area`); `Ambiental` (always 0) is ignored.
- Faturamento mirrors this via `GERENC_VW_POSFIN_RESULTFAT` (extract key
  `faturamento_area`).
- **`faturas_analitico` corrected (2026-07-03 probe):** `FAT_FATURA` was the
  wrong source — it is invoice *headers* with **no payment date, no líquido, no
  `ID_CASO`**. The per-case detail is built on `GERENC_VW_POSFIN_RESULTFAT`
  (`ID_CASO` + `VALOR1` + `ANO_MES`) joined to `CAD_CASO` (`CODIGO`, `ASSUNTO`,
  `ID_AREAJURIDICA`). Grain is per case (not per invoice); client name lives
  behind `CAD_CLIENTE`→`CAD_PESSOA` (unverified 2-hop) so it is omitted — the
  case `ASSUNTO` is shown instead, matching the workbook's "Nome do caso".

---

## 10. Data egress — how the automation actually reaches the DB

The DB (`172.16.237.9:1521`) sits on a **private OCI VCN**. Only `MBC-LDESK01`
(the RDP/PowerBI-gateway box) can route to it. So our backend on the VPS cannot
connect to Oracle directly. Options, best-first:

### Option A (recommended) — a small "push" agent on MBC-LDESK01

Mirror what the Power BI gateway does conceptually: run a tiny agent **on the
server** that has the only working route to the DB, and have **it** reach out to
our VPS (outbound HTTPS), so we never need an inbound firewall rule.

```
MBC-LDESK01 (has Oracle route)                Our VPS (public)
  agent (Python/PowerShell)  --- HTTPS POST --->  /api/ingest  (token-auth)
  runs the §1–§8 queries                          stores/normalizes -> ClosingProvider
  on a schedule (e.g. daily / on-demand)
```

- **Pros:** no inbound port on the server; uses the existing outbound path; the
  agent is small; credentials for Oracle never leave the server; we control the
  payload shape (already the SectionKey JSON).
- **Cons:** something must run on the server (a scheduled task / service).
- **Shape:** the agent runs the exact SQL in this doc via the Oracle client
  already installed (`C:\oracle11\...\sqlplus.exe` or, better, `python-oracledb`
  thin mode — no client needed), serializes to JSON, POSTs to our authenticated
  ingest endpoint. A `SisjuriDbSource` on our side then reads that JSON (same as
  `LegalDeskSource.from_recorded_payload`).

### Option B — reverse tunnel / gateway from the VPS to the server

Stand up a persistent outbound tunnel from MBC-LDESK01 to the VPS (e.g. SSH
reverse tunnel, WireGuard, or Cloudflare Tunnel), then our backend connects to
Oracle "through" the tunnel as if local.

- **Pros:** our backend keeps a normal DB connection; no bespoke agent code; the
  `SisjuriDbSource` can use `python-oracledb` directly.
- **Cons:** a always-on tunnel + service to keep alive on the server; slightly
  more moving parts / ops; exposes the DB port over the tunnel (scope it tightly).

### Option C — install Oracle connectivity on the VPS + network route (NOT viable alone)

Installing the Oracle client/driver on the VPS is easy, **but** it does not solve
the problem: the VPS still has **no network route** to the private VCN address
`172.16.237.9`. It would only work combined with a VPN/peering into the OCI VCN
(an infra change on MBC/OCI side) — i.e. Oracle-on-VPS is necessary but not
sufficient. Pursue only if MBC/OCI will grant the VPS a route into the VCN.

### Recommendation

Start with **Option A** (push agent on the server): it matches the existing,
already-approved Power BI egress pattern, needs no new inbound firewall rules or
VPN, and keeps DB credentials on the server. Use **`python-oracledb` in thin mode**
so no Oracle client install/upgrade is required; schedule it as a Windows Task
that POSTs the closing JSON to a token-authenticated `/api/ingest` on the VPS.
Keep Option B in reserve if we later want live/interactive queries instead of
scheduled snapshots.

### Backend integration (either option)

- New env (add to `backend/.env.example`): `SISJURI_DSN`, `SISJURI_USER`,
  `SISJURI_PASSWORD` (used by the agent or by the tunneled backend), or
  `INGEST_TOKEN` (Option A ingest auth).
- New `app/sources/sisjuri_db.py` implementing `Source`, emitting the same
  `SectionKey`s. Compose via `ClosingProvider` with `merge_policy` so it can
  augment or fall back relative to `LegalDeskSource` without touching the API
  contract or SPA.
- Reuse the recorded-payload pattern (`from_recorded_payload`) for tests so the
  DB source is unit-testable offline with a captured JSON fixture.

---

## 11. Per-area Custo equipe — the automation frontier (2026-07-07)

**Goal is FULL automation.** The workbook / dashboard / Demonstrativo are
development *aids* (ground-truth to validate against), **not** monthly inputs.
Nothing we ship may depend on those files arriving each month. Per-area Custo
equipe is the last DRE piece not yet automated, so it gets the strictest test:
we assume automation is possible and only accept manual config once impossibility
is *100% proven*.

### What is decomposed, and where each part lives

Per-area Custo equipe = Σ per-lawyer, per-account 030.* costs, grouped by area.

| Component | ~Share | Per-lawyer in DB? | Area in DB? | Verdict |
| --- | --- | --- | --- | --- |
| INSS, Convênio, Pró-Labore, Bolsa | ~20% | ✅ `SIGLA` (resumo) | ✅ prof→`CAD_GRUPOJURIDICO` | automatable now |
| **Distribuição Mensal Fixa** (`030.010.0010`) | ~80% | ✅ `LANCAMENTO.COD_ADVG` | ❓ `SIGLADEST` — **UNTESTED** | **the crux** |

Feb-2026 evidence: SISJURI per-lawyer grand total **215.310,35** vs ledger
**216.953,74** (Δ 0,76%). So the money is essentially all present — this is an
**allocation** problem, not a missing-data problem. The distribuição comes back
as a single lump (172.129,96, NULL sigla, NULL area) in `custo_equipe_prof`
*only because that query uses the resumo view*; the cash ledger
`FINANCE.LANCAMENTO` keys the same amount by `COD_ADVG` (lawyer) and carries a
`SIGLADEST` "cost center".

### The one unproven question (blocks the full-automation verdict)

Does `LANCAMENTO.COD_ADVG` + `SIGLADEST` reproduce the ledger's per-lawyer,
per-area distribuição **to the centavo — including the manual-looking splits**
(e.g. Aurelio `=3182.83/2`, half Contencioso / half Econômico)?

- If **yes** → the split is *booked in the accounting system*, not invented in
  the spreadsheet. A future lawyer's split flows through automatically. **Full
  automation is possible**; source distribuição from `LANCAMENTO` per CC and stop
  reading the workbook entirely.
- If **no** → then (and only then) do we discuss the minimal manual artifact
  (e.g. a per-lawyer area-allocation table that changes only on staff moves).

**Why it is not yet answered:** the snapshot's `distribuicao_socio` is **empty
(0 rows)** — the documented §6 query carries `AND LANCHISTORICO LIKE
'Distribui%Fixa%'`, a filter that has never been validated and apparently matches
nothing. So §6 has never actually returned data.

### Next step — run the probe (read-only, on MBC-LDESK01)

`ops/sisjuri-agent/probe_distribuicao_area.sql` (drops the untested historico
filter; inspects raw `COD_ADVG`/`SIGLADEST`, decodes `SIGLADEST`, checks GROSS
via `CONTASPAGAR`, and totals for reconciliation vs 172.129,96). Run it via the
same sqlplus-over-RDP recipe as the other probes and paste the output back.

**Do NOT** treat the workbook importer (`app/closing/ledger_import.py`,
`scripts/import_ledger.py`, built 2026-07-07) as the automation path — it mirrors
the monthly workbook and therefore does **not** reduce their manual work. It is
retained only as an offline validation harness (it ties to the dashboard to the
centavo) and as a temporary fallback until this probe settles the distribuição
question. If the probe proves automation, the importer is removed.

### Probe RESULT (2026-07-07) — FULL AUTOMATION PROVEN ✅

`probe_distribuicao_area.sql` ran on MBC-LDESK01 for Feb 2026. Findings:

- **Distribuição Mensal Fixa is per-lawyer AND per-area in the DB.**
  `FINANCE.LANCAMENTO` (account `030.010.0010`, **no** historico filter) returns
  one row per `(COD_ADVG, SIGLADEST)` — lawyer × destination cost-center. The
  documented `LANCHISTORICO LIKE 'Distribui%Fixa%'` filter was the bug: the real
  histórico text varies ("Pagamento de Distribuição Fixa Liquida Mensal", DL
  diferença, subsídio, bônus, …), so it matched nothing. **Drop that filter.**
- **Ties to the centavo:** Σ = **172.129,96** (21 rows) = the ledger lump. Nothing
  missing.
- **`SIGLADEST` is the AREA (cost-center), not a person.** Codes seen: `ECT`
  (Equipe Contencioso), `EDE` (Equipe Direito Econômico), `ESP` (Arbitragem).
  Every professional also maps to a home area via
  `CAD_PROFISSIONAL.ID_GRUPOJURIDICO → CAD_GRUPOJURIDICO.NOME` (grupos: Equipe
  Contencioso, Equipe Direito Econômico, Arbitragem, Equipe Ambiental,
  Administração, Não Alocados).
- **Cross-area splits ARE in the DB.** `BBX` (Beatriz) distribuição came back
  split **518,40 → ECT (Contencioso)** and **7.537,40 → EDE (Econômico)**. This is
  exactly the "Aurelio ÷2" pattern the ledger shows by hand — but it is *booked*
  against `SIGLADEST` at payment time. So **a future lawyer's split flows through
  automatically**; no spreadsheet, no manual per-lawyer table, no monthly labor.
- **Gross lives in `CONTASPAGAR`** (`CPGNVALORBASE`/`CPGNVALORBRUTO`, account
  `030.010.0010`) per `COD_ADVG` (AM 23.379, DC 23.379, EHF 12.879, …). Note
  `CONTASPAGAR` has **no** cost-center column, so the *area split* must come from
  `LANCAMENTO.SIGLADEST`; gross-vs-net reconciliation (LANCAMENTO net vs
  CONTASPAGAR gross) is the remaining detail to pin against the ledger's
  gross-basis rows.

**Conclusion:** per-area Custo equipe is **fully derivable from SISJURI** with no
monthly manual input. The workbook ledger importer is therefore **not** needed as
a data path and should be removed once the extract below is wired and validated.

**`SIGLADEST` → DRE area map** (to encode; confirm `ESP` = Arbitragem and capture
any other codes over a few months):
`ECT`→Contencioso, `EDE`→Econômico, `ESP`→Arbitragem;
`EAM`/Ambiental + `Administração` + `Não Alocados` → not one of the three DRE
cost centers (handle explicitly: Ambiental is ~0; Administração is institucional).

### Extract change needed (implementation-ready)
Replace the empty `distribuicao_socio` query and augment `custo_equipe_prof`:

```sql
-- Per-lawyer × area distribuição (NET), from the cash ledger. NO historico filter.
SELECT l.COD_ADVG AS sigla, l.SIGLADEST AS area_cc,
       ROUND(SUM(l.LANNVALOR),2) AS valor
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST='030.010.0010'
   AND l.LANDDATA >= :d_start AND l.LANDDATA < :d_end
 GROUP BY l.COD_ADVG, l.SIGLADEST;
```

Then per-area Custo equipe = (area-tagged 030.* small accounts from the resumo,
already in `custo_equipe_prof`) + (this distribuição folded by `SIGLADEST`→area).
Validate the three area subtotals against the ledger (76.342 / 78.817 / 61.794 for
Feb) to the centavo before removing the importer.

### CORRECTION (2026-07-07, later) — reconciliation is NOT clean; two real gaps

Pulling the **live Supabase snapshot** (2026-02) and joining per-lawyer against the
ledger's "Distribuição Mensal Fixa" rows exposed that the earlier "ties to the
centavo / splits are in the DB" claim was too optimistic. Reality:

1. **`distribuicao_socio` is already in the stored snapshots** (no backfill needed):
   2026-02 has 13 rows summing to **172.129,96**, with `cost_center` ∈ {ECT, EDE,
   ESP} and BBX genuinely split 518,40 ECT / 7.537,40 EDE. Good.

2. **Aurelio's 50/50 IS in the DB — but not in the transactions.** His distribuição
   is a *single* EDE (Econômico) row in both `LANCAMENTO` and `CONTASPAGAR`
   (23.379, no caso/cliente/second CC). The split lives in a **static config
   table**: `LDESK.CAD_RATEIO_GRUPO(ID_PROFISSIONAL, ID_GRUPOJURIDICO, PERCENTUAL,
   ANO_MES_INICIAL, ANO_MES_FINAL)`. AM has two ACTIVE rows (2022-08..9999-12):
   Equipe Contencioso **50%**, Equipe Direito Econômico **50%**. He is the ONLY
   multi-area lawyer in that table (19 rows total; everyone else single grupo).
   `SSJR.CAD_RATEIOADVG_HIST` has the same shape (COD_ADVG, ANO_MES, SETOR,
   PERCENTUAL) but is **stale** (last rows 2022-08) — do NOT use it; use
   `CAD_RATEIO_GRUPO` with the ANO_MES validity window.

3. **BUT even after applying AM 50/50, the per-area totals still DON'T match the
   ledger:**

   | area        | custo_area (net, SISJURI) | +AM 50/50 | ledger (Feb) | gap |
   |-------------|--------------------------:|----------:|-------------:|----:|
   | Contencioso |                 49.941,93 | 61.631,43 |    76.342,35 | **−14.710,92** |
   | Econômico   |                 94.571,59 | 82.882,09 |    78.817,05 |  +4.065,04 |
   | Arbitragem  |                 70.796,83 | 70.796,83 |    61.794,34 |  **+9.002,49** |
   | TOTAL       |                215.310,35 |215.310,35 |   216.953,74 |  −1.643,39 |

   The **total** is within 1.643 (that is broadly net-vs-gross + Reajuste top-ups),
   but the **per-area allocation is off by ±10–15k**. Arbitragem is +9k with no AM
   involvement at all, so `SIGLADEST` cost-center ≠ ledger area for several lawyers.

4. **Per-lawyer, SISJURI-net vs ledger-fixa diverge idiosyncratically** (not a
   uniform tax haircut): e.g. JGS +6.507, RB −6.053, DC −3.797, ASG +3.538. The
   finance team applies per-lawyer manual gross-ups / reajustes / timing that are
   **not present in account 030.010.0010** as booked.

**Honest verdict (as of this probe round):** per-area Custo equipe is **NOT yet
proven fully derivable to the centavo** from SISJURI. What IS proven:
- The distribuição data (per lawyer × cost-center) is in the snapshots.
- Aurelio's cross-area split is DB-derivable via `CAD_RATEIO_GRUPO` (%-based,
  future-proof for any multi-area professional).

What is NOT yet reconciled:
- Net (LANCAMENTO/`distribuicao_socio`) vs gross (CONTASPAGAR) vs the ledger's
  per-lawyer figure — the ledger figure is neither the raw net nor the raw gross
  for several lawyers (JGS, RB, DC…).
- Whether `SIGLADEST` (payment cost-center) or `CAD_RATEIO_GRUPO` (config %) is the
  authoritative area — they disagree, and neither alone reproduces the ledger.

**Next probes to close it (do NOT wire the extract until these pass):**
- Dump `CONTASPAGAR` gross per lawyer for account 030.010.0010 AND every 030.010.*
  sub-account for Feb, so we can rebuild each lawyer's full Custo equipe components
  (distribuição + reajuste + pró-labore + convênio + bolsa) the way the ledger does.
- Confirm the ledger's per-lawyer figure = Σ of which SISJURI accounts, per lawyer,
  so we know the exact account set and gross/net basis. Only then does per-area
  reconcile to the centavo.

### Component-level probe RESULTS (2026-07-07) — the real Custo equipe recipe

`probe_custo_components.sql` (Feb 2026) gave the per-lawyer × account breakdown.
This is the definitive account map for **Custo equipe** and resolves the gross/net
question. **Future agents: start here — do not re-derive.**

#### Custo equipe component accounts (all under `030.010.*`)
| account       | ledger line              | Feb basis seen                                  |
|---------------|--------------------------|-------------------------------------------------|
| `030.010.0010`| Distribuição Mensal Fixa (+ Reajuste) | GROSS in `CONTASPAGAR.CPGNVALORBASE`; NET in `LANCAMENTO.LANNVALOR`. Total NET 172.129,96 / GROSS base 184.439,20 |
| `030.010.0050`| INSS - Jurídico          | 3.890,40 (12 rows, **blank COD_ADVG in LANCAMENTO destination**) |
| `030.010.0110`| Convênio Médico          | 19.177,71 net (11 rows, **blank COD_ADVG in LANCAMENTO destination**) |
| `030.010.0130`| Pró-Labore               | GROSS 1.621/lawyer, NET 1.442,69/lawyer (per lawyer, `CONTASPAGAR.COD_ADVG`) |
| `030.010.0140`| Bolsa Auxílio            | JVO 2.800 (Contencioso) |

Plus AASP, Vale, Seguro, ISS, Subsídio lines in the ledger (small; need account
numbers — likely `030.010.00xx`; not all appeared in Feb LANCAMENTO destination).

#### GROSS vs NET — SOLVED
`CONTASPAGAR.CPGNVALORBASE` **= the ledger's gross figure**. Proof (account 0010):
- DC: net 19.582,18 → **base 23.379** = ledger 23.379 ✅
- RB: net 17.325,69 → **base 23.379** = ledger 23.379 ✅
- EHF: net 10.922,75 → **base 12.879** = ledger 12.879 ✅
`CPGNVALORBRUTO`/`CPGNVALORLIQUIDO` = the net (post-withholding). So: **use
`CPGNVALORBASE` for the ledger-basis gross; the base−liquido delta is INSS/IR.**

#### The AREA split — where it lives
- `CONTASPAGAR` has **NO cost-center** column. The area/CC (`SIGLADEST` ∈ ECT/EDE/ESP)
  is **only in `FINANCE.LANCAMENTO`** (destination cost-center of the cash movement).
- So per-area distribuição = **gross (CONTASPAGAR base) allocated by the SIGLADEST
  proportions from LANCAMENTO**, with **Aurelio (AM) overridden 50/50** by
  `CAD_RATEIO_GRUPO` (AM is the only multi-area lawyer; his single LANCAMENTO row is
  100% EDE, so SIGLADEST alone is wrong for him — the config table is authoritative).

#### STILL OPEN (next probe) — per-lawyer tagging for convênio & INSS
`030.010.0110` (Convênio) and `030.010.0050` (INSS) returned with **blank COD_ADVG /
SIGLADEST in the LANCAMENTO destination grouping**, yet the ledger splits convênio
per lawyer (e.g. Aurelio 1.591,41). The per-lawyer link for these must be in another
column — candidates: `LANCAMENTO.LANCPROFORG` (source professional),
`LANCAMENTO.COD_ADVG` on the *origin* side, or `CONTASPAGAR.COD_ADVG` (which DID
carry pró-labore per lawyer). Probe both: group `030.010.0110`/`0050` by
`CONTASPAGAR.COD_ADVG` and by every prof/CC column in LANCAMENTO.

#### Ledger block composition (Feb, from Base_Resultado, PROGRAMMATIC — trustworthy)
| area        | distrib_fixa | reajuste | prolabore | convenio | bolsa | subsidio | vale | aasp | iss | TOTAL |
|-------------|-------------:|---------:|----------:|---------:|------:|---------:|-----:|-----:|----:|------:|
| Contencioso |    58.210,90 | 2.084,40 |  5.673,50 | 6.161,10 |2.800 |        – |1.249,40|163,05|   – |76.342,35|
| Econômico   |    59.084,38 | 2.554,38 |  7.294,50 | 6.811,44 |    – | 3.018,00 |    – |54,35|1.500|80.317,05*|
| Arbitragem  |    50.866,40 | 1.610,40 |  4.863,00 | 2.833,54 |    – |        – |    – |   – |   – |61.794,34|
*Econ block sums 80.317 but subtotal row shows 78.817 — the 1.500 ISS/comissão line
sits outside the Custo-equipe subtotal (it's a Participação/comissão line). Confirm.

**Reconciliation status:** distribuição gross basis SOLVED; Aurelio split SOLVED via
CAD_RATEIO_GRUPO; pró-labore/bolsa per-lawyer SOLVED. Remaining: convênio + INSS
per-lawyer area tagging (one more probe), then full per-area Custo equipe should tie.

### Convênio/INSS per-lawyer key FOUND (2026-07-07) — `LANCPROFDEST`

`probe_convenio_inss.sql` (Feb 2026) revealed:
- **`CONTASPAGAR` only carries 0010 (distribuição), 0130 (pró-labore), 0140 (bolsa).**
  Grouping `CONTASPAGAR` by `COD_ADVG` for `030.010.0110`/`0050` returns **no rows** —
  convênio & INSS are NOT in CONTASPAGAR at all. They live only in `LANCAMENTO`.
- **The per-lawyer key for convênio/INSS is `LANCAMENTO.LANCPROFDEST`** (destination
  professional), NOT `COD_ADVG`/`SIGLADEST` (those are blank for these accounts).
  §3 showed all 12 lawyers tagged via `LANCPROFDEST` for both 0110 and 0050.
- **Full 030.010.* account catalogue** (from `FINANCE.PLANOCONTAS`, name col =
  `PCTCTITULO`; the code col is `PCTCNUMEROCONTA`, parent `PCTCNUMEROCONTAPAI`):
  0000 Custos c/ Pessoal (parent), 0010 Distribuição, 0020 Bônus Associados,
  0030 OAB, 0040 Rescisões, 0050 INSS-Jurídico, 0080 Participação E, 0090
  Estacionamento, 0100 Vale Refeição, 0110 Convênio Médico, 0120 Participação I,
  0130 Pró-Labores, 0140 Bolsa Auxílio, 0150 AASP, 0160 ISS, 0170 OAB anuidades,
  0180 Cursos/Trein., 0190 Adiantamento, 0200 Seguro de Vida, 0210 IR-Equipe,
  0220 Vale Transporte, 0230 Exame médico, 0240 Férias, 0250 Aux Home Office,
  0260 Aux Saúde, 0270 Headhunter.
- **Grand totals (Feb):** Σ CONTASPAGAR gross base `030.010.*` = **206.691,20** (34
  rows); Σ ledger Custo-equipe blocks ≈ 216.954. Gap ≈ convênio/INSS + small lines
  that are LANCAMENTO-only.

**Derivation recipe (per lawyer, per account):**
- **Amount:** gross where CONTASPAGAR has it (`CPGNVALORBASE`: 0010, 0130, 0140),
  else NET from `LANCAMENTO.LANNVALOR` (0110, 0050, small lines).
- **Lawyer key:** `CONTASPAGAR.COD_ADVG` for the gross accounts; `LANCAMENTO.LANCPROFDEST`
  for the LANCAMENTO-only accounts.
- **Area:** `LANCAMENTO.SIGLADEST` for 0010 (the only account with a real CC), else
  the lawyer's HOME area (`CAD_PROFISSIONAL.ID_GRUPOJURIDICO`), with **Aurelio (AM)
  overridden 50/50** via `CAD_RATEIO_GRUPO`.

### Full component matrix RESULTS (2026-07-07) — AREA solved, AMOUNT is the residual

`probe_lancprofdest.sql` (Feb 2026):
- **Σ ALL `030.010.*` NET = 215.310,35** (57 rows) = `custo_area` total exactly.
  Ledger Custo-equipe total = 216.953,74 → **only 1.643,39 more** (the distribuição
  gross-up). So SISJURI has essentially all the money; the question is allocation.
- **Convênio (0110) & INSS (0050) per-lawyer via `LANCPROFDEST`** confirmed
  (§3): INSS is a flat 324,20/lawyer (12 lawyers); convênio varies (AM 3.182,83,
  RB 3.427,58, …). Pró-labore (0130) 1.442,69/lawyer net.
- **AREA assignment is SOLVED = lawyer HOME area + AM 50/50.** Per-lawyer, the
  distribuição SIGLADEST area == home area == ledger area for **everyone except**:
  - **AM**: SIGLADEST 100% EDE, ledger 50/50 → use `CAD_RATEIO_GRUPO` (done).
  - **BBX**: SIGLADEST splits 518 ECT / 7.537 EDE, but home & ledger both = 100%
    Contencioso → **use HOME area, not SIGLADEST** (SIGLADEST is noisy for her).
  ⇒ **Rule: area = HOME grupo (`CAD_PROFISSIONAL.ID_GRUPOJURIDICO`) + `CAD_RATEIO_GRUPO`
    percentage override. Do NOT fold distribuição by SIGLADEST** (it disagrees for BBX).

- **RESIDUAL = per-lawyer AMOUNT on 0010**, same area:
  - JGS: net 15.885,98 vs ledger fixa 9.379 (Δ 6.507) — Arbitragem +.
  - RB:  net 17.325,69 vs ledger 23.379 (Δ −6.053) — Econômico −.
  - DC:  net 19.582,18 vs ledger 23.379; IAC net 17.171 vs ledger 15.605.
  These are NOT area errors; they are Fixa-vs-(Fixa+Reajuste+Diferença+gross) mix
  differences within account 0010. Probe `probe_0010_detail.sql` breaks 0010 by
  histórico (Fixa / Reajuste / Diferença / Bônus) net & gross to reconstruct the
  ledger's per-lawyer figure exactly.
