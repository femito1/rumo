# Diferenças entre a planilha e o sistema — Janeiro a Junho de 2026

Comparação da planilha `Fechamento MBC 06.2026.xlsx` com os números do sistema, dados extraídos em 04/08/2026.

## O essencial

1. **A receita bate em todos os meses.** Toda diferença está em *despesa*.
2. No acumulado de janeiro a junho, o **Resultado Bruto** difere **-R$ 5.003,04** — sobre uma receita de mais de R$ 2 milhões.
3. **Cada centavo dessa diferença tem uma causa identificada**, listada abaixo. Ter causa não é o mesmo que bater — os dois lados continuam diferentes, e um dos valores (a parte MBC do convênio do RB em janeiro) é uma **estimativa nossa**, não um valor lançado.
4. **Junho fecha**: a única diferença de despesa é a tarifa bancária de R$ 4,80 (o resto são centavos de arredondamento do recebimento). É o mês em que a planilha já está com as fórmulas certas e inclui o vale — a referência de como os dois lados batem quando ambos estão corretos.

Cada diferença vem **mês a mês** com a célula da planilha ao lado (aba `Areas Sintetico atualizado`, colunas **Jan=C**, **Fev=G**, **Mar=K**, **Abr=O**, **Mai=S**, **Jun=W**). Detalhamos as que passam de **R$ 1.000,00** no acumulado **ou em qualquer mês isolado**; as menores estão no fim.

Nas **Despesas Indiretas** — a linha que puxa também a Despesa Institucional das três áreas — a diferença é aberta até a **conta**: quais despesas, com que valor, em cada mês, dos dois lados. Para conferir um número específico, as seções são *Quais despesas, mês a mês* e *Conta por conta, onde há diferença*.

Este documento é só para entendimento: descreve o que cada lado faz e por que os números diferem. Não propõe mudança em nenhum dos dois.

## O que NÃO difere

| Linha | Jan | Fev | Mar | Abr | Mai | Jun | Acumulado |
|---|---:|---:|---:|---:|---:|---:|---:|
| Receita | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | -R$ 0,16 | -R$ 0,44 | **-R$ 0,60** |
| Impostos | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | -R$ 0,02 | -R$ 0,07 | **-R$ 0,09** |
| Amortização | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | **R$ 0,00** |

Os centavos de maio e junho são arredondamento — a planilha arredonda o
recebimento para reais inteiros.

## As quatro causas

Todas as linhas citadas abaixo estão na aba `Base_Resultado Mensal_V2` da planilha,
que é o detalhe por trás dos totais da `Areas Sintetico atualizado`.

1. **Fórmula deslocada na planilha** (linhas 204/205/206, janeiro a maio). Cada
   uma dessas linhas soma as despesas de uma área; nas cinco últimas parcelas
   (*Eventos*, *Material Gráfico*, *Patrocínio*, *Refeições*, *Viagens*) a fórmula
   aponta uma linha adiante e pega a da área vizinha. Junho já está certo. Afeta
   *Despesas Equipe* e — por meio da linha 203 — também a *Despesa Institucional*
   das três áreas, mas **não** o total institucional da linha 198.
2. **Despesa Institucional por área é o total institucional dividido entre as**
   **áreas.** A divisão não cria nem apaga dinheiro; a diferença vem do total (ver
   *Despesas Indiretas*) e da causa 1, através da linha 203.
3. **O vale entra no custo da área, e a planilha varia de mês.** Nos advogados, as
   linhas 26/27 (Contencioso) e 56/57 (Econômico) trazem o vale em alguns meses e
   ficam zeradas em mar/abr/mai. No administrativo, as linhas 122/123 usam três
   bases diferentes ao longo dos seis meses. O sistema usa sempre a mesma regra.
4. **A anotação do convênio médico está velha em jan/fev.** A *memória de cálculo*
   no lançamento diz quanto do plano é da MBC; nesses dois meses ela descrevia um
   plano antigo (o mesmo texto vinha desde 2025, com o plano mudando duas vezes). O
   sistema não depende dela: calcula a parte da MBC pela proporção dos meses em que
   a anotação está correta. Por isso um valor — a parte da MBC do convênio do RB em
   janeiro — é **estimado**, e não lido de um lançamento.

*Um total que fecha porque dois erros se anulam não está validado — por isso tudo*
*aparece mês a mês, não só no acumulado. Uma linha entra no detalhe abaixo se*
*passar de R$ 1.000,00 no acumulado **ou** em qualquer mês isolado.*

## Resumo: onde estão as diferenças

Diferença = Sistema − Planilha, por mês. `✓` = bate.

| Linha | Jan | Fev | Mar | Abr | Mai | Jun | Acumulado |
|---|---:|---:|---:|---:|---:|---:|---:|
| Despesas Indiretas | +R$ 1.533,77 | +R$ 1.249,19 | -R$ 2.947,69 | -R$ 2.070,03 | -R$ 2.151,43 | +R$ 4,80 | **-R$ 4.381,39** |
| Econômico · Custo equipe | -R$ 887,63 | -R$ 53,85 | +R$ 2.425,63 | +R$ 2.770,99 | +R$ 75,61 | +R$ 0,01 | **+R$ 4.330,76** |
| Arbitragem · Despesas Equipe | +R$ 1.058,47 | R$ 0,00 ✓ | +R$ 973,23 | +R$ 1.524,30 | +R$ 68,00 | R$ 0,00 ✓ | **+R$ 3.624,00** |
| Contencioso · Custo equipe | -R$ 97,70 | -R$ 163,06 | +R$ 1.226,80 | +R$ 937,26 | +R$ 1.236,90 | R$ 0,00 ✓ | **+R$ 3.140,20** |
| Contencioso · Despesa Institucional | +R$ 695,30 | +R$ 463,83 | -R$ 1.493,80 | -R$ 1.402,60 | -R$ 485,54 | +R$ 1,72 | **-R$ 2.221,09** |
| Contencioso · Despesas Equipe | -R$ 718,70 | +R$ 217,40 | R$ 0,00 ✓ | -R$ 302,20 | -R$ 1.358,73 | -R$ 0,01 | **-R$ 2.162,24** |
| Econômico · Despesa Institucional | +R$ 345,15 | +R$ 525,55 | -R$ 1.049,63 | -R$ 653,67 | -R$ 1.101,62 | +R$ 1,84 | **-R$ 1.932,38** |
| Arbitragem · Custo equipe | +R$ 0,96 | +R$ 1.911,95 | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | **+R$ 1.912,91** |
| Arbitragem · Despesa Institucional | +R$ 625,16 | +R$ 1.209,16 | -R$ 1.377,49 | -R$ 1.338,07 | -R$ 778,27 | +R$ 1,24 | **-R$ 1.658,27** |
| Econômico · Despesas Equipe | -R$ 471,62 | -R$ 1.166,75 | R$ 0,00 ✓ | +R$ 102,20 | +R$ 1.504,72 | R$ 0,00 ✓ | **-R$ 31,45** |
| Custos Diretos | -R$ 984,37 | +R$ 1.695,04 | +R$ 3.652,42 | +R$ 3.708,24 | +R$ 1.312,50 | R$ 0,00 ✓ | **+R$ 9.383,83** |
| Resultado Bruto | -R$ 549,40 | -R$ 2.944,23 | -R$ 704,73 | -R$ 1.638,21 | +R$ 838,77 | -R$ 5,24 | **-R$ 5.003,04** |
| Resultado Líquido | -R$ 549,40 | -R$ 2.944,23 | -R$ 704,73 | -R$ 1.638,21 | +R$ 838,79 | -R$ 5,17 | **-R$ 5.002,95** |
| Arbitragem · Resultado Bruto | -R$ 1.684,25 | -R$ 3.120,69 | +R$ 404,19 | -R$ 186,56 | +R$ 709,62 | -R$ 1,24 | **-R$ 3.878,93** |
| Econômico · Resultado Bruto | +R$ 1.014,44 | +R$ 694,64 | -R$ 1.376,07 | -R$ 2.219,25 | -R$ 479,14 | -R$ 2,14 | **-R$ 2.367,52** |
| Contencioso · Resultado Bruto | +R$ 121,45 | -R$ 518,55 | +R$ 267,20 | +R$ 767,10 | +R$ 607,09 | -R$ 1,85 | **+R$ 1.242,44** |

