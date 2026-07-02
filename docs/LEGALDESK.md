# LegalDesk OData — reference

> **Audience:** engineers changing `LegalDeskSource`, `legaldesk_client`, or closing
> builder logic. Credentials live in env (`LEGALDESK_*`), never in this file.

Sacred totals are locked by `backend/tests/test_legaldesk_source.py` against
`backend/tests/fixtures/legaldesk_2026_05.json`. A change that moves them is a
bug until proven otherwise.

## Connection

| Setting | Env var |
| --- | --- |
| Base URL | `LEGALDESK_BASE` (e.g. `https://legaldesk.mbclaw.com.br/API/v1/ODataGERALADV/`) |
| User | `LEGALDESK_USER` |
| Password | `LEGALDESK_PASSWORD` |

- **Protocol:** OData **v3** (not v4 — do not modernize query syntax).
- **Auth:** HTTP Basic, server-side only.
- **Response:** JSON rows under `"value": [ ... ]`.
- **Money fields** arrive as strings (e.g. `"316807.42"`). Cast to float before math.
- **Display:** Brazilian format — thousands `.`, decimals `,` (e.g. `415927.84` → `415.927,84`).
- **Pagination:** always pass a large `$top` (e.g. `5000`) **and** a `$filter`.
- **`AnoMes`:** competence month `'YYYY-MM'` (quoted in filters).
- **Date filters:** `datetimeoffset'YYYY-MM-DDT00:00:00Z'`.

Implementation: `backend/app/sources/legaldesk_client.py`, `backend/app/closing/builder.py`.

## What this API covers (and does not)

**In scope:** legal-practice data — invoices, receipts, cases, lawyers, fee splits.

**Out of scope for *this API*:** institutional expenses (payroll, rent, taxes, suppliers).
The OData API does not expose them. **However (2026-07-01):** these expenses were found in
the **SISJURI Oracle DB** `FINANCE` schema (`FINANCE.LANCAMENTO` + `FINANCE.PLANOCONTAS`),
readable via the bridge server — so the ~65 "manual" lines are **not** necessarily manual
forever. See `docs/SISJURI_DB.md`. This does not change the OData contract; it is an
alternative source.

**Dead ends (already investigated):**

- `/Web/*` is the ASP.NET UI with client-side encrypted login — not a data API.
- `ODataTRIBUTARIO` and the other area aliases return the **same** 631 entities as
  `ODataGERALADV` — no hidden finance module.
- Brute-force search across 1,700+ queries found **zero** institutional-expense values.

**Workbook year is 2026**, not 2025. An early 2025 investigation wrongly concluded
some revenue lines were not automatable.

## Two money regimes

| Concept | Endpoint family | Meaning |
| --- | --- | --- |
| Recebimento (cash) | `PosicaoFinanceiraResultadoRecebimentoViews` | money actually received |
| Faturamento (accrual) | `PosicaoFinanceiraResultadoFaturamentoViews` | invoiced |

Monthly total = **sum of `Valor1`** for the `AnoMes`.

**Receita de honorários** (workbook headline) == monthly Recebimento Bruto. Verified:
jan/2026 `279.821,07`, fev/2026 `319.233,58`, mai/2026 `415.927,84`.

## Four data primitives

### 1. `recebimento_bruto(ano_mes)`

- Entity: `PosicaoFinanceiraResultadoRecebimentoViews`
- Filter: `AnoMes eq '2026-05'`
- May 2026: **415927.84** (98 rows)

### 2. `faturamento_bruto(ano_mes)`

- Entity: `PosicaoFinanceiraResultadoFaturamentoViews`
- Filter: `AnoMes eq '2026-05'`
- May 2026: **719988.05** (97 rows)

### 3. `rateio_faturas(date_start, date_end)`

- Entity: `RateioFaturaProfissionalViews`
- Filter example: `FaturaDataEmissao ge datetimeoffset'2026-05-01T00:00:00Z' and FaturaDataEmissao lt datetimeoffset'2026-06-01T00:00:00Z'`
- May 2026: 286 rows, **53 distinct** `FaturaNumero`
- **De-duplicate** by `(FaturaNumero, ProfissionalSigla)` — each pair appears twice.

### 4. `faturas_centro_custo(date_start, date_end)`

- Entities: `FaturaViews` (header) + `RateioFaturaCasoViews` (per-case) on `FaturaNumero`
- Filter on `DataEmissao` with same date-range pattern as §3

## Tab automation map (15 tabs)

| Tab | Status | Source |
| --- | --- | --- |
| Resumo_Recebidas | API | §3 |
| FATURAS Analitico CENTRO CUSTO | API | §4 |
| Meta__2 (Recebimento + Faturamento) | API | §1 + §2 |
| Areas Sintetico (Receita / Faturamento) | API | §1 + §2 |
| Base_Resultado → Receita de honorários | API | §1 |
| Base_Resultado → ~65 expense lines | MANUAL | TOTVS Backoffice |
| Orçamento 2026 | MANUAL | API only has 2025 budget |
| DRE, Institucional, Contencioso, etc. | FORMULA | derive when sources filled |

Column layout in monthly tabs: **A = label, B = ANUAL, C..N = Jan..Dec** (May = G).

## Hard do-not list

1. Do not hunt institutional expenses in this API — proven absent.
2. Do not use OData v4 syntax, `$expand`, or `$select=*` tricks.
3. Do not ship credentials to the browser.
4. Do not forget Rateio row de-duplication.
5. Do not assume workbook year 2025.

## Ground-truth artifacts

| Path | Purpose |
| --- | --- |
| `reference/workbook/Copy of Fechamento MBC 02.2026.xlsx` | original spreadsheet |
| `reference/workbook/MBC_formula_audit_v2.xlsx` | formula audit |
| `reference/workbook/Juritis LegalDesk API.postman_collection.json` | Postman collection |
| `backend/tests/fixtures/legaldesk_2026_05.json` | recorded May 2026 payload (regression lock) |
