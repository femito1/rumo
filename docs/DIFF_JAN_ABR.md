# Diferenças Jan–Abr 2026 — nossos números vs a planilha

**Para levar à Renata.** Cada diferença abaixo tem uma causa nomeada. Nada aqui é
"não sei de onde vem": o que sobra sem explicação é zero.

Gerado em 2026-07-30, contra os snapshots **extract v3** (todos re-extraídos hoje,
`stale=false`) e `reference/workbook/Fechamento MBC 06.2026.xlsx`.
Reproduzir: `cd backend && python -m scripts.diff_jan_abr`.

> **Junho fecha ao centavo** nas cinco células que a Renata validou linha a linha.
> Maio também (regra dura). As diferenças estão só em Jan–Abr, e a maior parte tem
> causa **na planilha**, não no sistema — o que é esperado: são meses digitados à mão
> antes de o sistema existir.

---

## 1. O que NÃO difere

Linhas que batem exatamente em todos os quatro meses:

| Linha | Jan | Fev | Mar | Abr |
|---|---|---|---|---|
| Faturamento | ✅ | ✅ | ✅ | ✅ |
| Receita (recebimento) | ✅ | ✅ | ✅ | ✅ |
| Impostos (15% do recebimento) | ✅ | ✅ | ✅ | ✅ |
| Amortização (8.117/mês) | ✅ | ✅ | ✅ | ✅ |

Isso importa: a **receita** — o número sagrado do LegalDesk — não tem divergência
nenhuma. Toda a diferença está em **despesa**.

---

## 2. Resumo: o efeito no resultado

| | Jan | Fev | Mar | Abr |
|---|---|---|---|---|
| Δ Despesas institucionais | +1.533,77 | +1.249,19 | −2.947,69 | −2.070,03 |
| Δ Custo de equipe | −3.156,84 | −1.267,37 | +3.652,42 | +3.708,24 |
| **Δ Resultado bruto** | **+1.623,07** | **+18,18** | **−705,03** | **−1.638,21** |
| **Δ Reserva de bônus** | **+162,31** | **+1,82** | **−70,50** | **−163,82** |

Em quatro meses o efeito líquido no resultado bruto é de **−702 reais** sobre um
acumulado de mais de 3 milhões de faturamento.

---

## 3. Causa de cada diferença — Despesas institucionais

Os componentes somam **exatamente** o delta total de cada mês (conferido).

### 3.1 Vale ADM — meses não ajustados · **causa: planilha** · a maior parcela

| | Jan | Fev | Mar | Abr |
|---|---|---|---|---|
| Δ Salários Administração | +134,00 | +1.032,35 | **−2.199,08** | **−2.199,20** |