## Detalhe, linha por linha

Cada tabela é uma linha da aba `Areas Sintetico atualizado`; a coluna *Célula* dá
o endereço exato para conferir.

### Despesas Indiretas — -R$ 4.381,39 no acumulado

| Mês | Célula | Planilha | Sistema | Diferença |
|---|---|---:|---:|---:|
| Janeiro | `C13` | R$ 100.181,41 | R$ 101.715,18 | +R$ 1.533,77 |
| Fevereiro | `G13` | R$ 95.047,39 | R$ 96.296,58 | +R$ 1.249,19 |
| Março | `K13` | R$ 101.968,90 | R$ 99.021,21 | -R$ 2.947,69 |
| Abril | `O13` | R$ 110.156,11 | R$ 108.086,08 | -R$ 2.070,03 |
| Maio | `S13` | R$ 105.511,43 | R$ 103.360,00 | -R$ 2.151,43 |
| Junho | `W13` | R$ 105.927,36 | R$ 105.932,16 | +R$ 4,80 |
| **Acumulado** | — | **R$ 618.792,60** | **R$ 614.411,21** | **-R$ 4.381,39** |

Esta linha também explica a maior parte da Despesa Institucional das três áreas (ela é rateada daqui). Somando família por família, as partes dão **exatamente** a diferença de cada mês — não sobra centavo. Por mês, o que a compõe:

* **Vale do administrativo** — a causa dominante em mar (−2.199,08), abr (−2.199,20) e mai (−2.280,60). A planilha usa uma base **diferente em cada mês** nas linhas 122/123: só a pessoa do administrativo em fev e jun, as três pessoas em abr, e nenhuma das duas regras em jan/mar/mai. Nós usamos sempre a mesma regra (só a pessoa do administrativo; os estagiários vão para as áreas deles), por isso jan/fev/jun batem e os outros não.
* **Janeiro (+1.533,77)**: são duas coisas somadas. As **Associações** (+1.399,87) — a planilha não somou a AASP (195,40) nem o Canal de Arbitragem (1.204,47), que existem no sistema — e o **IR Fonte ADM** (+169,52), uma conta sem linha na planilha; menos os 35,52 do vale-transporte (item no fim do documento) e 0,10 de arredondamento. O prêmio de seguro **não** entra nesta conta, embora apareça como +2.539,84 em *Ocupação*: ele é cancelado por −2.539,84 em *Administrativas* (item abaixo).
* **Fevereiro (+1.249,19)**: o **e-Social** (+1.032,35), outra conta sem linha na planilha, mais +217,11 de Administrativas.
* **Janeiro, seguro — o caso que mais gera dúvida.** *Ocupação* difere +2.539,84 em janeiro e **esse número não aparece em nenhuma linha de Ocupação**, de lado nenhum. O motivo: temos uma conta só, *Seguros* 2.722,55, e a planilha usa duas linhas em **famílias diferentes** — *Seguro Locação* (linha 91, em Ocupação) 182,71 **mais** *Seguro de Responsabilidade Civil* (linha 133, em **Administrativas**) 2.539,84. As duas somam exatamente os nossos 2.722,55. Como a linha 133 está em Administrativas, ela falta em Ocupação (+2.539,84) e sobra em Administrativas (−2.539,84): as duas se cancelam na linha 198 e o total não se move. É também por isso que o prêmio não entra na conta de janeiro acima. Na tabela *Conta por conta* isto está na coluna *Onde está o resto*.
* **Administrativas (linha 124), mês a mês.** É a família que mistura mais mecanismos, então vai inteira:
    * **Janeiro −1.139,97** = +1.399,87 de *Associações* (a planilha não somou a **AASP 195,40** nem o **Canal de Arbitragem 1.204,47**) **−2.539,84** do seguro do item acima, que a planilha tem aqui (linha 133) e nós em Ocupação.
    * **Fevereiro +217,40** = a **AASP**. Ela está dentro da nossa conta única de Associações, e a planilha deixou a linha 125 vazia neste mês.
    * **Março +37,39** = a **tarifa bancária** (linha 136, zerada na planilha).
    * **Abril −110,00** = a assinatura **Adobe** (linha 128). Ela existe no sistema todo mês, mas em *Informática* (conta 040.040.0030, histórico *"PPRO*Adobe R$110,00"*) — não em Administrativas.
    * **Maio 0,00** — bate.
    * **Junho +4,80** = só a **tarifa bancária**. A AASP de 217,40 aparece dos dois lados neste mês (a planilha em *Assinaturas*, linha 125; nós dentro de *Associações*), então se cancela.
* **Assinaturas e Associações são uma coisa só do nosso lado.** Temos duas contas (020.060.0010 e 020.060.0020) onde a planilha usa oito linhas (125–132), divididas por área. Por isso o que importa é o **par somado**, não cada linha: em junho, por exemplo, a planilha põe 10.340,35 em *Assinaturas — Arbitragem* (linha 127) e nós a mesma quantia em *Informática* — é a assinatura da plataforma de faturamento do cliente, a mesma reclassificação já conhecida.
* **Aluguel** (abr +19,17 e mai +129,17): usamos o aluguel líquido da sublocação (crédito Belline).
* **Tarifa bancária**: existe no sistema e está zerada na planilha (linha 136). Não é mensal — só mar (37,39) e jun (4,80) nos seis meses. Em junho é a **única** diferença que sobra.
* **Trocas de família** (Endomarketing ↔ Prospecção, Ocupação ↔ Administrativas): a mesma conta em famílias diferentes de cada lado, mas as duas entram no total — efeito **zero** (ver *Diferenças de classificação*).
* **Março, vale da estagiária** (+543,22): um pagamento de benefícios fora da conta transitória (Vale Refeição 507,10 + Vale Transporte 36,12, com o nome dela no histórico). É o que faz a família de Salários Administração fechar em 0,00 de março a junho, depois de tirado o vale.
* **Março**: um curso de Arbitragem (−815,49) que a planilha pôs em institucional e nós na área; e Informática −237,60 (a planilha usou o valor bruto, nós o líquido).

