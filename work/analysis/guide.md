Guia de entendimento do workbook
Fechamento MBC 02.2026
Análise do fluxo, das fórmulas e dos pontos críticos para futura automação

1. O que esta pasta faz
Ela funciona como um fechamento financeiro mensal de um escritório de advocacia. O objetivo é combinar: receita recebida, custo das equipes jurídicas, despesas institucionais, despesas específicas por área, impostos e amortização.
O resultado final aparece em visão institucional e em visão por área: Contencioso, Econômico e Arbitragem/Compliance.
Na prática, a planilha tenta responder duas perguntas ao mesmo tempo: (i) como o escritório performou no mês; e (ii) como essa performance deve ser atribuída entre as áreas.
2. Mapa do workbook
3. Fluxo lógico do cálculo
Passo 1 — Receita bruta institucional: em Base_Resultado Mensal_V2!C4 e D4 os valores de receita de honorários de janeiro e fevereiro estão digitados manualmente (279.821,07 e 319.233,58).
Passo 2 — Custos e despesas: a BASE acumula custo da equipe por área, despesas institucionais, despesas por área e impostos.
Passo 3 — Receita por área: Areas Sintetico atualizado pega o total institucional e reparte entre as áreas usando valores-base hardcoded e ajustes vindos de Resumo_Recebidas.
Passo 4 — Rateio: Rateio Mensal usa a participação do custo de cada equipe para repartir despesas institucionais e amortização.
Passo 5 — Saídas finais: DRE 2026, Fluxo consolidado e as abas de cada área mostram o resultado bruto, líquido, margem e comparação com orçamento.
4. O que significa cada termo jurídico/financeiro relevante
5. Respostas objetivas às dúvidas do seu colega
5.1 De onde vem a RECEITA DE HONORÁRIOS da BASE?
Dentro do workbook, ela não vem de fórmula nenhuma. Os valores estão digitados manualmente em Base_Resultado Mensal_V2!C4 (279.821,07) e D4 (319.233,58).
Ou seja: a pasta não mostra a origem automática dessa receita. Portanto, hoje a “fonte de verdade” do cálculo não é uma aba do arquivo; é uma entrada manual feita por quem fecha o mês.
Importante: a soma das áreas bate com a BASE por construção, porque Areas Sintetico atualizado distribui esse total entre as áreas. Mas isso não prova a origem do número.
Conclusão prática: a aba FATURAS não alimenta o modelo. Nenhuma fórmula do workbook referencia a aba FATURAS. Então a diferença BASE x FATURAS não é “erro de soma” do Excel; é diferença de origem/processo. Isso precisa ser validado com a RUMO/TOTVS.
5.2 Como saber os valores a repassar de uma área para outra?
A lógica está na aba Resumo_Recebidas 2025_2026.
A parte da esquerda (colunas A:K) registra casos/faturas com área originadora, área destino e o valor a creditar.
A parte da direita consolida essas realocações por mês e por par origem→destino.
A área final em Areas Sintetico atualizado é calculada com esses consolidados, não direto pela aba FATURAS.
Exemplo de janeiro/2026: Arbitragem perde receita e Contencioso/Econômico ganham crédito. Isso aparece assim:
5.3 De onde vêm C36 e G36 em Areas Sintetico atualizado?
C36 (jan/2026 – receita do Contencioso): = 57.491 + Resumo!M142 + Resumo!O153 = 72.613,09
Leitura: 57.491 é um valor-base digitado dentro da própria fórmula; depois entram a realocação de Arbitragem para Contencioso e metade da comissão.
G36 (fev/2026 – receita do Contencioso): = 133.203 + Resumo!M144 + Resumo!O155 = 138.600,13
Leitura: 133.203 também é um valor-base digitado dentro da fórmula; depois entram a realocação de fevereiro e metade da comissão.
Ponto importante para automação: essas duas células não são 100% rastreáveis a uma fonte única. Elas misturam (i) uma parcela-base hardcoded e (ii) ajustes vindos do Resumo_Recebidas.
5.4 De onde pegar AMORTIZAÇÃO?
A memória da amortização está na aba Amortização. Ela mostra investimentos antigos de 2022 sendo espalhados em 60 parcelas mensais.
O valor mensal estabilizado é 8.117,31. Para 2026, a própria aba mostra parcelas 45/60 e 46/60 em jan/fev.
Mas atenção: o modelo principal não puxa isso por fórmula. Em DRE 2026!C24:N24 e Areas Sintetico atualizado!C29/F29 o valor 8.117 está hardcoded.
Depois, esse valor institucional é rateado entre as áreas via Rateio Mensal.
Recomendação de automação: tratar a aba Amortização como a regra de negócio e gerar o 8.117,31 automaticamente; não depender dos hardcodes em DRE/Areas.
6. Como cada aba funciona, em linguagem simples
Base_Resultado Mensal_V2: É o coração do realizado mensal. A linha 4 guarda a receita de honorários; depois vêm os blocos de custo de equipe por área, despesas de cliente, despesas institucionais, impostos e totalizações por área. É a melhor aba para entender a mecânica de fechamento mês a mês.
Areas Sintetico atualizado: Transforma a visão institucional em visão por área. Mistura orçamento, realizado, variação, margem bruta, impostos e amortização. É a aba mais “gerencial”, mas também uma das mais manuais.
Resumo_Recebidas 2025_2026: Funciona como tabela de exceções/regras de crédito. Quando um caso pertence a uma área de origem e o crédito precisa ir para outra, essa aba registra e consolida. Também há casos com comissão de 10%.
DRE 2026: É a visão institucional do orçamento. Ajuda a comparar o que foi planejado para o ano com o que está sendo alocado nas áreas.
Orçamento 2026: Detalha o orçamento por linha de custo. É útil para automação de metas e rateios, mas depende de arquivos externos antigos.
Rateio Mensal: Reparte despesas institucionais e amortização conforme o peso do custo de cada equipe. É uma regra central do modelo.
FATURAS Analitico CENTRO CUSTO: É um extrato detalhado de faturas e pagamentos. Muito útil como base de conferência, mas hoje não alimenta o cálculo automaticamente.
Amortização: É uma memória de cálculo, quase um caderno de apoio. Mostra de onde saiu a parcela mensal institucional.
7. Riscos e fragilidades que você precisa saber antes de automatizar
Receita principal digitada manualmente na BASE.
Aba FATURAS está desconectada do restante do modelo.
Aba Amortização documenta a lógica, mas o cálculo ativo usa hardcodes de 8.117.
Há 4 vínculos externos com outros arquivos antigos (orçamento, BP 2025 e fechamento 2022).
Há fórmulas com #REF! em Areas Sintetico atualizado!Q79 e Q82.
Há várias fórmulas com números embutidos (hardcoded), como percentuais, parcelas, divisões, valores-base por área e impostos.
Em algumas linhas de fevereiro da aba Areas Sintetico atualizado existem células em branco onde janeiro tem fórmula equivalente, o que sugere preenchimento parcial/manual.
8. O que eu perguntaria para a RUMO para fechar as lacunas
Qual é o relatório fonte da Receita de Honorários que é digitada em Base_Resultado Mensal_V2!C4:D4? É TOTVS? Banco? Outro fechamento?
A aba FATURAS deve reconciliar com a BASE? Se não, quais ajustes explicam a diferença? (impostos, câmbio, créditos parciais, exclusões, provisões, comissão, outros).
Qual é a regra formal para área originadora x área destino? Existe tabela mestre ou é decidido caso a caso?
A comissão de 10% sempre é dividida meio a meio entre Contencioso e Econômico quando a origem é Arbitragem, ou isso vale só para alguns casos?
A amortização de 8.117,31 vai até quando? O correto é encerrar em dez/2026?
Quais dados são sempre manuais e quais deveriam vir do TOTVS?
9. Melhor desenho para automação
Criar uma camada de entrada padronizada: receita recebida, custos por pessoa/mês, despesas institucionais, despesas por área, impostos, amortização.
Separar regras de negócio em tabelas: mapeamento de pessoa→área, regra de rateio, regra de comissão, regra de realocação por caso.
Substituir hardcodes por tabelas de parâmetros e datas efetivas.
Tornar FATURAS e/ou relatório TOTVS a fonte oficial da receita, com uma tabela separada de ajustes manuais aprovados.
Gerar o resultado institucional primeiro; depois distribuir para áreas por regras claras e auditáveis.
Só no fim construir as abas de apresentação (DRE, área sintética, fluxo, meta).
10. Minha conclusão
Hoje este workbook funciona mais como um fechamento operacional/gerencial apoiado por pessoas do que como um modelo contábil totalmente integrado. O principal ganho de automação será: separar claramente fonte de dados, regra de negócio e apresentação.
Em termos práticos, os quatro pontos mais importantes são: (1) receita da BASE é manual; (2) FATURAS não alimenta o cálculo; (3) realocações entre áreas vêm de Resumo_Recebidas; (4) amortização está documentada, mas não conectada.
Apêndice: entregáveis anexos
MBC_formula_audit.xlsx: inventário de fórmulas, resumo por aba, links externos e pontos críticos.

