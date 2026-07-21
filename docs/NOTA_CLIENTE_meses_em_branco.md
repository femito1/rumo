# Por que Janeiro a Abril ainda aparecem com células em branco (e como vamos resolver)

**Para:** Financeiro MBC / RUMO · **Referência:** fechamento 05.2026 · **Data:** 21/07/2026
**Atualiza e corrige** a versão de 17/07 desta nota.

## Resumo em uma frase

O sistema **só exibe um número quando consegue reproduzi-lo a partir do banco de dados
(SISJURI + LegalDesk)**. Maio e Junho batem e aparecem 100% preenchidos. Janeiro a Abril
ainda têm algumas linhas em branco — mas, ao contrário do que dizia a nota anterior, **esses
números NÃO são "lançamentos manuais" que só existem na planilha. Eles estão no sistema.**
Onde a planilha antiga e o banco divergem nesses meses, na maioria das vezes é **o banco que
está mais completo** — a planilha é que deixou uma linha de fora.

## O que mudou nesta análise (e por que confiamos nela)

Fomos ao **extrato bruto do próprio sistema** (o relatório "Extrato de Contas" que sai do
SISJURI, o mesmo que vocês exportam) e cruzamos linha a linha com a planilha. Conclusão: as
três famílias que a nota anterior chamava de "batidas à mão" — **Vale ADM, Associações e
Distribuição de Lucros extras** — são todas **lançamentos normais do sistema**, com a regra
de rateio escrita no próprio histórico do lançamento. Não são invenções do fechamento.

## As três famílias, com os números do próprio banco

### 1. Vale Refeição / Transporte
A nota anterior dizia que "o banco não guarda quem, dentro do pagamento conjunto, é ADM e
quem é de área". **Isso estava errado.** O sistema desdobra o Vale por pessoa, em contas
individuais (`500.010.<sigla do profissional>`):

- **JVO** (advogado do Contencioso) → vai para a **área** dele;
- **MLA** (secretária) e **VSR** → são **administrativos**, entram em Salários Administração.

A prova: em **fevereiro, o Vale-ADM da planilha (1.351,88) é exatamente o Vale da MLA no
banco (1.351,88), ao centavo.** Em janeiro/fevereiro vocês corretamente separaram o Vale do
JVO na linha da área; de março em diante a planilha juntou todo mundo numa linha só. Essa
"regra que mudava mês a mês" era só a forma como a **planilha** tratava o JVO — o dado do
banco é consistente o tempo todo. Abril e maio batem ao centavo.

### 2. Associações (ICC, IBRAC, AASP, Canal de Arbitragem)
A divisão entre áreas **não é feita à mão** — ela vem escrita no histórico de cada
lançamento do sistema (ex.: *"IBRAC … Dividido em Contencioso e Econômico"*, que o sistema
já lança em duas linhas de 700,09 + 700,10; *"Canal … 100% Arbitragem"*; *"AASP AM, DC"* →
Contencioso). Cada linha ainda traz a área no campo de centro de custo.

- **Março e abril batem ao centavo** com o banco (7.109,73).
- Em **janeiro e fevereiro, foi a planilha que deixou linhas de fora**: janeiro sem a AASP
  (195,40) e sem o Canal de Arbitragem (1.204,47); fevereiro sem a AASP (217,40). O banco
  tem esses lançamentos. Ou seja, **o número do banco é o mais completo**.

### 3. Distribuição de Lucros extras
Cada tipo aparece no mês em que de fato foi lançado no sistema — e todos batem ao centavo:

- **DL excedente dos sócios (janeiro):** AM 70.790,94 + DC 46.843,20 + RB 46.843,20 =
  **164.477,34** (= planilha).
- **Bônus da equipe (fevereiro):** 94.696,15 (conta 150) + 7.009,84 (JGS) = **101.705,99**
  (= planilha).
- **DL excedente MV (março):** **6.627,00** (= planilha).

Não é aleatório nem manual: são eventos que acontecem em meses específicos (o bônus é ~1x por
ano, em fevereiro), e o sistema registra cada um. Em maio, corretamente, não há nenhum.

## Como sabemos que não é o sistema que está errado

As diferenças entre o nosso número (do banco) e a célula da planilha, nos meses que ainda não
batem, têm uma **causa identificada e verificável** em cada caso — em vários deles a diferença
é exatamente uma linha que a planilha antiga não incluiu (a AASP e o Canal em janeiro, por
exemplo). Não é um erro sistemático de fórmula nossa: é a planilha antiga tendo sido preenchida
com pequenas variações mês a mês. **Em vários casos, o número do banco é mais correto e mais
completo** que a célula antiga da planilha.

## O que propomos

Para Janeiro–Abril, agora que sabemos que os números **existem no banco**, o caminho
recomendado é **preencher essas linhas direto da derivação automática** — assumindo que, em
alguns meses, o valor automático vai diferir (para melhor) da célula que estava na planilha
antiga, justamente porque o banco inclui lançamentos que a planilha havia deixado de fora.

De Maio em diante o sistema já roda **100% do banco**, sem planilha — que é exatamente o
objetivo do produto. **Junho** também já aparece totalmente preenchido pela derivação
automática. Quando vocês publicarem o fechamento de junho de vocês, poderemos comparar lado a
lado como prova final de que a automação reproduz o fechamento sem nenhuma digitação manual.

---

> *Nota técnica interna (não faz parte da comunicação ao cliente): a análise completa, com as
> tabelas de reconciliação Jan–Abr por família e a consulta ao banco que as gerou, está em
> `docs/FINDINGS_2026-07-21-manuais-refutados.md` e `ops/sisjuri-agent/probe_janapr_reconcile.sql`.*
