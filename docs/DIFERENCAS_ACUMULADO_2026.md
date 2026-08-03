# Diferenças entre a planilha e o sistema — acumulado Janeiro a Junho de 2026

> Documento gerado por `backend/scripts/build_diferencas_doc.py` a partir dos
> dados ao vivo do sistema e de `Fechamento MBC 06.2026.xlsx`. Cada diferença
> abaixo já foi diagnosticada e tem causa identificada — **não é uma lista de**
> **erros**. Junho fecha exatamente e é o melhor mês de referência.

## Como ler este documento

Para cada linha em que a planilha e o sistema divergem no acumulado, mostramos
sempre na mesma ordem: **o que a planilha mostra**, **o que o sistema mostra**,
**a diferença**, e **por quê**. Onde há algo a decidir, isso está em *O que
precisamos de vocês*.

Só entram as diferenças de **R$ R$ 1.000,00 ou mais** no acumulado. As
menores estão somadas no final, para que nenhuma fique de fora sem explicação.

## O que NÃO difere

| Linha | Planilha | Sistema | Diferença |
|---|---:|---:|---:|
| Receita | R$ 2.130.830,87 | R$ 2.130.830,27 | **-R$ 0,60** |
| Impostos | R$ 319.624,63 | R$ 319.624,54 | **-R$ 0,09** |
| Amortização | R$ 48.702,00 | R$ 48.702,00 | **+R$ 0,00** |

**A receita, os impostos e a amortização batem em todos os meses.** Toda a
diferença está em *despesa*. No consolidado institucional o Resultado Bruto
difere **+R$ 131,84** sobre uma receita de R$ 2.130.830,27.

⚠ Um total consolidado que bate pode esconder diferenças que se cancelam, por
isso o documento detalha **por área**, e não só o consolidado.

## Resumo das diferenças relevantes

| Linha | Planilha | Sistema | Diferença |
|---|---:|---:|---:|
| Arbitragem · Despesas Equipe | R$ 21.943,74 | R$ 25.567,73 | **+R$ 3.623,99** |
| Econômico · Despesa Institucional | R$ 213.471,40 | R$ 210.090,84 | **-R$ 3.380,56** |
| Contencioso · Custo equipe | R$ 447.703,64 | R$ 450.843,83 | **+R$ 3.140,19** |
| Contencioso · Despesas Equipe | R$ 14.438,75 | R$ 12.276,53 | **-R$ 2.162,22** |
| Arbitragem · Custo equipe | R$ 336.798,02 | R$ 338.710,93 | **+R$ 1.912,91** |
| Contencioso · Despesa Institucional | R$ 203.432,60 | R$ 201.998,65 | **-R$ 1.433,95** |
| Arbitragem · Resultado Bruto | -R$ 54.277,18 | -R$ 58.817,16 | **-R$ 4.539,98** |
| Despesas Indiretas | R$ 618.792,60 | R$ 614.411,21 | **-R$ 4.381,39** |
| Custos Diretos | R$ 1.258.219,16 | R$ 1.262.468,11 | **+R$ 4.248,95** |
| Econômico · Resultado Bruto | R$ 256.102,41 | R$ 260.317,96 | **+R$ 4.215,55** |

As três causas por trás de praticamente tudo isso:

1. **A fórmula das linhas 204/205/206 da planilha está deslocada uma linha de**
   **janeiro a maio.** É a causa que mais pesa: move a Despesa Institucional e
   as Despesas Equipe das três áreas ao mesmo tempo. As fórmulas de junho já
   estão corretas.
2. **O vale dos advogados no custo de equipe** — regra confirmada por vocês
   (sempre incluir); as colunas de janeiro a maio da planilha não incluem.
3. **O convênio médico de janeiro/fevereiro** — a única diferença que ainda
   depende de uma definição de vocês.

## Detalhe, linha por linha

### Arbitragem · Despesas Equipe — diferença de R$ 3.623,99

| | Valor |
|---|---:|
| Planilha (*Areas Sintetico*, linha 77, Jan–Junho) | R$ 21.943,74 |
| Nosso sistema | R$ 25.567,73 |
| **Diferença** | **+R$ 3.623,99** |

**Por quê:** A mesma fórmula deslocada das linhas 204/205/206. Na Arbitragem o efeito é maior porque as cinco linhas da área ficam de fora da soma e as cinco do Institucional entram no lugar.

**Onde conferir:** Base_Resultado linha 206.

**O que precisamos de vocês:** Mesma confirmação das fórmulas 204/205/206.

### Econômico · Despesa Institucional — diferença de -R$ 3.380,56

