# Automation Implementation Guide — MBC Monthly Closing Dashboard (v0)

> **AUDIENCE: this document is written for an LLM coding agent that will build a v0 dashboard.** It is self-contained. Read it top to bottom before writing code. Every fact here was empirically validated against the live API on 2026-06-03. Do not re-derive what is already stated; trust the verified mappings and build.

## 0. TL;DR / Mission

Build a **v0 web dashboard** that reproduces, as close to **1:1 as possible**, the MBC monthly-closing spreadsheet `Copy of Fechamento MBC 02.2026.xlsx`, for the target month **May 2026 (`AnoMes = '2026-05'`)**.

- The dashboard must visually mirror the spreadsheet's tabs and line items, so a human can eyeball "what is automated vs. still manual".
- **Automated cells** (fed from the API) must be clearly marked (e.g. green badge "API") and show the live value.
- **Manual cells** (not available in this API) must be clearly marked (e.g. grey badge "MANUAL") and left blank or show a placeholder.
- Target month is May 2026 because it is the most recent **fully closed** month (June 2026 is still partial — verified: June recebimento has only 13 rows vs. May's 98).

## 1. The data source (the ONLY API you have)

- **Base URL:** `https://legaldesk.mbclaw.com.br/API/v1/ODataGERALADV/`
- **Protocol:** OData **v3** (NOT v4 — do not use v4 syntax).
- **Auth:** HTTP Basic. User `integracao`, password `RumoTech1!`.
- **Response shape:** JSON. Rows are always under the `value` key: `{ "value": [ {row}, {row}, ... ] }`.
- **Money fields arrive as STRINGS** (e.g. `"316807.42"`). Always cast to float.
- **Decimal point** in the API is `.`; the spreadsheet displays Brazilian format (`.` thousands, `,` decimal). Convert for display.
- **Pagination caveat:** always pass a large `$top` (e.g. `$top=5000`) AND a `$filter`. Without a filter some views silently return stale paginated data.
- **`AnoMes`** is the competence month, format `'YYYY-MM'` (string, quoted in filters).
- **Date filters** use OData v3 syntax: `datetimeoffset'YYYY-MM-DDT00:00:00Z'`.

### 1.1. Minimal fetch helper (reference implementation, Python)

```python
import requests
from requests.auth import HTTPBasicAuth

BASE = "https://legaldesk.mbclaw.com.br/API/v1/ODataGERALADV"
session = requests.Session()
session.auth = HTTPBasicAuth("integracao", "RumoTech1!")
session.headers["Accept"] = "application/json"

def api_get(entity: str, filter_: str | None = None, top: int = 5000) -> list[dict]:
    url = f"{BASE}/{entity}?$top={top}"
    if filter_:
        url += f"&$filter={filter_}"
    r = session.get(url, timeout=120)
    r.raise_for_status()
    return r.json().get("value", [])
```

(If building in TypeScript/Node, replicate exactly: Basic auth header, read `.value`, cast money strings to numbers.)

## 2. Critical context an LLM MUST internalize before building

1. **The spreadsheet year is 2026.** An earlier investigation wrongly assumed 2025 and concluded several lines were "not automatable". That was an artifact of querying the wrong year. With the correct year, the two hardest lines (Receita de honorários, Faturamento Realizado) are **exact matches**. Always query the target year (2026).
2. **This API only covers LEGAL-PRACTICE data** (invoices, receipts, cases, lawyers, fee splits). It does **NOT** contain institutional expenses (payroll, rent, taxes, suppliers). Those live in separate TOTVS Backoffice modules we have **no credentials for**. ~65 of the spreadsheet's manual lines are therefore **not automatable in v0** — render them as MANUAL. Do not waste time hunting for them; an exhaustive brute-force numeric search (1,700+ queries across 279 decimal fields) already confirmed they are absent.
3. **Two numbers, two regimes:**
   - **Recebimento (cash basis)** = money actually received. Endpoint: `PosicaoFinanceiraResultadoRecebimentoViews`.
   - **Faturamento (accrual basis)** = invoiced. Endpoint: `PosicaoFinanceiraResultadoFaturamentoViews`.
   - Both: the monthly total = **sum of `Valor1`** across all rows for that `AnoMes`.
4. **"Receita de honorários" (the spreadsheet's headline revenue line) == monthly Recebimento Bruto.** Verified exact for 2026-01 (279.821,07) and 2026-02 (319.233,58), delta 0.00.
5. **Row duplication in fee-split views:** `RateioFaturaProfissionalViews` returns each professional's line **twice** (one per timesheet entry). You MUST group/sum by `(FaturaNumero, ProfissionalSigla)` to match spreadsheet values.

## 3. The four automation primitives (verified endpoints)

These are the only API calls the v0 needs. Each is verified. For May 2026 (`'2026-05'`) the live totals are noted so the agent can sanity-check its implementation.

### 3.1. `recebimento_bruto(ano_mes)` → monthly cash received

- **Endpoint:** `PosicaoFinanceiraResultadoRecebimentoViews`
- **Filter:** `AnoMes eq '2026-05'`
- **Compute:** `sum(float(row["Valor1"]) for row in rows)`
- **May 2026 expected total:** `415927.84` (98 rows)
- **Feeds spreadsheet:** `Base_Resultado` line 4 "Receita de honorários"; `Meta__2` Recebimento column.
- **Row fields:** `AnoMes`, `Valor1` (gross), `Valor2/3/4` (deductions, negative), `CasoId`, `ProfissionalSigla`, `Tipo` (= "RR").

### 3.2. `faturamento_bruto(ano_mes)` → monthly invoiced (accrual)

- **Endpoint:** `PosicaoFinanceiraResultadoFaturamentoViews`
- **Filter:** `AnoMes eq '2026-05'`
- **Compute:** `sum(float(row["Valor1"]) for row in rows)`
- **May 2026 expected total:** `719988.05` (97 rows)
- **Feeds spreadsheet:** `Areas Sintetico atualizado` "Faturamento Realizado"; `Meta__2` Faturamento column.

### 3.3. `rateio_faturas(date_start, date_end)` → per-invoice, per-lawyer fee split

- **Endpoint:** `RateioFaturaProfissionalViews`
- **Filter (date range, end-exclusive):**
  `FaturaDataEmissao ge datetimeoffset'2026-05-01T00:00:00Z' and FaturaDataEmissao lt datetimeoffset'2026-06-01T00:00:00Z'`
- **May 2026:** 286 rows across 53 invoices (REMEMBER: rows are duplicated — group by `(FaturaNumero, ProfissionalSigla)` and the per-pair value is taken once, not summed twice).
- **Feeds spreadsheet:** entire `Resumo_Recebidas 2025_2026` tab.
- **Row fields:** `FaturaNumero`, `FaturaDataEmissao`, `ProfissionalSigla`, `ProfissionalPessoaNome`, `ValorTrabalhado`, `ValorFaturado`, `ClientePessoaNome`, `CasoAssunto`, `CasoCodigo`, `Porcentagem`.

### 3.4. `faturas_centro_custo(date_start, date_end)` → invoice headers + per-case breakdown

- **Endpoints:** `FaturaViews` (header) joined to `RateioFaturaCasoViews` (per-case) on `FaturaNumero`.
- **FaturaViews filter:** `DataEmissao ge datetimeoffset'2026-05-01T00:00:00Z' and DataEmissao lt datetimeoffset'2026-06-01T00:00:00Z'`
- **Feeds spreadsheet:** `FATURAS Analitico CENTRO CUSTO` tab.
- **FaturaViews fields:** `Numero`, `DataEmissao`, `DataVencimento`, `ValorHonorarios`, `ValorDespesas`, `ValorDesconto`, `Situacao` (R=regular, C=cancelled), `Tipo`, `ClientePessoaNome`, `RazaoSocial`, `ProfissionalResponsavelSigla`.
- **RateioFaturaCasoViews fields:** `FaturaNumero`, `FaturaValorHonorarios`, `FaturaDataEmissao`, `FaturaRazaoSocial`, `CasoCodigo`, `CasoAssunto`, `CasoClienteCodigo`, `CasoClientePessoaNome`, `TotalFaturado`, `TotalRateado`.

## 4. Spreadsheet structure (the 1:1 mapping target)

The workbook has 15 tabs. Column layout in the monthly tabs: **column A = label, column B = ANUAL, columns C..N = Jan..Dec.** So **May = column G** (C=Jan, D=Feb, E=Mar, F=Apr, **G=May**, H=Jun, ...). The v0 should render the "May 2026" column.

### 4.1. Tab-by-tab automation status

| Spreadsheet tab | v0 status | Source |
| --------------- | --------- | ------ |
| `Resumo_Recebidas 2025_2026` | ✅ AUTOMATED | `RateioFaturaProfissionalViews` (§3.3) |
| `FATURAS Analitico CENTRO CUSTO` | ✅ AUTOMATED | `FaturaViews` + `RateioFaturaCasoViews` (§3.4) |
| `Meta__2` (Recebimento + Faturamento rows) | ✅ AUTOMATED | §3.1 + §3.2 |
| `Areas Sintetico atualizado` → Receita & Faturamento Realizado | ✅ AUTOMATED | §3.1 + §3.2 |
| `Base_Resultado Mensal_V2` → line 4 "Receita de honorários" | ✅ AUTOMATED | §3.1 |
| `Base_Resultado Mensal_V2` → ~65 expense lines | ⛔ MANUAL | TOTVS Backoffice (no API) |
| `Orçamento 2026` | ⛔ MANUAL (API only has 2025 budget) | n/a |
| `DRE 2026` | ⚙️ FORMULA (depends on Orçamento → blocked) | n/a |
| `Institucional`, `Contencioso`, `Econômico`, `Arbitragem`, `Rateio Mensal`, `Amortização`, `Fluxo consolidado`, `Institucional ano` | ⚙️ FORMULA | recompute once sources are filled |

> **For v0:** render every tab, but only the ✅ rows carry live values. Mark ⛔ rows as MANUAL and ⚙️ formula rows as "derived (pending manual inputs)".

### 4.2. `Base_Resultado Mensal_V2` line-by-line map (the core 1:1 reference)

This is the heart of the workbook (295 rows). Below is the structural map. Only line 4 is API-automatable; the rest are manual (institutional) or formula totals. Render ALL rows for 1:1 fidelity; fill only what is marked API.

| Row(s) | Label | v0 status |
| ------ | ----- | --------- |
| 3 | Movimentação de Entradas (= line 4) | ⚙️ formula (mirrors line 4) |
| **4** | **Receita de honorários** | ✅ **API** = `recebimento_bruto('2026-05')` |
| 5 | Custo equipe - Contencioso (total) | ⚙️ formula `=SUM(rows 6..27)` |
| 6–27 | Per-lawyer Contencioso: Convênio Médico, Distribuição Mensal Fixa, Pró-labore, AASP, Bolsa auxílio, ISS Trimestral, Vale Refeição, Vale Transporte | ⛔ MANUAL (TOTVS RH/Folha) |
| 28–29 | Participação/Comissão, Repasse - Contencioso | ⛔ MANUAL |
| 30 | Custo equipe - Econômico (total) | ⚙️ formula `=SUM(rows 31..57)` |
| 31–57 | Per-lawyer Econômico (same benefit categories) | ⛔ MANUAL (TOTVS RH/Folha) |
| 58 | Custo equipe - Arbitragem e Compliance (total) | ⚙️ formula `=SUM(rows 59..76)` |
| 59–76 | Per-lawyer Arbitragem (same categories) | ⛔ MANUAL (TOTVS RH/Folha) |
| 77–79 | Despesas para Clientes / Não Reembolsáveis / Reembolsáveis | ⛔ MANUAL |
| 80 | Ocupação (total) | ⚙️ formula |
| 81–89 | Aluguel, Condomínio, Camera, Energia, IPTU, Seguro Locação, Telecomunicações, Internet, Telefonia Fixa | ⛔ MANUAL (TOTVS Contas a Pagar) |
| 90 | Despesas Gerais (total) | ⚙️ formula |
| 91–104 | Cartório, Cópias, Correio, Estacionamento, Limpeza, Manutenções, Material, Motoboy, OAB, Táxi | ⛔ MANUAL |
| 105 | Consultoria (total) | ⚙️ formula |
| 106–110 | Consultoria Adm/Fin, Marketing, Contabilidade, Taxas Fiscais, Escrituração | ⛔ MANUAL |
| 111 | Salários Administração (total) | ⚙️ formula |
| 112–118 | 13º, Convênio ADM, Exame, Férias, Salário ADM, VR ADM, VT | ⛔ MANUAL (TOTVS RH/Folha) |
| 119 | Administrativas (total) | ⚙️ formula |
| 120–~160 | Assinaturas, Associações, Seguros, Investimentos Prospecção, Refeições, Eventos, Material Gráfico, Gestão Conhecimento, Endomarketing (per area) | ⛔ MANUAL |
| ~164–177 | Impostos: COFINS, CSLL Trimestral, E-social, FGTS, Impostos 3ºs, INSS, IRRF Folha, IRRF Trimestral, ISS, PIS, Data Center | ⛔ MANUAL (TOTVS Tributário) |
| Remaining totals/margins | Resultado Bruto, Margem, etc. | ⚙️ formula |

> **Implementation note:** the agent does NOT need to reproduce the formula math for v0. For ⚙️ rows, either leave blank with a "derived" badge, or (nice-to-have) compute `=SUM(children)` over whatever children are filled. The point of v0 is to SHOW the 1:1 layout and which cells the API already fills.

### 4.3. Other tabs — column headers (for faithful rendering)

- **`Resumo_Recebidas 2025_2026`** header columns: `Fatura Nº | Cliente | Nº | Caso | Advogado | Valor | Area Originador | DT Receb | Valor a Creditar | Area Destino`. Build one block per invoice: a header row + one row per lawyer (from §3.3, grouped). `Valor` ← `ValorTrabalhado` (grouped), invoice total ← `ValorFaturado`.
- **`FATURAS Analitico CENTRO CUSTO`** header columns: `Núm. Fat. | Cód. Cliente | Razão Social Cliente | Caso | Nome do caso | Data Pagto/Canc. | Valor Original Hon. | Valor Líquido | Sócio Responsável`. Map from §3.4: `Núm. Fat.`←`Numero`/`FaturaNumero`, `Razão Social`←`RazaoSocial`, `Caso`/`Nome do caso`←`CasoCodigo`/`CasoAssunto`, `Valor Original Hon.`←`ValorHonorarios`, `Sócio Responsável`←`ProfissionalResponsavelSigla`/area.
- **`Meta__2`** has two stacked tables: top = 2026 (current year, what v0 fills), bottom = 2025 (prior year). For v0 fill the 2026 table's Recebimento (§3.1) and Faturamento (§3.2) for each closed month Jan–May.

## 5. v0 build specification

### 5.1. Recommended architecture

- A single static-ish web app (Next.js/React or plain Vite+React). A small backend (or build-time script) calls the API (Basic auth must stay server-side — do NOT ship the password to the browser).
- **Pattern:** build-time/server fetch → produce a `data.json` → frontend renders. This avoids CORS and credential exposure, and makes the v0 reproducible.

### 5.2. Layout (mirror the spreadsheet)

- **Left nav / tabs** = the 15 spreadsheet tabs (same names).
- Each tab renders a **table that matches the spreadsheet's columns/rows**.
- **Cell badges:**
  - `API` (green): value came live from the API. Show the number.
  - `MANUAL` (grey): not in this API. Show empty / "—" / input placeholder.
  - `FORMULA` (blue): derived/recomputes from other cells.
- **Header KPIs for May 2026:** Receita de honorários `415.927,84`, Faturamento Realizado `719.988,05` (these are the live May numbers — show them prominently as the proof the automation works).
- **Coverage meter:** e.g. "X of Y line items automated" so the boss sees scope at a glance.

### 5.3. Display formatting

- Brazilian currency: thousands `.`, decimals `,`, 2 decimal places. (e.g. `415927.84` → `415.927,84`).
- Always cast API money strings to number before formatting.

### 5.4. Sanity checks the agent should assert (fail loudly if mismatched)

- `recebimento_bruto('2026-05')` ≈ `415927.84`
- `faturamento_bruto('2026-05')` ≈ `719988.05`
- `rateio_faturas(May)` → 53 distinct `FaturaNumero`.
- Cross-check (historical, optional): `recebimento_bruto('2026-01')` == `279821.07`, `('2026-02')` == `319233.58`.

## 6. Hard "do NOT" list (saves the next agent hours)

1. Do **not** look for a separate `ODataFinanceiro` service — it doesn't exist; the 6 area aliases all return identical legal-module data.
2. Do **not** try to pull institutional expenses from this API — proven absent (2025 and 2026).
3. Do **not** use OData v4 syntax, `$expand`, or `$select=*` to find hidden columns — none exist.
4. Do **not** ship the API password to the browser — keep fetches server-side.
5. Do **not** forget to de-duplicate `RateioFaturaProfissionalViews` rows.
6. Do **not** assume the workbook is 2025 — it is **2026**.

## 7. Reference artifacts in this repo

- `docs/AUTOMATION_FINDINGS_PTBR.md` — full findings (PT-BR), validated mapping, what is/ isn't automatable and why.
- `docs/ORIGEM_DOS_DADOS_API.md` / `.pdf` — per-source "where the data comes from + sample shape" (built for the human who does the closing manually).
- `work/analysis/fechamento_values/*.tsv` — the actual spreadsheet values dumped per tab (ground truth to mirror layouts and validate against).
- `work/analysis/fechamento_formulas/*.tsv` — the spreadsheet formulas (use to understand ⚙️ derived cells).
- `work/analysis/fechamento_sheets.json` — tab names + dimensions.

---

*End of guide. Build the v0 against May 2026. Mark everything; fill what the API proves.*
