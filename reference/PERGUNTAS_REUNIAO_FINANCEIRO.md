# Reunião financeiro MBC — apoio visual às perguntas
### Planilha: `Fechamento MBC 05.2026.xlsx` · aba **`Base_Resultado Mensal_V2`** · colunas C=jan … G=mai

> Como usar: abra a planilha nessa aba e vá direto na célula citada. A coluna
> "o que aparece na célula" é **exatamente** o conteúdo digitado (fórmula ou número).
> A pergunta é sempre a mesma ideia: **de onde veio esse número que vocês digitaram?**

---

## Pergunta 1 — Vale Refeição / Vale Transporte da equipe ADM  ⭐ (a que mais trava)

Linhas **122 e 123** (dentro de "Salários Administração", linha 116).

| célula | mês | o que aparece na célula | valor |
|---|---|---|---|
| `C123` | jan | `=35.52+262.64` | 298,16 |
| `E123` | mar | `=543.22+674` | 1.217,22 |
| `E122` | mar | `2766` (digitado) | 2.766,00 |
| `G122` | mai | `2719.9` (digitado) | 2.719,90 |

**Vale-ADM total por mês:** jan 1.127,96 · fev 1.351,88 · mar 3.983,22 · abr 3.421,36 · mai 3.326,94

O que mostrar: essas células são **números batidos à mão** (às vezes uma soma de
dois valores). Não existe conta de "Vale ADM" no sistema — só achamos Vale de
estagiário/área. **Pergunta:** *"Quando vocês preenchem o Vale Refeição-ADM e o
Vale Transporte-ADM, de qual documento tiram esse número? (fatura do cartão VR/VT,
relatório da folha, e-mail do RH?) Podem nos mostrar a origem do valor de maio,
2.719,90 + 607,04?"*

---

## Pergunta 2 — Transferências de recebimento entre áreas

A base por área já sai do sistema, mas vocês reclassificam recebimento entre áreas
(o que a antiga aba "Resumo_Recebidas" fazia). Mostrar a aba **`Areas Sintetico
atualizado`** / abas por área (`Contencioso`, `Econômico`, `Arbitragem`) e a linha
de recebimento de cada uma.

O que mostrar: os totais por área não fecham só com o rateio automático — há um
ajuste manual entre elas. **Pergunta:** *"Quando vocês passam recebimento de uma
área para outra no fechamento, isso segue uma regra fixa ou é decidido caso a caso?
Quem decide e olhando o quê?"*

---

## Pergunta 3 — Distribuição de Lucros extras

Linhas **192–195** ("Distribuição de Lucros extras", começa na linha 191).

| célula | mês | o que aparece na célula |
|---|---|---|
| `D192` (Bônus equipe) | fev | `=94696+7009.84` |
| `C193` (DL excedente sócios) | jan | `=70790.94+46843.2+46843.2` |
| `E194` (DL excedente MV) | mar | `6627` (digitado) |

O que mostrar: são valores digitados/somados à mão, aparecem só em alguns meses.
**Pergunta:** *"Esses valores de distribuição extraordinária (bônus, DL excedente
sócios/MV, repasse Cacione) — vocês recebem de quem? É decisão dos sócios informada
a vocês, ou sai de algum relatório? Com que frequência?"*

---

## Pergunta 4 — Despesas de Área: reclassificação manual entre áreas

Linhas **204–206** (Despesas Área por área). Repare na fórmula da linha 205:

| célula | o que aparece na célula |
|---|---|
| `G204` Contencioso | `=G125+G129+G140+G144+G148+G152+G156+G160` |
| `G205` Econômico | `=G126+G130+G141+G145+G149+G153++G157++G161` |
| `G206` Arbitragem | `=G127+G131+G139+G143+G147+G151+G155+G159` |

E as **Associações** (linhas 129–131), que vocês dividem à mão:

| célula | mês | o que aparece na célula |
|---|---|---|
| `C129` Contencioso | jan | `=1400.19/2` |
| `E129` Contencioso | mar | `=(4287.67/3)+(1400.19/2)+217.4` |
| `D131` Arbitragem | fev | `=+(4287.67/3)+1204.47` |

O que mostrar: uma mesma despesa (ex.: 1.400,19) é **partida à mão** entre áreas
(÷2, ÷3, +217,40). **Pergunta:** *"Para dividir uma despesa institucional entre as
áreas, vocês usam sempre a mesma regra (metade, um terço…) ou é decisão de vocês em
cada caso? Existe uma tabela de qual despesa vai para qual área?"*

---

## Pergunta 5 — Cursos/Treinamento: a parte ADM é descartada?

Linha **158** "Gestão do Conhecimento" = `=SUM(G159:G163)`; a linha **161** "Cursos
e Treinamentos - Direito Econômico" (mai) = `1600`.

O que mostrar: em abril, o sistema tinha um curso com parte de área (1.450) + parte
ADM (200), e a planilha só considera a parte da área. **Pergunta:** *"Quando um
curso tem uma parte de uma área e uma parte administrativa, vocês sempre pegam só a
parte da área e descartam a parte ADM? É intencional?"*

---

## Regras que vocês JÁ confirmaram (não perguntar de novo)

- Não existe API do Juritis — só acesso ao banco de dados. ✔
- Planilha oficial = **05.2026**. ✔
- Advogado em duas áreas: **sempre divide em 2 (50/50)**. ✔
- O número de verdade é **o da planilha** (o financeiro não mexe no banco). ✔