| | Valor |
|---|---:|
| Planilha (*Areas Sintetico*, linha 60, Jan–Junho) | R$ 213.471,40 |
| Nosso sistema | R$ 210.090,84 |
| **Diferença** | **-R$ 3.380,56** |

**Por quê:** A mesma fórmula deslocada das linhas 204/205/206 (ver Contencioso).

**Onde conferir:** Base_Resultado linhas 204, 205 e 206, colunas de janeiro a maio.

**O que precisamos de vocês:** Mesma confirmação das fórmulas 204/205/206.

### Contencioso · Custo equipe — diferença de R$ 3.140,19

| | Valor |
|---|---:|
| Planilha (*Areas Sintetico*, linha 39, Jan–Junho) | R$ 447.703,64 |
| Nosso sistema | R$ 450.843,83 |
| **Diferença** | **+R$ 3.140,19** |

**Por quê:** Vale-refeição e vale-transporte dos advogados. A regra confirmada por vocês é sempre incluir o vale no custo da equipe da área; as colunas de janeiro a maio da planilha não o incluem (as de junho sim, e junho fecha exatamente). Somam-se a isso duas diferenças que não mudam nenhum total: o ISS trimestral, que o sistema lança por advogado e a planilha digita numa única linha da área, e a AASP, que a planilha lança dentro do custo de equipe e o sistema classifica como Despesa de Área.

**Onde conferir:** Base_Resultado linhas 26/27 (Vale), 25/54/79 (ISS Trimestral) e 9/18/36 (AASP). Fechamento por pessoa e por conta: resíduo 0,00 nos quatro meses.

### Contencioso · Despesas Equipe — diferença de -R$ 2.162,22

| | Valor |
|---|---:|
| Planilha (*Areas Sintetico*, linha 41, Jan–Junho) | R$ 14.438,75 |
| Nosso sistema | R$ 12.276,53 |
| **Diferença** | **-R$ 2.162,22** |

**Por quê:** Mesma fórmula deslocada das linhas 204/205/206, que é justamente a linha de Despesas Equipe por área, mais a classificação da AASP (a planilha a lança no custo de equipe, o sistema em Despesa de Área — o valor existe nos dois lados, em seções diferentes).

**Onde conferir:** Base_Resultado linha 204; contas `020.060.*`.

**O que precisamos de vocês:** Mesma confirmação das fórmulas 204/205/206.

### Arbitragem · Custo equipe — diferença de R$ 1.912,91

| | Valor |
|---|---:|
| Planilha (*Areas Sintetico*, linha 75, Jan–Junho) | R$ 336.798,02 |
| Nosso sistema | R$ 338.710,93 |
| **Diferença** | **+R$ 1.912,91** |

**Por quê:** Convênio médico de um advogado da Arbitragem em **fevereiro**. O memo do sistema em janeiro e fevereiro declara uma base de plano diferente da de março a junho, e é internamente consistente nessa base (`1.795,86 - 1.192,36 (Parte MBC) = 603,50` para outro advogado, mesma mecânica). A planilha repete a constante de março nos seis meses, ou seja, em jan/fev ela não segue o próprio memo do sistema.

**Onde conferir:** Base_Resultado linha 69; conta `030.010.0110`.

**O que precisamos de vocês:** Uma definição: em janeiro e fevereiro vale o valor do memo do sistema ou a constante que está na planilha? É a maior diferença de custo de equipe do acumulado.

### Contencioso · Despesa Institucional — diferença de -R$ 1.433,95

| | Valor |
|---|---:|
| Planilha (*Areas Sintetico*, linha 42, Jan–Junho) | R$ 203.432,60 |
| Nosso sistema | R$ 201.998,65 |
| **Diferença** | **-R$ 1.433,95** |

**Por quê:** A fórmula de Despesas por área da planilha está deslocada uma linha de janeiro a maio: as linhas 204, 205 e 206 somam a linha de baixo em cinco famílias de despesa (Eventos e Happy Hour, Material Gráfico, Patrocínio, Refeições e Viagens). Como o bloco está ordenado Arbitragem / Contencioso / Direito Econômico / Institucional, cada área recebe a despesa da área seguinte. Isso desloca também o rateio da despesa institucional das três áreas. **As fórmulas de junho já estão corretas — é por isso que junho fecha exatamente com o nosso número.**

**Onde conferir:** Base_Resultado linhas 204, 205 e 206, colunas de janeiro a maio.

**O que precisamos de vocês:** Confirmar se as fórmulas de janeiro a maio devem ser copiadas de junho. É a causa que mais pesa no acumulado das três áreas.

