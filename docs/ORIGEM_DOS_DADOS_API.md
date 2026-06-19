# De onde vêm os dados 

**API:** Juritis LegalDesk OData v3 — base: `https://legaldesk.mbclaw.com.br/API/v1/ODataGERALADV/`
**Autenticação:** Basic Auth (usuário `integracao`)
**Formato:** todas as respostas vêm em JSON, dentro de uma lista `"value": [ ... ]`. Cada item da lista é uma linha.

> Observação rápida sobre os filtros das URLs: `$filter` filtra as linhas (ex.: por mês ou por número de fatura), `$top` limita a quantidade. `AnoMes` é o mês de competência no formato `'AAAA-MM'`. Datas usam o formato `datetimeoffset'AAAA-MM-DDT00:00:00Z'`.

---

## 1. ORÇAMENTO — view `OrcamentoViews`

**O que é:** o orçado por plano de contas, mês a mês.

**Caminho (endpoint):**

```
GET /API/v1/ODataGERALADV/OrcamentoViews?$filter=AnoMes eq '2025-01'&$top=2000
```

**Campos que vêm em cada linha:**
`AnoMes`, `PlanoContasContaFinanceira` (o código contábil), `PlanoContasTitulo` (o nome da conta), `Valor`, `GrupoJuridicoNome`, `EscritorioNome`, `MoedaSigla`, além de Id/datas de inclusão.

**Como o dado chega (amostra real, Jan/2025):**


| AnoMes  | Conta Financeira | Título                      | Valor      |
| ------- | ---------------- | --------------------------- | ---------- |
| 2025-01 | 010.010.0010     | Recebimento de Honorários   | 700.000,00 |
| 2025-01 | 020.090.0010     | Viagens para Prospecção     | 10.774,45  |
| 2025-01 | 040.040.0030     | Licenças de Uso de Software | 15.116,53  |
| 2025-01 | 020.060.0020     | Associações                 | 3.737,98   |
| 2025-01 | 020.060.0040     | Seguros                     | 2.885,95   |
| 2025-01 | 020.030.0090     | Motoboy                     | 71,03      |


São 46 itens por mês. **Importante:** hoje a API só devolve o orçado de **2025** (12 meses). Não há dados de 2026 nessa view.

---

## 2. FATURAS ANALÍTICO CENTRO DE CUSTO — `FaturaViews` + `RateioFaturaCasoViews`

São duas views combinadas: uma traz o **cabeçalho da fatura**, a outra traz a **quebra por caso/cliente**.

### 2a) Cabeçalho da fatura — `FaturaViews`

**Caminho:**

```
GET /API/v1/ODataGERALADV/FaturaViews?$filter=DataEmissao ge datetimeoffset'2026-01-01T00:00:00Z' and DataEmissao lt datetimeoffset'2026-02-01T00:00:00Z'&$top=1000
```

**Campos principais:**
`Numero`, `DataEmissao`, `DataVencimento`, `ValorHonorarios`, `ValorDespesas`, `ValorDesconto`, `Situacao` (R = regular, C = cancelada), `Tipo`, `ClientePessoaNome`, `RazaoSocial`, `ProfissionalResponsavelSigla`.

**Amostra real (faturas emitidas em Jan/2026):**


| Fatura | Emissão    | Valor Honorários | Situação |
| ------ | ---------- | ---------------- | -------- |
| 3964   | 2026-01-05 | 1.368,51         | R        |
| 3965   | 2026-01-05 | 1.000,00         | R        |
| 3968   | 2026-01-05 | 466,66           | R        |
| 3966   | 2026-01-05 | 466,66           | R        |


### 2b) Quebra por caso — `RateioFaturaCasoViews`

**Caminho:**

```
GET /API/v1/ODataGERALADV/RateioFaturaCasoViews?$filter=FaturaNumero eq 3964&$top=50
```

**Campos principais:**
`FaturaNumero`, `FaturaValorHonorarios`, `FaturaDataEmissao`, `FaturaRazaoSocial`, `CasoCodigo`, `CasoAssunto`, `CasoClienteCodigo`, `CasoClientePessoaNome`, `TotalFaturado`, `TotalRateado`, `TotalPorcentagem`.

**Amostra real (fatura 3964):** cliente **VLI Multimodal S.A**, honorários 1.368,51, com a quebra por caso/centro de custo dentro da fatura.

---

## 3. RESUMO RECEBIDAS — view `RateioFaturaProfissionalViews`

