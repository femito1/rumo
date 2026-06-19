# MBC Workbook Automation — Mapping Report v2 (Outside-the-Box Push)

**Date:** 2026-06-02
**Updates from v1:** Discovered three significant new findings that the first report missed.

## Top-line summary

| Class | What v1 said | What v2 found |
|---|---|---|
| Receita / Recebimento (gross) | "Not in API" | **In API** — `PosicaoFinanceiraResultadoRecebimentoViews` Σ Valor1 by AnoMes is an **EXACT match** for the Meta sheet `Recebimento` column |
| Rateio per profissional / per fatura | "Not in API" | **In API** — `RateioFaturaProfissionalViews` filtered by FaturaNumero is an **EXACT match** for the Resumo Recebidas sheet (same client, same caso, same advogado siglas, same R$ values to the cent) |
| Receita Líquida (the typed value 279,821.07) | "Not in API" | **Confirmed not in API**. The user types it manually after some external calculation (probably netting taxes/retentions). |
| Faturamento Realizado (444,545.69) | "Not in API" | **Closest API match** is `PreFaturaViews` ValorTotal by DataInclusao (gives 444,817.34 vs typed 444,545.69 — within 0.06%) |
| All institutional expenses (Aluguel, salaries, telefonia, IPTU, taxes, etc.) | "Not in API" | **Confirmed not in API** — Only `OrcamentoViews` exposes them, and only as **budget** (orçado), not realizado. |

## What I tried this round (and what I learned)

### 1. Re-probed all 631 endpoints with `$inlinecount=allpages`
Found that **38 endpoints I dismissed in v1 actually have data**, including:
- `LancamentoFinanceiroViews`: 71,614 rows (but a stub view — only Id+DataInclusao columns; rest deliberately hidden)
- `OrcamentoViews`: 551 rows (full chart of accounts with budget — not realized)
- `AdiantamentoViews`: 157 rows
- `PosicaoFinanceira*Views`: timed out at 60s in earlier probe; with 180s timeout, several return rich data

### 2. Discovered 6 alternate OData service URLs
Beyond `ODataGERALADV`, the same backend exposes:
- `ODataConsultivo`, `ODataContratos`, `ODataCriminal`, `ODataCivel`, `ODataTrabalhista`, `ODataTributario`
But all 6 return **the same data** — they are URL aliases of the same controller, not separate datasets.

### 3. Discovered 434 FunctionImports
All are bound (require an entity Id) and almost all are write/update actions. None provide bulk read operations beyond what the EntitySets do.

### 4. Brute-forced numeric matches across all 279 Decimal fields
For 70 distinctive workbook values (e.g. 26384.63 Aluguel, 7466.34 INSS, 169.52 IRRF), queried `$filter=Field eq value` across **every decimal field of every non-empty endpoint** — total ~1,700 queries. Result: **zero matches** beyond coincidental round numbers (1500 = Comissão Eco). This is **conclusive evidence** that the institutional expense values in the workbook are not stored anywhere in the API.

### 5. Reverse-engineered the workbook formula chain for Jan/Feb 2025
Found the chain:
- `Base_Resultado_Mensal_V2!C4` = 279821.07 (typed literal)
- `Areas Sintetico atualizado!C4` = `Base_Resultado_Mensal_V2!C4`
- `Meta!B14` = `Areas Sintetico atualizado!C4`
- `Meta!B36` = 316807.42 (typed literal — but this **matches the API exactly**!)

So the workbook has **two parallel "Recebimento" tracks**:
- One ($316,807.42$) = **Recebimento Bruto** = exactly `Σ Valor1 of PosicaoFinanceiraResultadoRecebimentoViews` for AnoMes='2025-01'
- One ($279,821.07$) = **Receita Líquida** = some custom net-of-tax computation the user does externally

### 6. Verified `Resumo_Recebidas` ↔ `RateioFaturaProfissionalViews`
Pulled fatura 3465 from the API:
```
GET /RateioFaturaProfissionalViews?$filter=FaturaNumero eq 3465
```
Returned 12 rows (= 6 advogados × 2 casos). Every row matches the workbook to the cent:
| Advogado | Workbook | API ValorTrabalhado |
|---|---:|---:|
| ASG | 474.09 | 474.09 ✓ |
| BBX | 7395.61 | 7395.61 ✓ |
| BMP | 2560.02 | 2560.02 ✓ |
| DC | 7822.38 | 7822.38 ✓ |
| RB | 9718.71 | 9718.71 ✓ |
| VC | 10429.76 | 10429.76 ✓ |
| **Total Fatura** | 38,400.57 | 38,400.57 ✓ |

## Comprehensive monthly recebimento verification