*Conferir:* Todas na aba `Base_Resultado Mensal_V2`: linhas **122/123** (vale ADM), **86** (aluguel), **128–131** (Associações), **133** (seguro), **136** (tarifa bancária, zerada), **158** (curso), **180** (Informática). O total é a linha **198** — e, depois de nomear cada item acima, ele fecha sem sobra.

#### Quais despesas, mês a mês

As dez famílias de despesa institucional, com a diferença de cada uma em cada mês.
Elas somam exatamente o total dos dois lados — a linha **198** na planilha e a
*Despesas* no sistema — então esta tabela é a diferença inteira, sem resto.

| Família (linha) | Jan | Fev | Mar | Abr | Mai | Jun | Acumulado |
|---|---:|---:|---:|---:|---:|---:|---:|
| Ocupação (r85) | +R$ 2.539,84 | -R$ 0,29 | R$ 0,00 ✓ | +R$ 129,17 | +R$ 129,17 | R$ 0,00 ✓ | **+R$ 2.797,89** |
| Telecomunicações (r92) | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | **R$ 0,00** |
| Despesas Gerais (r95) | -R$ 0,10 | R$ 0,00 ✓ | +R$ 105,00 | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | **+R$ 104,90** |
| Consultoria (r110) | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | **R$ 0,00** |
| Salários Administração (r116) | +R$ 134,00 | +R$ 1.032,35 | -R$ 2.199,08 | -R$ 2.199,20 | -R$ 2.280,60 | R$ 0,00 ✓ | **-R$ 5.512,53** |
| Administrativas (r124) | -R$ 1.139,97 | +R$ 217,40 | +R$ 37,39 | -R$ 110,00 | R$ 0,00 ✓ | +R$ 4,80 | **-R$ 990,38** |
| Investimentos em Prospecção (r137) | -R$ 1.317,71 | -R$ 1.166,75 | +R$ 162,09 | -R$ 200,00 | R$ 0,00 ✓ | R$ 0,00 ✓ | **-R$ 2.522,37** |
| Gestão do Conhecimento (r158) | R$ 0,00 ✓ | R$ 0,00 ✓ | -R$ 815,49 | +R$ 200,00 | R$ 0,00 ✓ | R$ 0,00 ✓ | **-R$ 615,49** |
| Endomarketing (r164) | +R$ 1.317,71 | +R$ 1.166,75 | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | **+R$ 2.484,46** |
| Informática (r180) | R$ 0,00 ✓ | -R$ 0,27 | -R$ 237,60 | +R$ 110,00 | R$ 0,00 ✓ | R$ 0,00 ✓ | **-R$ 127,87** |
| **Total** |  |  |  |  |  |  | **-R$ 4.381,39** |

Batem em todos os meses as famílias que não aparecem abaixo. As que diferem em
algum mês são *Ocupação*, *Despesas Gerais*, *Salários Administração*, *Administrativas*, *Investimentos em Prospecção*, *Gestão do Conhecimento*, *Endomarketing*, *Informática* — e para cada uma delas os lançamentos vêm a seguir.

#### Conta por conta, onde há diferença

Para cada família e mês que difere: as contas de cada lado, já **descontadas as que
batem**. Ou seja, o que está listado é exatamente o que explica aquela diferença —
nada mais. Quando um valor aparece só de um lado, é porque a conta existe só ali ou
está somada de outra forma (a planilha divide algumas contas por área, o sistema as
mantém unidas; o inverso também acontece).

A conta fecha em cada linha: **(soma do sistema) − (soma da planilha) = diferença**,
e os subtotais estão na tabela para que dê para conferir sem somar à mão.

A coluna **Onde está o resto** resolve o caso que confunde mais: quando o valor que
falta não está nesta família, e sim em **outra**, na mesma planilha. Aí a diferença
desta linha existe, mas é compensada em outro lugar — e sem essa coluna não havia
como encontrá-la.

**Ocupação** — linha 85 da planilha

| Mês | Só na planilha | Σ | Só no sistema | Σ | Batem | Diferença | Onde está o resto |
|---|---|---:|---|---:|---:|---:|---|
| Janeiro | r91 Seguro Locação · R$ 182,71 | R$ 182,71 | Seguros · R$ 2.722,55 | R$ 2.722,55 | 3 | +R$ 2.539,84 | Seguros R$ 2.722,55 = r91 Seguro Locação · R$ 182,71 + r133 Seguro de Responsabilidade Civil · R$ 2.539,84 (**Administrativas**) |
| Fevereiro | r91 Seguro Locação · R$ 183,00 | R$ 183,00 | Seguros · R$ 182,71 | R$ 182,71 | 4 | -R$ 0,29 | — |
| Abril | r86 Aluguel · R$ 23.137,56 | R$ 23.137,56 | Aluguel · R$ 23.266,73 | R$ 23.266,73 | 4 | +R$ 129,17 | — |
| Maio | r86 Aluguel · R$ 24.230,60 | R$ 24.230,60 | Aluguel · R$ 24.359,77 | R$ 24.359,77 | 4 | +R$ 129,17 | — |

**Despesas Gerais** — linha 95 da planilha

| Mês | Só na planilha | Σ | Só no sistema | Σ | Batem | Diferença | Onde está o resto |
|---|---|---:|---|---:|---:|---:|---|
| Janeiro | r102 Manutenção ar condicionado · R$ 919,76<br>r104 Manutenção do Jardim · R$ 836,00<br>r106 Material de Higiene e Copa · R$ 995,49 | R$ 2.751,25 | Material de Copa/Higiene · R$ 995,39<br>Manutenção do Escritório · R$ 1.755,76 | R$ 2.751,15 | 3 | -R$ 0,10 | — |
| Março | r102 Manutenção ar condicionado · R$ 919,76<br>r104 Manutenção do Jardim · R$ 919,60 | R$ 1.839,36 | Manutenção do Escritório · R$ 1.839,36<br>Estacionamento · R$ 105,00 | R$ 1.944,36 | 3 | +R$ 105,00 | — |

**Salários Administração** — linha 116 da planilha

