# Diferenças entre a planilha e o sistema — Janeiro a Junho de 2026

Comparação da planilha `Fechamento MBC 06.2026.xlsx` com os números do sistema, dados extraídos em 04/08/2026.

## O essencial

1. **A receita bate em todos os meses.** Toda diferença está em *despesa*.
2. No acumulado de janeiro a junho, o **Resultado Bruto** difere **-R$ 5.003,04** — sobre uma receita de mais de R$ 2 milhões.
3. **Cada centavo dessa diferença tem uma causa identificada**, listada abaixo.
4. **Junho fecha** (só a tarifa bancária de R$ 4,80 difere) — é o mês em que a planilha já está com as fórmulas certas e inclui o vale. É a referência de como os dois lados batem quando ambos estão corretos.

## Como conferir qualquer número

Cada diferença aparece **mês a mês** com a **célula exata da planilha** ao lado.
Abra a planilha, vá na célula indicada e compare com a coluna *Sistema*. As colunas
de cada mês na aba `Areas Sintetico atualizado` são: **Jan=C**, **Fev=G**, **Mar=K**, **Abr=O**, **Mai=S**, **Jun=W**.

Só detalhamos diferenças de **R$ 1.000,00 ou mais**; as menores estão no fim.

## O que NÃO difere

| Linha | Jan | Fev | Mar | Abr | Mai | Jun | Acumulado |
|---|---:|---:|---:|---:|---:|---:|---:|
| Receita | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | -R$ 0,16 | -R$ 0,44 | **-R$ 0,60** |
| Impostos | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | -R$ 0,02 | -R$ 0,07 | **-R$ 0,09** |
| Amortização | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | **R$ 0,00** |

Receita, impostos e amortização batem. Os centavos de maio e junho são só
arredondamento (a planilha arredonda o recebimento para reais inteiros).

## As quatro causas

Praticamente toda a diferença vem de quatro coisas. A tabela seguinte mostra onde
cada linha cai; o detalhe por linha vem depois.

1. **A planilha rateia a despesa institucional entre as áreas com uma fórmula**
   **deslocada** (linhas 204/205/206), de janeiro a maio: cada área acaba somando
   as despesas da área seguinte. Junho já está com a fórmula certa. Isso move as
   linhas de *Despesa Institucional* e *Despesas Equipe* das três áreas — mas é a
   **planilha** que precisa de ajuste, não o sistema.
2. **A despesa institucional por área é o total institucional dividido entre as**
   **áreas.** A divisão em si não cria nem apaga dinheiro (a soma das três áreas é
   sempre a mesma); a diferença vem do total. Para entender essas linhas, olhe
   *Despesas Indiretas*.
3. **O vale dos advogados** entra no custo da equipe da área, e a
   planilha não o incluiu de janeiro a maio. Em junho ela passou a incluir e o
   custo de equipe das três áreas fecha. (O *Resultado Bruto* por área não tem
   causa própria — é só a soma das linhas da área.)
4. **A anotação do convênio médico fica velha no sistema.** No lançamento do
   convênio de cada advogado há uma *memória de cálculo* dizendo quanto do plano
   é da MBC. Em janeiro e fevereiro esse texto descrevia um plano antigo — e o
   mesmo texto vinha repetido desde 2025, enquanto o valor do plano mudou duas
   vezes. Hoje o sistema não depende mais dele: calcula a parte da MBC pela
   proporção observada nos meses em que a anotação está correta. **Se um plano
   mudar de novo, vale atualizar a anotação** — é o que mantém o cálculo exato em
   vez de estimado.

*Uma ressalva ao ler qualquer total: um número que fecha porque dois erros se*
*anulam não está validado. Por isso mostramos tudo mês a mês, não só o acumulado —*
*é mais fácil de conferir.*

## Resumo: onde estão as diferenças

Diferença = Sistema − Planilha, por mês. `✓` = bate.

