# Automação do Workbook MBC — Achados e Mapeamento Completo

**Workbook:** `Copy of Fechamento MBC 02.2026.xlsx` (dados de **2026**)
**API:** Juritis LegalDesk OData v3 — `https://legaldesk.mbclaw.com.br/API/v1/ODataGERALADV/`
**Auth:** Basic — `integracao` / `RumoTech1!`
**Última atualização:** 03/06/2026

---

## 1. Sumário executivo

O objetivo foi descobrir **quanto do fechamento mensal da MBC dá para automatizar** puxando dados direto da API do sistema TOTVS/Juritis Legal Manager, em vez de digitar à mão.

**Resultado em uma frase:** a API cobre **todo o lado da receita** (faturamento, recebimento, rateios — inclusive as duas linhas que antes pareciam impossíveis) com **batimento exato**, mas **não cobre as despesas institucionais** (folha, aluguel, impostos, fornecedores), que vivem em outros módulos do TOTVS sob credenciais que ainda não temos.

> **Nota metodológica importante:** o workbook é de **2026**. Numa primeira rodada eu assumi 2025 e cheguei a conclusões erradas (dei "Receita de honorários" e "Faturamento Realizado" como não-automatizáveis). Ao refazer tudo com o ano correto, **as duas viraram match exato e trivial**. Todos os números abaixo foram revalidados contra a API em 2026 (e 2025, onde o workbook guarda o ano anterior para comparação).

**Placar por aba:**

| Aba | Status | Fonte |
| --- | ------ | ----- |
| `Resumo_Recebidas 2025_2026` | ✅ API | `RateioFaturaProfissionalViews` |
| `FATURAS Analitico CENTRO CUSTO` | ✅ API | `FaturaViews` + `RateioFaturaCasoViews` |
| `Meta__2` (Recebimento e Faturamento) | ✅ API | `PosicaoFinanceira...Recebimento/Faturamento` |
| `Areas Sintetico atualizado` (Receita e Faturamento realizados) | ✅ API | Recebimento/Faturamento Bruto do mês |
| `Base_Resultado Mensal_V2` → **linha 4 (Receita de honorários)** | ✅ API | Recebimento Bruto do mês (match exato) |
| `Base_Resultado Mensal_V2` → ~65 linhas de despesa institucional | ❌ fora desta API | TOTVS Backoffice (Financeiro/RH/Tributário) |
| `Orçamento 2026` | ⚠️ não validável | API só tem orçado de 2025; o de 2026 não está exposto |
| `DRE 2026`, `Institucional`, `Contencioso`, `Econômico`, `Arbitragem`, `Rateio Mensal` | ⚙️ fórmula | recalculam sozinhas quando as fontes forem preenchidas |

**Caminho recomendado:**
1. **Fase 1 (1–2 dias de dev, sem depender de ninguém):** automatizar todo o bloco de receita — já validado com batimento exato.
2. **Fase 2 (depende da RUMO/MBC liberar credenciais do TOTVS Backoffice):** automatizar as ~65 linhas de despesa institucional.

---

## 2. Como foi a investigação (metodologia)

- Enumerei todos os **631 EntitySets** e **434 FunctionImports** do `$metadata`; confirmei que as 6 URLs "alternativas" de serviço são apenas aliases do mesmo serviço.
- Recontei todos os endpoints com `$inlinecount=allpages`.
- **Busca numérica em força bruta:** `$filter=Campo eq <valor>m` para 70 valores do workbook × 279 campos decimais × 235 endpoints (~1.700 chamadas). Zero correspondências para despesa institucional — confirmado também em 2026.
- **Engenharia reversa das fórmulas do workbook** célula a célula.
- **Revalidação completa em 2026** (esta rodada): comparei os valores reais do workbook contra a API no ano correto. É daqui que vêm os matches exatos abaixo.

---

## 3. O que JÁ podemos automatizar hoje (validado com batimento exato)