| Mês | Só na planilha | Σ | Só no sistema | Σ | Batem | Diferença | Onde está o resto |
|---|---|---:|---|---:|---:|---:|---|
| Janeiro | r122 Vale Refeição- ADM · R$ 829,80<br>r123 Vale Transporte · R$ 298,16 | R$ 1.127,96 | IR Fonte - ADM · R$ 169,52<br>Vale Refeição/Transporte - ADM · R$ 1.092,44 | R$ 1.261,96 | 3 | +R$ 134,00 | — |
| Fevereiro | r122 Vale Refeição- ADM · R$ 1.014,20<br>r123 Vale Transporte · R$ 337,68 | R$ 1.351,88 | Relatórios trabalhistas - e-Social · R$ 1.032,35<br>Vale Refeição/Transporte - ADM · R$ 1.351,88 | R$ 2.384,23 | 2 | +R$ 1.032,35 | — |
| Março | r122 Vale Refeição- ADM · R$ 2.766,00<br>r123 Vale Transporte · R$ 1.217,22 | R$ 3.983,22 | Vale Refeição · R$ 507,10<br>Vale Transporte · R$ 36,12<br>Vale Refeição/Transporte - ADM · R$ 1.240,92 | R$ 1.784,14 | 2 | -R$ 2.199,08 | — |
| Abril | r122 Vale Refeição- ADM · R$ 2.766,00<br>r123 Vale Transporte · R$ 655,36 | R$ 3.421,36 | Vale Refeição/Transporte - ADM · R$ 1.222,16 | R$ 1.222,16 | 2 | -R$ 2.199,20 | — |
| Maio | r122 Vale Refeição- ADM · R$ 2.719,90<br>r123 Vale Transporte · R$ 607,04 | R$ 3.326,94 | Vale Refeição/Transporte - ADM · R$ 1.046,34 | R$ 1.046,34 | 3 | -R$ 2.280,60 | — |

**Administrativas** — linha 124 da planilha

| Mês | Só na planilha | Σ | Só no sistema | Σ | Batem | Diferença | Onde está o resto |
|---|---|---:|---|---:|---:|---:|---|
| Janeiro | r129 Associações - Contencioso ( ICC e IBRAC AASP) · R$ 700,10<br>r130 Associações - Direito Econômico (ICC, IBRAC) · R$ 700,10<br>r133 Seguro de Responsabilidade Civil · R$ 2.539,84 | R$ 3.940,04 | Associações · R$ 2.800,06 | R$ 2.800,06 | 1 | -R$ 1.139,97 ¹ | — |
| Fevereiro | r129 Associações - Contencioso ( ICC e IBRAC AASP) · R$ 2.129,32<br>r130 Associações - Direito Econômico (ICC, IBRAC) · R$ 2.129,32<br>r131 Associações - Arbitragem e Compliance (Canal de Arbitragem, ICC, CBAR) · R$ 2.633,69 | R$ 6.892,33 | Associações · R$ 7.109,73 | R$ 7.109,73 | 0 | +R$ 217,40 | — |
| Março | r129 Associações - Contencioso ( ICC e IBRAC AASP) · R$ 2.346,72<br>r130 Associações - Direito Econômico (ICC, IBRAC) · R$ 2.129,32<br>r131 Associações - Arbitragem e Compliance (Canal de Arbitragem, ICC, CBAR) · R$ 2.633,69 | R$ 7.109,73 | Associações · R$ 7.109,73<br>Tarifas e Taxas Bancárias · R$ 37,39 | R$ 7.147,12 | 0 | +R$ 37,39 | — |
| Abril | r128 Assinaturas - Institucional (ADOBE e Valor) · R$ 110,00<br>r129 Associações - Contencioso ( ICC e IBRAC AASP) · R$ 2.346,72<br>r130 Associações - Direito Econômico (ICC, IBRAC) · R$ 2.129,32<br>r131 Associações - Arbitragem e Compliance (Canal de Arbitragem, ICC, CBAR) · R$ 2.633,69 | R$ 7.219,73 | Associações · R$ 7.109,73 | R$ 7.109,73 | 1 | -R$ 110,00 | r128 R$ 110,00 → no sistema em **Informática**: dentro de `040.040.0030` · R$ 110,00 — *"PPRO*Adobe R$110,00 referente março 2026"* |
| Junho | r125 Assinaturas - Contencioso (AASP) · R$ 217,40<br>r129 Associações - Contencioso ( ICC e IBRAC AASP) · R$ 700,10<br>r130 Associações - Direito Econômico (ICC, IBRAC) · R$ 700,10<br>r131 Associações - Arbitragem e Compliance (Canal de Arbitragem, ICC, CBAR) · R$ 1.257,35 | R$ 2.874,95 | Associações · R$ 2.874,94<br>Tarifas e Taxas Bancárias · R$ 4,80 | R$ 2.879,74 | 1 | +R$ 4,80 ¹ | — |

**Investimentos em Prospecção** — linha 137 da planilha

| Mês | Só na planilha | Σ | Só no sistema | Σ | Batem | Diferença | Onde está o resto |
|---|---|---:|---|---:|---:|---:|---|
| Janeiro | r139 Eventos e Happy hour - Contencioso · R$ 146,00<br>r141 Eventos e Happy hour - Institucional · R$ 1.171,71 | R$ 1.317,71 | — | R$ 0,00 | 0 | -R$ 1.317,71 | r139 R$ 146,00 → no sistema em **Investimento em Prospecção**: dentro de `020.090.0040` · R$ 146,00 — *"DeLadoPão - Compra de 20 pães de queijo para a participação "* |
| Fevereiro | r141 Eventos e Happy hour - Institucional · R$ 1.166,75 | R$ 1.166,75 | — | R$ 0,00 | 0 | -R$ 1.166,75 | r141 R$ 1.166,75 → no sistema em **Endomarketing**: Eventos e Happy Hour · R$ 1.166,75 |
| Março | — | R$ 0,00 | Deslocamento e Transportes Prospecção · R$ 162,09 | R$ 162,09 | 1 | +R$ 162,09 | — |
| Abril | r140 Eventos e Happy hour - Direito Econômico · R$ 200,00<br>r150 Refeições - Arbitragem e Compliance · R$ 835,74<br>r152 Refeições - Direito Econômico · R$ 102,20 | R$ 1.137,94 | Refeições Prospecção · R$ 937,94 | R$ 937,94 | 1 | -R$ 200,00 | — |

**Gestão do Conhecimento** — linha 158 da planilha