**O que é:** cada fatura quebrada por advogado (quem trabalhou e quanto).

**Caminho (uma fatura específica):**

```
GET /API/v1/ODataGERALADV/RateioFaturaProfissionalViews?$filter=FaturaNumero eq 3964&$top=50
```

**Caminho (todas as faturas de um período):**

```
GET /API/v1/ODataGERALADV/RateioFaturaProfissionalViews?$filter=FaturaDataEmissao ge datetimeoffset'2026-01-01T00:00:00Z' and FaturaDataEmissao lt datetimeoffset'2026-03-01T00:00:00Z'&$top=5000
```

**Campos principais:**
`FaturaNumero`, `FaturaDataEmissao`, `ProfissionalSigla`, `ProfissionalPessoaNome`, `ValorTrabalhado`, `ValorFaturado`, `ClientePessoaNome`, `CasoAssunto`, `CasoCodigo`, `Porcentagem`.

**Amostra real (fatura 3964 — VLI Multimodal S.A):**


| Fatura | Advogado | Valor Trabalhado | Valor Faturado |
| ------ | -------- | ---------------- | -------------- |
| 3964   | BBX      | 2.886,54         | 299,65         |
| 3964   | DC       | 2.718,41         | 282,20         |
| 3964   | JVO      | 877,60           | 91,10          |
| 3964   | IAC      | 438,80           | 45,55          |
| 3964   | ESC      | 0,00             | 650,00         |


> Atenção ao conferir: a API devolve **as linhas em duplicidade** (um lançamento por entrada de timesheet). Para chegar ao valor por advogado da planilha, é preciso **agrupar/somar por advogado**. No exemplo acima, cada advogado aparece duas vezes.

---

## 4. BASE RESULTADO MENSAL (Receita / Recebimento) — view `PosicaoFinanceiraResultadoRecebimentoViews`

**O que é:** o recebimento (dinheiro que entrou) do mês. A soma do campo `Valor1` de todas as linhas do mês = a **"Receita de honorários"** da Base_Resultado (e a linha "Recebimento" do Meta).

**Caminho:**

```
GET /API/v1/ODataGERALADV/PosicaoFinanceiraResultadoRecebimentoViews?$filter=AnoMes eq '2026-01'&$top=3000
```

**Campos principais:**
`AnoMes`, `Valor1` (recebimento bruto), `Valor2`/`Valor3`/`Valor4` (deduções/retenções, vêm negativos), `CasoId`, `ProfissionalSigla`, `Tipo`.

**Como o dado chega (amostra real, 2026-01):** cada linha é um recebimento, com o bruto em `Valor1` e as deduções nos demais campos:


| AnoMes  | Valor1 (bruto) | Valor2  | Valor3    | Valor4    |
| ------- | -------------- | ------- | --------- | --------- |
| 2026-01 | 682,56         | -106,62 | -326,97   | -51,80    |
| 2026-01 | 0,00           | 0       | -820,62   | -136,31   |
| 2026-01 | 0,00           | 0       | -8.685,26 | -1.322,37 |


**Validação que eu já fiz (bate exatamente):**


| Mês     | Σ Valor1 da API | Valor na planilha |
| ------- | --------------- | ----------------- |
| 2026-01 | **279.821,07**  | 279.821,07 ✓      |
| 2026-02 | **319.233,58**  | 319.233,58 ✓      |


> A mesma view, trocando o `AnoMes`, dá a linha "Recebimento" do Meta para qualquer mês (validamos os 7 meses de 2025 — todos batem).
>
> Para o **Faturamento Realizado** é a view irmã `PosicaoFinanceiraResultadoFaturamentoViews` (mesma lógica, soma de `Valor1`): 2026-01 = 444.545,69 e 2026-02 = 534.752,84 — também batem exatamente.

---

## Resumo


| Bloco da planilha                    | View / endpoint da API                       | O dado                                         |
| ------------------------------------ | -------------------------------------------- | ---------------------------------------------- |
| Orçamento                            | `OrcamentoViews`                             | orçado por conta contábil (só 2025 disponível) |
| Faturas Analítico Centro de Custo    | `FaturaViews` + `RateioFaturaCasoViews`      | cabeçalho da fatura + quebra por caso          |
| Resumo Recebidas                     | `RateioFaturaProfissionalViews`              | fatura quebrada por advogado                   |
| Base Resultado (Receita/Recebimento) | `PosicaoFinanceiraResultadoRecebimentoViews` | recebimento do mês (Σ Valor1)                  |


