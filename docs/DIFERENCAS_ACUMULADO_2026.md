# Diferenças entre a planilha e o sistema — Janeiro a Junho de 2026

> Gerado por `backend/scripts/build_diferencas_doc.py` a partir dos dados ao vivo
> do sistema e da planilha `Fechamento MBC 06.2026.xlsx`. Cada diferença abaixo já foi
> diagnosticada e tem causa identificada — **não é uma lista de erros**.

**Período:** janeiro a junho de 2026 — é até onde a planilha de referência
vai. O sistema já tem julho e agosto, mas não há coluna correspondente na
planilha para comparar, então eles ficam fora deste documento.

**Dados do sistema:** extraídos em 04/08/2026.

## Como conferir

Cada diferença aparece **mês a mês**, com a **célula exata da planilha** ao lado.
Para checar qualquer número: abra a planilha, vá na aba e na célula indicada, e
compare com a coluna *Sistema*.

As abas usadas são duas:

* **`Areas Sintetico atualizado`** — os totais por linha. O Realizado de cada mês
  fica numa coluna diferente: **Jan = coluna C**, **Fev = coluna G**, **Mar = coluna K**, **Abr = coluna O**, **Mai = coluna S**, **Jun = coluna W**.
* **`Base_Resultado Mensal_V2`** — o detalhe que forma esses totais. Aqui os meses
  são colunas seguidas: **Jan = C**, **Fev = D**, **Mar = E**, **Abr = F**, **Mai = G**, **Jun = H**.

Só detalhamos as diferenças de **R$ 1.000,00 ou mais** no acumulado; as
menores estão listadas no fim, também mês a mês.

## O que NÃO difere: receita, impostos e amortização

| Linha | Jan | Fev | Mar | Abr | Mai | Jun | Acumulado |
|---|---:|---:|---:|---:|---:|---:|---:|
| Receita | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | -R$ 0,16 | -R$ 0,44 | **-R$ 0,60** |
| Impostos | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | -R$ 0,02 | -R$ 0,07 | **-R$ 0,09** |
| Amortização | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | **R$ 0,00** |

**A receita bate em todos os meses** — as diferenças acima são de centavos de
arredondamento (a planilha arredonda o recebimento de maio e junho para reais
inteiros). Impostos e amortização acompanham. **Toda diferença relevante está em**
***despesa*** — é para lá que o resto do documento olha.

## Resumo: onde estão as diferenças

Diferença = Sistema − Planilha, por mês.

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

Quatro causas explicam tudo, e cada uma foi medida — não é suposição:

1. **Despesa Institucional por área não é um problema por área: é o POOL**
   **institucional rateado.** Separando a diferença nos dois fatores da conta
   (POOL × participação de cada área), a parte da *participação* **soma zero em**
   **todos os meses** — é só redistribuição — e todo o dinheiro vem do POOL
   (Jan–Jun −5.811,73). Para explicar essas três linhas, olhe *Despesas
   Indiretas*. Junho prova: POOL difere R$ 4,80 (a tarifa bancária) e as três
   áreas ficam em 1,72 / 1,84 / 1,24.
2. **A fórmula das linhas 204/205/206 lê as linhas da área SEGUINTE, de janeiro**
   **a maio** — conferido nos rótulos, não deduzido. Recalculando com a fórmula
   de junho, o erro cai **66%** e as células que batem vão de 4 para 11 de 18.
   É a causa que mais pesa em Despesas Equipe.
3. **O vale dos advogados no custo de equipe** — regra confirmada por vocês
   (sempre incluir). Em junho o Custo equipe das três áreas fecha (0,00 no
   Contencioso e na Arbitragem, 0,01 no Econômico), porque a planilha passou a
   incluir o vale a partir desse mês.
4. **O convênio médico de fevereiro na Arbitragem** — aparece só em fevereiro
   (+1.911,95), e **a própria planilha responde**: em fevereiro ela mantém a
   distribuição e o pró-labore desse advogado e zera só o convênio. Quem recebe
   distribuição está na folha, então o plano é custo real. Não é dúvida.