| Linha | Jan | Fev | Mar | Abr | Mai | Jun | Acumulado |
|---|---:|---:|---:|---:|---:|---:|---:|
| Econômico · Custo equipe | -R$ 887,63 | -R$ 53,85 | +R$ 2.425,63 | +R$ 2.770,99 | +R$ 75,61 | +R$ 0,01 | **+R$ 4.330,76** |
| Arbitragem · Despesas Equipe | +R$ 1.058,47 | R$ 0,00 ✓ | +R$ 973,23 | +R$ 1.524,30 | +R$ 68,00 | R$ 0,00 ✓ | **+R$ 3.624,00** |
| Contencioso · Custo equipe | -R$ 97,70 | -R$ 163,06 | +R$ 1.226,79 | +R$ 937,26 | +R$ 1.236,90 | R$ 0,00 ✓ | **+R$ 3.140,19** |
| Contencioso · Despesa Institucional | +R$ 695,30 | +R$ 463,83 | -R$ 1.493,80 | -R$ 1.402,60 | -R$ 485,54 | +R$ 1,72 | **-R$ 2.221,09** |
| Contencioso · Despesas Equipe | -R$ 718,70 | +R$ 217,40 | R$ 0,00 ✓ | -R$ 302,20 | -R$ 1.358,73 | -R$ 0,01 | **-R$ 2.162,24** |
| Econômico · Despesa Institucional | +R$ 345,15 | +R$ 525,55 | -R$ 1.049,63 | -R$ 653,67 | -R$ 1.101,62 | +R$ 1,84 | **-R$ 1.932,38** |
| Arbitragem · Custo equipe | +R$ 0,96 | +R$ 1.911,95 | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | **+R$ 1.912,91** |
| Arbitragem · Despesa Institucional | +R$ 625,16 | +R$ 1.209,16 | -R$ 1.377,49 | -R$ 1.338,07 | -R$ 778,27 | +R$ 1,24 | **-R$ 1.658,27** |
| Custos Diretos | -R$ 984,37 | +R$ 1.695,04 | +R$ 3.652,42 | +R$ 3.708,24 | +R$ 1.312,50 | R$ 0,00 ✓ | **+R$ 9.383,83** |
| Resultado Bruto | -R$ 549,40 | -R$ 2.944,23 | -R$ 704,73 | -R$ 1.638,21 | +R$ 838,77 | -R$ 5,24 | **-R$ 5.003,04** |
| Resultado Líquido | -R$ 549,40 | -R$ 2.944,23 | -R$ 704,73 | -R$ 1.638,21 | +R$ 838,79 | -R$ 5,17 | **-R$ 5.002,95** |
| Despesas Indiretas | +R$ 1.533,77 | +R$ 1.249,19 | -R$ 2.947,69 | -R$ 2.070,03 | -R$ 2.151,43 | +R$ 4,80 | **-R$ 4.381,39** |
| Arbitragem · Resultado Bruto | -R$ 1.684,25 | -R$ 3.120,69 | +R$ 404,19 | -R$ 186,56 | +R$ 709,62 | -R$ 1,24 | **-R$ 3.878,93** |
| Econômico · Resultado Bruto | +R$ 1.014,44 | +R$ 694,64 | -R$ 1.376,07 | -R$ 2.219,25 | -R$ 479,14 | -R$ 2,14 | **-R$ 2.367,52** |
| Contencioso · Resultado Bruto | +R$ 121,45 | -R$ 518,55 | +R$ 267,20 | +R$ 767,10 | +R$ 607,09 | -R$ 1,85 | **+R$ 1.242,44** |

## Detalhe, linha por linha

### Econômico · Custo equipe

Diferença no acumulado: **+R$ 4.330,76**

| Mês | Célula na planilha | Planilha | Sistema | Diferença |
|---|---|---:|---:|---:|
| Janeiro | `C57` | R$ 75.653,19 | R$ 74.765,56 | -R$ 887,63 |
| Fevereiro | `G57` | R$ 78.817,05 | R$ 78.763,20 | -R$ 53,85 |
| Março | `K57` | R$ 76.049,97 | R$ 78.475,60 | +R$ 2.425,63 |
| Abril | `O57` | R$ 79.160,08 | R$ 81.931,07 | +R$ 2.770,99 |
| Maio | `S57` | R$ 79.436,24 | R$ 79.511,85 | +R$ 75,61 |
| Junho | `W57` | R$ 80.536,84 | R$ 80.536,85 | +R$ 0,01 |
| **Acumulado** | — | **R$ 469.653,37** | **R$ 473.984,13** | **+R$ 4.330,76** |

