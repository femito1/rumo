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