| Mês | Só na planilha | Σ | Só no sistema | Σ | Batem | Diferença | Onde está o resto |
|---|---|---:|---|---:|---:|---:|---|
| Março | r159 Cursos e Treinamentos - Arbitragem e Compliance · R$ 1.094,49 | R$ 1.094,49 | Cursos / Treinamento Jurídico · R$ 279,00 | R$ 279,00 | 0 | -R$ 815,49 | r159 R$ 1.094,49 → no sistema em **Custos com Pessoal Técnico**: Cursos / Treinamento Jurídico (`030.010.0180`) · R$ 1.094,49 |
| Abril | r160 Cursos e Treinamentos - Contencioso · R$ 1.450,00 | R$ 1.450,00 | Cursos / Treinamento Jurídico · R$ 1.650,00 | R$ 1.650,00 | 0 | +R$ 200,00 | Cursos / Treinamento Jurídico R$ 1.650,00 = r140 Eventos e Happy hour - Direito Econômico · R$ 200,00 (**Investimentos em Prospecção**) + r160 Cursos e Treinamentos - Contencioso · R$ 1.450,00 |

**Endomarketing** — linha 164 da planilha

| Mês | Só na planilha | Σ | Só no sistema | Σ | Batem | Diferença | Onde está o resto |
|---|---|---:|---|---:|---:|---:|---|
| Janeiro | — | R$ 0,00 | Eventos e Happy Hour · R$ 1.317,71 | R$ 1.317,71 | 0 | +R$ 1.317,71 | Eventos e Happy Hour R$ 1.317,71 = r139 Eventos e Happy hour - Contencioso · R$ 146,00 (**Investimentos em Prospecção**) + r141 Eventos e Happy hour - Institucional · R$ 1.171,71 (**Investimentos em Prospecção**) |
| Fevereiro | — | R$ 0,00 | Eventos e Happy Hour · R$ 1.166,75 | R$ 1.166,75 | 0 | +R$ 1.166,75 | Eventos e Happy Hour R$ 1.166,75 = r141 Eventos e Happy hour - Institucional · R$ 1.166,75 (**Investimentos em Prospecção**) |

**Informática** — linha 180 da planilha

| Mês | Só na planilha | Σ | Só no sistema | Σ | Batem | Diferença | Onde está o resto |
|---|---|---:|---|---:|---:|---:|---|
| Fevereiro | r185 Licenças de Uso de Software - Institucional · R$ 12.193,48<br>r189 Suporte Totvs · R$ 3.387,47 | R$ 15.580,95 | Licenças de Uso de Software · R$ 15.580,68 | R$ 15.580,68 | 1 | -R$ 0,27 | — |
| Março | r185 Licenças de Uso de Software - Institucional · R$ 12.148,80<br>r188 Suporte de Informática · R$ 2.040,00<br>r189 Suporte Totvs · R$ 2.917,77 | R$ 17.106,57 | Serviços de Informática · R$ 9.252,45<br>Licenças de Uso de Software · R$ 7.616,52 | R$ 16.868,97 | 0 | -R$ 237,60 | — |
| Abril | r185 Licenças de Uso de Software - Institucional · R$ 11.533,41<br>r188 Suporte de Informática · R$ 2.040,00<br>r189 Suporte Totvs · R$ 2.917,77<br>r190 Microcomputadores / Servidores · R$ 1.166,69 | R$ 17.657,87 | Serviços de Informática · R$ 9.252,45<br>Microcomputadores / Servidores · R$ 904,68<br>Impressoras e Periféricos · R$ 262,01<br>Licenças de Uso de Software · R$ 7.348,73 | R$ 17.767,87 | 1 | +R$ 110,00 | — |

¹ Nestas linhas (Administrativas / Janeiro, Administrativas / Junho) os subtotais reconstroem a diferença
com **um centavo** de folga: a planilha divide a conta de Associações entre as
três áreas e cada parte carrega meio centavo, que reaparece ao somar. Não é
dinheiro faltando — é arredondamento da própria divisão.

### Econômico · Custo equipe — +R$ 4.330,76 no acumulado

| Mês | Célula | Planilha | Sistema | Diferença |
|---|---|---:|---:|---:|
| Janeiro | `C57` | R$ 75.653,19 | R$ 74.765,56 | -R$ 887,63 |
| Fevereiro | `G57` | R$ 78.817,05 | R$ 78.763,20 | -R$ 53,85 |
| Março | `K57` | R$ 76.049,97 | R$ 78.475,60 | +R$ 2.425,63 |
| Abril | `O57` | R$ 79.160,08 | R$ 81.931,07 | +R$ 2.770,99 |
| Maio | `S57` | R$ 79.436,24 | R$ 79.511,85 | +R$ 75,61 |
| Junho | `W57` | R$ 80.536,84 | R$ 80.536,85 | +R$ 0,01 |
| **Acumulado** | — | **R$ 469.653,37** | **R$ 473.984,13** | **+R$ 4.330,76** |

Três coisas. Em **janeiro** (−887,63), a parte MBC do convênio do **RB** (−789,94, causa 4 do resumo — é a nossa estimativa) mais a **AASP** (−97,70, classificação: troca de linha dentro da área). Em **março e abril** (+2.425,63 e +2.770,99), duas coisas iguais nos dois meses: o **vale dos advogados** (+1.008,40 em cada) e a distribuição de uma advogada (ASG), que a planilha lança **líquida** e nós bruta (+1.509,00 em cada). O que os separa é pequeno: em março, um **seguro de vida** que só a planilha tem (−92,45); em abril, o **ISS trimestral** (+253,59), que sai do Contencioso e entra aqui. Fevereiro e maio ficam abaixo de cem reais.

A **estagiária do Direito Econômico** entra na planilha em março e nós a reproduzimos ao centavo — ela não gera diferença, mas explica por que o custo da área sobe nos dois lados a partir daquele mês.

*Conferir:* Planilha, aba `Base_Resultado Mensal_V2`, linhas **44 e 48** (convênio de EHF e de RB) e **52** (a bolsa da estagiária).

### Arbitragem · Despesas Equipe — +R$ 3.624,00 no acumulado

| Mês | Célula | Planilha | Sistema | Diferença |
|---|---|---:|---:|---:|
| Janeiro | `C77` | R$ 146,00 | R$ 1.204,47 | +R$ 1.058,47 |
| Fevereiro | `G77` | R$ 2.633,69 | R$ 2.633,69 | R$ 0,00 ✓ |
| Março | `K77` | R$ 3.728,18 | R$ 4.701,41 | +R$ 973,23 |
| Abril | `O77` | R$ 2.633,69 | R$ 4.157,99 | +R$ 1.524,30 |
| Maio | `S77` | R$ 1.204,47 | R$ 1.272,47 | +R$ 68,00 |
| Junho | `W77` | R$ 11.597,70 | R$ 11.597,70 | R$ 0,00 ✓ |
| **Acumulado** | — | **R$ 21.943,73** | **R$ 25.567,73** | **+R$ 3.624,00** |

A **fórmula deslocada** da planilha (causa 1) — na Arbitragem o efeito é o maior dos três, porque a linha 206 é a que perde as parcelas de maior valor. O resíduo de janeiro (+1.204,47) é o **Canal de Arbitragem**, que a planilha daquele mês não somou.