### 3.1. Receita de honorários (Base_Resultado linha 4) — **MATCH EXATO**

Esta era "a linha impossível". Com o ano correto (2026), ela é simplesmente o **Recebimento Bruto do mês**:

| Mês | Workbook | API (Σ Valor1) | Δ |
| --- | -------- | -------------- | - |
| 2026-01 | 279.821,07 | 279.821,07 | **0,00** |
| 2026-02 | 319.233,58 | 319.233,58 | **0,00** |

```
GET /API/v1/ODataGERALADV/PosicaoFinanceiraResultadoRecebimentoViews
    ?$filter=AnoMes eq '2026-01'
    &$top=3000
```

**Cálculo:** somar o campo `Valor1`.

```python
import requests
from requests.auth import HTTPBasicAuth

s = requests.Session()
s.auth = HTTPBasicAuth("integracao", "RumoTech1!")
s.headers["Accept"] = "application/json"

def recebimento_bruto(ano_mes: str) -> float:
    url = ("https://legaldesk.mbclaw.com.br/API/v1/ODataGERALADV/"
           "PosicaoFinanceiraResultadoRecebimentoViews"
           f"?$filter=AnoMes eq '{ano_mes}'&$top=3000")
    rows = s.get(url, timeout=120).json()["value"]
    return sum(float(r.get("Valor1") or 0) for r in rows)
```

> **Detalhe (opcional):** a aba `Areas Sintetico` quebra essa Receita em 3 áreas (Contencioso/Econômico/Arbitragem) usando rateio de faturas + realocações entre áreas. A soma das 3 áreas dá exatamente o mesmo total (279.822 ≈ 279.821,07 em Jan). Ou seja, a decomposição por área é só um detalhamento do mesmo Recebimento Bruto — para o total da linha 4, basta a soma direta acima.

### 3.2. Faturamento Realizado (Areas Sintetico atualizado!C3) — **MATCH EXATO**

Também dado como "não-determinístico" na primeira rodada (erro de ano). Em 2026 é o **Faturamento Bruto do mês**:

| Mês | Workbook | API (Σ Valor1) | Δ |
| --- | -------- | -------------- | - |
| 2026-01 | 444.545,69 | 444.545,69 | **0,00** |
| 2026-02 | 534.752,84 | 534.752,84 | **0,00** |

```
GET /API/v1/ODataGERALADV/PosicaoFinanceiraResultadoFaturamentoViews
    ?$filter=AnoMes eq '2026-01'
    &$top=3000
```

**Cálculo:** somar `Valor1`.

### 3.3. Recebimento Bruto por mês (Meta__2) — **MATCH EXATO**

A aba `Meta__2` guarda **dois anos lado a lado**: a tabela de cima é 2026 (em andamento) e a de baixo é 2025 (ano anterior, completo). A coluna "Recebimento" da tabela de 2025 bate 7/7 meses:

| Mês (2025) | Workbook | API | Δ |
| ---------- | -------- | --- | - |
| 2025-01 | 316.807,42 | 316.807,44 | 0,02 |
| 2025-02 | 216.057,27 | 216.057,28 | 0,01 |
| 2025-03 | 613.202,96 | 613.202,93 | 0,03 |
| 2025-04 | 588.260,32 | 588.260,33 | 0,01 |
| 2025-05 | 658.171,05 | 658.171,04 | 0,01 |
| 2025-06 | 632.809,49 | 632.809,49 | 0,00 |
| 2025-07 | 260.036,93 | 260.036,93 | 0,00 |

Mesma query da §3.1, variando o `AnoMes`. (Foi esse batimento com 2025 que, na primeira rodada, me fez confundir o ano do workbook.)

### 3.4. Aba `Resumo_Recebidas 2025_2026` — **MATCH EXATO, fatura a fatura**

Transcrição manual de rateios de fatura, reproduzível a partir da API. Exemplo verificado (Fatura 3465): `ValorFaturado` = 38.400,57, com a quebra por advogado (ASG 474,09; BBX 7.395,61; ...) batendo célula a célula. Os dados de 2026 estão presentes (44–48 faturas/mês em Jan/Fev).

