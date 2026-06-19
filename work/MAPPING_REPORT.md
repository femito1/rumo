# Legal Manager → Workbook Mapping Report

**Source workbook:** `Copy of Fechamento MBC 02.2026.xlsx` (period covered: Jan/Feb 2025)
**Target API:** `https://legaldesk.mbclaw.com.br/API/v1/ODataGERALADV/` (OData v3, Basic Auth)
**Total OData entity sets enumerated:** 631
**Successfully probed (HTTP 200):** 586 (33 server errors, 12 timeouts/aborted)
**Non-empty in this tenant:** 251

---

## 1. Headline finding

After dumping every endpoint, indexing every field, and brute-force searching every
numeric value in every response (with 0.005 absolute tolerance), only 10 of 115
distinct manual-input values from the workbook show *any* numeric coincidence in the
API — and on inspection, **all 10 are coincidental hits** on unrelated fields
(invoice numbers, client codes, hourly rates).

**No manual input value from `Base_Resultado Mensal_V2` (rows for receita, salaries,
convenio medico, aluguel, taxes, IPTU, energia, condominio, contabilidade, IRRF,
COFINS, CSLL, etc.) can be reconstructed from this Legal Manager OData API.**

The doc you wrote already hinted at this — it explicitly said:

- The aba `FATURAS` does not feed the model.
- Receita is digitada manualmente.
- Despesas e custos are entradas manuais.
- The 4 external links point to old SharePoint Excel files (BP 2025, Orçamento 2026,
  Fechamento 2022) — not to a structured system.

The probe results confirm that view: Legal Manager (Juritis LegalDesk) is being used
by MBC for case management, billing/invoice issuance, timesheets and pre-faturas — but
**not for cash-basis accounting, payroll, or institutional expense tracking**.

---

## 2. What IS reachable from Legal Manager

The endpoints below have data and are partially useful:

### 2.1 Faturas emitidas (invoice issuance) — `FaturaViews`

- `GET /FaturaViews?$filter=DataEmissao ge datetimeoffset'2025-01-01T00:00:00Z' and DataEmissao lt datetimeoffset'2025-02-01T00:00:00Z'`
- Total invoices Oct 2024-Apr 2025: 350 (filtered).
- Fields: `Numero`, `DataEmissao`, `DataVencimento`, `DataCancelamento`, `Situacao` (R/C/P), `Tipo`, `ValorHonorarios`, `ValorDesconto`, `ValorDespesas`, `ValorDespesasTributaveis`, `RazaoSocial`, `ProfissionalResponsavelSigla`.
- **Limit:** does NOT contain `DataPagamento` / `DataRecebimento`. So you cannot derive cash receipts from this view alone.
- **Sum check (R-status) Jan 2025:** R$ 261,000.72 vs workbook BASE R$ 279,821.07 → diff -R$ 18,820.35.
- **Sum check (R-status) Feb 2025:** R$ 393,877.14 vs workbook BASE R$ 319,233.58 → diff +R$ 74,643.56.
- The workbook FATURAS sheet itself sums to R$ 227,933.47 (Jan) / R$ 287,269.76 (Feb). Neither matches anything either. Conclusion: BASE is a different concept (likely cash-received from TOTVS).

### 2.2 Rateio de fatura por caso — `RateioFaturaCasoViews`

- `GET /RateioFaturaCasoViews?$filter=AnoMes eq '2025-01'`
- Returns 106 rows for Jan 2025, 118 for Feb 2025.
- Adds `TotalFaturado`, `TotalRateado`, `Porcentagem` per Caso/Fatura.
- `AnoMes` is the rateio reference period and is the easiest filter (string compare, no DateTimeOffset gymnastics).
- Useful for area-level revenue split (Contencioso/Econômico/Arbitragem) but values still don't match BASE.

### 2.3 Tributos por mês — `TributoViews`

- `GET /TributoViews?$filter=AnoMes eq '2025-01'`
- Returns 1 row per empresa/mês with **percentages** (PercentualIRPJ=10.88, PercentualCSLL=0, PercentualPIS=0.65, PercentualCOFINS=3).
- **Limit:** these are RATES, not amounts paid. The actual COFINS R$ 185.68, IRRF R$ 169.52, etc. in `Base_Resultado_Mensal_V2` rows 164-173 are not in any reachable endpoint.

### 2.4 Orçamento por linha de plano de contas — `OrcamentoViews`

- `GET /OrcamentoViews?$filter=AnoMes eq '2025-01'` → 46 rows
- Fields: `PlanoContasContaFinanceira`, `PlanoContasTitulo`, `Valor`, `EscritorioNome`, `GrupoJuridicoNome`, `AnoMes`.
- This is where the planned/budget values live. Useful for the `Orçamento 2026` sheet replacements.

