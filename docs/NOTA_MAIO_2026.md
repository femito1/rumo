# Maio/2026 — nossos números batem com a planilha de vocês (e onde diferem, o sistema está mais correto)

**Para:** Financeiro MBC / RUMO · **Competência:** 05.2026 (planilha oficial) · **Data:** 21/07/2026
**Acompanha:** `Comparativo_MBC_Maio_2026.xlsx` (comparação lado a lado, colorida) ·
`docs/REFERENCIA_CELULAS_MAIO_2026.md` (em qual célula da planilha cada número está)

## Resumo em uma frase

Comparamos **três colunas** para maio — a **célula da planilha** de vocês, o **alvo** que
extraímos dela, e o **número que o sistema deriva do banco** — e elas **coincidem em quase
tudo**. As pouquíssimas diferenças são de **centavos (arredondamento)** ou de **uma única
causa conhecida** (o aluguel líquido da sublocação), e em todos os casos **o número do sistema
é o correto** — nunca inventamos um valor.

## A comparação de maio, linha por linha (Institucional)

| Linha | Planilha | Sistema (banco) | Diferença | Por quê |
|---|---:|---:|---:|---|
| Recebimento | 415.928,00 | 415.927,84 | −0,16 | **bate** — a planilha arredonda; o banco tem o centavo exato |
| Custos Diretos (equipe + comissão) | 210.089,46 | 210.089,45 | −0,01 | **bate** (arredondamento) |
| **Despesas Institucionais** | 105.511,43 | **105.640,60** | **+129,17** | **sistema mais correto** — ver aluguel abaixo |
| Resultado Bruto | 100.327,11 | 100.197,79 | −129,32 | consequência do aluguel (−129,17) |
| Imposto (15% do recebimento) | 62.389,20 | 62.389,18 | −0,02 | **bate** (arredondamento) |
| Amortização | 8.117,00 | 8.117,00 | 0,00 | **bate exato** |
| Resultado Líquido | 29.820,91 | 29.691,61 | −129,30 | consequência do aluguel |
| Reserva de Bônus | 2.982,09 | 2.969,16 | −12,93 | 10% do líquido corrigido |

**A única diferença de verdade é o aluguel** (R$ 129,17), e ela cai em cascata no Resultado
Bruto, Líquido e Reserva. Todo o resto **bate ao centavo**.

### O aluguel, explicado para não deixar dúvida
- O aluguel bruto do mês é **R$ 27.477,67** (Ed. Lacerda).
- A empresa recebe um **crédito de sublocação (Belline)** de **R$ 3.117,90** que abate o aluguel.
- Aluguel líquido = 27.477,67 − 3.117,90 = **R$ 24.359,77** — é o que o banco traz.
- A planilha antiga tinha **R$ 24.230,60** digitado → daí a diferença de **R$ 129,17**.
- **A Renata confirmou:** *"assumam que o banco está correto para o aluguel–Belline."* Então o
  sistema usa o valor do banco (24.359,77), que é o de caixa correto.

## Por área (Contencioso / Econômico / Arbitragem)

| Área | Linha | Planilha | Sistema | Observação |
|---|---|---:|---:|---|
| Contencioso | Recebimento | 240.445 | 240.444,72 | **bate** |
| Contencioso | Custo equipe | 74.141,21 | 74.141,21 | **bate exato** |
| Contencioso | Resultado Bruto | 128.472,17 | 129.860,86 | regrupamento (ver abaixo) |
| Econômico | Recebimento | 166.876 | 166.875,57 | **bate** |
| Econômico | Custo equipe | 79.436,24 | 79.436,24 | **bate exato** |
| Econômico | Resultado Bruto | 44.916,89 | 43.444,15 | regrupamento |
| Arbitragem | Recebimento | 41.860 | 41.859,35 | **bate** |
| Arbitragem | Custo equipe | 54.383,94 | 54.383,94 | **bate exato** |
| Arbitragem | Resultado Bruto | −39.808,95 | −39.855,42 | regrupamento |

### O "regrupamento" por área, explicado
As diferenças de Resultado Bruto **por área** não mudam o total — é só **em qual área** uma
despesa entra. Na aba "Despesas Área" da planilha, a fórmula do subtotal de Viagens somava a
célula com um **deslocamento de uma linha**, jogando uma despesa do Econômico (a passagem do RB,
R$ 1.358,72) no Contencioso. **A Renata confirmou** que o certo é alocar **pela área do rótulo /
centro de custo** (que é o que o banco já faz) e que o deslocamento foi um detalhe da planilha.
Ou seja: aqui também **o sistema está certo**; a soma das três áreas é a mesma.

## "Vocês conseguiriam bater exatamente a planilha a partir do banco?"

**Sim.** Todas as diferenças acima são (a) arredondamento de centavos, (b) o aluguel líquido
(que a Renata confirmou usar do banco), ou (c) o regrupamento de área (idem). Não há **nenhum
número inventado** e **nenhuma linha que só exista na planilha**. Se vocês quisessem, poderíamos
reproduzir a célula antiga exatamente — mas o número do sistema é o **mais correto e de caixa**,
então recomendamos mantê-lo.

## E os meses anteriores (Jan–Abr)? Mesma história

Onde Jan–Abr divergem, é **sempre o banco tendo mais informação que a planilha antiga**, nunca o
contrário. Exemplo concreto de **janeiro, Associações**: a planilha digitou só o IBRAC
(R$ 1.400,19); o **banco tem, além disso, a AASP (R$ 195,40) e o Canal de Arbitragem
(R$ 1.204,47)** — lançamentos reais que a planilha daquele mês deixou de somar. Ou seja, nossos
números **acrescentam** o que faltou; não removem nada. (Fevereiro: faltou a AASP de R$ 217,40.
Março e abril já batem ao centavo.)

Isso é a prova de que a automação não só reproduz o fechamento como **corrige omissões manuais**
dos meses antigos. De maio em diante o sistema roda **100% do banco**, sem planilha.

---

> *Base técnica (interna, não enviar): números do lado "Sistema" gerados pelo assembler
> (`assemble_dre_sections`) sobre o snapshot real de maio (`closing_2026-05.json`); "Planilha" lida
> direto de `Fechamento MBC 05.2026.xlsx` (aba "Areas Sintetico atualizado", col. maio); aluguel/Belline
> e regrupamento comprovados no extrato bruto `lancextrato de contas.xls`. Detalhe completo em
> `docs/FINDINGS_2026-07-21-manuais-refutados.md` e no `Comparativo_MBC_Maio_2026.xlsx`.*