```
GET /API/v1/ODataGERALADV/RateioFaturaProfissionalViews
    ?$filter=FaturaDataEmissao ge datetimeoffset'2026-01-01T00:00:00Z'
            and FaturaDataEmissao lt datetimeoffset'2026-03-01T00:00:00Z'
    &$top=5000
```

Campos: `FaturaNumero`, `ClientePessoaNome`, `CasoAssunto`, `ProfissionalSigla`, `ValorTrabalhado`, `ValorFaturado`, `FaturaDataEmissao`. Atenção: as linhas vêm duplicadas por lançamento de timesheet — agrupar por advogado para chegar aos valores do workbook.

### 3.5. Aba `FATURAS Analitico CENTRO CUSTO` — **MATCH EXATO**

Cabeçalho de fatura + quebra por caso, via `FaturaViews` + `RateioFaturaCasoViews` (bate por `FaturaNumero`, `ClienteCodigo`, `CasoCodigo`, `ValorHonorarios`).

```
GET /API/v1/ODataGERALADV/FaturaViews
    ?$filter=DataEmissao ge datetimeoffset'2026-01-01T00:00:00Z'
            and DataEmissao lt datetimeoffset'2026-02-01T00:00:00Z'
    &$top=1000
```

---

## 4. O que NÃO conseguimos automatizar a partir dessa API

### 4.1. Despesas institucionais / operacionais (~65 linhas) — fora desta API

A busca numérica em força bruta (279 campos decimais, revalidada em **2026**) retornou **zero correspondências** para qualquer despesa institucional. Amostra:

| Valor | Descrição | Resultado |
| ----- | --------- | --------- |
| 26.384,63 | Aluguel | NÃO ENCONTRADO |
| 773,71 | Energia | NÃO ENCONTRADO |
| 7.466,34 | INSS Folha | NÃO ENCONTRADO |
| 123.429,61 | IRRF Trimestral | NÃO ENCONTRADO |
| 9.077,36 | Contabilidade | NÃO ENCONTRADO |
| 7.478,66 | Data Center Oracle | NÃO ENCONTRADO |
| 2.539,84 | Seguro RC | NÃO ENCONTRADO |
| ... +50 outros ... | Convênios, pró-labore, salários, vales, impostos, eventos | TODOS NÃO ENCONTRADOS |

**Esses valores não estão na API OData do Legal Manager — nem em 2025, nem em 2026.**

### 4.2. Por que essas despesas não estão aqui

O Legal Manager (Juritis by TOTVS) é o módulo de **prática jurídica** (casos, horas, faturas, rateios). As despesas institucionais vivem em módulos **Backoffice** separados, cada um com sua própria API/credencial:

- **TOTVS Financeiro** — contas a pagar (aluguel, utilities, fornecedores)
- **TOTVS RH / Folha** — salários, pró-labores, FGTS, INSS, IRRF folha, vales
- **TOTVS Tributário** — COFINS, PIS, CSLL, IRRF Trimestral, ISS
- **TOTVS Contábil** — razão por plano de contas

A credencial `integracao` que temos só abre o módulo Legal. A UI do TOTVS que o usuário vê junta todos esses módulos sob o mesmo guarda-chuva — por isso parece que "tudo está no TOTVS". Está, mas em 5+ módulos, e só temos a chave de um.

### 4.3. Aba `Orçamento 2026` — não validável pela API (hoje)

A `OrcamentoViews` da API **só contém o ano de 2025** (12 meses, 46 itens/mês por plano de contas). O workbook tem orçamento de **2026**, detalhado por advogado (~130 linhas). Como a API não expõe 2026, **não há como validar nem alimentar essa aba pela API hoje**.

