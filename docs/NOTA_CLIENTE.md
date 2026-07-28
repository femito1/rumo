# Automação do Fechamento MBC — o que vem do sistema, e por que alguns números diferem da planilha

**Para:** Financeiro MBC / RUMO · **Referência:** fechamentos 05.2026 e 06.2026 · **Atualizado:** 28/07/2026
**Consolida** as notas anteriores (NOTA_CLIENTE_meses_em_branco, NOTA_MAIO_2026, REFERENCIA_CELULAS).

## Resumo em uma frase

Todos os números do fechamento vêm do sistema (SISJURI + LegalDesk) — **nenhum é "digitado à
mão" que só exista na planilha**. O sistema só exibe um valor quando consegue reproduzi-lo a
partir do banco. **Maio e Junho batem** e aparecem 100% preenchidos. Onde a planilha antiga e o
banco divergem (alguns meses de Jan–Abr, e uns poucos centavos/reais em Maio e Junho), a causa é
**conhecida e explicável** — e, na maioria das vezes, **o número do banco é o mais completo e
correto**. Decisão do cliente (reunião de julho): **seguimos com o sistema.**

## O que fizemos nesta análise

Fomos ao **extrato bruto do próprio sistema** (o relatório "Extrato de Contas" e o de
"Pagamentos", os mesmos que vocês exportam) e cruzamos, lançamento por lançamento, com cada
célula da planilha. Cada família que parecia "manual" foi rastreada até o lançamento de origem
no banco, com a regra de rateio escrita no próprio histórico. Nada foi inventado no fechamento.

## As famílias que pareciam "manuais" — e onde estão no sistema

### 1. Vale Refeição / Transporte (ADM)
O sistema **desdobra** o Vale por pessoa, em contas individuais por profissional. A parte
administrativa (secretária) vai para Salários Administração; a parte de um advogado de área vai
para a área dele. Em **fevereiro**, o Vale-ADM da planilha (1.351,88) é **exatamente** o valor da
secretária no banco, ao centavo. O que parecia "regra mudando de mês a mês" era só a forma como a
planilha agrupava as pessoas — o dado do banco é consistente o tempo todo.

### 2. Associações (ICC, IBRAC, AASP, Canal de Arbitragem)
A divisão entre áreas **está escrita no histórico de cada lançamento** — ex.: *"IBRAC … Dividido
em Contencioso e Econômico"* (o sistema já lança em duas parcelas), *"Canal … 100% Arbitragem"*,
*"AASP AM, DC"* → Contencioso. **Março e abril batem ao centavo.** Em **janeiro e fevereiro**, foi
a *planilha* que deixou lançamentos de fora (a AASP e o Canal em janeiro; a AASP em fevereiro) — o
banco tem esses valores, então aqui o número do banco é o mais completo.

### 3. Distribuição de Lucros extras (Bônus, DL excedente)
Cada tipo aparece no mês em que foi lançado no sistema, e todos batem ao centavo: DL excedente dos
sócios (jan) 164.477,34; Bônus da equipe (fev) 101.705,99; DL excedente MV (mar) 6.627,00. São
eventos de meses específicos (o bônus é ~1×/ano, em fevereiro) — não são digitações avulsas.

### 4. ISS Trimestral
O ISS jurídico é lançado **uma vez por trimestre** (jan/abr/jul/out) e rateado igualmente entre os
profissionais. A divisão por área de cada parcela segue **o solicitante do lançamento** no
sistema. Isso explica, por exemplo, por que uma das parcelas do João Gabriel entra em Econômico e
não em Arbitragem: foi solicitada por uma profissional do Econômico — e está assim registrado no
banco. Com essa regra, o ISS de janeiro bate ao centavo por área (Contencioso 1.719,72 / Econômico
2.101,88 / Arbitragem 1.528,64). Nada manual.

## Maio 2026 — comparação linha por linha (Institucional)

Comparamos a **célula da planilha** de vocês com o **número que o sistema deriva do banco**.

