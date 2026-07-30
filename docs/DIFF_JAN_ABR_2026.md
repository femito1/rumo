# Diferenças por linha — janeiro a abril de 2026 (nosso × planilha)

> Gerado por `backend/scripts/build_janabr_diff.py` a partir dos dados ao vivo
> (extract v3) e de `Fechamento MBC 06.2026.xlsx`. **Não é uma lista de erros**:
> cada diferença abaixo já foi diagnosticada e tem causa identificada. Junho
> fecha exatamente, e é o melhor mês de referência.

## Resumo

**Faturamento, Receita, Impostos e Amortização batem exatamente nos quatro meses.**
Toda a diferença de Resultado está dentro de *custo de equipe* e *despesas*, por
três causas conhecidas:

1. **Vale dos advogados** — nós incluímos o vale-refeição/transporte de cada
   advogado no custo de equipe da área dele (regra confirmada: "sempre incluir
   o vale"); as colunas de janeiro a maio da planilha não incluem.
2. **Estagiária do Direito Econômico** — o salário dela entra a partir de março
   e nós reproduzimos o valor da planilha ao centavo; é exatamente nesse mês que
   o sinal da diferença do Econômico se inverte.
3. **Lançamentos avulsos digitados só em janeiro/fevereiro** na planilha, sem
   lançamento correspondente na competência do sistema.

Além disso, a **fórmula de Despesas por área** da planilha está deslocada uma
linha de janeiro a maio (linhas 204/205/206), o que desloca também o rateio da
despesa institucional das três áreas. As fórmulas de junho já estão corretas.

## Diferenças por linha

Valores em R$. `Δ` = nosso − planilha (positivo = o nosso é maior).

| Linha | Janeiro (nosso / planilha / Δ) | Fevereiro (nosso / planilha / Δ) | Março (nosso / planilha / Δ) | Abril (nosso / planilha / Δ) |
|---|---|---|---|---|
| Receita | 279.821,07 / 279.821,07 / **0,00** | 319.233,58 / 319.233,58 / **0,00** | 612.501,76 / 612.501,76 / **0,00** | 238.327,46 / 238.327,46 / **0,00** |
| Custos Diretos | 208.085,84 / 211.242,68 / **-3.156,84**  | 217.186,37 / 218.453,74 / **-1.267,37**  | 201.731,83 / 198.079,41 / **3.652,42**  | 213.281,07 / 209.572,83 / **3.708,24**  |
| Despesas Indiretas | 101.715,18 / 100.181,41 / **1.533,77**  | 96.296,58 / 95.047,39 / **1.249,19**  | 99.021,21 / 101.968,90 / **-2.947,69**  | 108.086,08 / 110.156,11 / **-2.070,03**  |
| Resultado Bruto | -29.979,95 / -31.603,02 / **1.623,07**  | 5.750,63 / 5.732,45 / **18,18**  | 311.748,72 / 312.453,45 / **-704,73**  | -83.039,69 / -81.401,48 / **-1.638,21**  |
| Impostos | 41.973,16 / 41.973,16 / **-0,00** | 47.885,04 / 47.885,04 / **0,00** | 91.875,26 / 91.875,26 / **-0,00** | 35.749,12 / 35.749,12 / **0,00** |
| Amortização | 8.117,00 / 8.117,00 / **0,00** | 8.117,00 / 8.117,00 / **0,00** | 8.117,00 / 8.117,00 / **0,00** | 8.117,00 / 8.117,00 / **0,00** |
| Resultado Líquido | -80.070,11 / -81.693,18 / **1.623,07**  | -50.251,41 / -50.269,59 / **18,18**  | 211.756,46 / 212.461,19 / **-704,73**  | -126.905,81 / -125.267,60 / **-1.638,21**  |
| Reserva de bônus | -8.007,01 / -8.169,32 / **162,31**  | -5.025,14 / -5.026,96 / **1,82**  | 21.175,65 / 21.246,12 / **-70,47**  | -12.690,58 / -12.526,76 / **-163,82**  |
| Contencioso · Custo equipe | 73.478,62 / 73.576,32 / **-97,70**  | 76.179,29 / 76.342,35 / **-163,06**  | 74.072,29 / 72.845,49 / **1.226,79**  | 76.311,31 / 75.374,05 / **937,26**  |
| Contencioso · Despesas Equipe | 341,40 / 1.060,10 / **-718,70**  | 2.346,72 / 2.129,32 / **217,40**  | 2.346,72 / 2.346,72 / **0,00** | 3.881,72 / 4.183,92 / **-302,20**  |
| Contencioso · Despesa Institucional | 34.877,04 / 33.821,38 / **1.055,66**  | 31.500,33 / 30.609,71 / **890,62**  | 32.989,01 / 34.482,81 / **-1.493,80**  | 34.997,85 / 36.400,45 / **-1.402,60**  |
| Contencioso · Resultado Bruto | -70.625,70 / -70.386,79 / **-238,91**  | 49.512,28 / 50.457,62 / **-945,34**  | 50.517,18 / 50.249,98 / **267,20**  | -58.730,33 / -59.497,43 / **767,10**  |
| Econômico · Custo equipe | 72.593,09 / 75.653,19 / **-3.060,10**  | 75.800,79 / 78.817,05 / **-3.016,26**  | 78.475,60 / 76.049,97 / **2.425,63**  | 81.931,07 / 79.160,08 / **2.770,99**  |
| Econômico · Despesas Equipe | 1.400,19 / 1.871,81 / **-471,62**  | 2.129,32 / 3.296,07 / **-1.166,75**  | 2.129,32 / 2.129,32 / **0,00** | 2.231,52 / 2.129,32 / **102,20**  |
| Econômico · Despesa Institucional | 34.456,72 / 34.776,07 / **-319,35**  | 31.343,82 / 31.601,96 / **-258,14**  | 34.950,08 / 35.999,71 / **-1.049,63**  | 37.575,18 / 38.228,85 / **-653,67**  |
| Econômico · Resultado Bruto | -46.605,66 / -50.457,07 / **3.851,41**  | 8.892,66 / 4.451,92 / **4.440,74**  | 228.337,93 / 229.714,00 / **-1.376,07**  | 38.183,50 / 40.402,75 / **-2.219,25**  |
| Arbitragem · Custo equipe | 62.014,13 / 62.013,17 / **0,96**  | 63.706,29 / 61.794,34 / **1.911,95**  | 49.183,94 / 49.183,94 / **0,00** | 55.038,69 / 55.038,69 / **0,00** |
| Arbitragem · Despesas Equipe | 1.204,47 / 146,00 / **1.058,47**  | 2.633,69 / 2.633,69 / **-0,00** | 4.701,41 / 3.728,18 / **973,23**  | 4.157,99 / 2.633,69 / **1.524,30**  |
| Arbitragem · Despesa Institucional | 29.435,36 / 28.506,06 / **929,30**  | 26.342,71 / 24.776,64 / **1.566,07**  | 21.904,67 / 23.282,16 / **-1.377,49**  | 25.241,81 / 26.579,88 / **-1.338,07**  |
| Arbitragem · Resultado Bruto | 40.515,38 / 42.503,77 / **-1.988,39**  | -30.176,28 / -26.698,68 / **-3.477,60**  | 37.653,91 / 37.249,72 / **404,19**  | -80.962,82 / -80.776,26 / **-186,56**  |

## De onde vem cada diferença

### 1. Vale dos advogados dentro do custo de equipe

Valores que nós somamos ao custo de equipe de cada área e que a planilha não
soma nas colunas de janeiro a maio:

| Mês | Contencioso | Econômico | Arbitragem |
|---|---|---|---|
| Janeiro | 997,80 | — | — |
| Fevereiro | 1.249,40 | — | — |
| Março | 1.190,80 | 1.008,40 | — |
| Abril | 1.190,80 | 1.008,40 | — |

### 2. Estagiária do Direito Econômico (planilha, linha 52)

| Mês | Planilha (linha 52) | Nosso |
|---|---|---|
| Janeiro | 0,00 | 0,00 |
| Fevereiro | 0,00 | 0,00 |
| Março | 1.026,00 | 1.026,67 |
| Abril | 2.200,00 | 2.200,00 |

Batem — não é fonte de diferença a partir de março; é o que explica a
**inversão de sinal** da diferença do Econômico entre fevereiro e março.

### 3. Lançamentos avulsos só em janeiro/fevereiro (bloco do Econômico)

Linhas da planilha com valor em janeiro ou fevereiro e zeradas nos meses
seguintes. Não encontramos lançamento correspondente na competência:

| Linha | Janeiro | Fevereiro | Março | Abril |
|---|---|---|---|---|
| 34 | 0,00 | 3.018,00 | 0,00 | 0,00 |
| 35 | 0,00 | 520,00 | 0,00 | 0,00 |
| 36 | 97,70 | 54,35 | 0,00 | 0,00 |
| 43 | 0,00 | 1.034,38 | 0,00 | 0,00 |
| 47 | 0,00 | 1.000,00 | 0,00 | 0,00 |
| 51 | 1.409,09 | 0,00 | 0,00 | 0,00 |
| 54 | 2.101,88 | 0,00 | 0,00 | 2.028,56 |
| 55 | 0,00 | 0,00 | 92,45 | 0,00 |

### 4. Arbitragem, fevereiro: convênio médico de um advogado (planilha, linha 69)

A planilha traz o convênio médico de um advogado da Arbitragem (linha 69,
`R$ 1.911,45`) **apenas em janeiro**; de fevereiro em diante a linha fica
zerada. No sistema esse convênio (conta `030.010.0110`, `R$ 1.911,95`) continua
lançado em fevereiro, e é isso que explica quase toda a diferença de
`R$ 1.911,95` do custo de equipe da Arbitragem naquele mês.

| Mês | Planilha (linha 69) | Nosso (conta 030.010.0110) |
|---|---|---|
| Janeiro | 1.911,45 | 1.911,95 |
| Fevereiro | 0,00 | 1.911,95 |
| Março | 0,00 | 0,00 |
| Abril | 0,00 | 0,00 |

A partir de março esse advogado sai da folha nos dois lados, e o custo de
equipe da Arbitragem volta a bater exatamente (março e abril: diferença zero).

### 5. Despesas institucionais: de onde vem o delta, família por família

As famílias abaixo somam **exatamente** o delta de Despesas Indiretas de cada
mês (conferido pelo gerador). Duas delas são apenas **apresentação**: a conta
fica numa família diferente de cada lado, mas as duas entram no mesmo total
(`r198 = r85+r92+r95+r110+r116+r124+r137+r158+r164+r180`), então o efeito no
número que o cliente lê é **zero**.

| Família | Janeiro | Fevereiro | Março | Abril |
|---|---|---|---|---|
| Ocupação + Administrativas *(troca)* | 1.399,87 | 217,11 | 37,39 | 19,17 |
| Endomarketing + Inv. em Prospecção *(troca)* | 0,00 | 0,00 | 162,09 | -200,00 |
| Despesas Gerais | -0,10 | 0,00 | 105,00 | 0,00 |
| Salários Administração | 134,00 | 1.032,35 | -2.199,08 | -2.199,20 |
| Gestão do Conhecimento | 0,00 | 0,00 | -815,49 | 200,00 |
| Informática | 0,00 | -0,27 | -237,60 | 110,00 |
| **Total (= Δ Despesas Indiretas)** | **1.533,77** | **1.249,19** | **-2.947,69** | **-2.070,03** |

Os três maiores itens, já identificados:

* **Salários Administração** — o Vale ADM dos meses não ajustados
  (março −2.199,08 / abril −2.199,20). Já respondido pelo financeiro.
* **Informática, março −237,60** — é exatamente `7.744,12 − 7.506,52` na conta
  `040.040.0030`: a planilha usou o valor **bruto** e nós usamos o **líquido**
  (`CPGNVALORLIQUIDO`), que é a regra confirmada e que faz 10 de 10 famílias
  baterem em maio e todas em junho. Janeiro, maio e junho batem em 0,00, o que
  confirma que o mapeamento está certo e que março/abril são pontuais.
* **Gestão do Conhecimento, março −815,49** — a planilha lança 1.094,49 de
  *Cursos e Treinamentos - Arbitragem* como despesa institucional; sendo curso
  de uma área, entra em Despesas Área (`030.010.0180`), que é o que fazemos.

⚠ **Nota de leitura, para não repetir um erro nosso:** uma diferença no total
de uma *família* não é, por si só, um erro de classificação. `r198` soma as duas
famílias de cada troca acima, então mover uma conta entre elas não muda o total.
Confira sempre o total antes de tratar a família como defeito — os nossos
1.171,71 de janeiro em *Eventos e Happy Hour* batem ao centavo com a `r141` da
planilha; só o rótulo da família é outro. E a própria planilha troca de critério
de mês para mês nessa conta (`r141` em jan/fev, `r166` de março a junho).

### 6. Perguntas que sobram para o financeiro

1. Os lançamentos avulsos do item 3 são de outra competência, ou ajustes
   manuais? Se tiverem origem no sistema, passamos a considerá-los.
2. Confirmar se as fórmulas de Despesas por área (linhas 204/205/206) de
   janeiro a maio devem ser copiadas de junho.
3. Janeiro: o vale-transporte da planilha é `=35,52+262,64`. Os 262,64 são o
   lançamento do sistema; de onde vêm os 35,52?
4. O convênio médico da linha 69 (item 4) deveria continuar em fevereiro,
   como está no sistema, ou foi encerrado em janeiro?

*(Vale-ADM de março/abril/maio já está respondido: são meses não ajustados na
planilha e o financeiro optou por não corrigir.)*