Uma observação que vale para ler todas as tabelas: **Resultado Bruto não tem**
**causa própria** — nas 18 células (3 áreas × 6 meses) a diferença dele é igual à
soma das diferenças das linhas que o compõem, com erro máximo de R$ 0,01.

**O que mudou em relação à versão anterior deste documento.** O sistema passou a
calcular sozinho a parte MBC do convênio quando a anotação do lançamento está
desatualizada (explicado em *Econômico · Custo equipe*). Com isso o Resultado
Bruto acumulado saiu de −R$ 7.640,50 para **−R$ 5.003,04**, e o Resultado Bruto do
Econômico de −R$ 5.737,92 para **−R$ 2.367,52**. Fevereiro do Econômico, que era a
maior distorção, foi de +R$ 1.405,83 para −R$ 53,85.

⚠ **Uma ressalva de leitura, que vale sempre:** um total que fecha porque dois
erros se anulam **não é um número validado**. Já aconteceu aqui: numa versão
anterior as três áreas de fevereiro somavam −1.267,37 e pareciam próximas, mas era
−3.016,26 do Econômico anulando +1.911,95 da Arbitragem. Preferimos cada linha
certa a um total bonito — por isso mostramos mês a mês, e não só o acumulado.

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

**Por quê:** Três coisas, todas identificadas:

* **Convênio médico de janeiro e fevereiro — era um erro nosso, agora resolvido sem depender de ninguém.** A anotação (*memória de cálculo*) que o financeiro deixa no lançamento do convênio está **desatualizada** nesses dois meses: descreve um plano de 968,65 quando o valor lançado era 2.122,30. Não é um descuido isolado — o mesmo texto (*603,50 / 524,28*) aparece nos **doze meses de 2025** e segue até fevereiro de 2026, enquanto o plano lançado mudou duas vezes por baixo dele. Então não pedimos mais que a anotação seja corrigida: o sistema passou a **calcular a parte MBC sozinho**. Ele aprende, nos meses em que a anotação está correta, qual proporção do valor lançado cabe à MBC (a mesma em todos eles) e aplica essa proporção ao valor lançado *do próprio mês*. Fevereiro passou de +R$ 1.405,83 para −R$ 53,85 contra a planilha.
* **Vale dos advogados** — regra confirmada por vocês (sempre incluir); as colunas de janeiro a maio da planilha não incluem.
* **A estagiária do Direito Econômico**, que entra na planilha a partir de março e que nós reproduzimos ao centavo — é por causa dela que o sinal da diferença se inverte entre fevereiro e março.

⚠ **Uma estimativa nossa, em janeiro:** o plano do RB realmente mudou (2.355,73 em janeiro contra 3.427,58 de fevereiro em diante). A planilha repete 2.526,09 em todos os meses, ou seja não acompanha essa mudança; nós acompanhamos, mas como nenhum lugar registra qual era a parte MBC do RB em janeiro, aplicamos a mesma proporção dos outros meses. Esse número específico é uma estimativa, e é a maior parte da diferença de janeiro.

**Onde conferir o detalhe:** Planilha, linhas **44 e 48** (convênio de EHF e RB: a mesma constante nos seis meses) e **52** (estagiária). No sistema, a conta `030.010.0110` e a anotação do lançamento. O cálculo completo está em `scripts/audit_convenio_share.py`.

**O que precisamos de vocês:** **Nada.** Este item deixou de depender do financeiro em 04/08/2026. Se quiserem, vale confirmar qual era a parte MBC do **RB em janeiro** — é o único número aqui que estimamos — mas o fechamento não fica esperando por isso.

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

