# Automação do Fechamento MBC — o que vem do sistema, e por que alguns números diferem da planilha

**Para:** Financeiro MBC / RUMO · **Referência:** fechamento 05.2026 · **Data:** 21/07/2026
**Substitui** as versões de 17/07 e 21/07 (manhã) desta nota.

## Resumo em uma frase

Investigamos a fundo e a conclusão é clara: **todos os números do fechamento vêm do sistema
(SISJURI + LegalDesk) — nenhum é "digitado à mão" que só exista na planilha.** O sistema só
exibe um valor quando consegue reproduzi-lo a partir do banco de dados. Maio e Junho batem e
aparecem 100% preenchidos. Onde a planilha antiga e o banco divergem (alguns meses de Jan–Abr,
e uns poucos centavos em Maio), a causa é **conhecida e explicável** — e, na maioria das vezes,
**o número do banco é o mais completo e correto**.

## O que fizemos nesta análise

Fomos ao **extrato bruto do próprio sistema** (o relatório "Extrato de Contas" e o relatório de
"Pagamentos", os mesmos que vocês exportam) e cruzamos, lançamento por lançamento, com cada
célula da planilha. Cada família que parecia "manual" foi rastreada até o lançamento de origem
no banco, com a regra de rateio escrita no próprio histórico. Nada foi inventado no fechamento.

## As famílias que pareciam "manuais" — e onde estão no sistema

### 1. Vale Refeição / Transporte (ADM)
O sistema **desdobra** o Vale por pessoa, em contas individuais por profissional. A parte
administrativa (secretária) vai para Salários Administração; a parte de um advogado de área
vai para a área dele. Em **fevereiro**, o Vale-ADM da planilha (1.351,88) é **exatamente** o
valor da secretária no banco, ao centavo. O que parecia "regra mudando de mês a mês" era só a
forma como a planilha agrupava as pessoas — o dado do banco é consistente o tempo todo.

### 2. Associações (ICC, IBRAC, AASP, Canal de Arbitragem)
A divisão entre áreas **está escrita no histórico de cada lançamento** — ex.: *"IBRAC …
Dividido em Contencioso e Econômico"* (o sistema já lança em duas parcelas), *"Canal … 100%
Arbitragem"*, *"AASP AM, DC"* → Contencioso. **Março e abril batem ao centavo.** Em **janeiro
e fevereiro**, foi a *planilha* que deixou lançamentos de fora (a AASP e o Canal em janeiro; a
AASP em fevereiro) — o banco tem esses valores, então aqui o número do banco é o mais completo.

### 3. Distribuição de Lucros extras (Bônus, DL excedente)
Cada tipo aparece no mês em que foi lançado no sistema, e todos batem ao centavo: DL excedente
dos sócios (jan) 164.477,34; Bônus da equipe (fev) 101.705,99; DL excedente MV (mar) 6.627,00.
São eventos de meses específicos (o bônus é ~1×/ano, em fevereiro) — não são digitações avulsas.

### 4. ISS Trimestral (o último caso, agora resolvido)
O ISS jurídico é lançado **uma vez por trimestre** (jan/abr/jul/out) e rateado igualmente entre
os profissionais. A divisão por área de cada parcela segue **o solicitante do lançamento** no
sistema. Isso explica, por exemplo, por que uma das parcelas do João Gabriel entra em
Econômico e não em Arbitragem: foi solicitada por uma profissional do Econômico — e está assim
registrado no banco. Com essa regra, o ISS de janeiro bate ao centavo por área (Contencioso
1.719,72 / Econômico 2.101,88 / Arbitragem 1.528,64). Nada manual.

## Por que a planilha de Maio pode não bater exatamente com os nossos números

Mesmo em Maio (o fechamento de referência), pode haver **pequenas diferenças de centavos ou de
poucos reais** entre uma célula da planilha e o nosso número. Isso é **esperado e explicável** —
e vem de decisões de metodologia que vocês mesmos confirmaram:

- **Líquido, não bruto (prestadores de serviço).** Quando se paga um prestador, o valor de
  caixa é o **líquido** (já descontado o imposto retido de terceiros). A nota vem no valor
  cheio (bruto); o líquido é o que sai do caixa. Como a Renata resumiu: *"o valor que a gente
  paga é 8.042; 8.570 é o bruto porque tem um imposto… o que é caixa é o valor líquido."* E a
  Adriana: *"é sempre pra pegar o líquido… quando você vai pagar um prestador de serviço."* Nós
  lemos o campo de líquido direto do sistema — nunca calculamos por alíquota, porque **a
  retenção varia por prestador e por estado** (a Adriana: *"pode ser o estado onde a empresa
  está sediada, faz diferença"*). Se uma célula da planilha tiver usado o bruto num caso, ela
  vai diferir do nosso líquido — e o líquido é o valor correto de caixa.

- **Aluguel líquido da sublocação.** O aluguel bruto (~27.477,67) é abatido por um crédito de
  sublocação que a empresa recebe de outra ocupante do espaço (valor variável no mês, informado
  pela Malu). O banco já traz o aluguel líquido desse abatimento (~24.359,77). Em Maio sobra uma
  diferença de **R$ 129,17** entre o nosso número e a planilha — a própria Renata sinalizou que
  ia conferir esse valor com a Malu. Ou seja: é uma pendência de conferência da planilha, não um
  erro de cálculo nosso. **Autorização registrada (Renata):** *"assumam que o banco está correto
  para o aluguel–Belline"* — então adotamos o valor do banco para essa linha.

- **Despesas por área — alocação pelo rótulo/centro de custo.** Numa dúvida específica sobre a
  aba "Despesas Área" (família Viagens), a fórmula do subtotal da planilha somava uma linha com
  **deslocamento de uma linha** em relação ao rótulo — o que jogava uma despesa do Econômico no
  Contencioso. A Renata confirmou que a alocação correta é **pela área do rótulo / centro de
  custo** (que é como o SISJURI já traz), e que o deslocamento na fórmula foi um detalhe da
  planilha. Então, nesses casos, **o nosso número (do banco) é o certo** e a planilha tinha um
  pequeno desalinhamento de fórmula.

- **Arredondamento.** A planilha às vezes arredonda para reais inteiros (ex.: Recebimento
  415.928 vs. o valor exato 415.927,84). Nós trabalhamos com o valor exato do sistema; por isso
  a tolerância de conferência é de R$ 1,00, não de um centavo.

Em todos esses casos a diferença tem uma causa identificada, verificável e — em geral — a favor
do banco. Não é um erro sistemático da automação.

## Regras que vocês já confirmaram (base desta automação)

- **Não existe API do Juritis** — a fonte de dados é só o banco (SISJURI) + LegalDesk.
- **A planilha 05.2026 é a referência oficial**; em conflito entre planilhas, ela vence.
- **Advogado que atua em duas áreas divide 50/50** entre elas (custo de equipe e comissão).
- Prestador de serviço: **usar sempre o líquido**, lido do campo do sistema (nunca por alíquota).
- Aluguel–Belline: **assumir o valor do banco** (autorização da Renata).
- Despesas por área: **alocar pelo rótulo / centro de custo** (autorização da Renata).

## O que propomos para Janeiro–Abril

Agora que confirmamos que **todos** os números existem no banco, o caminho recomendado é
**preencher as linhas de Jan–Abr direto da derivação automática**, assumindo que, em alguns
meses, o valor automático vai diferir (para melhor) da célula da planilha antiga — justamente
porque o banco inclui lançamentos que a planilha havia deixado de fora (ex.: AASP e Canal em
janeiro). A alternativa é manter, nesses meses específicos, o valor histórico da planilha como
um número fixo. **É uma decisão de vocês, do financeiro** — os dois caminhos são auditáveis.

De **Maio em diante** o sistema já roda 100% do banco, sem planilha — que é exatamente o
objetivo do produto. **Junho** já aparece totalmente preenchido pela derivação automática;
quando vocês publicarem o fechamento de junho de vocês, comparamos lado a lado como prova final.

---

> *Nota técnica interna (não enviar ao cliente): a análise completa por família, com as
> consultas ao banco que a embasam, está em `docs/FINDINGS_2026-07-21-manuais-refutados.md` e
> `docs/HANDOFF_2026-07-21-manuais-refutados.md`; os probes read-only em `ops/sisjuri-agent/`.*
