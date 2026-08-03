# Diferenças entre a planilha e o sistema — Janeiro a Junho de 2026

> Gerado por `backend/scripts/build_diferencas_doc.py` a partir dos dados ao vivo
> do sistema e da planilha `Fechamento MBC 06.2026.xlsx`. Cada diferença abaixo já foi
> diagnosticada e tem causa identificada — **não é uma lista de erros**.

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
| Arbitragem · Despesas Equipe | +R$ 1.058,47 | R$ 0,00 ✓ | +R$ 973,23 | +R$ 1.524,30 | +R$ 68,00 | R$ 0,00 ✓ | **+R$ 3.624,00** |
| Econômico · Despesa Institucional | -R$ 319,35 | -R$ 258,14 | -R$ 1.049,63 | -R$ 653,67 | -R$ 1.101,62 | +R$ 1,84 | **-R$ 3.380,57** |
| Contencioso · Custo equipe | -R$ 97,70 | -R$ 163,06 | +R$ 1.226,79 | +R$ 937,26 | +R$ 1.236,90 | R$ 0,00 ✓ | **+R$ 3.140,19** |
| Contencioso · Despesas Equipe | -R$ 718,70 | +R$ 217,40 | R$ 0,00 ✓ | -R$ 302,20 | -R$ 1.358,73 | -R$ 0,01 | **-R$ 2.162,24** |
| Arbitragem · Custo equipe | +R$ 0,96 | +R$ 1.911,95 | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | **+R$ 1.912,91** |
| Contencioso · Despesa Institucional | +R$ 1.055,66 | +R$ 890,62 | -R$ 1.493,80 | -R$ 1.402,60 | -R$ 485,54 | +R$ 1,72 | **-R$ 1.433,94** |
| Arbitragem · Resultado Bruto | -R$ 1.988,39 | -R$ 3.477,60 | +R$ 404,19 | -R$ 186,56 | +R$ 709,62 | -R$ 1,24 | **-R$ 4.539,98** |
| Despesas Indiretas | +R$ 1.533,77 | +R$ 1.249,19 | -R$ 2.947,69 | -R$ 2.070,03 | -R$ 2.151,43 | +R$ 4,80 | **-R$ 4.381,39** |
| Custos Diretos | -R$ 3.156,84 | -R$ 1.267,37 | +R$ 3.652,42 | +R$ 3.708,24 | +R$ 1.312,50 | R$ 0,00 ✓ | **+R$ 4.248,95** |
| Econômico · Resultado Bruto | +R$ 3.851,41 | +R$ 4.440,74 | -R$ 1.376,07 | -R$ 2.219,25 | -R$ 479,14 | -R$ 2,14 | **+R$ 4.215,55** |

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
   (+1.911,95) e é a única diferença que ainda depende de uma definição de vocês.

Uma observação que vale para ler todas as tabelas: **Resultado Bruto não tem**
**causa própria** — nas 18 células (3 áreas × 6 meses) a diferença dele é igual à
soma das diferenças das linhas que o compõem, com erro máximo de R$ 0,01.

## Detalhe, linha por linha

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

### Econômico · Despesa Institucional

Diferença no acumulado: **-R$ 3.380,57**

| Mês | Célula na planilha | Planilha | Sistema | Diferença |
|---|---|---:|---:|---:|
| Janeiro | `C60` | R$ 34.776,07 | R$ 34.456,72 | -R$ 319,35 |
| Fevereiro | `G60` | R$ 31.601,96 | R$ 31.343,82 | -R$ 258,14 |
| Março | `K60` | R$ 35.999,71 | R$ 34.950,08 | -R$ 1.049,63 |
| Abril | `O60` | R$ 38.228,85 | R$ 37.575,18 | -R$ 653,67 |
| Maio | `S60` | R$ 38.094,71 | R$ 36.993,09 | -R$ 1.101,62 |
| Junho | `W60` | R$ 34.770,11 | R$ 34.771,95 | +R$ 1,84 |
| **Acumulado** | — | **R$ 213.471,41** | **R$ 210.090,84** | **-R$ 3.380,57** |