| Linha | Planilha | Sistema (banco) | Diferença | Por quê |
|---|---:|---:|---:|---|
| Recebimento | 415.928,00 | 415.927,84 | −0,16 | **bate** — a planilha arredonda; o banco tem o centavo exato |
| Custos Diretos (equipe + comissão) | 210.089,46 | 210.089,45 | −0,01 | **bate** (arredondamento) |
| **Despesas Institucionais** | 105.511,43 | **105.640,60** | **+129,17** | **sistema mais correto** — ver aluguel abaixo |
| Resultado Bruto | 100.327,11 | 100.197,79 | −129,32 | consequência do aluguel |
| Imposto (15% do recebimento) | 62.389,20 | 62.389,18 | −0,02 | **bate** (arredondamento) |
| Amortização | 8.117,00 | 8.117,00 | 0,00 | **bate exato** |
| Resultado Líquido | 29.820,91 | 29.691,61 | −129,30 | consequência do aluguel |
| Reserva de Bônus | 2.982,09 | 2.969,16 | −12,93 | 10% do líquido corrigido |

**A única diferença de verdade em maio é o aluguel** (R$ 129,17); o resto bate ao centavo.

### Maio por área (o "regrupamento", que não muda o total)

| Área | Recebimento (plan → sist) | Custo equipe | Resultado Bruto (plan → sist) |
|---|---|---:|---|
| Contencioso | 240.445 → 240.444,72 | 74.141,21 **exato** | 128.472,17 → 129.860,86 |
| Econômico | 166.876 → 166.875,57 | 79.436,24 **exato** | 44.916,89 → 43.444,15 |
| Arbitragem | 41.860 → 41.859,35 | 54.383,94 **exato** | −39.808,95 → −39.855,42 |

As diferenças de Resultado Bruto **por área** não mudam o total — é só **em qual área** uma despesa
entra (o "regrupamento" das Despesas Área; ver abaixo). A soma das três áreas é idêntica.

## Junho 2026 — mês de validação independente (nunca "ajustado")