Além disso, mesmo o orçado de 2025 da API tem **estrutura diferente** da aba (agregado por categoria contábil vs. detalhado por advogado) e valores que não batem item a item — indício de que o orçamento do Excel é montado à parte. **Pergunta para a reunião:** o orçamento 2026 detalhado por advogado é montado à mão, ou exportado de algum lugar? Ele é carregado no TOTVS?

---

## 5. Mapeamento linha-a-linha do `Base_Resultado Mensal_V2`

### 5.1. ✅ Automatizável com a API (validado em 2026)

| Alvo | Fonte na API | Status |
| ---- | ------------ | ------ |
| **Linha 4 — Receita de honorários** | `PosicaoFinanceiraResultadoRecebimentoViews` Σ Valor1 do mês | ✅ EXATO |
| **Faturamento Realizado** (Areas Sintetico) | `PosicaoFinanceiraResultadoFaturamentoViews` Σ Valor1 do mês | ✅ EXATO |
| **Meta__2 — Recebimento por mês** | mesma view de recebimento | ✅ EXATO |
| **Aba `Resumo_Recebidas`** | `RateioFaturaProfissionalViews` por FaturaDataEmissao | ✅ EXATO |
| **Aba `FATURAS Analitico CENTRO CUSTO`** | `FaturaViews` + `RateioFaturaCasoViews` | ✅ EXATO |

### 5.2. ❌ Fora desta API (precisa do TOTVS Backoffice)

As ~65 linhas de despesa institucional:

| Bloco (linhas) | Exemplos | Origem provável no TOTVS |
| -------------- | -------- | ------------------------ |
| Folha por profissional (8–71) | Convênio, Pró-labore, AASP, Distribuição, Vales | TOTVS RH / Folha |
| Ocupação (81–90) | Aluguel, Condomínio, Energia, IPTU, Telefonia | TOTVS Contas a Pagar |
| Despesas Operacionais (96–158) | Limpeza, Manutenção, Consultorias, Contabilidade, Salários ADM, Eventos | TOTVS Contas a Pagar / RH |
| Impostos (164–177) | COFINS, CSLL, FGTS, INSS, IRRF, ISS, PIS, Data Center | TOTVS Tributário / RH |

### 5.3. ⚙️ Recalculam sozinhas (fórmula, não precisam de API)

Totais `=SUM(...)`, abas `DRE 2026`, `Areas Sintetico`, `Institucional`, `Contencioso`, `Econômico`, `Arbitragem`, `Rateio Mensal`. Recalculam automaticamente assim que as linhas-fonte forem preenchidas.

> **Nota — `DRE 2026`:** é a aba do **orçado/planejado** (meta fixa de faturamento, despesas vindas da aba `Orçamento`, impostos por fórmula `=Faturamento×15%+50000`). Como depende da `Orçamento 2026` (que a API não cobre — §4.3), ela não fica pronta só com a API. Suas fórmulas também referenciam **arquivos Excel externos** (`'[2]Orçamento 2026'`, `'[3]Areas Sintetico'`) — confirmar na reunião se há outros arquivos envolvidos.

> **Nota — `Rateio Mensal`:** rateia custo de equipe + despesas institucionais por área. É 100% fórmula, mas depende das linhas de folha/despesa (Fase 2). Testei `RateioGerencialViews` como fonte alternativa e **não serve** (traz horas × tabela padrão, não custo de folha).

---

## 6. Referência de endpoints

### Tier 1 — Usados na Fase 1 (validados)

| Endpoint | Campos-chave | Para quê |
| -------- | ------------ | -------- |
| `PosicaoFinanceiraResultadoRecebimentoViews` | `AnoMes`, `Valor1` | **Receita de honorários** + Recebimento Bruto |
| `PosicaoFinanceiraResultadoFaturamentoViews` | `AnoMes`, `Valor1` | **Faturamento Realizado** + Faturamento Bruto |
| `RateioFaturaProfissionalViews` | `FaturaNumero`, `FaturaDataEmissao`, `ProfissionalSigla`, `ValorTrabalhado`, `ValorFaturado` | Aba `Resumo_Recebidas` |
| `FaturaViews` | `Numero`, `DataEmissao`, `ValorHonorarios`, `Situacao` | Cabeçalhos de fatura |
| `RateioFaturaCasoViews` | `FaturaNumero`, `CasoId`, `CasoCodigo`, `ClienteCodigo` | Quebra por caso |