Na planilha: aba **Areas Sintetico atualizado**, linha **60**.

**Por quê:** Mesma origem do Contencioso: é o POOL institucional rateado, e a parte da participação por área soma zero. Ver a explicação em *Contencioso · Despesa Institucional*.

**Onde conferir o detalhe:** Planilha, linha **207** (`=198−203`) para o POOL, e linhas **5 / 30 / 60** para o custo de equipe de cada área. Rode `python -m scripts.audit_desp_inst_rateio`.

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

**Por quê:** Convênio médico de um advogado da Arbitragem em **fevereiro**. O memo do sistema em janeiro e fevereiro declara uma base de plano diferente da de março a junho, e é internamente consistente nessa base (`1.795,86 - 1.192,36 (Parte MBC) = 603,50` para outro advogado, mesma mecânica). A planilha repete a constante de março nos seis meses, ou seja, em jan/fev ela não segue o próprio memo do sistema.

**Onde conferir o detalhe:** Base_Resultado linha 69; conta `030.010.0110`.

**O que precisamos de vocês:** Uma definição: em janeiro e fevereiro vale o valor do memo do sistema ou a constante que está na planilha? É a maior diferença de custo de equipe do acumulado.

### Contencioso · Despesa Institucional

Diferença no acumulado: **-R$ 1.433,94**

| Mês | Célula na planilha | Planilha | Sistema | Diferença |
|---|---|---:|---:|---:|
| Janeiro | `C42` | R$ 33.821,38 | R$ 34.877,04 | +R$ 1.055,66 |
| Fevereiro | `G42` | R$ 30.609,71 | R$ 31.500,33 | +R$ 890,62 |
| Março | `K42` | R$ 34.482,81 | R$ 32.989,01 | -R$ 1.493,80 |
| Abril | `O42` | R$ 36.400,45 | R$ 34.997,85 | -R$ 1.402,60 |
| Maio | `S42` | R$ 35.555,40 | R$ 35.069,86 | -R$ 485,54 |
| Junho | `W42` | R$ 32.562,84 | R$ 32.564,56 | +R$ 1,72 |
| **Acumulado** | — | **R$ 203.432,59** | **R$ 201.998,65** | **-R$ 1.433,94** |

Na planilha: aba **Areas Sintetico atualizado**, linha **42**.

**Por quê:** **Não é uma diferença da área — é a despesa institucional TOTAL, rateada.** A conta é `Despesa Institucional da área = POOL × (custo de equipe da área ÷ custo de equipe total)`, onde o POOL é a despesa institucional menos as despesas de área (planilha, linha 207 = 198 − 203). Decompondo a diferença nos dois fatores (`scripts/audit_desp_inst_rateio.py`, exato ao centavo nas 18 células): a parte que vem da **participação de cada área soma ZERO em todos os meses** — é só redistribuição entre elas — e **toda a diferença de dinheiro vem do POOL** (Jan–Jun: −5.811,73). Ou seja: para explicar esta linha, olhe a linha *Despesas Indiretas* do institucional. **Junho prova o mecanismo:** o POOL difere exatamente **R$ 4,80** (a tarifa bancária que a planilha zera), a participação não muda nada, e por isso as três áreas ficam em centavos (1,72 / 1,84 / 1,24).

**Onde conferir o detalhe:** Planilha, linha **207** (`=198−203`) para o POOL, e linhas **5 / 30 / 60** para o custo de equipe de cada área. Rode `python -m scripts.audit_desp_inst_rateio`.

### Arbitragem · Resultado Bruto

Diferença no acumulado: **-R$ 4.539,98**

| Mês | Célula na planilha | Planilha | Sistema | Diferença |
|---|---|---:|---:|---:|
| Janeiro | `C79` | R$ 42.503,77 | R$ 40.515,38 | -R$ 1.988,39 |
| Fevereiro | `G79` | -R$ 26.698,68 | -R$ 30.176,28 | -R$ 3.477,60 |
| Março | `K79` | R$ 37.249,72 | R$ 37.653,91 | +R$ 404,19 |
| Abril | `O79` | -R$ 80.776,26 | -R$ 80.962,82 | -R$ 186,56 |
| Maio | `S79` | -R$ 39.808,95 | -R$ 39.099,33 | +R$ 709,62 |
| Junho | `W79` | R$ 13.253,22 | R$ 13.251,98 | -R$ 1,24 |
| **Acumulado** | — | **-R$ 54.277,18** | **-R$ 58.817,16** | **-R$ 4.539,98** |