Já discutido e resolvido nos áudios de 30/07: em mar/abr a planilha lançou o valor
cheio da transitória (as três pessoas) em Salários Administração, e o correto é só a
parte administrativa. A Renata pediu para **não corrigir** ("não vale a pena, o valor
é irrisório"). Nós derivamos por pessoa e batemos **fev e jun ao centavo**.

*Jan (+134,00) e Fev (+1.032,35) têm sinal oposto e vêm de convênio/férias no mesmo
bloco — a conferir junto, se ela quiser.*

### 3.2 Jan −35,52 no vale-transporte · **causa: planilha**

`C123` da Base_Resultado é uma soma digitada: **`=35,52 + 262,64`**. Os 262,64 são o
lançamento do sistema; os 35,52 não têm lançamento na competência, então não
conseguimos reproduzi-los.

**Pergunta:** de onde vêm os 35,52? Outra competência, ou um acerto?

### 3.3 Cursos e treinamentos de área · **causa: classificação (planilha)**

| | Mar | Abr |
|---|---|---|
| Δ Gestão do Conhecimento | −815,49 | +200,00 |

Em março a planilha lança **1.094,49 de "Cursos e Treinamentos - Arbitragem"** dentro
de Gestão do Conhecimento (institucional). Sendo um curso de uma área específica, ele
entra em **Despesas Área** — que é o que fazemos (`030.010.0180`).

### 3.4 Informática: bruto vs líquido · **causa: planilha** · nosso número é o correto

| | Jan | Fev | Mar | Abr | Mai | Jun |
|---|---|---|---|---|---|---|
| Δ Informática | 0,00 | −0,27 | **−237,60** | +110,00 | 0,00 | 0,00 |

Em março a diferença é **exatamente** `7.744,12 − 7.506,52 = 237,60` na conta
`040.040.0030`: a planilha usou o valor **bruto** e nós usamos o **líquido**
(`CPGNVALORLIQUIDO`), que é a regra que a própria Renata confirmou e que faz 10 de 10
famílias baterem em maio e todas em junho. Jan/Mai/Jun batem em zero, o que confirma
que o mapeamento está certo e que Mar/Abr são pontuais.

### 3.5 Diferenças de apresentação que somam ZERO · **nenhuma ação**

Duas contas ficam em famílias diferentes nas nossas telas e na planilha, mas **as duas
famílias entram no mesmo total** (`r198 = r85+…+r124+r137+…+r164+r180`), então o
efeito no número que interessa é **zero**:

| Conta | Nós | Planilha | Efeito no total |
|---|---|---|---|
| `020.090.0040` Eventos e Happy Hour | Endomarketing | Investimentos em Prospecção (jan/fev) / Endomarketing (mar–jun) | **0,00** |
| `020.060.0040` Seguro de Resp. Civil | Ocupação | Administrativas | **0,00** |

Vale registrar que a planilha **muda de critério de mês para mês** no primeiro caso:
o mesmo gasto de confraternização vai para `r141` (bloco Prospecção) em jan/fev e para
`r166` (Endomarketing) em mar–jun. Os nossos 1.171,71 de janeiro batem **exatamente**
com o `r141` dela — só a família é outra.

---

## 4. Custo de equipe

| | Jan | Fev | Mar | Abr |
|---|---|---|---|---|
| Δ Custo de equipe (Σ 3 áreas) | −3.156,84 | −1.267,37 | +3.652,42 | +3.708,24 |

Muda de sinal entre os meses, o que descarta uma regra nossa errada (uma regra errada
erraria sempre para o mesmo lado). A parcela identificada é o **Vale dos advogados**:
o critério de incluí-lo no custo da área foi confirmado pelo cliente em junho, e
junho fecha ao centavo (Contencioso 75.424,21 · Econômico 80.536,85).

**Pergunta:** em jan/fev o Vale dos estagiários entrou no custo das áreas na planilha,
ou ficou de fora?

---

## 5. Despesas por área — a fórmula deslocada · **causa: planilha**

Independente de tudo acima, e já explicado no painel "Diferenças conhecidas" do
sistema: nas linhas **204, 205 e 206** da Base_Resultado, as fórmulas de **jan a mai**
somam a linha de baixo em cinco famílias (Eventos e Happy Hour, Material Gráfico,
Patrocínio, Refeições, Viagens). Como o bloco está ordenado Arbitragem / Contencioso /
Direito Econômico / Institucional, cada área recebe a despesa da área seguinte:

```
Contencioso  soma  "... - Direito Econômico"   (deveria ser "... - Contencioso")
Econômico    soma  "... - Institucional"       (deveria ser "... - Direito Econômico")
Arbitragem   soma  "... - Contencioso"         (deveria ser "... - Arbitragem")
```

As cinco linhas de Arbitragem ficam de fora e as cinco de Institucional entram no
lugar. **As fórmulas de junho já estão corretas** — é por isso que junho fecha com o
nosso número. Isso também afeta o rateio da despesa institucional por área
(`r207 = r198 − r203`).

**Sugestão:** copiar as fórmulas de junho para jan–mai nessas três linhas.

⚠ E um alerta de leitura: no acumulado, o **Econômico parece bater** — mas isso é
efeito de compensação, não acerto. Mês a mês ele tem o **maior** erro bruto dos três
(Σ|Δ| = 15.426), com ~94% se anulando entre meses. Contencioso compensa 74% e
Arbitragem 34% — é só por isso que esses dois mostram resíduo visível.
`backend/scripts/audit_area_ytd_formulas.py` reproduz.

---

## 6. Perguntas, em ordem de valor

1. **Jan, R$ 35,52** (`C123`): de onde vem essa parcela digitada?
2. **Jan/Fev, custo de equipe**: o Vale dos estagiários entrou no custo das áreas?
3. **Jan +134,00 / Fev +1.032,35** em Salários Administração: convênio ou férias com
   critério diferente?
4. **Fórmulas 204/205/206 de jan–mai**: podemos considerar junho como o correto?

Nada disso muda o fechamento de junho, que está validado.
