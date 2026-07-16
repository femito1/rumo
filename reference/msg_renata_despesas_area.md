Mensagem para a Renata — Despesas por Área (maio/2026)

(copiar o bloco abaixo — texto puro, com aba e célula em cada referência)

---

Oi Renata, tudo bem? Uma dúvida pontual sobre o Fechamento MBC 05.2026, na aba "Base_Resultado Mensal_V2", no bloco "Despesas Área". Em maio (coluna G) os subtotais por área são: Contencioso G204 = 2.276,22, Econômico G205 = 2.300,10, Arbitragem G206 = 1.204,47.

Reparei que os subtotais somam as linhas de detalhe com um deslocamento de uma linha para as famílias Viagens, Eventos, Material Gráfico, Patrocínio, Refeições e Cursos. Exemplo em Viagens: a célula G156, que está na linha rotulada em A156 como "Viagens - Direito Econômico", vale 1.358,72 — mas a fórmula do subtotal do Contencioso (G204) é que soma essa célula G156. Já em "Associações" o rótulo e o subtotal batem certinho: A129 "Associações - Contencioso" (G129 = 917,50) entra no Contencioso.

No SISJURI essa despesa de 1.358,72 é do RB (área Direito Econômico), o que bate com o rótulo A156 "Viagens - Direito Econômico". Então queria confirmar contigo: a intenção é alocar pela área do rótulo (nesse caso, Econômico) e o deslocamento na fórmula foi só um detalhe da planilha? Ou existe uma regra de alocação diferente que eu deva reproduzir?

Pergunto porque estamos automatizando essa aba direto do SISJURI e quero garantir que a área de cada despesa saia igual à sua. Uma última: a célula A154 "Viagens - Arbitragem e Compliance" (G154 = 68,00) não está sendo somada em nenhum subtotal — pode ter sido intencional, mas queria checar. Obrigado!

---

Fatos exatos (referência interna — NÃO enviar, é só o embasamento)

Aba "Base_Resultado Mensal_V2", competência maio = coluna G.

Subtotais "Despesas Área":
- Contencioso G204 = 2.276,22 = fórmula G125+G129+G140+G144+G148+G152+G156+G160
- Econômico G205 = 2.300,10 = G126+G130+G141+G145+G149+G153+G157+G161
- Arbitragem G206 = 1.204,47 = G127+G131+G139+G143+G147+G151+G155+G159

Família Associações — rótulo (col A) == subtotal (alinhado):
- A129 "Associações - Contencioso" / G129 = 917,50 → soma em Contencioso ✓
- A130 "Associações - Direito Econômico" / G130 = 700,10 → Econômico ✓
- A131 "Associações - Arbitragem" / G131 = 1.204,47 → Arbitragem ✓

Família Viagens — deslocamento de 1 linha entre rótulo (col A) e subtotal:
- A154 "Viagens - Arbitragem e Compliance" / G154 = 68,00 → nenhum subtotal referencia G154
- A155 "Viagens - Contencioso" / G155 = vazio → referenciada pelo subtotal de Arbitragem
- A156 "Viagens - Direito Econômico" / G156 = 1.358,72 → referenciada pelo subtotal de Contencioso (G204)
- A157 "Viagens - Institucional" / G157 = vazio → referenciada pelo subtotal de Econômico
- (mesmo padrão em Eventos, Material Gráfico, Patrocínio, Refeições e Cursos)

SISJURI para a linha de 1.358,72 (FINANCE.CONTASPAGAR, conta 020.090.0010): COD_ADVG = RB, centro de custo SIGLA = EDE (Direito Econômico), histórico "Despesa referente a passagem aérea e Uber de viagem". Área home do RB = Direito Econômico. Ou seja, DB e rótulo A156 concordam (Econômico); só a fórmula do subtotal difere (Contencioso).

Efeito líquido em maio:
- Planilha (subtotais G204/205/206): Conten 2.276,22 / Econ 2.300,10 / Arb 1.204,47 (Σ 5.780,79)
- SISJURI (por centro de custo, do bloco despesas_equipe_area do extract): Conten 917,49 / Econ 3.804,82 / Arb 1.272,47 (Σ 5.994,78)
- Difs: (a) a linha Viagens 1.358,72 (célula G156, rótulo Econômico) o SISJURI aloca no Econômico e a planilha soma no Contencioso; (b) a célula G154 "assento" R$ 68 não é somada em nenhum subtotal na planilha, o SISJURI a coloca em Arbitragem; (c) o SISJURI inclui em Econômico uma linha de R$ 146 (pão de queijo p/ reunião c/ cliente WM, centro de custo EDE) que na planilha não aparece nos subtotais de maio.

Pergunta objetiva: a alocação por área das "Despesas Área" deve seguir o rótulo/centro de custo (= o que o SISJURI traz) ou há uma regra de alocação específica por trás da disposição atual das fórmulas? E a célula A154/G154 (R$ 68, assento) deve entrar em Arbitragem?