[TABLE 0]
Resumo em 30 segundos: esta planilha não é um modelo 100% integrado. Ela mistura entradas manuais, fórmulas internas, consolidações por área e algumas referências externas antigas. O fluxo principal é: BASE_Resultado Mensal_V2 → Areas Sintetico atualizado / DRE 2026 → Rateio Mensal → abas finais de apresentação. As abas FATURAS e Amortização servem mais como apoio documental do que como fonte viva do cálculo.

[TABLE 1]
Aba || Papel no processo || Observação importante
Base_Resultado Mensal_V2 || Base operacional mensal do realizado || É a aba central do fechamento. Mistura inputs manuais com somas por categoria.
Areas Sintetico atualizado || P&L por área || Distribui a receita entre Contencioso, Econômico e Arbitragem usando valores-base + realocações da aba Resumo_Recebidas.
Resumo_Recebidas 2025_2026 || Motor de realocação entre áreas || Guarda casos em que a área originadora é diferente da área que recebe o crédito. Também consolida comissões.
DRE 2026 || Visão institucional orçada || Usa orçamento e alguns valores hardcoded; serve de comparação / meta.
Orçamento 2026 || Orçamento detalhado || Tem muitas referências externas antigas e premissas estáticas.
Rateio Mensal || Distribuição de despesas institucionais e amortização entre áreas || Usa o mesmo peso do custo das equipes.
FATURAS Analitico CENTRO CUSTO || Extrato analítico de faturas pagas/canceladas || Importante: nenhuma fórmula do modelo lê esta aba.
Amortização || Memória de cálculo do valor mensal de amortização || Importante: o modelo usa 8.117 hardcoded; esta aba explica a lógica, mas não alimenta por fórmula.
Meta (2), Fluxo consolidado, Institucional, Contencioso, Econômico, Arbitragem || Abas de apresentação / resumo || São saídas ou cortes do cálculo principal.