**Por quê:** **Causa provada, não suposta:** a fórmula das linhas 204/205/206 da planilha lê as linhas da área SEGUINTE, de janeiro a maio. Verificado nos rótulos: a fórmula do Contencioso soma *“Eventos e Happy hour - Direito Econômico”*, a do Econômico soma *“... - Institucional”*, e a da Arbitragem soma *“... - Contencioso”* — cinco famílias cada (Eventos/HH, Material Gráfico, Patrocínio, Refeições, Viagens). **Medido:** recalculando janeiro a maio com a fórmula de junho, o erro absoluto total cai de 10.216,31 para 3.494,78 (**−66%**) e as células que batem vão de **4 para 11 de 18**. As fórmulas de junho já estão corretas. Na Arbitragem o efeito é o maior dos três, porque as cinco linhas da própria área ficam fora da soma. O resíduo de janeiro (+1.204,47) é exatamente o **Canal de Arbitragem**, que a planilha daquele mês não somou.

**Onde conferir o detalhe:** Planilha, linhas **204 / 205 / 206** (colunas C a G) e as linhas 125–161 que elas somam. Rode `python -m scripts.audit_despesas_area` para ver a recomposição.

**O que precisamos de vocês:** Mesma confirmação das fórmulas 204/205/206.

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

**Por quê:** Vale-refeição e vale-transporte dos advogados. A regra confirmada por vocês é sempre incluir o vale no custo da equipe da área; as colunas de janeiro a maio da planilha não o incluem (as de junho sim, e junho fecha exatamente). Somam-se a isso duas diferenças que não mudam nenhum total: o ISS trimestral, que o sistema lança por advogado e a planilha digita numa única linha da área, e a AASP, que a planilha lança dentro do custo de equipe e o sistema classifica como Despesa de Área.

**Onde conferir o detalhe:** Base_Resultado linhas 26/27 (Vale), 25/54/79 (ISS Trimestral) e 9/18/36 (AASP). Fechamento por pessoa e por conta: **resíduo 0,00 nas 18 células** (3 áreas × 6 meses), conferido por `scripts/reconcile_custo_equipe.py`.

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

**Por quê:** **Não é uma diferença da área — é a despesa institucional TOTAL, rateada.** A conta é `Despesa Institucional da área = POOL × (custo de equipe da área ÷ custo de equipe total)`, onde o POOL é a despesa institucional menos as despesas de área (planilha, linha 207 = 198 − 203). Decompondo a diferença nos dois fatores (`scripts/audit_desp_inst_rateio.py`, exato ao centavo nas 18 células): a parte que vem da **participação de cada área soma ZERO em todos os meses** — é só redistribuição entre elas — e **toda a diferença de dinheiro vem do POOL** (Jan–Jun: −5.811,73). Ou seja: para explicar esta linha, olhe a linha *Despesas Indiretas* do institucional. **Junho prova o mecanismo:** o POOL difere exatamente **R$ 4,80** (a tarifa bancária que a planilha zera), a participação não muda nada, e por isso as três áreas ficam em centavos (1,72 / 1,84 / 1,24).

**Onde conferir o detalhe:** Planilha, linha **207** (`=198−203`) para o POOL, e linhas **5 / 30 / 60** para o custo de equipe de cada área. Rode `python -m scripts.audit_desp_inst_rateio`.

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

**Por quê:** **Causa provada, não suposta:** a fórmula das linhas 204/205/206 da planilha lê as linhas da área SEGUINTE, de janeiro a maio. Verificado nos rótulos: a fórmula do Contencioso soma *“Eventos e Happy hour - Direito Econômico”*, a do Econômico soma *“... - Institucional”*, e a da Arbitragem soma *“... - Contencioso”* — cinco famílias cada (Eventos/HH, Material Gráfico, Patrocínio, Refeições, Viagens). **Medido:** recalculando janeiro a maio com a fórmula de junho, o erro absoluto total cai de 10.216,31 para 3.494,78 (**−66%**) e as células que batem vão de **4 para 11 de 18**. As fórmulas de junho já estão corretas. O que sobra depois disso é **janeiro** e é conhecido: a planilha de janeiro não somou a AASP (195,40) nem o Canal de Arbitragem (1.204,47) — lançamentos reais que existem no sistema (o Canal de Arbitragem é exatamente o resíduo da Arbitragem). E as duas fatias de Associações: a planilha divide 700,10 para o Contencioso (linha 129) e 700,10 para o Econômico (linha 130), enquanto o sistema marca as duas no centro de custo do Econômico — por isso o nosso Econômico lê 1.400,19. Isso é o critério que a Renata já definiu: alocar pelo rótulo / centro de custo.