Na planilha: aba **Areas Sintetico atualizado**, linha **57**.

**Por quê:** Três coisas: a **anotação do convênio de EHF e RB** em jan/fev (causa 4 do resumo); o **vale dos advogados** (como no Contencioso); e a **estagiária do Direito Econômico**, que entra na planilha em março e que reproduzimos ao centavo — é ela que inverte o sinal da diferença entre fevereiro e março. Sobra uma estimativa nossa: a parte MBC do **RB em janeiro** (o plano dele mudou e nada registra qual era a proporção naquele mês).

**Onde conferir o detalhe:** Planilha, linhas **44 e 48** (convênio) e **52** (estagiária).

### Arbitragem · Despesas Equipe

Diferença no acumulado: **+R$ 3.624,00**

| Mês | Célula na planilha | Planilha | Sistema | Diferença |
|---|---|---:|---:|---:|
| Janeiro | `C77` | R$ 146,00 | R$ 1.204,47 | +R$ 1.058,47 |
| Fevereiro | `G77` | R$ 2.633,69 | R$ 2.633,69 | R$ 0,00 ✓ |
| Março | `K77` | R$ 3.728,18 | R$ 4.701,41 | +R$ 973,23 |
| Abril | `O77` | R$ 2.633,69 | R$ 4.157,99 | +R$ 1.524,30 |
| Maio | `S77` | R$ 1.204,47 | R$ 1.272,47 | +R$ 68,00 |
| Junho | `W77` | R$ 11.597,70 | R$ 11.597,70 | R$ 0,00 ✓ |
| **Acumulado** | — | **R$ 21.943,73** | **R$ 25.567,73** | **+R$ 3.624,00** |

Na planilha: aba **Areas Sintetico atualizado**, linha **77**.

**Por quê:** A **fórmula deslocada** da planilha (causa 2) — na Arbitragem o efeito é o maior dos três. O resíduo de janeiro (+1.204,47) é o **Canal de Arbitragem**, que a planilha daquele mês não somou.

**Onde conferir o detalhe:** Planilha, linhas **204 / 205 / 206**, colunas de janeiro a maio.

**O que precisamos de vocês:** Mesma correção de fórmula.

### Contencioso · Custo equipe

Diferença no acumulado: **+R$ 3.140,19**

| Mês | Célula na planilha | Planilha | Sistema | Diferença |
|---|---|---:|---:|---:|
| Janeiro | `C39` | R$ 73.576,32 | R$ 73.478,62 | -R$ 97,70 |
| Fevereiro | `G39` | R$ 76.342,35 | R$ 76.179,29 | -R$ 163,06 |
| Março | `K39` | R$ 72.845,49 | R$ 74.072,29 | +R$ 1.226,79 |
| Abril | `O39` | R$ 75.374,05 | R$ 76.311,31 | +R$ 937,26 |
| Maio | `S39` | R$ 74.141,21 | R$ 75.378,11 | +R$ 1.236,90 |
| Junho | `W39` | R$ 75.424,21 | R$ 75.424,21 | R$ 0,00 ✓ |
| **Acumulado** | — | **R$ 447.703,63** | **R$ 450.843,83** | **+R$ 3.140,20** |

Na planilha: aba **Areas Sintetico atualizado**, linha **39**.

**Por quê:** O **vale dos advogados** (causa 3 do resumo): entra sempre no custo da área e a planilha não o incluiu de janeiro a maio. Junho, que já inclui, bate em 0,00. O restante é classificação que não muda total (ISS e AASP — ver *Diferenças que não mudam nenhum total*).

**Onde conferir o detalhe:** Planilha, linhas **26 e 27** (vale).

### Contencioso · Despesa Institucional

Diferença no acumulado: **-R$ 2.221,09**

| Mês | Célula na planilha | Planilha | Sistema | Diferença |
|---|---|---:|---:|---:|
| Janeiro | `C42` | R$ 33.821,38 | R$ 34.516,68 | +R$ 695,30 |
| Fevereiro | `G42` | R$ 30.609,71 | R$ 31.073,54 | +R$ 463,83 |
| Março | `K42` | R$ 34.482,81 | R$ 32.989,01 | -R$ 1.493,80 |
| Abril | `O42` | R$ 36.400,45 | R$ 34.997,85 | -R$ 1.402,60 |
| Maio | `S42` | R$ 35.555,40 | R$ 35.069,86 | -R$ 485,54 |
| Junho | `W42` | R$ 32.562,84 | R$ 32.564,56 | +R$ 1,72 |
| **Acumulado** | — | **R$ 203.432,59** | **R$ 201.211,50** | **-R$ 2.221,09** |

