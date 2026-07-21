# Onde olhar na planilha — células de referência (Maio/2026)

**Arquivo:** `Fechamento MBC 05.2026.xlsx` · **Competência:** 05.2026
**Acompanha:** `NOTA_MAIO_2026.md` (o texto explicativo) e `Comparativo_MBC_Maio_2026.xlsx`

> Este documento diz **em qual célula da própria planilha de vocês** cada número da
> NOTA está, para conferirem lado a lado. Todos os valores abaixo foram lidos direto
> do arquivo. Duas abas importam.

---

## Aba **"Areas Sintetico atualizado"** — os totais das tabelas da NOTA
**Maio = coluna S.**

### Institucional (tabela "linha por linha" da NOTA)

| Linha da NOTA | Célula | Valor na planilha |
|---|---|---:|
| Recebimento | **S4** | 415.928 |
| Custos Diretos (equipe + comissão) | **S6** | 210.089,46 |
| Despesas Institucionais | **S13** | 105.511,43 |
| Resultado Bruto | **S25** | 100.327,11 |
| Imposto (15% do recebimento) | **S28** | 62.389,20 |
| Amortização | **S29** | 8.117 |
| Resultado Líquido | **S30** | 29.820,91 |
| Reserva de Bônus | **S32** | 2.982,09 |

### Por área

| Área | Linha | Célula | Valor |
|---|---|---|---:|
| Contencioso | Recebimento | **S36** | 240.445 |
| Contencioso | Custo equipe | **S39** | 74.141,22 |
| Contencioso | Resultado Bruto | **S43** | 128.472,17 |
| Econômico | Recebimento | **S54** | 166.876 |
| Econômico | Custo equipe | **S57** | 79.436,25 |
| Econômico | Resultado Bruto | **S61** | 44.916,89 |
| Arbitragem | Recebimento | **S72** | 41.860 |
| Arbitragem | Custo equipe | **S75** | 54.383,94 |
| Arbitragem | Resultado Bruto | **S79** | −39.808,95 |

> ⚠️ As três células de **Resultado Bruto por área** (S43 / S61 / S79) são **fórmulas**
> — é nelas que mora o "regrupamento" (ver G156 abaixo). Por isso o RB por área difere
> do sistema, mas **a soma das três áreas é idêntica**.

---

## Aba **"Base_Resultado Mensal_V2"** — o detalhe do *porquê* das diferenças
**Maio = coluna G.**

| O que a NOTA explica | Célula | Valor |
|---|---|---:|
| **Aluguel** — a planilha digitou 24.230,60; o banco traz 24.359,77 (líquido de sublocação Belline). É a única diferença "de verdade" (+129,17). | **G86** | 24.230,60 |
| Subtotal "Despesas Institucional" (row 198) | **G198** | 105.511,43 |
| **Associações — Contencioso** (ICC + IBRAC) | **G129** | 917,50 |
| **Associações — Econômico** | **G130** | 700,10 |
| **Associações — Arbitragem/Compliance** (Canal) | **G131** | 1.204,47 |
| **Viagens — Econômico** — a passagem do RB (1.358,72) que a fórmula do subtotal de Despesas Área somou com **deslocamento de 1 linha**, jogando-a no Contencioso. É o "regrupamento". | **G156** | 1.358,72 |
| ISS Trimestral (por área) — **trimestral** (Jan/Abr/Jul/Out), por isso **vazio em maio** | **G25 / G54 / G79** | (vazio) |

---

## Meses anteriores (Jan–Abr) — mesma aba, outra coluna
**Janeiro = coluna C.** O exemplo de janeiro da NOTA (Associações):

| Linha | Célula (Jan) | Observação |
|---|---|---|
| Associações — Contencioso | **C129** | planilha antiga só tinha o IBRAC (1.400,19) |
| Associações — Econômico | **C130** | — |
| Associações — Arbitragem (Canal) | **C131** | a AASP (195,40) e o Canal (1.204,47) **faltavam** na planilha de Jan; o banco os traz |

> Colunas por mês na "Base_Resultado Mensal_V2": **C**=Jan, **D**=Fev, **E**=Mar,
> **F**=Abr, **G**=Mai, **H**=Jun … **N**=Dez.

---

### Resumo para a conversa
- Números da NOTA → aba **Areas Sintetico atualizado**, coluna **S**.
- "Por que difere" → aba **Base_Resultado Mensal_V2**, coluna **G** (aluguel **G86**,
  Viagens/regrupamento **G156**, Associações **G129–G131**).
- A única diferença real é o **aluguel (G86)**; o resto é arredondamento de centavos
  ou o regrupamento por área (soma total idêntica).
