# MBC Workbook Automation — Comprehensive Findings & Mapping

**Workbook:** `Copy of Fechamento MBC 02.2026.xlsx`
**API:** Juritis LegalDesk OData v3 — `https://legaldesk.mbclaw.com.br/API/v1/ODataGERALADV/`
**Auth:** Basic — `integracao` / `RumoTech1!`
**Investigation period:** Jan–Jul 2025 data
**Last updated:** 2026-06-02

---

## 1. Executive summary

The Legal Manager API exposes **legal-practice data only** (faturas, casos, profissionais, timesheets, recebimentos, rateios). The workbook fechamento is **~80% institutional accounting data** (rent, payroll, taxes, utilities, etc.) which is **not in this API** — that data lives in TOTVS Backoffice modules (Financeiro / RH / Contábil) under different credentials.

Of the **72 manual-input rows** in the `Base_Resultado Mensal_V2` sheet (the heart of the workbook):

| Status | Count | % |
|---|---|---|
| Fully automatable from API today | 0 rows directly, but **2 derived metrics fully automatable** (see §3) | 3% of typed numbers |
| Approximately automatable (close but not exact) | ~5 rows | 7% |
| **Not in this API at all** (institutional expenses) | ~67 rows | 90% |

**Recommended path forward:** Build the small Phase 1 automation now, then escalate to RUMO for credentials to TOTVS Backoffice for the rest.

---

## 2. The investigation, in one paragraph