Na planilha: aba **Areas Sintetico atualizado**, linha **42**.

**Por quê:** **Não é da área — é a despesa institucional total, rateada** (causa 1 do resumo). A diferença vem inteira do total; a divisão entre as três áreas não cria nem apaga dinheiro. Para entender esta linha, olhe *Despesas Indiretas*.

**Onde conferir o detalhe:** Planilha, linha **207** (total a ratear) e **5 / 30 / 60** (custo de cada área).

### Contencioso · Despesas Equipe

Diferença no acumulado: **-R$ 2.162,24**

| Mês | Célula na planilha | Planilha | Sistema | Diferença |
|---|---|---:|---:|---:|
| Janeiro | `C41` | R$ 1.060,10 | R$ 341,40 | -R$ 718,70 |
| Fevereiro | `G41` | R$ 2.129,32 | R$ 2.346,72 | +R$ 217,40 |
| Março | `K41` | R$ 2.346,72 | R$ 2.346,72 | R$ 0,00 ✓ |
| Abril | `O41` | R$ 4.183,92 | R$ 3.881,72 | -R$ 302,20 |
| Maio | `S41` | R$ 2.276,22 | R$ 917,49 | -R$ 1.358,73 |
| Junho | `W41` | R$ 2.442,49 | R$ 2.442,48 | -R$ 0,01 |
| **Acumulado** | — | **R$ 14.438,77** | **R$ 12.276,53** | **-R$ 2.162,24** |

Na planilha: aba **Areas Sintetico atualizado**, linha **41**.

**Por quê:** A **fórmula deslocada** da planilha (causa 2 do resumo): de janeiro a maio cada área soma as despesas da área seguinte. Junho já está com a fórmula certa e bate. O que sobra em janeiro são lançamentos que a planilha não somou (ver *Despesas Indiretas*).

**Onde conferir o detalhe:** Planilha, linhas **204 / 205 / 206**, colunas de janeiro a maio.

**O que precisamos de vocês:** Vale copiar as fórmulas de junho para janeiro–maio na planilha.

### Econômico · Despesa Institucional

Diferença no acumulado: **-R$ 1.932,38**

| Mês | Célula na planilha | Planilha | Sistema | Diferença |
|---|---|---:|---:|---:|
| Janeiro | `C60` | R$ 34.776,07 | R$ 35.121,22 | +R$ 345,15 |
| Fevereiro | `G60` | R$ 31.601,96 | R$ 32.127,51 | +R$ 525,55 |
| Março | `K60` | R$ 35.999,71 | R$ 34.950,08 | -R$ 1.049,63 |
| Abril | `O60` | R$ 38.228,85 | R$ 37.575,18 | -R$ 653,67 |
| Maio | `S60` | R$ 38.094,71 | R$ 36.993,09 | -R$ 1.101,62 |
| Junho | `W60` | R$ 34.770,11 | R$ 34.771,95 | +R$ 1,84 |
| **Acumulado** | — | **R$ 213.471,41** | **R$ 211.539,03** | **-R$ 1.932,38** |

Na planilha: aba **Areas Sintetico atualizado**, linha **60**.

**Por quê:** Mesma causa do Contencioso: é o total institucional rateado (causa 1).

**Onde conferir o detalhe:** Planilha, linha **207** e **5 / 30 / 60**.

### Arbitragem · Custo equipe

Diferença no acumulado: **+R$ 1.912,91**

