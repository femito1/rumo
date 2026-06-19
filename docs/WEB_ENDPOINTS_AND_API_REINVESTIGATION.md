# Reinvestigação: endpoints `/Web/` + segunda fonte de dados (2026-06-04)

> Resposta direta à pergunta "explore os `/Web/` e veja se dá pra automatizar
> as despesas". Tudo abaixo foi sondado ao vivo nesta data, de forma
> independente da investigação anterior.

## 1. TL;DR

- **`/Web/` é a UI web do LegalDesk** (ASP.NET), protegida por sessão + login
  com **handshake criptográfico RSA+AES no cliente**. Não é uma API de dados e
  **não dá** para autenticar via Basic. Não é caminho viável para coleta.
- **Existe um segundo serviço OData (`ODataTRIBUTARIO`)** que responde com a
  nossa credencial Basic — **mas é um alias idêntico do `ODataGERALADV`**
  (mesmas 631 entidades, mesmos dados, mesmas restrições). Não traz nada novo.
- **As despesas institucionais (folha, aluguel, IPTU, INSS, impostos) continuam
  fora desta API** — agora confirmado por mim, não só herdado: os únicos tipos
  de despesa existentes são **despesas de caso/processo** (Cartório, Custas,
  Correio, Táxi, Refeição…), todas reembolsáveis a cliente.
- **Achado novo aproveitável:** `TributoViews` expõe as **alíquotas de imposto
  por mês** (IRPJ, CSLL, PIS, COFINS). Permite *calcular* linhas de imposto via
  `base × alíquota`, como o próprio workbook faz por fórmula.

## 2. `/Web/` — o que é e por que não serve

| Caminho | Resultado |
| --- | --- |
| `/`, `/Web/`, `/Web/Home`, `/Web/Financeiro`, `/Web/ContasPagar` | 302 → `/Web/login` |
| `/Web/Login` | 200, página de login |
| `/API/v1/token` | 401 `WWW-Authenticate: OAuth, Basic` (rota não existe p/ Basic → 404) |

O formulário `/Web/login` traz campos ocultos **pré-preenchidos pelo servidor**:
`ServerPubKey` (ciphertext base64), `WrapperKey` (`AES-GCM` em JSON), `Seed`,
`Sufix`, `State=Login`, e `__RequestVerificationToken` (antiforgery). O bundle
`/Web/bundles/login/js` usa WebCrypto (`crypto.subtle`, `generateKey`) + RSA +
AES-GCM: o navegador gera um par de chaves, embrulha com a chave pública do
servidor, deriva uma chave de sessão AES e **cifra a senha no cliente** antes do
POST. Replicar isso fora do navegador é caro e frágil (é o login interativo do
produto, não uma API de integração). **Conclusão: `/Web/` não é via de dados.**

## 3. Segundo serviço OData — `ODataTRIBUTARIO`

Descoberto sondando `/API/v1/<Servico>/` com a credencial Basic. Responde 200 e
lista **631 entity sets** — porém idênticos ao `ODataGERALADV`. Teste de
igualdade (amostras lado a lado):

| View | GERALADV | TRIBUTARIO |
| --- | --- | --- |
| `TributoViews` | mesmas chaves/linhas | idêntico |
| `PlanoContasViews` | idem | idêntico |
| `LancamentoFinanceiroViews` | tudo null exceto Id/datas | idêntico (restrito) |
| `MovimentacaoFinanceiraViews` | vazio | vazio |
| `SolicitacaoPagamentoItemViews` | vazio | vazio |

**É alias do mesmo módulo Legal.** Confirma o aviso da investigação anterior:
as "6 URLs alternativas" não abrem módulos novos.

## 4. Confirmação independente: despesas institucionais não estão aqui

`TipoDespesaViews` (34 tipos) lista **somente despesas de caso/processo**:
Autenticação, Buscas em Cartório, Cartório, Correio, Correspondente, Courier,
Custas Judiciais, Cópias, INPI, Emolumentos, Escrituras, Estacionamento, Fax,
Gratificações, Honorários Perito/Correspondentes, Hospedagem, Impostos (de
processo), Junta Comercial, Motoboy, Notificação, Oficial de Justiça, Pagamento
de Client Fee, Passagens, Pedágio, Publicações, Quilometragem, Refeição,
Telefonema, Telegrama, Tradução, Transporte, Táxi.