*Conferir:* Planilha, aba `Base_Resultado Mensal_V2`, linha **206**, colunas de janeiro a maio (compare com a de junho).

### Contencioso · Custo equipe — +R$ 3.140,20 no acumulado

| Mês | Célula | Planilha | Sistema | Diferença |
|---|---|---:|---:|---:|
| Janeiro | `C39` | R$ 73.576,32 | R$ 73.478,62 | -R$ 97,70 |
| Fevereiro | `G39` | R$ 76.342,35 | R$ 76.179,29 | -R$ 163,06 |
| Março | `K39` | R$ 72.845,49 | R$ 74.072,29 | +R$ 1.226,80 |
| Abril | `O39` | R$ 75.374,05 | R$ 76.311,31 | +R$ 937,26 |
| Maio | `S39` | R$ 74.141,21 | R$ 75.378,11 | +R$ 1.236,90 |
| Junho | `W39` | R$ 75.424,21 | R$ 75.424,21 | R$ 0,00 ✓ |
| **Acumulado** | — | **R$ 447.703,63** | **R$ 450.843,83** | **+R$ 3.140,20** |

O **vale dos advogados** (causa 3 do resumo): entra sempre no custo da área, e a planilha só o lança em alguns meses — nas linhas 26 e 27 ele aparece em jan/fev/jun e fica **zerado em mar/abr/mai**, que são exatamente os três meses com diferença acima de mil reais. Em janeiro e fevereiro o vale está nos dois lados e o que sobra é só classificação: a **AASP** (−97,70 e −163,06), que a planilha põe no Custo equipe e nós em Despesa de Área — sai desta linha e entra em outra da mesma área, sem mexer no Resultado Bruto. Junho bate em 0,00. Em abril há ainda o **ISS trimestral** (−253,55), que é o mesmo tipo de troca. Ver *Diferenças de classificação*.

*Conferir:* Planilha, aba `Base_Resultado Mensal_V2`, linhas **26 e 27** (Vale Refeição e Vale Transporte do Contencioso) — compare jan/fev/jun com mar/abr/mai.

### Contencioso · Despesa Institucional — -R$ 2.221,09 no acumulado

| Mês | Célula | Planilha | Sistema | Diferença |
|---|---|---:|---:|---:|
| Janeiro | `C42` | R$ 33.821,38 | R$ 34.516,68 | +R$ 695,30 |
| Fevereiro | `G42` | R$ 30.609,71 | R$ 31.073,54 | +R$ 463,83 |
| Março | `K42` | R$ 34.482,81 | R$ 32.989,01 | -R$ 1.493,80 |
| Abril | `O42` | R$ 36.400,45 | R$ 34.997,85 | -R$ 1.402,60 |
| Maio | `S42` | R$ 35.555,40 | R$ 35.069,86 | -R$ 485,54 |
| Junho | `W42` | R$ 32.562,84 | R$ 32.564,56 | +R$ 1,72 |
| **Acumulado** | — | **R$ 203.432,59** | **R$ 201.211,50** | **-R$ 2.221,09** |

**Não é da área — é a despesa institucional total, rateada** (causa 2 do resumo). A divisão entre as três áreas não cria nem apaga dinheiro, então esta linha não tem causa própria: olhe *Despesas Indiretas*.

Duas coisas se somam aqui. A maior parte vem do **total** (a linha 198, detalhada em *Despesas Indiretas*). O resto vem da **fórmula deslocada** (causa 1): o que se rateia é o total **menos** as despesas das áreas (linha 207 = 198 − 203), e a linha 203 é a soma das linhas 204/205/206 — as mesmas que estão erradas de janeiro a maio. Por isso a soma das três áreas não é igual à diferença do total nesses meses: em abril, por exemplo, as áreas somam −3.394,34 contra −2.070,03 do total, e os R$ 1.324,31 de diferença são exatamente o erro da linha 203.

*Conferir:* Planilha, aba `Base_Resultado Mensal_V2`: linha **207** (total a ratear = 198 − 203) e linha **203**. O custo de cada área, que dá a proporção do rateio, está nas linhas **5 / 30 / 60** da mesma aba.

#### De onde sai a Despesa Institucional de cada área

O rateio tem só duas entradas: o **valor a ratear** (linha 207 = 198 − 203) e a
**parte de cada área no Custo equipe** (linhas 5 / 30 / 60). Multiplicando as duas
chega-se ao número de cada área, ao centavo, nos dois lados. A tabela mostra as
duas entradas para que se veja qual delas causa a diferença em cada mês.

| Mês | A ratear (planilha) | A ratear (sistema) | Diferença |
|---|---:|---:|---:|
| Janeiro | R$ 97.103,51 | R$ 98.769,12 | +R$ 1.665,61 |
| Fevereiro | R$ 86.988,31 | R$ 89.186,85 | +R$ 2.198,54 |
| Março | R$ 93.764,68 | R$ 89.843,76 | -R$ 3.920,92 |
| Abril | R$ 101.209,18 | R$ 97.814,85 | -R$ 3.394,33 |
| Maio | R$ 99.730,65 | R$ 97.365,22 | -R$ 2.365,43 |
| Junho | R$ 90.812,09 | R$ 90.816,89 | +R$ 4,80 |

E a parte de cada área (percentual do Custo equipe total):

| Mês | Contencioso | Econômico | Arbitragem |
|---|---|---|---|
| Janeiro | 34,83% → 34,95% | 35,81% → 35,56% | 29,36% → 29,49% |
| Fevereiro | 35,19% → 34,84% | 36,33% → 36,02% | 28,48% → 29,14% |
| Março | 36,78% → 36,72% | 38,39% → 38,90% | 24,83% → 24,38% |
| Abril | 35,97% → 35,78% | 37,77% → 38,41% | 26,26% → 25,81% |
| Maio | 35,65% → 36,02% | 38,20% → 37,99% | 26,15% → 25,99% |
| Junho | 35,86% → 35,86% | 38,29% → 38,29% | 25,85% → 25,85% |

Lê-se *planilha → sistema*. Em junho os percentuais são idênticos e as três áreas
batem; nos outros meses a diferença de cada área vem das duas entradas juntas — o
valor a ratear (que é a linha 198, detalhada acima, menos a linha 203, afetada pela
fórmula deslocada) e a parte de cada área, que muda quando o Custo equipe muda.

### Contencioso · Despesas Equipe — -R$ 2.162,24 no acumulado