### Arbitragem · Resultado Bruto — diferença de -R$ 4.539,98

| | Valor |
|---|---:|
| Planilha (*Areas Sintetico*, linha 79, Jan–Junho) | -R$ 54.277,18 |
| Nosso sistema | -R$ 58.817,16 |
| **Diferença** | **-R$ 4.539,98** |

**Por quê:** Consequência das linhas acima — o resultado bruto é a soma delas, não uma diferença independente.

**Onde conferir:** Ver Custo equipe, Despesas Equipe e Despesa Institucional da área.

### Despesas Indiretas — diferença de -R$ 4.381,39

| | Valor |
|---|---:|
| Planilha (*Areas Sintetico*, linha 13, Jan–Junho) | R$ 618.792,60 |
| Nosso sistema | R$ 614.411,21 |
| **Diferença** | **-R$ 4.381,39** |

**Por quê:** Duas causas conhecidas e pequenas: o vale do administrativo em março, abril e maio (a planilha lançou o valor cheio da conta transitória, com as três pessoas, e não só a parte do administrativo — vocês já avaliaram que não vale corrigir) e a tarifa bancária, que vem do sistema e está zerada no Excel (R$ 4,80 por mês).

**Onde conferir:** Base_Resultado linhas 122 e 123; conta `020.070.0030`.

### Custos Diretos — diferença de R$ 4.248,95

| | Valor |
|---|---:|
| Planilha (*Areas Sintetico*, linha 6, Jan–Junho) | R$ 1.258.219,16 |
| Nosso sistema | R$ 1.262.468,11 |
| **Diferença** | **+R$ 4.248,95** |

**Por quê:** É a soma dos custos de equipe das três áreas, então reflete as mesmas causas já descritas por área (vale dos advogados, ISS trimestral, AASP e o convênio de fevereiro).

**Onde conferir:** Ver as três linhas de Custo equipe por área.

### Econômico · Resultado Bruto — diferença de R$ 4.215,55

| | Valor |
|---|---:|
| Planilha (*Areas Sintetico*, linha 61, Jan–Junho) | R$ 256.102,41 |
| Nosso sistema | R$ 260.317,96 |
| **Diferença** | **+R$ 4.215,55** |

**Por quê:** Consequência das linhas acima — o resultado bruto é a soma delas, não uma diferença independente.

**Onde conferir:** Ver Custo equipe, Despesas Equipe e Despesa Institucional da área.

## Diferenças menores (abaixo do limiar)

| Linha | Planilha | Sistema | Diferença |
|---|---:|---:|---:|
| Arbitragem · Despesa Institucional | R$ 152.704,42 | R$ 151.707,20 | -R$ 997,22 |
| Econômico · Custo equipe | R$ 469.653,40 | R$ 468.849,25 | -R$ 804,15 |
| Contencioso · Resultado Bruto | R$ 25.247,01 | R$ 25.702,30 | +R$ 455,29 |
| Resultado Líquido | -R$ 114.507,52 | -R$ 114.375,59 | +R$ 131,93 |
| Resultado Bruto | R$ 253.819,11 | R$ 253.950,95 | +R$ 131,84 |
| Econômico · Despesas Equipe | R$ 12.801,69 | R$ 12.770,26 | -R$ 31,43 |
| Receita | R$ 2.130.830,87 | R$ 2.130.830,27 | -R$ 0,60 |
| Impostos | R$ 319.624,63 | R$ 319.624,54 | -R$ 0,09 |

Somadas: **-R$ 1.114,43**. As causas conhecidas
são a tarifa bancária que vem do sistema e está zerada no Excel (R$ 4,80 por
mês), o vale do administrativo de março a maio e centavos de arredondamento.

## O que precisamos de vocês, em ordem

1. **Convênio médico de janeiro e fevereiro** (EHF e RB): o memo do sistema
   nesses dois meses declara uma base de plano diferente da de março a junho, e
   a planilha usa a constante de março nos seis meses. Qual vale para jan/fev?
2. **Fórmulas das linhas 204/205/206** de janeiro a maio: podem ser copiadas de
   junho, que já está correto?
3. **Janeiro, vale-transporte:** a planilha traz `=35,52+262,64`. Os 262,64 são
   o lançamento do sistema; de onde vêm os 35,52?
4. **Lançamentos avulsos de janeiro e fevereiro** (linhas 34, 35, 43, 47, 51 e
   54): são de outra competência ou ajustes manuais? Se tiverem origem no
   sistema, passamos a considerá-los.
5. **Convênio médico da linha 69:** deveria continuar em fevereiro, como está no
   sistema, ou foi encerrado em janeiro?