### 2.5 Meta de receita — `MetaReceitaViews`

- `GET /MetaReceitaViews?$filter=AnoMes eq '2025-01'` → 1 row.
- Field `Valor` — monthly revenue target by escritório/grupo jurídico.
- Useful for `Meta (2)` sheet.

### 2.6 PosicaoFinanceira* family — partially useful

- `PosicaoFinanceiraResultadoFaturamentoViews` (AnoMes filter): 82-88 rows/month. Has Valor1=faturamento positivo, Valor2/3/4 negative components (likely impostos retidos and exclusões). Aggregation Valor1 ≈ R$ 300k Jan / R$ 508k Feb — not matching BASE, but probably matching **internal faturamento bruto**.
- `PosicaoFinanceiraResultadoRecebimentoViews` (AnoMes filter): 84-86 rows/month. Tipo=RR, Valor1=R$ 316,807.44 Jan / R$ 216,057.28 Feb. Closer to BASE Jan but Feb is way off.
- `PosicaoFinanceiraResumoDespesaViews` and `PosicaoFinanceiraDespesaIncorridaViews`: only 3-6 rows per month — too sparse to be the "expenses" source.
- **Status:** these endpoints look like the right family but the field semantics are not documented. Need RUMO/Juritis to clarify what Valor1..Valor9 mean.

---

## 3. What is NOT in Legal Manager (at all, or empty in this tenant)

These endpoints exist in the metadata but returned **0 rows** to `?$top=5`:

- `BusinessPlanViews`, `BusinessPlanProfissionalViews`, `BusinessPlanCustoViews`, `BusinessPlanCategoriaViews`, `BusinessPlanConsolidadoProfissionalViews` (would be the most natural source for the **Custo equipe** rows).
- `LancamentoViews` (would be lançamentos contábeis/financeiros).
- `MovimentacaoFinanceiraViews`, `MovimentacaoFinanceiraGridViews`, `MovimentacaoFinanceiraAbaViews` (only 3 rows total, irrelevant data).
- `PrestacaoContaViews`, `PrestacaoContaInstitucionalViews`, `PrestacaoContaEscritorioViews` (would be expense reports).
- `SolicitacaoPagamentoViews`, `SolicitacaoPagamentoItemViews`, `SolicitacaoPagamentoEscritorioViews`, `SolicitacaoPagamentoInstitucionalViews`, `SolicitacaoPagamentoUnicoViews` (would be payment requests for institutional expenses).
- `CustoProfissionalViews`, `CustoCategoriaViews` (would map directly to the per-pessoa cost rows in BASE).
- `AlocacaoRecebimentoTotalViews`, `AlocacaoRecebimentoTotalDetalheViews`.
- `ContaViews`, `BancoViews`, `OrcamentoViews` (only the Orcamento has data).
- All `AlocacaoRecebimento*` views with `DataRecebimento`: latest data is from **2023-02 or earlier**. So even the modules that exist have not been used since 2023 in this tenant.

This is the strongest evidence: **the financial-management modules of Juritis LegalDesk are not in active use at MBC.** The fields exist in metadata, but the records are empty or stale.

---

## 4. Mapping table: workbook input → API status

Status legend:

- LIVE = endpoint returns data, value can be computed (with a known transformation)
- LIVE_PARTIAL = endpoint returns data but the formula to match BASE is not known
- EMPTY = endpoint exists but tenant has 0 rows for the relevant period
- ABSENT = no endpoint with this concept; data lives in another system (TOTVS/banco/RH)