| Mês | Célula | Planilha | Sistema | Diferença |
|---|---|---:|---:|---:|
| Janeiro | `C41` | R$ 1.060,10 | R$ 341,40 | -R$ 718,70 |
| Fevereiro | `G41` | R$ 2.129,32 | R$ 2.346,72 | +R$ 217,40 |
| Março | `K41` | R$ 2.346,72 | R$ 2.346,72 | R$ 0,00 ✓ |
| Abril | `O41` | R$ 4.183,92 | R$ 3.881,72 | -R$ 302,20 |
| Maio | `S41` | R$ 2.276,22 | R$ 917,49 | -R$ 1.358,73 |
| Junho | `W41` | R$ 2.442,49 | R$ 2.442,48 | -R$ 0,01 |
| **Acumulado** | — | **R$ 14.438,77** | **R$ 12.276,53** | **-R$ 2.162,24** |

A **fórmula deslocada** da planilha (causa 1 do resumo): de janeiro a maio a linha 204 soma as linhas de *Eventos*, *Material Gráfico*, *Patrocínio*, *Refeições* e *Viagens* uma linha abaixo da sua — pega a do Direito Econômico em vez da do Contencioso. Junho já está com a fórmula certa e bate.

*Conferir:* Planilha, aba `Base_Resultado Mensal_V2`, linha **204**: compare a fórmula de junho (`=H125+H129+H139+H143+...`) com a de maio (`=G125+G129+G140+G144+...`) — as cinco últimas parcelas estão uma linha adiante nos meses de janeiro a maio.

### Econômico · Despesa Institucional — -R$ 1.932,38 no acumulado

| Mês | Célula | Planilha | Sistema | Diferença |
|---|---|---:|---:|---:|
| Janeiro | `C60` | R$ 34.776,07 | R$ 35.121,22 | +R$ 345,15 |
| Fevereiro | `G60` | R$ 31.601,96 | R$ 32.127,51 | +R$ 525,55 |
| Março | `K60` | R$ 35.999,71 | R$ 34.950,08 | -R$ 1.049,63 |
| Abril | `O60` | R$ 38.228,85 | R$ 37.575,18 | -R$ 653,67 |
| Maio | `S60` | R$ 38.094,71 | R$ 36.993,09 | -R$ 1.101,62 |
| Junho | `W60` | R$ 34.770,11 | R$ 34.771,95 | +R$ 1,84 |
| **Acumulado** | — | **R$ 213.471,41** | **R$ 211.539,03** | **-R$ 1.932,38** |

Mesma causa do Contencioso: é o total institucional rateado (causa 2).

*Conferir:* Planilha, aba `Base_Resultado Mensal_V2`, linhas **207** e **203**; custo das áreas nas linhas **5 / 30 / 60**.

### Arbitragem · Custo equipe — +R$ 1.912,91 no acumulado

| Mês | Célula | Planilha | Sistema | Diferença |
|---|---|---:|---:|---:|
| Janeiro | `C75` | R$ 62.013,17 | R$ 62.014,13 | +R$ 0,96 |
| Fevereiro | `G75` | R$ 61.794,34 | R$ 63.706,29 | +R$ 1.911,95 |
| Março | `K75` | R$ 49.183,94 | R$ 49.183,94 | R$ 0,00 ✓ |
| Abril | `O75` | R$ 55.038,69 | R$ 55.038,69 | R$ 0,00 ✓ |
| Maio | `S75` | R$ 54.383,94 | R$ 54.383,94 | R$ 0,00 ✓ |
| Junho | `W75` | R$ 54.383,94 | R$ 54.383,94 | R$ 0,00 ✓ |
| **Acumulado** | — | **R$ 336.798,02** | **R$ 338.710,93** | **+R$ 1.912,91** |

Convênio médico de um advogado (JGS) em **fevereiro** — e a própria planilha responde. Em fevereiro ela mantém a distribuição (linha 70) e o pró-labore (linha 71) dele e deixa só o convênio (linha 69) em branco. Quem recebe distribuição está na folha, então o plano é custo real, e o sistema o tem lançado. De março em diante ele sai dos dois lados e a Arbitragem bate em 0,00. **Não é dúvida — é uma omissão da coluna de fevereiro.**

*Conferir:* Planilha, aba `Base_Resultado Mensal_V2`, linhas **69, 70 e 71** (o convênio, a distribuição e o pró-labore dele), coluna de fevereiro (**D**).

### Arbitragem · Despesa Institucional — -R$ 1.658,27 no acumulado

| Mês | Célula | Planilha | Sistema | Diferença |
|---|---|---:|---:|---:|
| Janeiro | `C78` | R$ 28.506,06 | R$ 29.131,22 | +R$ 625,16 |
| Fevereiro | `G78` | R$ 24.776,64 | R$ 25.985,80 | +R$ 1.209,16 |
| Março | `K78` | R$ 23.282,16 | R$ 21.904,67 | -R$ 1.377,49 |
| Abril | `O78` | R$ 26.579,88 | R$ 25.241,81 | -R$ 1.338,07 |
| Maio | `S78` | R$ 26.080,54 | R$ 25.302,27 | -R$ 778,27 |
| Junho | `W78` | R$ 23.479,14 | R$ 23.480,38 | +R$ 1,24 |
| **Acumulado** | — | **R$ 152.704,42** | **R$ 151.046,15** | **-R$ 1.658,27** |

Mesma causa do Contencioso: é o total institucional rateado (causa 2).

*Conferir:* Planilha, aba `Base_Resultado Mensal_V2`, linhas **207** e **203**; custo das áreas nas linhas **5 / 30 / 60**.

### Econômico · Despesas Equipe — -R$ 31,45 no acumulado

| Mês | Célula | Planilha | Sistema | Diferença |
|---|---|---:|---:|---:|
| Janeiro | `C59` | R$ 1.871,81 | R$ 1.400,19 | -R$ 471,62 |
| Fevereiro | `G59` | R$ 3.296,07 | R$ 2.129,32 | -R$ 1.166,75 |
| Março | `K59` | R$ 2.129,32 | R$ 2.129,32 | R$ 0,00 ✓ |
| Abril | `O59` | R$ 2.129,32 | R$ 2.231,52 | +R$ 102,20 |
| Maio | `S59` | R$ 2.300,10 | R$ 3.804,82 | +R$ 1.504,72 |
| Junho | `W59` | R$ 1.075,09 | R$ 1.075,09 | R$ 0,00 ✓ |
| **Acumulado** | — | **R$ 12.801,71** | **R$ 12.770,26** | **-R$ 31,45** |

A **fórmula deslocada** da planilha (causa 1), na linha 205. Junho está certo e bate. O acumulado quase se anula (−31,45) porque os meses têm sinais opostos — **não** porque a linha esteja certa: fevereiro difere −1.166,75 e maio +1.504,72. É o caso que este documento usa para dizer que um total que fecha por compensação não está validado.

*Conferir:* Planilha, aba `Base_Resultado Mensal_V2`, linha **205**, colunas de janeiro a maio (compare com a de junho).

### Linhas que são somas de outras