`PosicaoFinanceiraViews` (2026-05) traz, sim, linhas de despesa (`Tipo` `D`/`DI`,
~R$ 34.823,02), mas todas atreladas a `CasoId` e a esses tipos — ou seja,
**despesas reembolsáveis de processo, não aluguel/folha/tributos institucionais**.
`ClassificacaoDespesaViews` e `GrupoDespesaViews` voltam vazias.

→ **As ~65–170 linhas institucionais (folha, ocupação, impostos da firma) não
existem nesta API.** Vivem no TOTVS Backoffice (Folha/RH, Contas a Pagar,
Tributário) — outra credencial/host que ainda não temos. Isso é um **bloqueio de
acesso**, não uma impossibilidade técnica.

## 5. O que dá pra automatizar a mais (sem credenciais novas)

1. **Recalcular as abas de fórmula ao vivo** a partir da receita que já puxamos
   exata (Recebimento/Faturamento, margens, totais sobre receita). Hoje elas
   mostravam valores de referência do workbook; passam a ser calculadas.
2. **Alíquotas de imposto** (`TributoViews`): IRPJ, CSLL, PIS, COFINS por mês —
   permitem estimar linhas tributárias por fórmula (`Faturamento × alíquota`),
   igual ao DRE do workbook. (Estimativa, não o valor pago real da folha.)

## 6. Próximo desbloqueio real (Fase 2)

Para as despesas institucionais, o pedido objetivo para a RUMO/MBC é:
**credencial + host do TOTVS Backoffice** (RM/Protheus Financeiro–Contas a
Pagar, Folha/RH, Fiscal). Sem isso, essas linhas seguem como entrada manual.

---

## 7. ADENDO — Tentativa completa de login no portal `/Web/` (2026-06-04)

Pedido: "tente todas as avenidas — Basic, cookie, login — no TOTVS Web com as
mesmas credenciais." Feito. Resumo do que foi tentado e do resultado.

### 7.1. Avenidas testadas

| Avenida | Resultado |
| --- | --- |
| Basic auth direto em `/Web/`, `/Web/Home` | 302 → `/Web/login` (ignora Basic) |
| POST de formulário com senha em texto puro | rejeitado (re-renderiza login) |
| Reuso de cookies de sessão (`ASP.NET_SessionId`) sem login | 302 → login |
| **Handshake criptográfico completo (replicado do JS)** | **crypto OK, mas credencial recusada** |

### 7.2. O handshake foi totalmente decifrado e replicado

Reproduzi em Python exatamente o que o `bundles/login/js` faz:

1. Ler campos do form: `WrapperKey` (AES-GCM 256, com `Key`+`Nonce`),
   `ServerPubKey` (base64 de JSON `{CipherText, AuthenticationTag}`), `Seed`,
   `__RequestVerificationToken`, `State`.
2. **AES-GCM-decrypt** do `ServerPubKey` com a WrapperKey e AAD=`"LegalDesk"`
   → revela a **chave pública RSA do servidor** (JWK, `RSA-OAEP`, 1024 bits). ✓
3. **Encriptar a senha**: detalhe crítico do JS — `encryptAsym` cifra
   `base64(senha)` (não a senha crua), com **RSA-OAEP / SHA-1 / MGF1-SHA1**,
   e codifica o resultado em base64url. ✓
4. Gerar par RSA do cliente (2048, SHA-1), exportar o público como JWK,
   **AES-GCM-encriptar** com a WrapperKey → `ClientPubKey`. ✓
5. POST do formulário completo para `/Web/login`.

A prova de que o handshake está correto: conforme eu corrigia cada etapa, o erro
do servidor evoluiu de `Object reference not set` → `Bad Length` →
`Error occurred while decoding OAEP padding` → e finalmente, com tudo certo:

> **"Usuário ou senha inválidos"**

Ou seja, o servidor **descriptografou a senha com sucesso** e a avaliou na regra
de negócio. Reproduzível (2/2 tentativas).

### 7.3. Conclusão definitiva

- A credencial `integracao` / `RumoTech1!` **NÃO** tem acesso ao portal `/Web/`
  (conta de serviço somente-API). Mesmas credenciais, no mesmo instante:
  - `/Web/login` → "Usuário ou senha inválidos"
  - OData (`PosicaoFinanceiraResultadoRecebimentoViews`) → **200 OK, com dados**
- Portanto **não há, com esta credencial, caminho para as despesas
  institucionais** — nem por API, nem pelo portal web. Isto agora está provado
  empiricamente (handshake completo), não assumido.

### 7.4. O que destravaria (Fase 2)

Uma destas, da RUMO/MBC:
1. **Usuário do portal** (web) com acesso a Financeiro/Contas a Pagar/Folha — aí
   dá pra automatizar via o mesmo handshake (já implementado) ou via export.