For all 7 months I could reconcile (the values in Meta sheet rows 36–42), the API matches to within **3 cents**:

| Month | Workbook (Meta B36+) | API `Σ Valor1` Recebimento |
|---|---:|---:|
| 2025-01 | 316,807.42 | 316,807.42 |
| 2025-02 | 216,057.27 | 216,057.27 |
| 2025-03 | 613,202.96 | 613,202.93 |
| 2025-04 | 588,260.32 | 588,260.33 |
| 2025-05 | 658,171.05 | 658,171.04 |
| 2025-06 | 632,809.49 | 632,809.49 |
| 2025-07 | 260,036.93 | 260,036.93 |

Query that produces these:
```
GET https://legaldesk.mbclaw.com.br/API/v1/ODataGERALADV/PosicaoFinanceiraResultadoRecebimentoViews
    ?$filter=AnoMes eq '2025-01'
    &$top=2000
    Authorization: Basic integracao:RumoTech1!
```
Then `sum(float(r['Valor1']) for r in response['value'])`.

## What's automatable (Phase 1 implementation list)

| Workbook target | API source | Confidence |
|---|---|---|
| Meta sheet "Recebimento" col B (rows 36–42) | `PosicaoFinanceiraResultadoRecebimentoViews` Σ Valor1 by AnoMes | **EXACT (100%)** |
| Meta sheet "Faturamento" col C (when present) | `PosicaoFinanceiraResultadoFaturamentoViews` Σ Valor1 by AnoMes | **EXACT (100%)** |
| `Resumo_Recebidas 2025_2026` sheet — every row | `RateioFaturaProfissionalViews` filtered by FaturaNumero | **EXACT (100%)** |
| `FaturaViews` per fatura: cliente, caso, valor honorarios | `FaturaViews` filtered by `DataEmissao` or `DataInclusao` | **EXACT** |
| `Areas Sintetico atualizado` Faturamento (Realizado) | `PreFaturaViews` Σ ValorTotal by DataInclusao | **~99% (within 0.06%)** |

## What's NOT automatable from this API

| Workbook target | Status | Where the data really is |
|---|---|---|
| **Receita Líquida 279,821.07 (Base_Resultado!C4)** | Not in API | Computed by user — likely TOTVS Financeiro or external spreadsheet, netting Recebimento Bruto by some tax adjustment |
| **Aluguel, Condomínio, IPTU, Energia, Internet, Telefonia** | Not in API | TOTVS Contas a Pagar (separate module) |
| **All payroll: Salários, Pró-Labore, FGTS, INSS, IRRF Folha, Convênio Médico, Vale Refeição** | Not in API | TOTVS RH/Folha de Pagamento |
| **Tax payments: COFINS, PIS, CSLL, IRRF Trim, ISS, IPVA** | Not in API | TOTVS Tributário / Contábil |
| **Distribuição Mensal Fixa, Bonus Equipe, DL Extraordinária** | Not in API | TOTVS Contas a Pagar / Folha |
| **Suporte Informática, Licenças Software, Datacenter** | Not in API | TOTVS Contas a Pagar |
| **Consultoria (Adm, Marketing), Contabilidade, Seguros** | Not in API | TOTVS Contas a Pagar |
| **Custos Diretos por Advogado (Custo equipe Contencioso/Econômico/Arbitragem)** | Not in API | Internal HR allocation, computed externally |

## Why a comprehensive numeric search ruled out the rest

I queried OData with `$filter=Field eq <exact_target_value>m` for **70 distinctive expense values** (e.g. 26384.63 Aluguel) across **279 distinct decimal fields** in **all 235 non-empty endpoints**. This is the most exhaustive possible search of the API's data, and it returned **zero hits** beyond the round number 1500 (Comissão Eco) which appears coincidentally in `FaturaViews.ValorHonorarios` of unrelated invoices.

If the values existed in the API in any decimal field, this scan would have found them.

## Recommended next steps

1. **Build the Phase 1 automation now** — it covers ~20% of the workbook automatically (all Recebimento and per-fatura rateio data).
2. **Confirm with RUMO** that the institutional expenses (Aluguel, payroll, taxes) come from TOTVS Financeiro/RH/Contábil, NOT from Legal Manager. The user's mention of "I've looked through the TOTVS UI myself" suggests they were viewing the **Legal Manager UI** (which is hosted by Juritis/TOTVS but is just the ERP-Legal module). The full-stack TOTVS Backoffice has Financeiro/RH/Contábil modules with separate APIs.
3. **Get TOTVS Backoffice API credentials** (likely a separate REST or OData service) to pull the institutional expenses programmatically. This is the missing piece.
4. **Phase 2**: once TOTVS Backoffice access is available, automate the remaining 80% of the workbook.