Estas não têm causa própria — cada uma é a soma das linhas acima (Resultado
Bruto e Líquido dentro de cada bloco; Custos Diretos = as três áreas). Elas
aparecem aqui só para fechar o acumulado:

Conferindo: *Custos Diretos* é exatamente a soma dos três *Custo equipe*, mês a
mês. Já a soma dos três *Resultado Bruto* por área dá −R$ 5.004,01 contra os
−R$ 5.003,04 do Resultado Bruto institucional: os **97 centavos** de diferença
são o rateio da Despesa Institucional, que a planilha e o sistema arredondam em
pontos diferentes ao dividir o total entre três áreas.

| Linha | Jan | Fev | Mar | Abr | Mai | Jun | Acumulado |
|---|---:|---:|---:|---:|---:|---:|---:|
| Custos Diretos | -R$ 984,37 | +R$ 1.695,04 | +R$ 3.652,42 | +R$ 3.708,24 | +R$ 1.312,50 | R$ 0,00 ✓ | **+R$ 9.383,83** |
| Resultado Bruto | -R$ 549,40 | -R$ 2.944,23 | -R$ 704,73 | -R$ 1.638,21 | +R$ 838,77 | -R$ 5,24 | **-R$ 5.003,04** |
| Resultado Líquido | -R$ 549,40 | -R$ 2.944,23 | -R$ 704,73 | -R$ 1.638,21 | +R$ 838,79 | -R$ 5,17 | **-R$ 5.002,95** |
| Arbitragem · Resultado Bruto | -R$ 1.684,25 | -R$ 3.120,69 | +R$ 404,19 | -R$ 186,56 | +R$ 709,62 | -R$ 1,24 | **-R$ 3.878,93** |
| Econômico · Resultado Bruto | +R$ 1.014,44 | +R$ 694,64 | -R$ 1.376,07 | -R$ 2.219,25 | -R$ 479,14 | -R$ 2,14 | **-R$ 2.367,52** |
| Contencioso · Resultado Bruto | +R$ 121,45 | -R$ 518,55 | +R$ 267,20 | +R$ 767,10 | +R$ 607,09 | -R$ 1,85 | **+R$ 1.242,44** |

## Diferenças menores

| Linha | Jan | Fev | Mar | Abr | Mai | Jun | Acumulado |
|---|---:|---:|---:|---:|---:|---:|---:|
| Receita | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | -R$ 0,16 | -R$ 0,44 | **-R$ 0,60** |
| Impostos | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | R$ 0,00 ✓ | -R$ 0,02 | -R$ 0,07 | **-R$ 0,09** |

Somadas: **-R$ 0,69** no acumulado, e nenhuma passa de mil reais em nenhum mês isolado — são centavos de
arredondamento do recebimento, que a planilha digita em reais inteiros.

## Dois pontos que ajudam a ler os números

Nada aqui pede mudança de lado nenhum — é só o que é útil saber ao comparar as duas
colunas.

### O efeito real da fórmula das linhas 204/205/206

A fórmula deslocada (causa 1) afeta **a divisão entre as áreas**, não o total. Se as
fórmulas de junho valessem para janeiro–maio, o erro mensal de *Despesas Equipe*
cairia de R$ 10.216 para R$ 4.245 (somados os seis meses em módulo) e o de *Despesa
Institucional* cerca de um terço — mas o **Resultado Bruto praticamente não se
move**: de R$ 14.175 para R$ 14.009 em erro mensal somado, e o acumulado de
−R$ 5.003 para −R$ 5.004.

O motivo é que a linha **198** — o total institucional, que é o que chega ao
Resultado Bruto — não referencia as linhas 204/205/206. Vale registrar porque a
conclusão é contra-intuitiva: é a maior das causas por número de células afetadas e,
ainda assim, não é ela que explica o acumulado.

### O único número sem origem: R$ 35,52 no vale-transporte de janeiro

Na aba `Base_Resultado Mensal_V2`, a célula `C123` traz `=35,52+262,64`. Os
**262,64** são o vale-transporte da pessoa do administrativo (14 dias × R$ 18,76) e
conferem. Os **35,52** não aparecem em nenhum lançamento do sistema — nem em
janeiro, nem em nenhum outro mês. Não é vale-refeição (o menor do ano é R$ 783,70) e
não corresponde a um número inteiro de dias em nenhuma diária de vale.

Também não é um pedaço que falte do nosso número: o vale-transporte de janeiro
(R$ 262,64) já está completo, então os 35,52 estão somados por cima. Depois de nomear
tudo o que está neste documento, é o único valor da comparação inteira que não tem um
lançamento atrás dele.

**Ponto encerrado** (definido com o cliente em 05/08/2026): não é para investigar.
Fica registrado apenas para que ninguém volte a procurar a origem dele — o valor é
de R$ 35,52 e afeta só o vale do administrativo em janeiro.

## Diferenças de classificação

Estas são de **onde** o valor aparece, não de **quanto** ele é: o lançamento existe
nos dois lados, em seções diferentes. Ficam registradas porque **se repetem todo
mês** e costumam gerar dúvida.

Não mudam **nenhum** total — a conta entra na mesma soma dos dois lados:

* **Endomarketing × Prospecção** e **Ocupação × Administrativas** — a mesma conta em
  famílias diferentes de cada lado; as duas entram na linha 198.
* **Prêmio de seguro** — é anual (lançado em janeiro e julho); a planilha o divide
  em parcelas mensais e o classifica em *Administrativas* (linha 133), o sistema em
  *Ocupação*. Como as duas famílias somam na linha 198, o total não se move.

Movem uma linha, mas **não** movem o Resultado Bruto da área — o valor só troca de
seção dentro da mesma área, e as duas seções ficam acima do Resultado Bruto:

* **AASP** — dentro do Custo equipe na planilha, em Despesa de Área no sistema.
  Contencioso, −97,70 em janeiro e −163,06 em fevereiro.

Move valor **entre áreas** — some no total, mas cada área sente:

* **ISS trimestral** — o sistema lança por advogado, a planilha numa única linha da
  área. No acumulado sobra R$ 0,04, mas em abril são −R$ 253,55 no Contencioso e
  +R$ 253,59 no Econômico: o Resultado Bruto **de cada área** muda, o institucional
  não.

Estas duas **mudam** o total e estão contadas nas diferenças acima — ficam aqui só
porque também são decisões de método, não erros de nenhum dos lados:

* **Vale do administrativo** — a planilha muda de base a cada mês (linhas 122/123:
  só a pessoa do administrativo em fev/jun, as três em abril, nenhuma das duas em
  jan/mar/mai); o sistema usa sempre a mesma regra, com os estagiários no custo das
  áreas deles. É a maior das diferenças de despesa no acumulado.
* **Aluguel** — o sistema usa o valor líquido da sublocação (crédito Belline),
  a planilha o bruto. Diferença de +R$ 129,17 em abril e maio.