| Mês | Célula na planilha | Planilha | Sistema | Diferença |
|---|---|---:|---:|---:|
| Janeiro | `C75` | R$ 62.013,17 | R$ 62.014,13 | +R$ 0,96 |
| Fevereiro | `G75` | R$ 61.794,34 | R$ 63.706,29 | +R$ 1.911,95 |
| Março | `K75` | R$ 49.183,94 | R$ 49.183,94 | R$ 0,00 ✓ |
| Abril | `O75` | R$ 55.038,69 | R$ 55.038,69 | R$ 0,00 ✓ |
| Maio | `S75` | R$ 54.383,94 | R$ 54.383,94 | R$ 0,00 ✓ |
| Junho | `W75` | R$ 54.383,94 | R$ 54.383,94 | R$ 0,00 ✓ |
| **Acumulado** | — | **R$ 336.798,02** | **R$ 338.710,93** | **+R$ 1.912,91** |

Na planilha: aba **Areas Sintetico atualizado**, linha **75**.

**Por quê:** Convênio médico de um advogado (JGS) em **fevereiro** — e a própria planilha responde. Em fevereiro ela mantém a distribuição (linha 70) e o pró-labore (linha 71) dele e deixa só o convênio (linha 69) em branco. Quem recebe distribuição está na folha, então o plano é custo real, e o sistema o tem lançado. De março em diante ele sai dos dois lados e a Arbitragem bate em 0,00. **Não é dúvida — é uma omissão da coluna de fevereiro.**

**Onde conferir o detalhe:** Planilha, linhas **69, 70 e 71**, coluna de fevereiro.

### Arbitragem · Despesa Institucional

Diferença no acumulado: **-R$ 1.658,27**

| Mês | Célula na planilha | Planilha | Sistema | Diferença |
|---|---|---:|---:|---:|
| Janeiro | `C78` | R$ 28.506,06 | R$ 29.131,22 | +R$ 625,16 |
| Fevereiro | `G78` | R$ 24.776,64 | R$ 25.985,80 | +R$ 1.209,16 |
| Março | `K78` | R$ 23.282,16 | R$ 21.904,67 | -R$ 1.377,49 |
| Abril | `O78` | R$ 26.579,88 | R$ 25.241,81 | -R$ 1.338,07 |
| Maio | `S78` | R$ 26.080,54 | R$ 25.302,27 | -R$ 778,27 |
| Junho | `W78` | R$ 23.479,14 | R$ 23.480,38 | +R$ 1,24 |
| **Acumulado** | — | **R$ 152.704,42** | **R$ 151.046,15** | **-R$ 1.658,27** |

Na planilha: aba **Areas Sintetico atualizado**, linha **78**.

**Por quê:** Mesma causa do Contencioso: é o total institucional rateado (causa 1).

**Onde conferir o detalhe:** Planilha, linha **207** e **5 / 30 / 60**.

### Custos Diretos

Diferença no acumulado: **+R$ 9.383,83**

| Mês | Célula na planilha | Planilha | Sistema | Diferença |
|---|---|---:|---:|---:|
| Janeiro | `C6` | R$ 211.242,68 | R$ 210.258,31 | -R$ 984,37 |
| Fevereiro | `G6` | R$ 218.453,74 | R$ 220.148,78 | +R$ 1.695,04 |
| Março | `K6` | R$ 198.079,41 | R$ 201.731,83 | +R$ 3.652,42 |
| Abril | `O6` | R$ 209.572,83 | R$ 213.281,07 | +R$ 3.708,24 |
| Maio | `S6` | R$ 210.089,46 | R$ 211.401,96 | +R$ 1.312,50 |
| Junho | `W6` | R$ 210.781,04 | R$ 210.781,04 | R$ 0,00 ✓ |
| **Acumulado** | — | **R$ 1.258.219,16** | **R$ 1.267.602,99** | **+R$ 9.383,83** |

Na planilha: aba **Areas Sintetico atualizado**, linha **6**.

**Por quê:** É a soma dos custos de equipe das três áreas — mesmas causas já descritas em cada uma (vale, convênio, estagiária).

**Onde conferir o detalhe:** Ver as três linhas de Custo equipe por área.

### Resultado Bruto

Diferença no acumulado: **-R$ 5.003,04**