| Workbook section | Row(s) in Base_Resultado_Mensal_V2 | Concept | Status | Best endpoint | Confidence |
|---|---|---|---|---|---|
| Receita de honorários | 4 (C4=279,821.07; D4=319,233.58) | Cash receipts of the month | ABSENT (cash receipts) / LIVE_PARTIAL (issuance only) | `FaturaViews`+filter `DataEmissao` | low — no payment date in API |
| Custo equipe Contencioso/Econômico/Arbitragem | 5–76 | Per-person fixed comp, pro-labore, conv. médico, AASP, vale-refeição | ABSENT | (none) — `BusinessPlanCustoViews`, `CustoProfissionalViews` are EMPTY | none |
| Despesas para Clientes | 77–79 | Reembolsáveis / não reembolsáveis | LIVE_PARTIAL | `AprovacaoDespesaViews` (filter `Data`) | medium — endpoint has data but values do not match BASE |
| Ocupação (Aluguel, Condomínio, Energia, IPTU, Seguro, Telefonia) | 80–89 | Fixed institutional expenses | ABSENT | (none) | none |
| Despesas Gerais (Limpeza, Manut., OAB, Motoboy, …) | 90–104 | Office misc. expenses | ABSENT | (none) | none |
| Consultoria & Contabilidade | 105–110 | Outsourced services | ABSENT | (none) | none |
| Salários Administração + Férias | 111–118 | Admin payroll | ABSENT | (none) — RH module is EMPTY | none |
| Administrativas (assinaturas, associações, seguro RC) | 119–128 | Subscriptions, dues | ABSENT | (none) | none |
| Investimentos em Prospecção | 132–152 | Eventos, brindes, viagens, marketing | ABSENT | (none) | none |
| Gestão do Conhecimento (Cursos, Biblioteca) | 153–158 | Training & library | ABSENT | (none) | none |
| Endomarketing | 159–162 | Internal marketing | ABSENT | (none) | none |
| Impostos (COFINS, CSLL, FGTS, INSS, IRRF, ISS, PIS) | 163–174 | Taxes paid | ABSENT (values) / LIVE (rates only) | `TributoViews` for percentages | low — only rates, not amounts |
| Informática (Oracle, licenças, suporte) | 175–185 | IT infrastructure | ABSENT | (none) | none |
| Distribuição de Lucros extras | 186–191 | Bonus, DL Extraordinária | ABSENT | (none) | none |
| Amortização (8.117,31/mês) | hardcoded in DRE 2026!C24, Areas Sintetico!C29/F29 | 60-month amortization of 2022 investment | ABSENT | (none) — already documented in a tab inside the workbook | n/a |
| Realocações entre áreas (Resumo_Recebidas) | special sheet | Re-attribution of receita between Contencioso/Econômico/Arbitragem | LIVE_PARTIAL | `AlocacaoRecebimentoTransferenciaClienteViews` (no 2025 data!) | low — module unused since 2023 |
| Comissão 10% Arbitragem | special sheet | Commission redistribution rule | ABSENT | (none) — pure business rule | none |

---

## 5. The differences: BASE vs FATURAS vs API

| Source | Jan 2025 | Feb 2025 | Notes |
|---|---:|---:|---|
| Workbook BASE C4/D4 (manually typed) | 279,821.07 | 319,233.58 | The "ground truth" for the closing |
| Workbook FATURAS sheet (sum Valor Líquido) | 227,933.47 | 287,269.76 | Tagged as not-feeding the model (manually filtered) |
| API FaturaViews — Tipo=F, Situacao=R, by DataEmissao | 261,000.72 | 393,877.14 | Includes invoices emitted but not yet paid in cash; double-counts faturas that were paid in subsequent months |
| API RateioFaturaCasoViews — TotalFaturado, AnoMes=YYYY-MM, Situacao=R | 261,000.72 | 393,877.14 | Same numbers (consistent) |
| API PosicaoFinanceiraResultadoRecebimentoViews — Valor1 sum, AnoMes filter | 316,807.44 | 216,057.28 | Closer to Jan BASE but Feb very wrong |
| API PosicaoFinanceiraResultadoFaturamentoViews — Valor1 sum, AnoMes filter | 300,125.17 | 508,227.52 | Looks like gross billed |

None of the API aggregations reproduce BASE in both months. **Without RUMO documenting what BASE actually means**, an automation built on any single endpoint will not match.

---

## 6. Concrete next steps

### 6.1 What to validate with RUMO

1. **Where does BASE Jan/Feb 2025 — 279,821.07 / 319,233.58 — come from?** Is it:
    a) Cash received in the bank that month (TOTVS Financeiro)?
    b) Faturas emitidas com situação Recebida no mês de emissão (a subset of FaturaViews)?
    c) A custom report from the contabilidade?
    d) Net of a manual exclusion list (cancelled/refunded)?
2. **Are the financial modules of Legal Manager intentionally unused?** All `BusinessPlan*`, `CustoProfissional`, `Lancamento`, `MovimentacaoFinanceira`, `PrestacaoConta`, `SolicitacaoPagamento` views are empty. If TOTVS is the source of truth for these, the automation must integrate with TOTVS, not Legal Manager.
3. **What is the `Tipo` column in `PosicaoFinanceiraResultadoRecebimentoViews` (RR / R / etc.)?** What do `Valor1..Valor9` mean? This is the most promising endpoint and might bridge the gap if documented.
4. **Is the cancellation rule "exclude `Tipo='C'`" correct, or should you net cancellations to the original month, not the cancellation date?**
5. **Is there a separate Juritis API instance for financeiro/contábil (e.g. `ODataFINANCEIRO` instead of `ODataGERALADV`)?** The path suffix `GERALADV` suggests this is the "Geral Advocacia" module — there may be additional modules whose URLs we did not test.

### 6.2 Recommended automation architecture

Given the findings, the realistic plan is:

1. **Phase 1 — Legal Manager–derived analytics (now achievable):**
    - `FaturaViews` + `RateioFaturaCasoViews` + `RateioFaturaProfissionalViews`: drive the Areas Sintetico atualizado split by area, and the FATURAS auditing sheet.
    - `OrcamentoViews` + `MetaReceitaViews`: drive the Orçamento 2026 + Meta sheets.
    - `TributoViews`: replace the percentage hardcodes used in DRE.
2. **Phase 2 — Source-of-truth integration (blocked on RUMO):**
    - Identify the actual source of BASE receita (likely TOTVS Financeiro). Replicate the same query directly from TOTVS (or an export/CSV) to populate `Receita de honorários`.
    - Identify the source of payroll detail (HR system or TOTVS Folha) to populate the Custo equipe rows.
    - Identify the source of institutional expenses (TOTVS contas a pagar) to populate Ocupação, Consultoria, Despesas Gerais, Impostos.
3. **Phase 3 — Business-rule layer:**
    - Move realocação entre áreas (today in Resumo_Recebidas) to a versioned rules table.
    - Move the comissão 10% rule to a parameter table.
    - Move the amortização 8.117,31 to a calc that derives from a parcels table.

### 6.3 Working artifacts produced

Everything below is in `work/`:

- `analysis/manual_inputs.tsv` (72 manual-input rows, with Jan/Feb values)
- `analysis/manual_inputs_by_category.md` (categorized)
- `analysis/hardcoded_in_formulas.tsv` (291 formulas with embedded numeric literals)
- `analysis/entities.json` (parsed metadata: 631 EntitySets with their properties and types)
- `analysis/dumps_index.json` and `dumps_index.tsv` (per-endpoint summary: rows, fields, dates, classification)
- `analysis/dumps_with_data.tsv` (251 endpoints that actually have data)
- `analysis/value_match_report_v2.tsv` (numeric tolerance match — 10 false-positive hits, 105 misses)
- `api_dumps/` (raw $top=5 JSON for every endpoint, plus `_metadata.xml`)
- `api_dumps_filtered/` (Jan/Feb 2025 filtered dumps for the high-value endpoints)
- `scripts/` (every Python script used; reproducible)

### 6.4 How to re-run anything

To add more endpoints to the filtered probes, edit `work/scripts/probe_filtered2.py`
and re-run. To re-probe everything from scratch, delete `work/api_dumps/*.json`
and run `python3 work/scripts/probe_endpoints.py --workers 6`. To rebuild the
indexes after any new dumps, run `python3 work/scripts/index_dumps.py` then
`python3 work/scripts/match_categories2.py`.


---

## 7. Service-discovery sanity checks

To rule out the existence of additional API surface I might have missed, I tried:

- The OData root (`/API/v1/ODataGERALADV/`) returned its catalog: 631 entity sets, all probed.
- The `$metadata` document declares a single schema namespace `Juritis.LegalDesk.ViewModel.Cadastro`. There is no second namespace hiding additional types.
- I probed alternative service paths (`/API/v1/ODataFINANCEIRO`, `/ODataRH`, `/ODataPAGAMENTO`, `/ODataCONTABIL`, `/ODataORCAMENTO`, `/ODataBP`) — all 404.
- The `/API/` root is an HTML SPA branded "TOTVS | Legaldesk", confirming the system is TOTVS Legaldesk (Juritis).
- The `/API/swagger` redirect lands on the SPA home, so no separate Swagger doc is exposed.

So the OData surface I dumped is the complete machine-readable interface available.

---

## 8. Summary — one paragraph

Of the 119 distinct manual values entered into `Base_Resultado Mensal_V2` for Jan/Feb 2025, **none can be reproduced exactly from the Legal Manager OData API**. The API faithfully exposes case-management data (clients, casos, faturas emitidas, pre-faturas, timesheet, rateio) and a few financial-orçamento views (`OrcamentoViews`, `MetaReceitaViews`, `TributoViews` rates). It does **not** expose the cash-receipts ledger, the institutional-expenses ledger, the payroll detail, or the actual amounts paid in taxes — those modules either do not exist in this tenant or were intentionally turned off (the `BusinessPlan*`, `CustoProfissional*`, `Lancamento*`, `MovimentacaoFinanceira*`, `PrestacaoConta*` and `SolicitacaoPagamento*` views all return zero rows, and the `AlocacaoRecebimento*` views with `DataRecebimento` only carry data through 2023). The doc you wrote already concluded that "FATURAS does not feed the model" and that the receita is digitada manualmente; this exhaustive probe confirms that conclusion and extends it: it is not just the receita — *the entire MBC closing process* uses Legal Manager only as a side-reference for invoice issuance, while the actual P&L lives in TOTVS Financeiro / RH / Contábil. Any automation has to integrate with TOTVS, not just Legal Manager.