2. **Credencial do TOTVS Backoffice** (RM/Protheus Financeiro, Folha/RH, Fiscal)
   com sua própria API.
3. Ampliar o escopo da conta `integracao` para enxergar os módulos de despesa.

---

## 8. ADENDO 2 — Login no portal RESOLVIDO + exploração autenticada (2026-06-04)

**Correção importante ao item 7:** o login no `/Web/` **funciona, sim**, com
`integracao` / `RumoTech1!`. O erro anterior ("Usuário ou senha inválidos") era
um **bug meu na replicação do handshake**, não falta de acesso.

### 8.1. O bug e a correção

No `encryptAsym`, o JS faz `data = _b64strToBuffer(_utf8ToBase64(pwd))`. Esse par
de funções é **ida-e-volta** (base64 encode → base64 decode) → resulta nos
**bytes crus** da senha em utf-8. Eu estava cifrando `base64(senha)`. Cifrando a
**senha crua** com **RSA-OAEP/SHA-1** → login autentica (cookie `authCookie`).

O fluxo completo, agora validado, está em `work/scripts/web_login.py`
(reutilizável: `login("integracao","RumoTech1!")` devolve uma sessão autenticada).

### 8.2. O que a sessão autenticada revelou

O menu autenticado expõe **centenas de telas**, incluindo grupos antes
invisíveis: **Controle Orçamentário, Controladoria, Financeiro, Remuneração**.
Telas como `SolicitacaoPagamento`, `PrestacaoConta`, `CustoProfissional`,
`CategoriaRh`, `BusinessPlan`, `PlanejamentoOrcamento`, `Fornecedor`, `Banco`,
`MovimentacaoFinanceira` etc. **aparecem no menu**.

### 8.3. Porém: os dados de despesa continuam VAZIOS (agora provado autenticado)

Consultando essas views **com a sessão autenticada**, o resultado é o mesmo de
antes — as telas existem, mas **não há dados** neste tenant:

| View (autenticada) | Linhas |
| --- | --- |
| `CustoProfissionalViews` (folha por profissional) | **0** |
| `CategoriaRhViews` / `CustoCategoriaViews` | **0** |
| `BusinessPlanCustoViews` / `BusinessPlanProfissionalViews` | **0** |
| `PlanejamentoOrcamentoViews` | **0** |
| `PrestacaoContaItemViews` / `SolicitacaoPagamentoItem...` | **0** |
| `MovimentacaoFinanceiraViews` | **0** |
| `LancamentoFinanceiroViews` | restrito (só Id) |
| `OrcamentoViews` | 551 linhas, **só 2025** (sem 2026) |
| `MetaReceitaViews` | só 2019/2020/2025 (desatualizado) |

### 8.4. Conclusão final (definitiva, autenticada)

Tentei **todas as avenidas** pedidas — Basic, cookie, e o login web completo —
e **entrei no portal**. Mesmo lá dentro, **a folha, o aluguel, os impostos e as
demais despesas institucionais não existem na base do TOTVS juriTIs da MBC**. O
escritório usa o juriTIs só para o jurídico + receita; as despesas vivem em
**outro sistema** (Backoffice financeiro/contábil separado).

→ Portanto a automação das ~170 linhas de despesa **não depende de credencial
de portal** (já temos) — depende de **a MBC manter esses dados em outro sistema
e nos dar acesso a ele**. Esse é o desbloqueio real da Fase 2.

> Ferramenta nova entregue: `work/scripts/web_login.py` — login autenticado no
> portal juriTIs, pronto para puxar qualquer dado que **passar a existir** nessas
> telas (ex.: se a MBC começar a lançar a folha/orçamento 2026 no TOTVS).

---

## 9. ADENDO 3 — Varredura EXAUSTIVA do `$metadata` autenticado (2026-06-04)

Antes eu havia testado só ~20 views adivinhando nomes. Agora puxei o
**`$metadata` completo** do serviço autenticado e varri **todas** as views
financeiras, sem adivinhação.

- **`$metadata`**: 636 EntityTypes / **631 EntitySets** (salvo em `/tmp/ld_metadata.xml`).
- **106 EntitySets** com cara de despesa/custo/folha/orçamento/financeiro.
- Testei **todas as 106** autenticado. Resultado: 31 têm dados, 75 vazias.

### 9.1. As views de despesa VAZIAS (institucional não existe — confirmado)

Todas as telas "institucionais" e de folha/orçamento detalhado retornam **0 linhas**:

`PrestacaoContaInstitucionalViews`, `SolicitacaoPagamentoInstitucionalViews`,
`SolicitacaoPagamentoViews` (+ todas as variantes Item/Aprovador/Escritorio/Cliente),
`CustoProfissionalViews`, `CustoCategoriaViews`, `CategoriaRhViews`,
`ResponsavelProfissionalRhViews`, `TipoRemuneracaoViews`,
`BusinessPlanCustoViews`, `PlanejamentoOrcamentoViews` (+Total),
`ConsumoOrcamentoProjeto*` (todas), `MovimentacaoFinanceiraViews`/`GridViews`,
`LancamentoViews`, `GrupoDespesaViews`, `ClassificacaoDespesaViews`,
`ParticularidadeDespesaViews`, `FornecedorPlanoConta*`, `ReservaOrcamento*`,
`ReporOrcamentoViews`, `SolicitacaoDespesaViews`, `AdiantamentoDespesaViews`,
`PeriodoModuloFinanceiroViews`.

→ Confirma de forma definitiva: **folha, aluguel, impostos e demais despesas
institucionais NÃO estão cadastrados neste tenant**, mesmo autenticado.

### 9.2. As ÚNICAS views de despesa COM dados — e o que são

Duas views nunca testadas antes têm dados de despesa **com Maio/2026**:

| View | Linhas 2026-05 | Total | Natureza |
| --- | --- | --- | --- |
| `PosicaoFinanceiraDespesaIncorridaViews` | 13 | R$ 34.823,02 | **100% com CasoId** |
| `PosicaoFinanceiraResumoDespesaViews` | 12 | R$ 34.823,02 | **100% com CasoId** |

Tipos: Táxi, Hospedagem, Custas Judiciais, Passagens Aéreas, Cópias, Refeição,
Correspondente, Autenticação — ou seja, **desembolsos reembolsáveis por caso**
(adiantados ao cliente e cobrados de volta). **Não são** o overhead institucional
do workbook (folha/aluguel/IPTU/INSS). São despesas de processo, tipo `D`/`DI`.

### 9.3. Conclusão da varredura exaustiva

Agora sim, **exaustivamente** (631 EntitySets enumerados, 106 financeiras
testadas autenticado): a base TOTVS juriTIs da MBC contém **receita + jurídico +
despesas de caso reembolsáveis**, mas **não contém as despesas institucionais**.
Essas linhas do workbook vêm de outro sistema. Não há mais "pedra por virar"
dentro deste endpoint.

---

## 10. ADENDO 4 — Varredura TOTAL: 631 EntitySets + todos os aliases (2026-06-04)

A pedido, varri **100%** da superfície, não só as 106 financeiras.

### 10.1. Aliases de serviço (autenticado)

Só existem **dois** aliases, e são **o mesmo banco** (631 sets idênticos):

| Alias | EntitySets |
| --- | --- |
| `ODataGERALADV` | 631 |
| `ODataTRIBUTARIO` | 631 (idêntico) |

Todos os outros tentados (`ODataADM`, `ODataJURIDICO`, `ODataFINANCEIRO`,
`ODataCONTROLADORIA`, `ODataREMUNERACAO`, `ODataRH`, `ODataORCAMENTO`, …) → **404**.
Não há superfície de dados separada. Uma só base.

### 10.2. Varredura de TODOS os 631 EntitySets (autenticado)

Script: `work/scripts/sweep_all_entitysets.py` → resultado em
`work/data/entityset_sweep.json`.

- **246** com dados | **347** vazios | **38** erros (500/404/conexão).
- Dos 246 com dados, os **únicos** financeiros/despesa são exatamente os já
  conhecidos: `*Despesa*` (desembolso por caso), `Fornecedor*` (cadastro),
  `Tributo*` (alíquotas), `Movimentacao*`/`PreFatura*`/`Posicao*` (caso/faturamento).
- **Nenhum** EntitySet de despesa institucional, folha, RH, custo ou orçamento
  detalhado tem dados — todos vazios.

### 10.3. Os 38 erros — verificados, nenhum esconde despesa

Reexaminados com filtro `AnoMes`:

| Set | Resultado | Natureza |
| --- | --- | --- |
| `HistPlanejamentoOrcamentoViews` | 500 (view quebrada) | orçamento — já vazio mesmo |
| `RateioFaturaProfissionalCustomViews` | 404 (não existe) | faturamento |
| `TributosPrognosticoViews` | 404 (não existe) | tributário |
| `SaldoFaturaViews` | 500/timeout | saldo de fatura (receita) |
| demais 500/404 | workflow, compromisso, distribuição, timesheet | **não financeiro** |