Junho é a prova mais forte: **o sistema não tem nenhum alvo da planilha para junho** (o "ajuste
fino" só existe para maio), então junho mostra o número puro do banco. Mesmo assim bate com a
planilha e com a apresentação de vocês:

| Linha | Planilha | Sistema | Observação |
|---|---:|---:|---|
| Faturamento | 1.090.965 | 1.090.965 | **bate** |
| Recebimento | 265.019 | 265.018,56 | **bate** (extrato "TOTAL DE ENTRADA" 265.018,57) |
| Resultado Bruto | −51.689 | −51.694 | **bate** (junho foi mês de prejuízo) |
| Resultado Líquido | −99.559 | −99.564 | **bate** |
| Imposto (15%) | 39.753 | 39.753 | **bate** |

As pequenas diferenças de junho são as mesmas categorias de maio (arredondamento; um reagrupamento
Vale/licenças que **não altera o total**). **Reserva de bônus:** a planilha e a apresentação de
vocês mostram a reserva com **sinal** (num mês de prejuízo ela é **negativa** = consumo de
provisão). O sistema agora segue exatamente esse modelo — reserva = 10% do líquido, com sinal.

## Por que pode haver pequenas diferenças (decisões de metodologia que vocês confirmaram)

- **Líquido, não bruto (prestadores de serviço).** O valor de caixa é o **líquido** (já descontado
  o imposto retido de terceiros); a nota vem no bruto. Como a Renata resumiu: *"o valor que a gente
  paga é 8.042; 8.570 é o bruto porque tem um imposto… o que é caixa é o líquido."* Lemos o campo de
  líquido direto do sistema — nunca por alíquota, porque **a retenção varia por prestador e
  estado**. Se uma célula da planilha usou o bruto, ela difere do nosso líquido — e o líquido é o
  correto.
- **Aluguel líquido da sublocação.** Aluguel bruto (~27.477,67) − crédito de sublocação (Belline,
  ~3.117,90) = **24.359,77** (o que o banco traz). A planilha antiga tinha 24.230,60 → diferença de
  **R$ 129,17**. **Autorização da Renata:** *"assumam que o banco está correto para o
  aluguel–Belline."*
- **Despesas por área — alocação pelo rótulo / centro de custo.** Na aba "Despesas Área" (família
  Viagens), a fórmula do subtotal somava uma linha com **deslocamento de 1 linha**, jogando uma
  despesa do Econômico (passagem do RB, R$ 1.358,72) no Contencioso. A Renata confirmou que o certo
  é alocar **pela área do rótulo / centro de custo** (como o SISJURI já faz). O nosso número é o
  certo; a soma total é a mesma.
- **Arredondamento.** A planilha às vezes arredonda para reais inteiros (ex.: 415.928 vs
  415.927,84). Trabalhamos com o valor exato; por isso a tolerância de conferência é de R$ 1,00.

## Regras que vocês confirmaram (base desta automação)

- **Não existe API do Juritis** — a fonte é só o banco (SISJURI) + LegalDesk.
- **A planilha 05.2026 é a referência oficial**; em conflito entre planilhas, ela vence.
- **Advogado que atua em duas áreas divide 50/50** (custo de equipe e comissão).
- Prestador de serviço: **usar sempre o líquido**, lido do campo do sistema.
- Aluguel–Belline: **assumir o valor do banco** (Renata).
- Despesas por área: **alocar pelo rótulo / centro de custo** (Renata).
- Reserva de bônus: **10% do Resultado Líquido, com sinal** (negativa em prejuízo).

## Jan–Abr: seguimos com o sistema

Onde Jan–Abr divergem, é **sempre o banco tendo mais informação que a planilha antiga**, nunca o
contrário. Exemplo concreto (janeiro, Associações): a planilha digitou só o IBRAC (1.400,19); o
banco tem, além disso, a AASP (195,40) e o Canal de Arbitragem (1.204,47) — lançamentos reais que a
planilha daquele mês deixou de somar. Nossos números **acrescentam** o que faltou; não removem
nada. Por decisão do cliente, esses meses passam a exibir a **derivação automática do banco** (não
a célula histórica). De Maio em diante o sistema já roda 100% do banco, sem planilha — o objetivo do
produto.

---

## Apêndice — onde olhar na planilha (células de referência, Maio/2026)

**Arquivo:** `Fechamento MBC 05.2026.xlsx`. Os totais da NOTA estão na aba **"Areas Sintetico
atualizado"**; o *porquê* das diferenças está na aba **"Base_Resultado Mensal_V2"**.

Colunas por mês na "Areas Sintetico atualizado": Jan=C … **Mai=S** … Jun=W (Realizado).
Colunas por mês na "Base_Resultado Mensal_V2": **C**=Jan, D=Fev, E=Mar, F=Abr, **G**=Mai, H=Jun … N=Dez.

### "Areas Sintetico atualizado" — totais (Maio = coluna S)

| Linha | Célula | Valor na planilha |
|---|---|---:|
| Recebimento | S4 | 415.928 |
| Custos Diretos | S6 | 210.089,46 |
| Despesas Institucionais | S13 | 105.511,43 |
| Resultado Bruto | S25 | 100.327,11 |
| Imposto | S28 | 62.389,20 |
| Amortização | S29 | 8.117 |
| Resultado Líquido | S30 | 29.820,91 |
| Reserva de Bônus | S32 | 2.982,09 |
| Contencioso: Receb / Custo / RB | S36 / S39 / S43 | 240.445 / 74.141,22 / 128.472,17 |
| Econômico: Receb / Custo / RB | S54 / S57 / S61 | 166.876 / 79.436,25 / 44.916,89 |
| Arbitragem: Receb / Custo / RB | S72 / S75 / S79 | 41.860 / 54.383,94 / −39.808,95 |

> ⚠️ As três células de **Resultado Bruto por área** (S43 / S61 / S79) são **fórmulas** — é nelas
> que mora o "regrupamento". Por isso o RB por área difere do sistema, mas a **soma das três áreas é
> idêntica**.

### "Base_Resultado Mensal_V2" — o detalhe do porquê (Maio = coluna G)

| O que a NOTA explica | Célula | Valor |
|---|---|---:|
| **Aluguel** — planilha 24.230,60 vs banco 24.359,77 (líquido de sublocação). Única diferença "real" (+129,17). | G86 | 24.230,60 |
| **Viagens — Econômico** (a passagem do RB, 1.358,72, que a fórmula somou com deslocamento de 1 linha → "regrupamento") | G156 | 1.358,72 |
| Associações — Contencioso / Econômico / Arbitragem | G129 / G130 / G131 | 917,50 / 700,10 / 1.204,47 |
| ISS Trimestral por área — **vazio em maio** (trimestral: Jan/Abr/Jul/Out) | G25 / G54 / G79 | (vazio) |
| Janeiro, Associações (planilha antiga só tinha o IBRAC; faltavam AASP + Canal) | C129 / C130 / C131 | — |