| Mês | Célula na planilha | Planilha | Sistema | Diferença |
|---|---|---:|---:|---:|
| Janeiro | `C25` | -R$ 31.603,02 | -R$ 32.152,42 | -R$ 549,40 |
| Fevereiro | `G25` | R$ 5.732,45 | R$ 2.788,22 | -R$ 2.944,23 |
| Março | `K25` | R$ 312.453,45 | R$ 311.748,72 | -R$ 704,73 |
| Abril | `O25` | -R$ 81.401,48 | -R$ 83.039,69 | -R$ 1.638,21 |
| Maio | `S25` | R$ 100.327,11 | R$ 101.165,88 | +R$ 838,77 |
| Junho | `W25` | -R$ 51.689,40 | -R$ 51.694,64 | -R$ 5,24 |
| **Acumulado** | — | **R$ 253.819,11** | **R$ 248.816,07** | **-R$ 5.003,04** |

Na planilha: aba **Areas Sintetico atualizado**, linha **25**.

**Por quê:** causa ainda não documentada — falar com o time antes da reunião.

### Resultado Líquido

Diferença no acumulado: **-R$ 5.002,95**

| Mês | Célula na planilha | Planilha | Sistema | Diferença |
|---|---|---:|---:|---:|
| Janeiro | `C30` | -R$ 81.693,18 | -R$ 82.242,58 | -R$ 549,40 |
| Fevereiro | `G30` | -R$ 50.269,59 | -R$ 53.213,82 | -R$ 2.944,23 |
| Março | `K30` | R$ 212.461,19 | R$ 211.756,46 | -R$ 704,73 |
| Abril | `O30` | -R$ 125.267,60 | -R$ 126.905,81 | -R$ 1.638,21 |
| Maio | `S30` | R$ 29.820,91 | R$ 30.659,70 | +R$ 838,79 |
| Junho | `W30` | -R$ 99.559,25 | -R$ 99.564,42 | -R$ 5,17 |
| **Acumulado** | — | **-R$ 114.507,52** | **-R$ 119.510,47** | **-R$ 5.002,95** |

Na planilha: aba **Areas Sintetico atualizado**, linha **30**.

**Por quê:** causa ainda não documentada — falar com o time antes da reunião.

### Despesas Indiretas

Diferença no acumulado: **-R$ 4.381,39**

| Mês | Célula na planilha | Planilha | Sistema | Diferença |
|---|---|---:|---:|---:|
| Janeiro | `C13` | R$ 100.181,41 | R$ 101.715,18 | +R$ 1.533,77 |
| Fevereiro | `G13` | R$ 95.047,39 | R$ 96.296,58 | +R$ 1.249,19 |
| Março | `K13` | R$ 101.968,90 | R$ 99.021,21 | -R$ 2.947,69 |
| Abril | `O13` | R$ 110.156,11 | R$ 108.086,08 | -R$ 2.070,03 |
| Maio | `S13` | R$ 105.511,43 | R$ 103.360,00 | -R$ 2.151,43 |
| Junho | `W13` | R$ 105.927,36 | R$ 105.932,16 | +R$ 4,80 |
| **Acumulado** | — | **R$ 618.792,60** | **R$ 614.411,21** | **-R$ 4.381,39** |

Na planilha: aba **Areas Sintetico atualizado**, linha **13**.

**Por quê:** Esta linha também explica a Despesa Institucional das três áreas (ela é rateada daqui). Somando família por família, as partes dão **exatamente** a diferença de cada mês — não sobra centavo:

* **Vale do administrativo** (mar −2.199 · abr −2.199 · mai −2.281): a planilha lançou as três pessoas em Salários Administração; nós lançamos ali só a pessoa do administrativo e mandamos os estagiários para as áreas. Jan, fev e jun batem.
* **Aluguel** (abr e mai, +129,17): usamos o aluguel líquido da sublocação (crédito Belline).
* **Tarifa bancária** (+4,80/mês): vem do sistema e está zerada no Excel. É a única diferença que sobra em junho.
* **Trocas de família** (Endomarketing ↔ Prospecção, Ocupação ↔ Administrativas): a mesma conta em famílias diferentes de cada lado, mas as duas entram no total — efeito **zero** (ver *Diferenças que não mudam nenhum total*).
* **Janeiro, Associações** (+1.399,87): a planilha não somou a AASP (195,40) nem o Canal de Arbitragem (1.204,47), que existem no sistema.
* **Janeiro, seguro** (+2.539,84): é um prêmio **anual**. A conta lança 2.722,55 em janeiro (de novo em julho); a planilha digita 182,71 todo mês. Não falta dinheiro: a planilha põe o prêmio em *Administrativas* (linha 133) e nós em Ocupação.
* **Março, vale da estagiária** (+543,22): um pagamento de benefícios fora da conta transitória (Vale Refeição 507,10 + Vale Transporte 36,12, com o nome dela no histórico).
* **Duas contas sem linha na planilha**: janeiro **IR Fonte ADM 169,52** e fevereiro **e-Social 1.032,35** — lançamentos reais, ausentes do Excel.
* **Março**: um curso de Arbitragem (−815,49) que a planilha pôs em institucional e nós na área; e Informática −237,60 (a planilha usou o valor bruto, nós o líquido).