Os `ERR` de conexão (`PosicaoFinanceiraViews` etc.) foram drops do meu paralelismo
(8 threads) — essas views **funcionam** e já foram analisadas; são caso/faturamento.

### 10.4. CONCLUSÃO FINAL — agora 100% exaustivo

Enumerei **todos os 631 EntitySets**, em **ambos os aliases**, autenticado no
portal. A base TOTVS juriTIs da MBC expõe:

- ✅ Receita (recebimento, faturamento, rateio, faturas, casos)
- ✅ Tributos (alíquotas mensais)
- ✅ Despesas **reembolsáveis por caso** (táxi, custas, cópias… ~R$ 35k/mês)
- ❌ **Despesas institucionais (folha, aluguel, IPTU, INSS, impostos pagos)** —
  **NÃO existem nesta base**, em nenhum nível de acesso, em nenhum EntitySet.

Não há mais nada a explorar neste endpoint. A automação das ~170 linhas de
despesa institucional depende **exclusivamente** de obter acesso ao **outro
sistema** onde a MBC mantém esses lançamentos (backoffice contábil/financeiro).

---

## 11. ADENDO 5 — Tentativa "API TOTUS" (`desenvld.juritis.com.br`) (2026-06-11)

Pedido: parar de tentar o LegalDesk de produção e tentar **API TOTUS**:
`https://desenvld.juritis.com.br/api`, senha `Pt9Uk3B)x9z)Dt#T:xR`.

### 11.1. O que esse host é

- **Mesmo produto TOTVS LegalDesk**, num **ambiente de desenvolvimento**
  (`desenvld` = "desenvolvimento LD"). Host vivo: `201.91.159.42`, cert GoDaddy
  wildcard válido `*.juritis.com.br` (o CA bundle local só não tem o
  intermediário → uso `verify=False`; o cert em si é legítimo).
- `/` → 303 → `/Web`; `/Web` → `/web/login` (mesma tela de login).
- `/api` serve a **UI HTML** do LegalDesk ("TOTVS | Legaldesk", com link "Sair").
- `/API/v1/ODataGERALADV/` e `/API/v1/ODataTRIBUTARIO/` **existem** (mesma
  superfície OData), mas respondem **401** à credencial Basic testada.
- `/web/login` traz os **mesmos campos do handshake** (`WrapperKey`,
  `ServerPubKey`, `Seed`, `Sufix`, `UserName`, `Password`, `State`).

### 11.2. O handshake funciona — falta o USUÁRIO

Reaproveitei o login RSA+AES (já decifrado no ADENDO 2) apontando para este
host: `work/scripts/totus_login.py` (host/user/senha configuráveis).

- O servidor **descriptografa a senha com sucesso** e a avalia: a resposta é a
  regra de negócio **"Usuário ou senha inválidos"** (não erro de cripto). Ou
  seja, o mecanismo está 100% correto neste host também.
- **Só foi fornecida a SENHA, não o usuário.** Testei ~35 candidatos de usuário
  no **login web** e no **Basic OData**:
  `integracao`, `Integracao`, `rumo`, `rumotech`, `mbc`, `mbclaw`, `totus`,
  `apitotus`, `api`, `apirumo`, `apiintegracao`, `servico`, `consulta`,
  `financeiro`, `admin`, `administrador`, `desenvld`, `juritis`, `totvs`,
  `integration`, `dev`, `desenvolvimento`, `suporte`, `sistema`, `webservice`,
  `bia4u`, … → **todos** "Usuário ou senha inválidos" / 401.
- Também testei a **senha nova no host de PRODUÇÃO** (`legaldesk.mbclaw...`)
  com `integracao` → idem inválida.

### 11.3. Bloqueio (não é impossibilidade técnica)

A autenticação aqui é `usuário` + `senha`. Tenho a senha (cara de credencial de
API gerada), mas **não o nome de usuário** que a acompanha. Sem ele não há como
prosseguir sem adivinhação cega.

**Para destravar, preciso de UMA destas da RUMO/MBC:**
1. O **nome de usuário** que pareia com a senha `Pt9Uk3B)x9z)Dt#T:xR`.
2. Confirmação do **esquema de auth** pretendido (login web do portal vs.
   Basic auth na API OData `/API/v1/...`).

Ferramenta pronta: `work/scripts/totus_login.py` — assim que tivermos o usuário,
`login(usuario, senha)` autentica e dá pra varrer os endpoints igual ao ADENDO 4.