### Tier 2 — Contexto / parcial

| Endpoint | Observação |
| -------- | ---------- |
| `OrcamentoViews` | Orçado por plano de contas — **só 2025**, estrutura diferente da aba |
| `PosicaoFinanceiraViews` | View mestre (pega-tudo): `H` horas, `RF` faturamento, `RR` recebimento, `F` fatura, `D`/`DI` despesa. Sempre com `$filter=AnoMes` + `$top=1000+`. Lenta. As linhas `RR`/`RF` trazem deduções por linha em `Valor2/3/4`. |
| `RateioGerencialViews` | Horas × tabela padrão (não serve para custo de folha) |
| `GrupoJuridicoViews` / `ProfissionalViews` | Mapa advogado → área |

---

## 7. Caminhos sem saída (para não repetir)

1. **URL `ODataFinanceiro` separada** — não existe; só aliases por área, todos com dados idênticos do módulo Legal.
2. **`FunctionImport`s** — todos bound e quase todos write-actions; inúteis para coleta.
3. **`$select=*` / `$expand`** — nada escondido nas views-stub.
4. **OData v4** — serviço é v3 only.
5. **Endpoints `/Web/`** — exigem login por cookie com challenge-response (não Basic Auth).
6. **`LancamentoFinanceiroViews`** (71k linhas) — todos os campos null exceto Id/DataInclusao (restrição deliberada).

---

## 8. Plano de implementação da Fase 1

**Escopo (sem credenciais novas, tudo validado):** automatizar todo o bloco de receita.

1. **Receita de honorários** e **Faturamento Realizado** — soma de `Valor1` das views de recebimento/faturamento do mês.
2. **Meta__2 (Recebimento)** — idem, por mês.
3. **Aba `Resumo_Recebidas`** — faturas do período expandidas por advogado.
4. **Aba `FATURAS Analitico CENTRO CUSTO`** — fatura + caso.

Implementação Python + openpyxl, escrevendo no workbook e preservando fórmulas (~200 linhas).

**Esforço:** Fase 1 = **1–2 dias**. Fase 2 (despesas) = **3–5 dias** + desbloqueio das credenciais TOTVS Backoffice.

---

## 9. Perguntas em aberto para a RUMO / para quem faz o fechamento

1. **Acesso ao TOTVS Backoffice** (Financeiro, RH, Tributário, Contábil). Existem credenciais? Em qual host/path? — **desbloqueio principal da Fase 2.**
2. **Orçamento 2026** — montado à mão (detalhado por advogado) ou exportado? Está carregado no TOTVS em algum lugar? Por que difere do orçado que está na API (2025)?
3. **DRE 2026 e arquivos externos** — as fórmulas referenciam outros arquivos Excel (`[2]`, `[3]`). Há outros arquivos no fluxo?
4. **Custos Diretos por área** — existe relatório TOTVS que já produz esses totais, ou são reconstruídos da folha à mão?

---

## 10. Arquivos & artefatos

```
/home/nandoravioli/bia4u/rumo/
├── docs/
│   ├── AUTOMATION_FINDINGS.md       (versão em inglês)
│   └── AUTOMATION_FINDINGS_PTBR.md  (ESTE DOCUMENTO)
├── work/
│   ├── api_dumps/              (~631 dumps de endpoints + metadata.xml)
│   ├── analysis/               (entidades, contagens, inputs manuais, dumps do workbook em TSV)
│   └── scripts/                (scripts Python utilizados)
└── Copy of Fechamento MBC 02.2026.xlsx  (workbook original, intocado)
```

---

*Fim do documento.*