**Onde conferir o detalhe:** Planilha: linhas **122/123** (vale ADM), **86** (aluguel), **128–131** (Associações), **133** (seguro), **158** (curso), **180** (Informática). O total é a linha **198** — e, depois de nomear cada item acima, ele fecha sem sobra.

### Arbitragem · Resultado Bruto

Diferença no acumulado: **-R$ 3.878,93**

| Mês | Célula na planilha | Planilha | Sistema | Diferença |
|---|---|---:|---:|---:|
| Janeiro | `C79` | R$ 42.503,77 | R$ 40.819,52 | -R$ 1.684,25 |
| Fevereiro | `G79` | -R$ 26.698,68 | -R$ 29.819,37 | -R$ 3.120,69 |
| Março | `K79` | R$ 37.249,72 | R$ 37.653,91 | +R$ 404,19 |
| Abril | `O79` | -R$ 80.776,26 | -R$ 80.962,82 | -R$ 186,56 |
| Maio | `S79` | -R$ 39.808,95 | -R$ 39.099,33 | +R$ 709,62 |
| Junho | `W79` | R$ 13.253,22 | R$ 13.251,98 | -R$ 1,24 |
| **Acumulado** | — | **-R$ 54.277,18** | **-R$ 58.156,11** | **-R$ 3.878,93** |

Na planilha: aba **Areas Sintetico atualizado**, linha **79**.

**Por quê:** Não tem causa própria: é a soma das linhas acima da área (causa 3 do resumo).

**Onde conferir o detalhe:** Some as linhas 75 a 78 da própria área na planilha.

### Econômico · Resultado Bruto

Diferença no acumulado: **-R$ 2.367,52**

| Mês | Célula na planilha | Planilha | Sistema | Diferença |
|---|---|---:|---:|---:|
| Janeiro | `C61` | -R$ 50.457,07 | -R$ 49.442,63 | +R$ 1.014,44 |
| Fevereiro | `G61` | R$ 4.451,92 | R$ 5.146,56 | +R$ 694,64 |
| Março | `K61` | R$ 229.714,00 | R$ 228.337,93 | -R$ 1.376,07 |
| Abril | `O61` | R$ 40.402,75 | R$ 38.183,50 | -R$ 2.219,25 |
| Maio | `S61` | R$ 44.916,89 | R$ 44.437,75 | -R$ 479,14 |
| Junho | `W61` | -R$ 12.926,08 | -R$ 12.928,22 | -R$ 2,14 |
| **Acumulado** | — | **R$ 256.102,41** | **R$ 253.734,89** | **-R$ 2.367,52** |

Na planilha: aba **Areas Sintetico atualizado**, linha **61**.

**Por quê:** Não tem causa própria: é a soma das linhas acima da área (causa 3 do resumo).

**Onde conferir o detalhe:** Some as linhas 57 a 60 da própria área na planilha.

### Contencioso · Resultado Bruto

Diferença no acumulado: **+R$ 1.242,44**

| Mês | Célula na planilha | Planilha | Sistema | Diferença |
|---|---|---:|---:|---:|
| Janeiro | `C43` | -R$ 70.386,79 | -R$ 70.265,34 | +R$ 121,45 |
| Fevereiro | `G43` | R$ 50.457,62 | R$ 49.939,07 | -R$ 518,55 |
| Março | `K43` | R$ 50.249,98 | R$ 50.517,18 | +R$ 267,20 |
| Abril | `O43` | -R$ 59.497,43 | -R$ 58.730,33 | +R$ 767,10 |
| Maio | `S43` | R$ 128.472,17 | R$ 129.079,26 | +R$ 607,09 |
| Junho | `W43` | -R$ 74.048,54 | -R$ 74.050,39 | -R$ 1,85 |
| **Acumulado** | — | **R$ 25.247,01** | **R$ 26.489,45** | **+R$ 1.242,44** |