[TABLE 2]
Termo || Explicação
Honorários || Receita do escritório pelos serviços jurídicos prestados. Em linguagem simples: o faturamento de advocacia.
Contencioso || Área de litígios/processos judiciais e administrativos.
Arbitragem || Resolução privada de conflitos fora do Judiciário, perante tribunal arbitral.
Compliance || Atividades de conformidade, controles e prevenção de riscos regulatórios.
Econômico || Aqui parece ser a prática de direito concorrencial / CADE / regulatório econômico.
Repasse || Transferência interna de crédito/resultado de uma área para outra. Não é despesa externa; é reclassificação interna.
Originador || Área ou sócio que originou o cliente/caso.
Área destino || Área que deve receber o crédito da receita depois da realocação.
Comissão || Percentual interno separado de alguns recebimentos. Na aba Resumo_Recebidas aparece como “10% Comiss”.
Pro labore || Remuneração fixa pelo trabalho do sócio/administrador, parecida com salário.
Distribuição mensal fixa || Distribuição de lucros / retirada mensal combinada, separada do pro labore.
Orçado || Meta ou valor planejado.
Realizado || Valor efetivamente ocorrido.
Rateio || Divisão proporcional de um custo comum entre centros de custo / áreas.
Despesas institucionais || Custos comuns do escritório como aluguel, telecom, TI, consultoria etc.
Amortização || Reconhecimento mensal de um investimento antigo ao longo do tempo. Aqui é tratada como um custo institucional fixo.

[TABLE 3]
Mês || BASE – Receita de honorários || FATURAS – soma Valor Líquido || Diferença
Jan/2026 || 279.821,07 || 227.933,47 || 51.887,60
Fev/2026 || 319.233,58 || 287.269,76 || 31.963,82

[TABLE 4]
Célula || Fórmula || Valor || Leitura de negócio
Resumo!M142 || =J137+J142 || 13.731,12 || Realocação jan/2026 de Arbitragem para Contencioso
Resumo!M143 || =J147 || 13.202,60 || Realocação jan/2026 de Arbitragem para Econômico
Resumo!M136 || =M142+M143 || 26.933,72 || Total que sai de Arbitragem em jan/2026
Resumo!M153 || =I140+I145 || 2.781,94 || Comissão consolidada de Arbitragem em jan/2026
Resumo!O153 || =M153/2 || 1.390,97 || Metade da comissão vai para Contencioso
Resumo!O154 || =M153/2 || 1.390,97 || Metade da comissão vai para Econômico
Resumo!M144 || =J152 || 4.362,58 || Realocação fev/2026 de Arbitragem para Contencioso
Resumo!M155 || =I155 || 2.069,11 || Comissão consolidada de Arbitragem em fev/2026
Resumo!O155 || =M155/2 || 1.034,55 || Metade da comissão vai para Contencioso
Resumo!O156 || =M155/2 || 1.034,55 || Metade da comissão vai para Econômico