**Onde conferir o detalhe:** Planilha, linhas **204 / 205 / 206** (colunas C a G) e as linhas 125–161 que elas somam. Rode `python -m scripts.audit_despesas_area` para ver a recomposição.

**O que precisamos de vocês:** Confirmar se as fórmulas das linhas 204/205/206 de janeiro a maio podem ser copiadas de junho, que já está correto.

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

**Por quê:** Mesma origem do Contencioso: é o POOL institucional rateado, e a parte da participação por área soma zero. Ver a explicação em *Contencioso · Despesa Institucional*.

**Onde conferir o detalhe:** Planilha, linha **207** (`=198−203`) para o POOL, e linhas **5 / 30 / 60** para o custo de equipe de cada área. Rode `python -m scripts.audit_desp_inst_rateio`.

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

**Por quê:** Convênio médico de um advogado (JGS) em **fevereiro**, e aqui a própria planilha responde: em fevereiro ela mantém a **distribuição mensal (9.379,00, linha 70)** e o **pró-labore (1.621,00, linha 71)** desse advogado, mas deixa o **convênio (linha 69) em branco**. Quem continua recebendo distribuição e pró-labore está na folha naquele mês, então o plano de saúde é um custo real — e o sistema o tem lançado (1.911,95). A partir de março as três linhas dele ficam vazias nos dois lados (ele sai) e a Arbitragem passa a bater em 0,00. Em janeiro a diferença é de 50 centavos (1.911,95 × 1.911,45). **É uma omissão da coluna de fevereiro da planilha, não uma dúvida.**

**Onde conferir o detalhe:** Planilha, linhas **69, 70 e 71**, coluna D (fevereiro): as duas últimas têm valor, a primeira está vazia.

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

**Por quê:** Mesma origem do Contencioso: POOL institucional rateado. Ver a explicação em *Contencioso · Despesa Institucional*.

**Onde conferir o detalhe:** Planilha, linha **207** (`=198−203`) para o POOL, e linhas **5 / 30 / 60** para o custo de equipe de cada área. Rode `python -m scripts.audit_desp_inst_rateio`.

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

**Por quê:** É a soma dos custos de equipe das três áreas, então reflete as mesmas causas já descritas por área (vale dos advogados, ISS trimestral, AASP e o convênio de fevereiro).

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

**Por quê:** Esta é a linha que **explica também a Despesa Institucional das três áreas** (ela é rateada a partir daqui). Decompondo por família de despesa, as partes somam **exatamente** a diferença de cada mês — são componentes do total, então não sobra resíduo:

* **Vale do administrativo** (março −2.199,08 · abril −2.199,20 · maio −2.280,60): a planilha lançou o valor cheio da conta transitória, com as três pessoas, em Salários Administração; nós lançamos ali só a parte da pessoa do administrativo e mandamos os dois estagiários para o custo de equipe das áreas deles. Em janeiro, fevereiro e junho a planilha fez o mesmo e esses meses batem. Vocês já avaliaram que não vale corrigir.
* **Aluguel** (abril e maio, +129,17 cada): o sistema usa o aluguel líquido da sublocação (crédito Belline). A Renata já autorizou: *“assumam que o banco está correto”*.
* **Tarifa bancária** (+4,80/mês): vem do sistema e está zerada no Excel. É a única diferença que sobra em junho.
* **Trocas de família que não mudam o total** (Endomarketing ↔ Investimentos em Prospecção, Ocupação ↔ Administrativas): a mesma conta aparece em famílias diferentes nos dois lados, mas as duas entram no total da linha 198 — o efeito no número final é **zero**. Em janeiro, por exemplo, os nossos 1.317,71 de Endomarketing são os mesmos 1.317,71 que a planilha põe em Investimentos em Prospecção.
* **Janeiro, Associações** (+1.399,87): a planilha não somou a AASP (195,40) nem o Canal de Arbitragem (1.204,47) — lançamentos reais do sistema.
* **Janeiro, seguro (+2.539,84): é um prêmio ANUAL, não mensal.** A conta `020.060.0040` lança **2.722,55** em janeiro (e de novo em julho), enquanto a planilha digita **182,71** todo mês. A diferença `2.722,55 − 182,71` é exatamente a diferença de Ocupação de janeiro. E não há dinheiro faltando em lugar nenhum: a planilha lança esse mesmo prêmio em *Administrativas*, linha 133 (*Seguro de Responsabilidade Civil*), e nós em Ocupação — somando as duas famílias, a diferença de janeiro cai de ±3.788 para os 1.399,87 das Associações acima.
* **Março, vale da estagiária (+543,22):** um pagamento de benefícios feito **fora** da conta transitória — `020.080.0050` Vale Refeição 507,10 + `020.080.0060` Vale Transporte 36,12, com o nome dela no histórico. É a peça que faltava para o resíduo de Salários Administração fechar em **0,00** em março, abril, maio e junho.
* **Duas contas que a planilha simplesmente não tem uma linha para** — o mesmo caso das Associações: janeiro `020.050.0070` **IR Fonte - ADM 169,52** e fevereiro `020.050.0160` **Relatórios trabalhistas - e-Social 1.032,35**. Lançamentos reais, únicos, ausentes do Excel. São o único resíduo que sobra em Salários Administração depois de tudo o mais.
* **Março**: um curso de Arbitragem (−815,49) que a planilha lança como institucional e que, sendo de uma área, vai para Despesas de Área; e Informática −237,60, que é `7.744,12 − 7.506,52` na conta `040.040.0030` (a planilha usou o valor bruto, nós usamos o líquido, que é a regra confirmada e faz 10 de 10 famílias baterem em maio).

**Onde conferir o detalhe:** Planilha: linhas **122 e 123** (vale ADM), **86** (aluguel), **124** (tarifa/administrativas), **128–131** (Associações), **133** (seguro), **158** (Gestão do Conhecimento), **180** (Informática). O total da linha é a **198**. A decomposição completa, família por família e mês por mês, está em `scripts/audit_despesas_indiretas.py` — **e ela fecha: depois de nomear cada item acima, não sobra nenhum centavo sem explicação.**

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

**Por quê:** **Não é uma diferença própria — é a soma das linhas acima.** Verificado nas 18 células (3 áreas × 6 meses): a diferença do Resultado Bruto é igual a `Δreceita − Δcusto de equipe − Δcomissão − Δdespesas equipe − Δdespesa institucional`, com erro máximo de R$ 0,01. Então não há nada a explicar aqui que não esteja explicado nas linhas que o compõem.

**Onde conferir o detalhe:** Some as linhas acima da própria área na planilha (linhas 39 a 42 do Contencioso, 57 a 60 do Econômico, 75 a 78 da Arbitragem).

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

**Por quê:** **Não é uma diferença própria — é a soma das linhas acima.** Verificado nas 18 células (3 áreas × 6 meses): a diferença do Resultado Bruto é igual a `Δreceita − Δcusto de equipe − Δcomissão − Δdespesas equipe − Δdespesa institucional`, com erro máximo de R$ 0,01. Então não há nada a explicar aqui que não esteja explicado nas linhas que o compõem.