Na planilha: aba **Areas Sintetico atualizado**, linha **79**.

**Por quê:** **Não é uma diferença própria — é a soma das linhas acima.** Verificado nas 18 células (3 áreas × 6 meses): a diferença do Resultado Bruto é igual a `Δreceita − Δcusto de equipe − Δcomissão − Δdespesas equipe − Δdespesa institucional`, com erro máximo de R$ 0,01. Então não há nada a explicar aqui que não esteja explicado nas linhas que o compõem.

**Onde conferir o detalhe:** Some as linhas acima da própria área na planilha (linhas 39 a 42 do Contencioso, 57 a 60 do Econômico, 75 a 78 da Arbitragem).

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
* **Março**: um curso de Arbitragem (−815,49) que a planilha lança como institucional e que, sendo de uma área, vai para Despesas de Área; e Informática −237,60, que é `7.744,12 − 7.506,52` na conta `040.040.0030` (a planilha usou o valor bruto, nós usamos o líquido, que é a regra confirmada e faz 10 de 10 famílias baterem em maio).

**Onde conferir o detalhe:** Planilha: linhas **122 e 123** (vale ADM), **86** (aluguel), **124** (tarifa/administrativas), **128–131** (Associações), **158** (Gestão do Conhecimento), **180** (Informática). O total da linha é a **198**.

### Custos Diretos

Diferença no acumulado: **+R$ 4.248,95**

| Mês | Célula na planilha | Planilha | Sistema | Diferença |
|---|---|---:|---:|---:|
| Janeiro | `C6` | R$ 211.242,68 | R$ 208.085,84 | -R$ 3.156,84 |
| Fevereiro | `G6` | R$ 218.453,74 | R$ 217.186,37 | -R$ 1.267,37 |
| Março | `K6` | R$ 198.079,41 | R$ 201.731,83 | +R$ 3.652,42 |
| Abril | `O6` | R$ 209.572,83 | R$ 213.281,07 | +R$ 3.708,24 |
| Maio | `S6` | R$ 210.089,46 | R$ 211.401,96 | +R$ 1.312,50 |
| Junho | `W6` | R$ 210.781,04 | R$ 210.781,04 | R$ 0,00 ✓ |
| **Acumulado** | — | **R$ 1.258.219,16** | **R$ 1.262.468,11** | **+R$ 4.248,95** |

Na planilha: aba **Areas Sintetico atualizado**, linha **6**.

**Por quê:** É a soma dos custos de equipe das três áreas, então reflete as mesmas causas já descritas por área (vale dos advogados, ISS trimestral, AASP e o convênio de fevereiro).

**Onde conferir o detalhe:** Ver as três linhas de Custo equipe por área.

### Econômico · Resultado Bruto

Diferença no acumulado: **+R$ 4.215,55**

| Mês | Célula na planilha | Planilha | Sistema | Diferença |
|---|---|---:|---:|---:|
| Janeiro | `C61` | -R$ 50.457,07 | -R$ 46.605,66 | +R$ 3.851,41 |
| Fevereiro | `G61` | R$ 4.451,92 | R$ 8.892,66 | +R$ 4.440,74 |
| Março | `K61` | R$ 229.714,00 | R$ 228.337,93 | -R$ 1.376,07 |
| Abril | `O61` | R$ 40.402,75 | R$ 38.183,50 | -R$ 2.219,25 |
| Maio | `S61` | R$ 44.916,89 | R$ 44.437,75 | -R$ 479,14 |
| Junho | `W61` | -R$ 12.926,08 | -R$ 12.928,22 | -R$ 2,14 |
| **Acumulado** | — | **R$ 256.102,41** | **R$ 260.317,96** | **+R$ 4.215,55** |