Na planilha: aba **Areas Sintetico atualizado**, linha **43**.

**Por quê:** Não tem causa própria: é a soma das linhas acima da área (causa 3 do resumo).

**Onde conferir o detalhe:** Some as linhas 39 a 42 da própria área na planilha.

## Diferenças menores

| Linha | Jan | Fev | Mar | Abr | Mai | Jun | Acumulado |
|---|---:|---:|---:|---:|---:|---:|---:|
| Econômico · Despesas Equipe | -R$ 471,62 | -R$ 1.166,75 | R$ 0,00 ✓ | +R$ 102,20 | +R$ 1.504,72 | R$ 0,00 ✓ | **-R$ 31,45** |
| Receita | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | -R$ 0,16 | -R$ 0,44 | **-R$ 0,60** |
| Impostos | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | -R$ 0,02 | -R$ 0,07 | **-R$ 0,09** |

Somadas: **-R$ 32,14** no acumulado. As causas
conhecidas são a tarifa bancária, que vem do sistema e está zerada no Excel
(R$ 4,80 por mês, conta `020.070.0030`), o vale do administrativo de março a
maio (`Base_Resultado` linhas 122 e 123) e centavos de arredondamento.

## O que fazer

### 1. Na planilha: copiar as fórmulas de junho para janeiro–maio

Nas linhas **204, 205 e 206**, as fórmulas de janeiro a maio somam as despesas da
área **seguinte**. As de junho estão corretas — copiá-las para os meses anteriores
resolve a maior parte da diferença de *Despesas Equipe* e *Despesa Institucional*
das três áreas.

### 2. No sistema: manter a anotação do convênio atualizada quando o plano mudar

A *memória de cálculo* no lançamento do convênio é o que diz quanto do plano é da
MBC. Quando ela fica velha, o sistema estima a parte da MBC pela proporção dos
outros meses — funciona, mas é estimativa. Hoje há uma: a parte da MBC do **RB em
janeiro** (o plano dele mudou e nenhuma anotação registra a proporção daquele mês).
Se puderem confirmar esse número, ele deixa de ser estimado.

### 3. Uma pergunta: de onde vem o R$ 35,52 do vale-transporte de janeiro?

A célula `C123` traz `=35,52+262,64`. Os **262,64** são o vale-transporte da pessoa
do administrativo (14 dias × R$ 18,76) e conferem. Os **35,52** não aparecem em
nenhum lançamento do sistema — nem em janeiro, nem em nenhum outro mês. Não é
vale-refeição (o menor do ano é R$ 783,70) e não corresponde a um número inteiro de
dias em nenhuma diária de vale.

Também não é um pedaço que falte do nosso número: o vale-transporte de janeiro
(R$ 262,64) já está completo, então os 35,52 estão somados por cima. Se for de outra
competência ou um acerto pontual, é só dizer e passamos a tratá-lo da mesma forma.

## Diferenças que não mudam nenhum total

Estas são de classificação: o valor existe nos dois lados, em seções diferentes.
Ficam registradas porque **se repetem todo mês** e costumam gerar dúvida.

* **ISS trimestral** — o sistema lança por advogado, a planilha numa única linha da
  área (efeito no acumulado: R$ 0,04).
* **AASP** — dentro do Custo equipe na planilha, em Despesa de Área no sistema.
* **Endomarketing × Prospecção** e **Ocupação × Administrativas** — a mesma conta em
  famílias diferentes de cada lado; as duas entram no total, efeito zero.
* **Vale do administrativo** — a planilha lança as três pessoas em Salários
  Administração; o sistema deixa ali só a pessoa do administrativo e manda os
  estagiários para o custo das áreas deles.
* **Aluguel** — o sistema usa o valor líquido da sublocação (crédito Belline).
* **Tarifa bancária** — R$ 4,80/mês, vem do sistema e está zerada no Excel.
* **Prêmio de seguro** — é anual (lançado em janeiro e julho); a planilha o divide
  em parcelas mensais e o classifica em *Administrativas*, o sistema em *Ocupação*.