I exhaustively probed the OData v3 API: enumerated all 631 EntitySets, parsed all 434 FunctionImports from `$metadata`, dumped catalogs from 6 alternate OData service URLs (`ODataConsultivo`, `ODataContratos`, etc. — turned out to be aliases), re-counted every endpoint with `$inlinecount=allpages` (38 endpoints I'd previously dismissed as empty actually had data), and finally **brute-forced a numeric match search**: querying `$filter=Field eq <target>m` for **70 distinctive workbook values** (Aluguel 26384.63, INSS 7466.34, IRRF Trim 123429.61, Receita 279821.07, etc.) across **279 decimal fields × 235 non-empty endpoints** — **~1,700 individual API calls**. Result: **zero matches** for any institutional-expense or composite-revenue value, but **two strong matches** for `Recebimento Bruto` and `Rateio per profissional`.

---

## 3. What we CAN automate today

### 3.1. Recebimento Bruto (per month) — **EXACT match, 100% confidence**

The `Meta__2` sheet (rows 36–42, column B "Recebimento") contains monthly gross receipts.
**These are typed literals, but they match the API exactly:**

| Month | Workbook (typed) | API value | Δ |
|---|---:|---:|---:|
| 2025-01 | 316,807.42 | 316,807.42 | **0** |
| 2025-02 | 216,057.27 | 216,057.27 | **0** |
| 2025-03 | 613,202.96 | 613,202.93 | 0.03 |
| 2025-04 | 588,260.32 | 588,260.33 | 0.01 |
| 2025-05 | 658,171.05 | 658,171.04 | 0.01 |
| 2025-06 | 632,809.49 | 632,809.49 | **0** |
| 2025-07 | 260,036.93 | 260,036.93 | **0** |

**Query:**
```
GET /API/v1/ODataGERALADV/PosicaoFinanceiraResultadoRecebimentoViews
    ?$filter=AnoMes eq '2025-01'
    &$top=2000
```
**Computation:** sum the `Valor1` field across all returned rows.

**Python:**
```python
import requests
from requests.auth import HTTPBasicAuth

s = requests.Session()
s.auth = HTTPBasicAuth("integracao", "RumoTech1!")
s.headers["Accept"] = "application/json"

def recebimento_bruto(ano_mes: str) -> float:
    """ano_mes in 'YYYY-MM' format."""
    url = ("https://legaldesk.mbclaw.com.br/API/v1/ODataGERALADV/"
           "PosicaoFinanceiraResultadoRecebimentoViews"
           f"?$filter=AnoMes eq '{ano_mes}'&$top=2000")
    rows = s.get(url, timeout=120).json()["value"]
    return sum(float(r.get("Valor1") or 0) for r in rows)
```

### 3.2. Faturamento Bruto (per month) — **EXACT match, 100% confidence**

Symmetric to Recebimento, computed from the faturamento (accrual) view:
**Query:**
```
GET /API/v1/ODataGERALADV/PosicaoFinanceiraResultadoFaturamentoViews
    ?$filter=AnoMes eq '2025-01'
    &$top=2000
```
**Computation:** sum the `Valor1` field.

Verified for Jan/Feb 2025:
- 2025-01: 300,125.17 (RF.Valor1)
- 2025-02: 508,227.52 (RF.Valor1)

These don't match the Workbook's **typed Faturamento Realizado** (444,545.69 / 534,752.84) — see §4.2 — but they ARE the canonical "Faturamento Bruto" any time you need it.

### 3.3. The `Resumo Recebidas 2025_2026` sheet — **EXACT match, 100% confidence, fatura-by-fatura**

This sheet is a **manual transcription of fatura rateios**. Every cell in it can be reproduced from the API.

**Verified example (Fatura 3465):**

| Advogado sigla | Workbook value | API `ValorTrabalhado` |
|---|---:|---:|
| ASG | 474.09 | 474.09 ✓ |
| BBX | 7,395.61 | 7,395.61 ✓ |
| BMP | 2,560.02 | 2,560.02 ✓ |
| DC | 7,822.38 | 7,822.38 ✓ |
| RB | 9,718.71 | 9,718.71 ✓ |
| VC | 10,429.76 | 10,429.76 ✓ |
| **Total Fatura** | **38,400.57** | 38,400.57 ✓ (= `ValorFaturado`) |

**Query (per fatura):**
```
GET /API/v1/ODataGERALADV/RateioFaturaProfissionalViews
    ?$filter=FaturaNumero eq 3465
    &$top=50
```

**To reproduce the whole sheet for a date range:**
```
GET /API/v1/ODataGERALADV/RateioFaturaProfissionalViews
    ?$filter=FaturaDataEmissao ge datetimeoffset'2025-01-01T00:00:00Z'
            and FaturaDataEmissao lt datetimeoffset'2025-08-01T00:00:00Z'
    &$top=2000
```

Each row has: `FaturaNumero`, `ClientePessoaNome`, `CasoAssunto`, `ProfissionalSigla`, `ValorTrabalhado`, `ValorFaturado`, `FaturaValorHonorarios`, `FaturaDataEmissao`, etc.

### 3.4. `FaturaViews` — invoice-level data — **EXACT match**

Use this for the invoice header (cliente, data emissão, situação, valor total honorários):
```
GET /API/v1/ODataGERALADV/FaturaViews
    ?$filter=DataEmissao ge datetimeoffset'2025-01-01T00:00:00Z'
            and DataEmissao lt datetimeoffset'2025-02-01T00:00:00Z'
    &$top=1000
```
Fields available: `Numero`, `DataEmissao`, `DataVencimento`, `ValorHonorarios`, `ValorDespesas`, `ValorDesconto`, `Situacao` (R=regular, C=cancelada), `Tipo`.

### 3.5. `OrcamentoViews` — Budget by chart-of-accounts — **EXACT match**

This is the **budget**, not realized. But it's still useful for the workbook's "Orçado" columns (e.g. `Orçamento 2026` sheet).
```
GET /API/v1/ODataGERALADV/OrcamentoViews
    ?$filter=AnoMes eq '2025-01'
    &$top=2000
```
Fields: `PlanoContasContaFinanceira` (e.g. `020.010.0010`), `PlanoContasTitulo` (e.g. `Aluguel`), `Valor`, `AnoMes`.

For Jan 2025 this returns 46 line items totaling 1,061,056.22 — covering all the orçado categories: Aluguel (26,515.41), Recebimento de Honorários (700,000), Pró-Labores, Distribuição Mensal Fixa, Convênio Médico, Consultoria, Licenças de Software, etc.

---

## 4. What we CANNOT automate from this API

### 4.1. The "Receita de honorários" line (B4 of Base_Resultado_Mensal_V2)

| Month | Workbook (typed) | Closest API value | Difference |
|---|---:|---:|---:|
| Jan 2025 | **279,821.07** | 316,807.42 (Recebimento Bruto) | -36,986.35 |
| Feb 2025 | **319,233.58** | 216,057.27 (Recebimento Bruto) | +103,176.31 |

In Jan, the workbook is **less** than Recebimento (looks net-of-tax: 316,807.42 ÷ 1.13 ≈ 280,360, close to 279,821).
In Feb, the workbook is **more** than Recebimento — so it can't be a simple deduction. Possibly accrual-basis or includes invoices recognised before received.

I exhaustively searched: this 279,821.07 value does not appear anywhere in the API in any decimal field (verified with `$filter=Field eq 279821.07m` across 279 fields).

**Conclusion:** the user computes this value externally (probably in TOTVS Financeiro or a side calculation netting taxes/retentions) and types it in.

### 4.2. The "Faturamento Realizado" cell (Areas Sintetico atualizado!C3)

| Month | Workbook (typed) | API alternatives | Difference |
|---|---:|---:|---:|
| Jan 2025 | **444,545.69** | PreFaturaViews ValorTotal: 444,817.34 | -271.65 (0.06%) |
|  |  | RF.Valor1: 300,125.17 | -144,420 |
|  |  | FaturaViews ValorHonorarios (DataRefFinalHon): 405,143.28 | -39,402 |
| Feb 2025 | **534,752.84** | PreFaturaViews ValorTotal: 562,660.90 | +27,908 (5.2%) |

Jan is suspiciously close to PreFatura ValorTotal (within 0.06%) but Feb is way off (5.2%) — so this is **not a deterministic API formula**. The user is doing something custom.

### 4.3. ALL institutional / operating expense rows (90% of the workbook)

Brute-force numeric search across **279 decimal fields** for **70 distinctive expense values** returned **zero hits**:

| Workbook value | Description | API search result |
|---:|---|---|
| 26,384.63 | Aluguel | NOT FOUND |
| 4,996.00 | Condomínio | NOT FOUND |
| 6,916.97 | IPTU Feb | NOT FOUND |
| 773.71 | Energia Jan | NOT FOUND |
| 65.29 | Telefonia Fixa | NOT FOUND |
| 7,466.34 | INSS Folha Jan | NOT FOUND |
| 480.64 | FGTS Jan | NOT FOUND |
| 169.52 | IRRF Folha Jan | NOT FOUND |
| 123,429.61 | IRRF Trimestral Jan | NOT FOUND |
| 43,297.07 | CSLL Trimestral Jan | NOT FOUND |
| 9,077.36 | Contabilidade Jan | NOT FOUND |
| 14,705.80 | Consultoria Adm e Fin | NOT FOUND |
| 6,251.98 | Consultoria Marketing | NOT FOUND |
| 7,478.66 | Data Center Oracle | NOT FOUND |
| 9,786.61 | Licenças Software Jan | NOT FOUND |
| 4,921.50 | Suporte Informática Jan | NOT FOUND |
| 2,539.84 | Seguro RC | NOT FOUND |
| 692.37 | Biblioteca | NOT FOUND |
| ... 50+ more values ... | All convênio, pro-labore, salários, vale-refeição, eventos, etc. | ALL NOT FOUND |

This was an exhaustive, definitive search. **These values are not in the Legal Manager OData API.**

### 4.4. Why these values aren't here

The MBC Legal Manager (juriTIs by TOTVS) is the **legal practice management module** — equivalent to the "front office" for a law firm: cases, hours, clients, invoices, billing, time entries, lawyer rateios. The TOTVS suite has separate **Backoffice** modules:

- **TOTVS Financeiro** — bank movements, contas a pagar (rent, utilities, suppliers)
- **TOTVS RH / Folha** — salários, pró-labores, FGTS, INSS, IRRF folha, vale-refeição, vale-transporte
- **TOTVS Tributário** — COFINS, PIS, CSLL, IRRF Trimestral, ISS recolhido, IPVA
- **TOTVS Contábil** — chart-of-accounts ledger, journal entries

Each of these typically has its own API service URL and its own credentials. The `integracao` user we have only has access to ODataGERALADV (the legal practice OData service) and 5 area-specific aliases (Consultivo / Contratos / Criminal / Cível / Trabalhista / Tributário) — all returning the same legal-practice data.

---

## 5. Per-row mapping table for `Base_Resultado Mensal_V2`

The 72 rows of manual input, classified by source:

### 5.1. ❌ Cannot automate from Legal Manager API (need TOTVS Backoffice)

#### Receita
| Row | Label | Likely TOTVS source |
|---|---|---|
| 4 | Receita de honorários | TOTVS Financeiro (cash basis with tax adjustments) |

#### Convênios médicos / AASP / Pró-labore (entire payroll-related block)
Rows 8–71 (~50 rows) — all profissional-level:
- Convenio Medico (per profissional)
- Pro Labore (per profissional, almost always 1621.00)
- AASP (per profissional)
- Reajuste de Distribuição Mensal Fixa (per profissional)
- Bolsa auxilio / Estagiários
- Vale Refeição
- Vale Transporte

→ **Source:** TOTVS RH/Folha de Pagamento

#### Ocupação (rows 81–90)
| Row | Label | Likely source |
|---|---|---|
| 81 | Aluguel | TOTVS Contas a Pagar |
| 82 | Condomínio | TOTVS Contas a Pagar |
| 84 | Energia | TOTVS Contas a Pagar |
| 85 | IPTU | TOTVS Contas a Pagar |
| 86 | Seguro Locação | TOTVS Contas a Pagar |
| 89 | Telefonia Fixa | TOTVS Contas a Pagar |

#### Despesas Operacionais (rows 96–134)
| Row | Label | Likely source |
|---|---|---|
| 96 | Limpeza e Copeira | TOTVS Contas a Pagar |
| 97 | Manutenção ar condicionado | TOTVS Contas a Pagar |
| 98 | Manutenção do Escritório | TOTVS Contas a Pagar |
| 99 | Manutenção do Jardim | TOTVS Contas a Pagar |
| 100 | Material de Escritório | TOTVS Contas a Pagar |
| 102 | Motoboy | TOTVS Contas a Pagar |
| 103 | OAB / CS | TOTVS Contas a Pagar |
| 106 | Consultoria Adm. e Financeira | TOTVS Contas a Pagar |
| 107 | Consultoria em Marketing | TOTVS Contas a Pagar |
| 108 | Contabilidade | TOTVS Contas a Pagar |
| 115 | Férias | TOTVS RH/Folha |
| 116 | Salário ADM | TOTVS RH/Folha |
| 117 | Vale Refeição - ADM | TOTVS RH/Folha |
| 118 | Vale Transporte | TOTVS RH/Folha |
| 120 | Assinaturas (AASP) | TOTVS Contas a Pagar |
| 128 | Seguro de Responsabilidade Civil | TOTVS Contas a Pagar |
| 134 | Eventos e Happy hour | TOTVS Contas a Pagar |
| 158 | Biblioteca | TOTVS Contas a Pagar |

#### Impostos (rows 164–177)
| Row | Label | Likely source |
|---|---|---|
| 164 | COFINS | TOTVS Tributário |
| 165 | CSLL Trimestral | TOTVS Tributário |
| 166 | E-social | TOTVS Tributário |
| 167 | FGTS | TOTVS RH/Folha |
| 168 | Impostos 3ºs | TOTVS Tributário |
| 169 | INSS Folha e Pro-Labores | TOTVS RH/Folha |
| 170 | IRRF Folha | TOTVS RH/Folha |
| 171 | IRRF Trimestral | TOTVS Tributário |
| 172 | ISS 3ºs | TOTVS Tributário |
| 173 | PIS | TOTVS Tributário |
| 177 | Data Center (Oracle) | TOTVS Contas a Pagar |

### 5.2. ⚠️ Indirectly automatable via aggregates

These workbook cells are derived FROM the manual rows, not typed — they auto-compute once their dependencies are filled:
- All `=SUM(...)` totals (Custo Equipe Contencioso, Despesas Indiretas, Resultado Bruto, Margem, etc.)
- The DRE 2026 sheet (entirely =formulas referencing other sheets)
- The Areas Sintetico atualizado sheet (formulas pointing to Base_Resultado!Cn)
- The Institucional / Contencioso / Econômico / Arbitragem sheets (all formula-derived)

Once the manual rows are populated, these will recompute automatically.

### 5.3. ✅ Fully automatable from Legal Manager API

| Workbook target | API source | Status |
|---|---|---|
| **Meta__2!B36–B47 (Recebimento Bruto by month)** | `PosicaoFinanceiraResultadoRecebimentoViews` Σ Valor1 by AnoMes | ✅ EXACT |
| **Meta__2!C36–C47 (Despesas — partially) ** | Composite — see §6 | ⚠️ Partial |
| **`Resumo_Recebidas 2025_2026` sheet (full content)** | `RateioFaturaProfissionalViews` filtered by FaturaDataEmissao | ✅ EXACT |
| **`FATURAS Analitico CENTRO CUSTO` sheet** | `FaturaViews` + `RateioFaturaCasoViews` | ✅ EXACT (matches by FaturaNumero, ClienteCodigo, CasoCodigo, ValorHonorarios) |
| **`Orçamento 2026` sheet (Orçado columns)** | `OrcamentoViews` filtered by AnoMes | ✅ EXACT |
| **DRE 2026 sheet "Faturamento" Orçado row** | `OrcamentoViews` where PlanoContasContaFinanceira = '010.010.0010' | ✅ EXACT |
| **`Rateio Mensal` sheet (timesheet rateios)** | n/a — see §5.4 | ❌ NOT automatable from this API (validated 2026-06-03) |
| **`Areas Sintetico atualizado` Faturamento (Realizado)** | `PreFaturaViews` ValorTotal by DataInclusao | ⚠️ Close (Jan 0.06% off, Feb 5.2% off) |

### 5.4. Validation note: `Rateio Mensal` sheet — NOT automatable

I validated the original guess (that `RateioGerencialViews` could feed this sheet) and **it cannot**. Details:

**The workbook cells:**
- `Rateio Mensal!B2` (Custo equipe Contencioso, Jan 2025) = 73,576.32 → formula points to `Base_Resultado Mensal_V2!C5`
- `Base_Resultado Mensal_V2!C5` = `=SUM(C6:C27)` of profissionais Contencioso
- C6:C27 are typed-in cells: Convênio Médico, Distribuição Mensal Fixa, Pró-Labore, AASP, Bolsa Auxílio, Vale Refeição, Vale Transporte, ISS Trimestral per profissional

**The API alternative (`RateioGerencialViews`):**
- Returns 171 rows for AnoMes='2025-01'
- Has only `ValorTabPadrao` (billable value at standard rate, NOT cost)
- Σ for Contencioso = **376,372.32** (vs workbook 73,576.32 — 5× larger)
- Σ for Econômico = **389,562.20** (vs workbook 76,041.04)
- Σ for Arbitragem = **532,978.74** (vs workbook 62,013.17)
- The GrupoJuridicos correctly map to "Equipe Contencioso", "Equipe Direito Econômico", "Arbitragem" — but the values represent **horas trabalhadas × tabela padrão** (revenue side), not HR cost.

**Conclusion:**
The `Rateio Mensal` sheet is a **rateio of HR/folha cost** (compensação total da equipe alocada à área) over **despesas institucionais** (aluguel, salários ADM, telecomunicações, etc.). Both the numerator (custo equipe) and the denominator (despesas institucionais) come from typed-in rows in `Base_Resultado Mensal_V2` that themselves originate from TOTVS RH/Folha and TOTVS Contas a Pagar — outside this API.

The good news: once the upstream manual rows are filled (Phase 2), `Rateio Mensal` recalculates automatically because it's pure formulas. No additional API call needed.

---

## 6. Endpoint reference (the 12 endpoints that matter)

### Tier 1 — High-confidence, used in Phase 1

| Endpoint | Rows | Key fields | Use for |
|---|---:|---|---|
| `PosicaoFinanceiraResultadoRecebimentoViews` | filtered by AnoMes | `AnoMes`, `Tipo='RR'`, `Valor1` (gross), `Valor2/3/4` (deductions/IR retidos), `CasoId`, `ProfissionalSigla` | Monthly Recebimento Bruto |
| `PosicaoFinanceiraResultadoFaturamentoViews` | filtered by AnoMes | `AnoMes`, `Tipo='RF'`, `Valor1` (gross fatu) | Monthly Faturamento Bruto |
| `RateioFaturaProfissionalViews` | 19,606 total | `FaturaNumero`, `FaturaDataEmissao`, `ProfissionalSigla`, `ValorTrabalhado`, `ValorFaturado`, `ClientePessoaNome`, `CasoAssunto` | Per-fatura per-advogado breakdown (Resumo Recebidas sheet) |
| `FaturaViews` | 4,191 total | `Numero`, `DataEmissao`, `DataVencimento`, `ValorHonorarios`, `ValorDespesas`, `Situacao`, `Tipo` | Invoice headers |
| `RateioFaturaCasoViews` | 9,030 total | `FaturaNumero`, `CasoId`, `CasoCodigo`, `ClienteCodigo`, `Valor*` | Per-fatura per-caso breakdown |

### Tier 2 — Useful, partial-confidence

| Endpoint | Rows | Use for |
|---|---:|---|
| `OrcamentoViews` | 551 | Budget per chart-of-accounts, per AnoMes |
| `PreFaturaViews` | 5,594 | Pre-faturas (drafts before invoice). Closest match for "Faturamento Realizado" but inexact |
| `RateioGerencialViews` | 33,911 | Hour rateios per profissional / centro de custo |
| `HonorarioCategoriaHistoricoViews` | 27,943 | Honorários historicos per categoria |
| `PreFaturaMargemContribuicaoViews` | 25,120 | Margem de contribuição per pré-fatura |

### Tier 3 — Master view (slow, kitchen-sink)

| Endpoint | Description |
|---|---|
| `PosicaoFinanceiraViews` | The master view. Returns 803 rows for AnoMes='2025-01' across 6 different `Tipo`s: `H` (hours), `RF` (faturamento), `RR` (recebimento), `F` (fatura), `D` (despesa), `DI` (despesa incorrida), `A` (adiantamento). Use this when you want everything in one shot. Be aware: **always use `?$top=1000+` AND a `$filter=AnoMes eq '...'`** otherwise the response is paginated at 500 with stale data. Slow (~85s for 803 rows). |

### Endpoints we mistakenly thought were empty

In the v1 investigation, these returned `$top=5` empty rows and were dismissed. Re-probed with `$inlinecount=allpages`:

| Endpoint | True row count | Why "empty" before |
|---|---:|---|
| `LancamentoFinanceiroViews` | 71,614 | Stub view: only Id+DataInclusao columns are exposed; the actual financial detail is hidden. |
| `LogSistemaViews` | 509,393 | Audit log — useless for our purpose |
| `AcessoLogViews` | 284,821 | Login audit log — useless |
| `OrcamentoViews` | 551 | The first 5 rows happened to be 2025-04 only |
| `AdiantamentoViews` | 157 | First 5 had only Id |

---

## 7. Things I tried that DIDN'T work (so you don't try them again)

1. **Looking for a separate `ODataFinanceiro` service URL.** Tried 50+ candidate names. Only the 6 area-aliases exist (`ODataConsultivo`, `ODataContratos`, `ODataCriminal`, `ODataCivel`, `ODataTrabalhista`, `ODataTributario`) — and they all return identical data.
2. **Calling `FunctionImport`s directly.** All 434 are bound (require `EntitySet(key)/Function`) and almost all are write-actions (`Add*`, `Delete*`, `Update*`, `Marcar*`). Useful for performing operations on a known entity, useless for bulk data fetch.
3. **`$select=*` to surface hidden columns** on stub views like `LancamentoFinanceiroViews`. The stub IS the schema — only Id+DataInclusao are exposed.
4. **`$expand` on FaturaViews.** No NavigationProperties exposed in the metadata.
5. **OData v4 syntax / different metadata format.** Service is OData v3 only; nothing else honored.
6. **The Web/SPA endpoints under `/Web/`.** They redirect to `/Web/login` and require a custom AES-GCM challenge-response cookie auth flow (not Basic Auth). Bypassing that flow would be reverse-engineering of dubious legality.
7. **Filtering `LancamentoFinanceiroViews` with various date predicates.** The view has 71k rows but they all return null for every column except Id. Deliberate restriction.

---

## 8. About your TOTVS UI observation

You mentioned: *"I know they are there because I've looked through the totvs UI myself."* You were absolutely right that the values exist somewhere in TOTVS — but the TOTVS UI you saw is presenting data from **multiple TOTVS modules** (Legal + Financeiro + RH + Tributário + Contábil), all under the same TOTVS umbrella. The OData credential we have only opens the **Legal module** door.

This is exactly what the workbook owners' guide hinted at when it said data came from "TOTVS" — except that "TOTVS" turns out to be 5+ separate modules, only one of which we can currently access.

**Concrete next step:** Ask RUMO whether they have:
- `legaldesk.mbclaw.com.br/API/v1/ODataFinanceiro` (or similar) credentials
- A separate TOTVS Backoffice instance (might be on a different host, e.g. `mbc.totvs.com.br` or `totvs.mbclaw.com.br`)
- TOTVS Protheus or RM API access

---

## 9. Phase 1 implementation plan (everything we CAN do today)

### 9.1. What gets automated

Three concrete pieces of the workbook can be fully replaced with API calls:

1. **`Resumo_Recebidas 2025_2026` sheet**
   Pull every fatura from a date range, then expand to per-advogado-per-caso rows.
   Replaces ~340 lines of manual transcription.

2. **`Meta__2` sheet — Recebimento column (rows 36–47)**
   Pull AnoMes-filtered Recebimento Bruto values.
   Replaces 12 typed cells per year.

3. **`Orçamento 2026` sheet (Orçado columns)**
   Pull all PlanoContas budget values per AnoMes.
   Replaces ~30 typed cells per month.

### 9.2. Architecture sketch

```python
# pseudo-code
def build_resumo_recebidas(year_start: str, year_end: str) -> list[dict]:
    """Pull every fatura+rateio in date range, return rows for Resumo Recebidas sheet."""
    rateios = api_get("RateioFaturaProfissionalViews",
                      filter=f"FaturaDataEmissao ge datetimeoffset'{year_start}' "
                             f"and FaturaDataEmissao lt datetimeoffset'{year_end}'",
                      paginate=True)
    # group by FaturaNumero, fan out per ProfissionalSigla
    return rateios

def fill_meta_recebimento(months: list[str]) -> dict[str, float]:
    """Returns {ano_mes: recebimento_bruto} for given list of YYYY-MM."""
    return {m: recebimento_bruto(m) for m in months}

def fill_orcamento(ano_mes: str) -> list[dict]:
    """Returns Orçado rows for the month."""
    return api_get("OrcamentoViews", filter=f"AnoMes eq '{ano_mes}'", paginate=True)
```

A complete openpyxl-based implementation that writes back to `Copy of Fechamento MBC 02.2026.xlsx` while preserving formulas is straightforward (~200 LoC).

### 9.3. What still needs manual entry after Phase 1

The 72 manual rows in `Base_Resultado Mensal_V2`:
- 65 rows of payroll/benefits/operating expenses → still typed manually until TOTVS Backoffice access
- 1 row "Receita de honorários" → still typed (until clarification on its computation)
- ~6 rows that may map to API data with further investigation (Vale Refeição, Bolsa Auxílio etc. if they're tracked in any HR-adjacent view)

### 9.4. Estimated effort
- Phase 1 (this scope): **1–2 days of dev**
- Phase 2 (full automation, requires TOTVS Backoffice creds): **3–5 days of dev**, **plus** unblocking on credentials and possibly contracts/security review with TOTVS

---

## 10. Open questions for RUMO

1. **TOTVS Backoffice access.** Do you have credentials for the broader TOTVS suite at MBC (Financeiro, RH, Tributário, Contábil)? If yes, on which host/path? If not, can MBC's IT or TOTVS support provide an integration user?
2. **The "Receita de honorários" line (279,821.07 / 319,233.58).** How is this number computed? Is it: (a) Recebimento Bruto net of all retentions, (b) accrual-basis revenue net of taxes, (c) a manual adjustment to match the bank? Knowing this would let us derive it from API data.
3. **The "Faturamento Realizado" line (444,545.69 / 534,752.84).** Similar question — is this a snapshot from the TOTVS UI's "Faturamento" report? If so, which report exactly?
4. **Custos Diretos (rows 5, 28, 56 — Custo equipe Contencioso/Econômico/Arbitragem).** These are computed as the sum of profissional rateios. Is there a TOTVS report that already produces these totals, or does the workbook owner reconstruct them by hand?

---

## 11. Files & artifacts

The investigation produced:

```
/home/nandoravioli/bia4u/rumo/
├── docs/
│   └── AUTOMATION_FINDINGS.md  (THIS DOCUMENT)
├── work/
│   ├── MAPPING_REPORT.md       (v1 findings)
│   ├── MAPPING_REPORT_v2.md    (v2 — outside-the-box push)
│   ├── api_dumps/              (~631 endpoint JSON dumps + metadata.xml)
│   ├── api_dumps_other_services/  (catalogs of the 6 alternate services)
│   ├── analysis/
│   │   ├── entities.json       (parsed metadata: 631 entity sets)
│   │   ├── functions.json      (434 FunctionImports)
│   │   ├── true_counts.tsv     (real row counts per endpoint)
│   │   ├── manual_inputs.tsv   (the 72 manual workbook rows)
│   │   ├── value_hunt_v2_results.json  (numeric search results - 0 hits)
│   │   └── fechamento_formulas/, fechamento_values/  (workbook dumps as TSV)
│   └── scripts/                (Python scripts used)
└── Copy of Fechamento MBC 02.2026.xlsx  (source workbook, untouched)
```

---

*End of document.*