Na planilha: aba **Areas Sintetico atualizado**, linha **61**.

**Por quê:** **Não é uma diferença própria — é a soma das linhas acima.** Verificado nas 18 células (3 áreas × 6 meses): a diferença do Resultado Bruto é igual a `Δreceita − Δcusto de equipe − Δcomissão − Δdespesas equipe − Δdespesa institucional`, com erro máximo de R$ 0,01. Então não há nada a explicar aqui que não esteja explicado nas linhas que o compõem.

**Onde conferir o detalhe:** Some as linhas acima da própria área na planilha (linhas 39 a 42 do Contencioso, 57 a 60 do Econômico, 75 a 78 da Arbitragem).

## Diferenças menores

| Linha | Jan | Fev | Mar | Abr | Mai | Jun | Acumulado |
|---|---:|---:|---:|---:|---:|---:|---:|
| Arbitragem · Despesa Institucional | +R$ 929,30 | +R$ 1.566,07 | -R$ 1.377,49 | -R$ 1.338,07 | -R$ 778,27 | +R$ 1,24 | **-R$ 997,22** |
| Econômico · Custo equipe | -R$ 3.060,10 | -R$ 3.016,26 | +R$ 2.425,63 | +R$ 2.770,99 | +R$ 75,61 | +R$ 0,01 | **-R$ 804,12** |
| Contencioso · Resultado Bruto | -R$ 238,91 | -R$ 945,34 | +R$ 267,20 | +R$ 767,10 | +R$ 607,09 | -R$ 1,85 | **+R$ 455,29** |
| Resultado Líquido | +R$ 1.623,07 | +R$ 18,18 | -R$ 704,73 | -R$ 1.638,21 | +R$ 838,79 | -R$ 5,17 | **+R$ 131,93** |
| Resultado Bruto | +R$ 1.623,07 | +R$ 18,18 | -R$ 704,73 | -R$ 1.638,21 | +R$ 838,77 | -R$ 5,24 | **+R$ 131,84** |
| Econômico · Despesas Equipe | -R$ 471,62 | -R$ 1.166,75 | R$ 0,00 ✓ | +R$ 102,20 | +R$ 1.504,72 | R$ 0,00 ✓ | **-R$ 31,45** |
| Receita | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | -R$ 0,16 | -R$ 0,44 | **-R$ 0,60** |
| Impostos | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | -R$ 0,02 | -R$ 0,07 | **-R$ 0,09** |

Somadas: **-R$ 1.114,42** no acumulado. As causas
conhecidas são a tarifa bancária, que vem do sistema e está zerada no Excel
(R$ 4,80 por mês, conta `020.070.0030`), o vale do administrativo de março a
maio (`Base_Resultado` linhas 122 e 123) e centavos de arredondamento.

## O que precisamos de vocês, em ordem

1. **Convênio médico de janeiro e fevereiro** (EHF e RB). O memo do sistema nesses
   dois meses declara uma base de plano diferente da de março a junho, e a
   planilha usa a constante de março nos seis meses. Qual vale para jan/fev?
   Conferir em `Base_Resultado Mensal_V2`, linhas 44 e 48, colunas C e D.
2. **Fórmulas das linhas 204/205/206** de janeiro a maio: podem ser copiadas de
   junho, que já está correto? Conferir em `Base_Resultado Mensal_V2`, linhas 204
   a 206, colunas C a G.
3. **Janeiro, vale-transporte:** a célula `C123` traz `=35,52+262,64`. Os 262,64
   são o lançamento do sistema; de onde vêm os 35,52?
4. **Lançamentos avulsos de janeiro e fevereiro:** `Base_Resultado Mensal_V2`
   linhas 34, 35, 43, 47, 51 e 54, colunas C e D. São de outra competência ou
   ajustes manuais? Se tiverem origem no sistema, passamos a considerá-los.
5. **Convênio médico da linha 69** (`C69` tem 1.911,45 e `D69` está vazia):
   deveria continuar em fevereiro, como está no sistema, ou foi encerrado em
   janeiro?