**Onde conferir o detalhe:** Some as linhas acima da própria área na planilha (linhas 39 a 42 do Contencioso, 57 a 60 do Econômico, 75 a 78 da Arbitragem).

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

**Por quê:** **Não é uma diferença própria — é a soma das linhas acima.** Verificado nas 18 células (3 áreas × 6 meses): a diferença do Resultado Bruto é igual a `Δreceita − Δcusto de equipe − Δcomissão − Δdespesas equipe − Δdespesa institucional`, com erro máximo de R$ 0,01. Então não há nada a explicar aqui que não esteja explicado nas linhas que o compõem.

**Onde conferir o detalhe:** Some as linhas acima da própria área na planilha (linhas 39 a 42 do Contencioso, 57 a 60 do Econômico, 75 a 78 da Arbitragem).

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

## O que precisamos de vocês

**Uma coisa só, e é pequena.** Tudo o mais que estava em aberto foi respondido
pelos próprios dados.

Em particular, **as anotações do convênio de janeiro e fevereiro já não são
necessárias**. Nós pedíamos que fossem corrigidas; depois vimos que o mesmo texto
desatualizado (*603,50 / 524,28*) aparece nos doze meses de 2025 e segue até
fevereiro de 2026, enquanto o plano lançado mudou duas vezes. Ou seja: não era um
descuido de dois meses. O sistema passou a calcular a parte MBC sozinho, a partir
da proporção que ele observa nos meses em que a anotação está correta — então
essas anotações podem ficar como estão. (Detalhe no item do Econômico acima; a
única estimativa que sobrou é a parte MBC do **RB em janeiro**.)

### Um valor digitado no vale-transporte de janeiro: R$ 35,52

Duas células de vale-transporte têm uma soma digitada à mão. **Uma das duas nós
conseguimos explicar inteira; a outra tem um pedaço que falta.**

| Célula | Fórmula | Primeiro termo | Segundo termo |
|---|---|---|---|
| `E123` (março) | `=543,22+674` | ✅ VR 507,10 + VT 36,12 da estagiária | ✅ VT do mês das três pessoas (674,12) |
| `C123` (janeiro) | `=35,52+262,64` | ❓ **35,52 — não encontramos** | ✅ VT da pessoa do ADM (14 dias × 18,76) |

**Março está resolvido, e a intuição de que era "um VR mais um VT" estava certa:**
os 543,22 são um pagamento de benefícios da estagiária feito **fora** da conta
transitória — `020.080.0050` Vale Refeição **507,10** + `020.080.0060` Vale
Transporte **36,12**. Os dois lançamentos estão no sistema, com o nome dela no
histórico.

**Janeiro é o que falta.** Procuramos os 35,52 por todos os caminhos:

* Não é vale-refeição: o VR é R$ 46,10/dia e nunca fica abaixo de R$ 783,70 no
  mês — 35,52 é pequeno demais.
* Todo vale do ano é um número inteiro de dias × uma diária (46,10 no VR; 10,80,
  18,76 e 33,60 no VT, por pessoa, e a conta vem escrita no próprio histórico do
  lançamento). **35,52 não é** nenhuma dessas combinações.
* **Não existe em lançamento nenhum.** Alargamos o campo de histórico do sistema
  (de 60/80 para 300 caracteres) e re-extraímos os oito meses justamente para
  poder afirmar isso: com o texto completo, o histórico do vale de janeiro é
  literalmente `"Vale refeição"` e `"Vale transporte"`, sem conta nenhuma — e
  35,52 não aparece em campo algum de nenhum dos oito meses. Também não está no
  extrato de contas de maio nem no de junho.
* As contas de benefício da estagiária que explicam março (`020.080.*`) **não
  existem em janeiro** — naquele mês há exatamente quatro lançamentos de vale
  (VR e VT de duas pessoas), e nenhum é 35,52.

**E sabemos que não é um pedaço faltando do nosso número.** Como todo vale é um
número inteiro de dias, dá para conferir mês a mês:

| Mês | VR (dias) | VT (dias, ADM) | Diferença |
|---|---:|---:|---:|
| Janeiro | 18 | 14 | +4 |
| Fevereiro | 22 | 18 | +4 |
| Março | 20 | 17 | +3 |
| Abril | 20 | 16 | +4 |
| Maio | 17 | 14 | +3 |
| Junho | 22 | 17 | +5 |

A diferença entre dias de VR e de VT fica entre **+3 e +5 em todos os meses** — o
VR é pago por dia trabalhado e o VT só pelos dias em que a pessoa veio. Janeiro,
com 14 dias de VT, está no mesmo padrão. A hipótese mais tentadora era que os
35,52 fossem dois dias de VT que faltavam (2 × 18,76 = 37,52, e aí janeiro fecharia
em 16 dias) — mas com 16 dias a diferença cairia para **+2**, que não acontece em
mês nenhum. Ou seja: **o nosso 262,64 é o vale-transporte completo dela em**
**janeiro**, e os 35,52 são algo somado em cima de um valor que já estava certo.

**Uma coisa que ficou clara em 04/08:** decompondo as Despesas Indiretas família
por família e mês por mês, todo o resto tem uma conta com nome e número atrás
(está em *Despesas Indiretas*, acima). Depois disso, **estes R$ 35,52 são o único**
**valor do acumulado inteiro que não conseguimos amarrar a um lançamento.** É
também a diferença exata entre o nosso vale do administrativo de janeiro
(1.092,44) e o da planilha (1.127,96) — ou seja, o número está isolado nessa
única célula, não espalhado por vários lugares.

**O que ajudaria:** de onde vêm esses R$ 35,52? Se for de outra competência ou um
acerto pontual, passamos a tratá-lo da mesma forma. Vale notar que é a **única**
coisa em todo o bloco de vale que continua sem explicação.

### E o que NÃO precisa mais de vocês

Ficam registrados aqui porque estavam na lista anterior:

* **Fórmulas das linhas 204/205/206** — continuam deslocadas de janeiro a maio e
  vale corrigir na planilha, mas não muda nada no sistema: é a planilha que lê a
  linha da área seguinte. Junho já está certo.
* **Convênio da linha 69 em fevereiro** — respondido pela própria planilha: ela
  mantém a distribuição e o pró-labore desse advogado em fevereiro e zera só o
  convênio. Ele estava na folha, o plano era custo real.
* **Lançamentos avulsos de janeiro e fevereiro** — conferimos um a um e eles
  **estão** no sistema, dentro do lançamento único de distribuição. Exemplo:
  Andrielly em fevereiro, planilha 9.822,92 (cinco linhas) × sistema 9.822,92 —
  bate em **R$ 0,00**. Era diferença de apresentação, não de valor.
* **Associações de janeiro** — a planilha não somou a AASP (195,40) nem o Canal
  de Arbitragem (1.204,47); os dois existem no sistema.
* **ISS trimestral** — o sistema lança por advogado e a planilha digita uma linha
  só da área. O total é idêntico; muda só a apresentação. Efeito no acumulado:
  **R$ 0,04**.
* **AASP** — a planilha lança dentro do Custo equipe e o sistema em Despesa de
  Área. O valor existe nos dois lados, em seções diferentes.
* **Endomarketing × Investimentos em Prospecção** e **Ocupação ×**
  **Administrativas** — a mesma conta em famílias diferentes de cada lado, mas as
  duas entram no total da linha 198, então o efeito é **zero**. Em janeiro, por
  exemplo, os nossos 1.317,71 de Endomarketing são os mesmos 1.317,71 que a
  planilha põe em Investimentos em Prospecção.
* **Vale ADM de março a maio** e **aluguel** — já respondidos por vocês.

Fechando: das seis perguntas que este documento tinha na versão anterior, **cinco**
foram respondidas pelos próprios dados. A que sobra é o R$ 35,52 — e, no valor, é
a menor de todas.

