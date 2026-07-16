# PROJECT_STATUS.md

> **Living status document. Read this first.**
> Agents and engineers working on this repo should treat this file as the
> single source of truth for *current* state, limitations, and plans.
> Keep it updated at the end of every milestone. When it disagrees with
> older docs, this file wins (except for the sacred LegalDesk numbers, which
> live in `docs/LEGALDESK.md`).

**Last updated:** 2026-07-14
**Product:** RUMO — Plataforma de Fechamento Mensal Multi-Cliente
**Architecture:** `docs/DESIGN.md` · **LegalDesk:** `docs/LEGALDESK.md`

---

## 0. Client-confirmed business rules (DO NOT re-ask — 2026-07-10)

These were confirmed directly by the client (RUMO/MBC finance) and are now
canonical. An agent must NOT ask the user about these again.

> **Product endgame (confirmed 2026-07-13):** the site must **fully replicate the
> workbook** — every tab, faithful to the layout — not just the DRE/KPIs. The
> workbook (`Fechamento MBC 05.2026.xlsx`) is the source of truth; every displayed
> number must tie to it (hard rule: blank if it doesn't match). Data comes only
> from LegalDesk (revenue) + the SISJURI Oracle DB (costs/expenses); no Juritis API.

> **2026-07-10 follow-up meeting + source deep-dive:** the client was UNHAPPY with
> the current site numbers. `docs/MEETING_2026-07-10.md` is now the authoritative
> spec for the DRE fixes (all reconciled to the centavo against the May dashboard):
> **Imposto = 15% do Recebimento** (maio 62.389,20, não 7.510); **Amortização
> 8.117/mês**; **Resultado Líquido = Bruto − Imposto − Amortização** (maio 29.821);
> **Reserva de bônus = 10% do líquido**; **Custo direto = Custo equipe + Participação
> + Comissão**; **Recebimento por área** vem do Demonstrativo LegalDesk (Ambiental
> soma em Arbitragem, + linha "Não Alocados"); **Vale-ADM** está em `200.010.0010`
> (transitória, por histórico VR/VT); rateio institucional usa só despesas de EQUIPE.
> Também: **remover "Faturas emitidas"** do produto.
>
> **IMPLEMENTADO (2026-07-10):** (1) Imposto = 15% do recebimento
> (`workbook_layouts.imposto_sobre_recebimento`; deixou de somar o razão) — fev
> 47.885,04 / mai 62.389,20, bate com o dashboard; cadeia líquido/reserva
> corrigida por consequência. (2) **Regra dura** `app/closing/verification.py`:
> célula Realizado que divergir do alvo do workbook além de R$ 0,01 fica em branco
> ("ainda não temos"); overlay `targets` passa por `assemble_dre_sections`.
> (3) Recebimento por área agora funde **Ambiental→Arbitragem** e exclui
> **"Não Alocados"** (`match_area`). (4) **Custos Diretos = Custo equipe +
> Participação/Comissão** (`RealizadoInputs.custos_diretos`; Institucional
> Resultado Bruto passa a subtrair comissão) — fev 218.453,74. (5) KPI "Faturas
> emitidas" removido. Backend **179 testes**, frontend **49**; ruff/mypy/eslint/tsc
> limpos.
>
> **REGRA DURA LIGADA (2026-07-10):** targets extraídos do workbook autoritativo
> (`scripts/build_workbook_targets.py` → `app/closing/workbook_targets_2026.json`),
> carregados por `app/closing/workbook_targets.py` e passados via `provider.py` →
> `AssemblerSource` → `assemble_dre_sections(targets=...)`. Meses sem workbook =
> no-op. Números/layout documentados em `docs/SISJURI_DB.md` ("Workbook targets")
> e `docs/MEETING_2026-07-10.md` §VI. Backend **183 testes**, frontend **49**.
> PENDENTE: custo equipe por área do SISJURI (Econômico mai alvo 79.436,24) e
> rateio institucional só de EQUIPE — para as células saírem do branco e exibirem
> o valor; DL extras; Vale-ADM (200.010.0010).
>
> **IMPLEMENTADO (2026-07-13) — pontos da reunião 10JUL2026:**
> - **PONTO 12 — Amortização manual por ANO.** A amortização deixou de ser só a
>   constante `AMORTIZACAO_MENSAL=8117`. O usuário informa UM valor anual (linha
>   `amortizacao` do orçamento, já editável no `BudgetEditor` com preview `/mês`);
>   a linha mensal do DRE = anual/12. `RealizadoInputs.from_snapshot` recebe
>   `amortizacao_mensal` (do orçamento) e cai no default 8.117 quando ausente/zero.
>   Regra dura do workbook intacta (alvo 8.117 em todos os meses do book).
> - **PONTO 13 — Orçamento Despesa por equipe.** `despesas_equipe` virou linha
>   orçável; `BudgetEditor` ganhou uma seção "Orçamento Despesa por equipe"
>   (Contencioso/Econômico/Arbitragem). Armazenado por `(área, line_key)` no
>   plumbing de orçamento existente; flui para a coluna Orçado de cada aba de área
>   (`_area_rows` já lia `orc.get(DESPESAS_EQUIPE)`).
> - **PONTO 16 — Bônus equipe da conta 150.000.0000.** `_base_resultado_rows` lê
>   uma chave de snapshot `bonus_equipe` (Σ da conta 150.* — bloco novo no
>   `extract.sql`), preenchendo a linha "Bônus equipe" do bloco "Distribuição de
>   Lucros extras"; um `distribuicao_extras.bonus_equipe` explícito ainda vence.
>   Em branco ("ainda não temos") quando ausente — robusto ao split de sócios
>   (PONTO 17, tarefa do RUMO) chegar depois. Conta documentada em `SISJURI_DB.md`.
> - **PONTO 18 — Drill-down por profissional.** Na aba Base_Resultado, as seções
>   "Custo equipe - {área}" agora são clicáveis: expandem para as linhas por
>   profissional daquela área (recolhidas por padrão). Drill-down genérico no
>   `RichTabView` (chaveado nos grupos `custo_*`).
>
> Backend **192 testes**, frontend **52**; ruff/mypy/eslint/tsc limpos.
>
> **IMPLEMENTADO (2026-07-13, tarde) — validação com dados SISJURI ao vivo (maio):**
> Sessão dedicada com o operador rodando probes/extract no RDP `MBC-LDESK01`. Tudo
> commitado e no `main`; extract re-rodado ao vivo (HTTP 200, snapshot fresco no
> Supabase). Contra o snapshot REAL de maio, batem ao centavo com o workbook:
> - **T1 — Custo equipe por área** (2 correções): Vale (`custo_equipe_area`,
>   `500.010.<SIGLA>`) NÃO entra no custo direto; convênio (`030.010.0110`) usa a
>   "Parte MBC" de `convenio_memo`. Contencioso **74.141,21** · Econômico
>   **79.436,24** · Arbitragem **54.383,94**; Σ 207.961,39.
> - **T2 — Comissão** (bug null resolvido): a linha `030.010.0120` tem
>   `LANCAMENTO.LANCPROFDEST` NULL (sigla só no histórico); o extract passou a ler
>   `CONTASPAGAR.COD_ADVG`. Ao vivo: EHF 2.128,06 → Econômico. Custos Diretos
>   **210.089,45** (wb 210.089,46). Comissão derivada agora aparece nas abas de área
>   mesmo sem ledger (`has_comissao_deriv`).
> - **Regra dura: tolerância R$0,01 → R$1,00.** O workbook arredonda para reais
>   inteiros (mai Recebimento 415.928 vs sacred 415.927,84); a tolerância antiga
>   zerava toda a cauda institucional. Drift máx. em células deriváveis = R$0,16.
> - **T4 — Vale-ADM** de `200.010.0010` (transitória, histórico "VR/VT Mensal", ao
>   vivo 3.326,94) + FGTS-ADM (`020.050.0060`) reclassificado p/ Impostos →
>   **Salários Administração 12.344,91** (bate exato).
> - **Bug de rótulo:** `030.010.0120` "com**iss**ões" era classificado como imposto
>   (substring "iss"); `is_comissao_account` + match por palavra inteira corrigem.
> - **T3/T6 — Bônus equipe (150.*) / DL extras:** bloco roda ao vivo (null em maio, correto —
>   150.* só posta ~1×/ano em fev); linhas em branco quando ausentes.
> - **Contas Transitórias (correção do cliente):** é uma CLASSE de contas
>   (`200.010.0010/.0020/.0030/.0050/.0060`, `200.020.0030`, `300.010.*`), não um hub.
>   O sistema **desdobra** cada uma nas contas de despesa via o campo `ORIENTAÇÃO`
>   do LANCAMENTO/CONTASPAGAR. Documentado em `SISJURI_DB.md`.
> Backend **208 testes**, frontend **52**; ruff/mypy limpos. CI: uma falha do
> frontend foi blip de infra do GitHub ("Failed to resolve action download") — não
> do nosso código; backend verde em todos os commits.
>
> **IMPLEMENTADO (2026-07-13, noite) — DESPESAS INSTITUCIONAL DECODIFICADA (T5):**
> A reunião com o financeiro (Renata) + probes fecharam o mistério das despesas. A
> regra, provada ao centavo contra o workbook (**10/10 famílias**, resíduo total
> **R$129,17** = pendência do próprio cliente com a Malu, não nossa):
> - **Despesa = LÍQUIDO, não bruto.** O workbook lança o valor líquido (net do
>   imposto retido de terceiros) dos prestadores; o `GERENC` dá o bruto. Fonte do
>   líquido = **`FINANCE.CONTASPAGAR.CPGNVALORLIQUIDO`**. Ex.: Contabilidade Ozai
>   bruto 8.570 → líquido **8.042,94** (bate exato); Suporte Totvs bruto 3.108,97 →
>   líquido **2.917,77**; Terceirização Limpeza **3.346,68**.
> - **Desdobramento de lumps** (cartão de crédito Itaú 32.408, plano de saúde 31.882,
>   transitórias) → tabela **`FINANCE.CPDESDOBRAMENTO`** (`DESCCONTADESTINO`,
>   `DESNVALOR`, `DESCHISTORICO`), 1 linha por fatia desdobrada.
> - **Aluguel líquido de sublocação:** bruto 27.477,67 − crédito Belline 3.117,90 =
>   **24.359,77** (já é o valor da conta `020.010.0010` no GERENC — usar esse, não o
>   bruto do CONTASPAGAR). Workbook tem 24.230,60 → os **R$129,17** que a Renata vai
>   conferir com a Malu (provável defasagem da planilha).
> - **Reclassificações** (confirmadas pelo cliente): "Contratação do Claude" 2.166,53
>   é licença de software → Informática (não Material de Copa); Custas (`020.030.0140`)
>   e Transporte e Frete (`020.030.0060`) saem do row-198; Cursos `030.010.0180` →
>   Gestão do Conhecimento.
> - **Implementação:** `extract.sql` ganhou blocos aditivos `despesas_liquido`
>   (CONTASPAGAR net por conta) + `despesas_desdobramento` (CPDESDOBRAMENTO). Módulo
>   puro `app/closing/despesas_liquido.py::net_by_account` aplica a receita.
>   `dre.py::from_snapshot` sobrepõe o bruto de cada conta institucional pelo líquido
>   quando os blocos existem (no-op caso contrário — seguro até o re-run). Locked por
>   `tests/test_despesas_liquido.py` + 2 testes de integração.
> - **PENDENTE (o gargalo):** rodar o `extract.sql` atualizado no RDP para maio (e
>   demais meses) popular os blocos; então a linha Despesas fecha e **Resultado
>   Bruto/Líquido/Reserva/margens deixam de ficar em branco**. Ver
>   `docs/HANDOFF_2026-07-13-despesas.md`.
>
> Backend **218 testes**, frontend **52**; ruff/mypy limpos.
>
> **IMPLEMENTADO (2026-07-14) — despesas ao vivo, backfill validado, DL/convênio
> provados, Nacional/Moedas automatizadas:** sessão com o operador no RDP.
> - **T5 despesas ao vivo:** re-rodado o extract (net blocks `despesas_liquido` +
>   `despesas_desdobramento`) para mai; snapshot fresco no Supabase reproduz a receita
>   ao centavo (aluguel 24.359,77, contabilidade 8.042,94, licenças 7.239,10 etc.).
>   Despesas mai = **105.640,60**.
> - **Gargalo do daily job RESOLVIDO:** o `extract.sql` da box ficara defasado um dia
>   inteiro (rodava a versão pré-T5). `run-agent.ps1` agora **auto-atualiza o
>   extract.sql do `main`** a cada run (sanity-checked + fail-safe → nunca para).
> - **Autorização da Renata (aluguel–Belline é DB-autoritativo, só ele):** override
>   dos alvos abr+mai (+129,17 em despesas, propagado ao bruto/líquido/reserva). **Mai
>   agora renderiza a cauda inteira** (bruto 100.197,94, líquido 29.691,74, reserva
>   2.969,17) — deixou de ficar em branco.
> - **Backfill jan–mai + validação multi-mês:** só **mai bate ao centavo**; jan/fev/mar
>   divergem no **layer manual do cliente** (Vale-ADM batido à mão, splits de Associações
>   ÷2/÷3) — NÃO é bug de DB; documentado. Nossos números são discutivelmente *mais*
>   corretos que as células antigas do workbook.
> - **DL/convênio provados ao vivo:** convênio extra por advogado deduzido da DL
>   (DC 3.796,78 / RB 5.151,75 / EHF 1.398,01, em `500.010.<SIGLA>`); **Bônus equipe**
>   fev = 94.696,15 (`150.010.0010`) + 7.009,84 JGS (`030.010.0010`) = 101.705,84 (bate
>   o workbook). Blocos aditivos `convenio_extra_dl` + `bonus_equipe_030` no extract;
>   `bonus_equipe` no dre.py agora soma os dois.
> - **T8 — abas Nacional/Moedas AUTOMATIZADAS:** fonte `LDESK.DB_VW_FATURASEMI_REC`
>   **validada ao centavo** (Σ `VALOR_HONORARIOS_NAC` mai = 719.988,05 = sacred, split
>   R$ 708.659,18 + US$ 11.328,87). Bloco `faturas_moeda` (GROUP BY NUMERO, per-fatura)
>   + `SectionKey.NACIONAL/MOEDAS` + `assemble_faturas_moeda`. Falta só um re-run p/ o
>   snapshot carregar o bloco e as abas irem ao ar.
> - **PENDENTE:** re-run final (self-update pega o `faturas_moeda`); **POINT 17 —
>   automatizar o split sócio/funcionário do bônus NÓS (não é tarefa do RUMO —
>   decisão do usuário 2026-07-14):** probe `probe_socio_split.sql` (commitada, não
>   rodada) procura flag estrutural de sócio no DB; a sigla já vem no histórico do
>   150.* e as siglas vistas são todas funcionárias → 150.* pode já excluir sócios.
>   Depois: wire do `convenio_extra_dl` no split de DL. jan–abr = layer manual
>   (esperar cliente / aceitar número do DB). **Só o Orçamento fica fora.**
> Backend **224 testes**, frontend **52**; ruff/mypy/tsc limpos.
>
> **VALIDAÇÃO INDEPENDENTE (2026-07-14, fim de dia) — estado ao vivo corrigido:**
> Auditoria contra o Supabase ao vivo + testes + prod (não só os docs). O que
> **confere ao vivo**: gates verdes (backend **228** testes — não 224, agora são
> *mais* —, ruff/mypy limpos; frontend **52**, lint/tsc limpos); números sagrados
> travados; **maio fecha ponta a ponta a partir do snapshot REAL** (bruto 100.197,79,
> líquido 29.691,61, reserva 2.969,16 — dentro da tolerância R$1); **Nacional/Moedas
> batem EXATO ao vivo** (708.659,18 + 11.328,87 = 719.988,05 sagrado); `faturas_moeda`
> (45–59 linhas/mês), `convenio_extra_dl` (DC 3.796,78 / RB 5.151,75 / EHF 1.398,01)
> e `bonus_equipe_030` (fev 7.009,84) **já estão nos snapshots** — o "gargalo do
> file-pull" do handoff de 16:04 **já foi resolvido** por um re-run posterior.
> - **⚠ NOVO GARGALO (não sinalizado no handoff):** a correção do PONTO 17 (commit
>   `a0537b4`, 16:55 — repontou o bloco `150.%` para `FINANCE.LANCAMENTO` + exclusão
>   de sócio via `CAD_PROFISSIONAL.SOCIO`) entrou **DEPOIS** do último re-run. Logo,
>   nos snapshots ao vivo hoje: `bonus_equipe`(150.*) = **None** em TODOS os meses,
>   e `dl_excedente_socios` / `dl_excedente_mv` = **None**. O código + 17 testes
>   passam, mas **o número não aparece em produção até um NOVO re-run** do
>   `extract.sql` corrigido. A afirmação "PONTO 17 feito" é verdade *em código*, não
>   *ao vivo*. O bônus de fev 101.705,84 NÃO é reproduzível do snapshot atual (só a
>   parte JGS 7.009,84 está lá).
> - **Correção de rótulo:** "~95% automatizado" descreve a *capacidade do código* para
>   *maio*, não o estado ao vivo de todos os meses. Falta 1 re-run para o bônus/split
>   de sócio de fato renderizarem; jan–abr seguem no layer manual do cliente.
> Backend **228 testes**, frontend **52**; ruff/mypy/tsc limpos; prod no ar
> (`/api/health` → 200, frontend → 200).

- **No Juritis/TOTVS API exists — and none is planned.** The *only* non-LegalDesk
  data path is the **direct SISJURI Oracle DB** (read-only, via `MBC-LDESK01`).
  Section 5's "when the Juritis API arrives" is therefore moot; the `JuritisSource`
  placeholder will never be filled by an API. Treat the DB as the permanent source.
- **Authoritative reference workbook = `Fechamento MBC 05.2026.xlsx`.** On any
  conflict between books, 05.2026 wins. Its structure is the target layout.
- **A lawyer who works in two areas is ALWAYS split 50/50** (divide em 2) between
  the two areas — for custo de equipe and comissão. This is a fixed rule, never
  case-by-case. (This is the "Aurélio ÷2 / Beatriz" pattern.)
- **The workbook figure is the number of record.** Finance does not, and will not,
  reconcile against the DB. When our DB-derived number and the workbook disagree,
  the **workbook is the target** and any residual is ours to explain via the DB —
  never something to raise with finance as a DB question. Finance are not DB users.


## 1. What this is

A production-grade, multi-tenant SaaS turning the old single-tenant MBC
monthly-closing script into a web product sold to **RUMO**:

- **RUMO** logs in as **ADMIN** and sees **all clients**, drilling into any
  client's monthly closing.
- Each **client** (e.g. MBC) logs in as **CLIENT** and sees **only their own**.
- Competence month is chosen **in the UI** (replacing the old CLI `--month`),
  with an optional **day-range refinement** for date-driven tabs.

Stack: **FastAPI** (Python) backend + **React + TypeScript (Vite)** SPA.
Credentials and the LegalDesk password stay server-side; the browser only
talks to our authenticated backend.

---

## 2. Current status (built vs stubbed)

### Built and tested
- Backend scaffold, `/api/health`, env-driven `Settings` (no hard-coded secrets).
- Verified MBC data logic ported into `backend/app/` (period, builder, layouts,
  LegalDesk client) behind the new Source/Provider seams — behavior preserved.
- Auth: argon2 password hashing, JWT issue/verify, `POST /api/auth/login`,
  `GET /api/auth/me`.
- Tenancy: `User`/`Client` models, `Role` enum, `can_access_client`; server-side
  guards (`require_user`, `require_admin`, `require_client_access`).
- Repository abstraction: `Repository` protocol, in-memory `FakeRepository`
  (tests), `SupabaseRepository` (prod) + `app/db/schema.sql`.
- Data layer: `SectionKey` (15 sections), `DayRange`, `Source` protocol,
  `ClosingProvider` (ordered sources, later-overrides-earlier merge).
- Sources: `LegalDeskSource` (wraps verified builder; locked by recorded
  fixture), `FixtureSource` (demo client), `JuritisSource` (placeholder).
- API: `/api/clients` (admin list), `/api/clients/{id}` (tenancy-guarded),
  `/api/clients/{id}/closing?month=&from=&to=` (month validation + day-range).
- Idempotent Supabase seed script (`backend/scripts/seed.py`).
- Frontend: typed API client + `ApiError`, auth store with silent session
  restore, route guards (`RequireAuth`/`RequireAdmin`), design tokens +
  primitives, `MonthPicker` + `DayRangeFilter`, `LoginPage`, `ClientsPage`,
  `WorkspacePage`, `TabView` (rich + grid), app shell. All PT-BR, dark fintech.
  Tables have **sticky column headers** (`thead` pinned inside the scroll body);
  rich tabs (Meta, Base_Resultado, Resumo Recebidas, Faturas Centro Custo) render
  their real structure and fill not-yet-available cells with **"ainda não temos"**
  instead of a placeholder paragraph.
- **`.xlsx` export:** `lib/exportClosing.ts` turns a `ClosingPayload` into a
  multi-sheet workbook (one sheet per tab). WorkspacePage exposes "Exportar tudo"
  (all sheets) and "Exportar esta página" (current tab only). Uses SheetJS
  (patched CDN build `xlsx-0.20.3`, **0 npm audit vulns**), lazy-imported so it
  ships as a separate chunk and stays out of the initial bundle.
- CI: GitHub Actions running ruff + mypy + pytest (backend) and eslint + tsc +
  vitest (frontend) on push/PR.
- Docker: `backend/Dockerfile`, `frontend/Dockerfile` + `nginx.conf`,
  `docker-compose.yml`. **Smoke-tested:** `docker compose build` builds both
  images; backend container boots and serves `/api/health` → 200.

### Stubbed / placeholder (intentional)
- **`JuritisSource`** — documented placeholder, NOT wired. `supports()` returns
  empty; `fetch()` raises `NotImplementedError`. See §5 for the migration paths.
- **`FixtureSource`** — minimal deterministic demo data; exists only to showcase
  the admin multi-client view. Not real client data.

### Workbook-faithful DRE rework (2026-07-02)
The closing tabs now mirror `Copy of Fechamento MBC 02.2026.xlsx` in vocabulary
and structure (base = **Recebimento**, not Faturamento):
- `app/closing/workbook_layouts.py` — canonical section vocabulary + account-
  family rollups (`020./040.*` → institutional sections by `nome_conta_pai`,
  `030.*` → Custo equipe, Impostos → Impostos).
- `app/closing/dre.py` rebuilt: **Institucional** (DRE block + section-by-section
  expense breakdown with sub-accounts, % of Recebimento), **area tabs**
  (Recebimento/Custo equipe/Comissão/Despesas Equipe/Despesa Institucional/
  Resultado Bruto), **Base_Resultado Mensal** (hierarchical: per-lawyer custo
  equipe grouped by area + institutional sections/sub-accounts + Impostos).
- `app/closing/secondary_tabs.py` — **Amortização** real fixed schedule (8 × 2022
  originations, 60 parcelas each = R$ 8.117,32/mês) + **Rateio Mensal** per-area
  shares.
- `ops/sisjuri-agent/extract.sql` extended with `custo_equipe_prof` (per-lawyer ×
  account 030.*, area via professional→grupo). **Needs a re-backfill** to
  populate historical months (existing snapshots lack this key; Base_Resultado
  per-lawyer rows show only for months re-run with the new extract).

### Per-area Recebimento — RULE CONFIRMED, now auto-derived (2026-07-03)
Per-area **Recebimento** *is* derivable from SISJURI after all (the earlier
2026-07-02 note below is superseded). The receipt view splits by **case → área
jurídica**: `GERENC_VW_POSFIN_RESULTREC` (via `ID_CASO`) → `CAD_CASO.
ID_AREAJURIDICA` → `CAD_AREAJURIDICA.NOME`, summing `VALOR1`. Verified to the
centavo vs the workbook base numbers for Jan & Fev 2026. See
`docs/SISJURI_QUERIES.md` §9 (2026-07-03) for the query + table.

Built on top of that:
- **`extract.sql`** emits `recebimento_area` (this split), `faturamento_area`
  (same split on the faturamento view) and `faturas_analitico` (per-CASE
  faturamento detail from `GERENC_VW_POSFIN_RESULTFAT`). All 29 months
  (2024-01 → last closed) backfilled to Supabase (2026-07-03). The agent emits
  the JSON in DBMS_OUTPUT chunks so it never hits sqlplus's 32767 LINESIZE
  ceiling (see `run-agent.ps1`/`extract.sql`).
- **`dre.py`** `RealizadoInputs.area_recebimento` parses `recebimento_area` and
  folds names onto the three areas; area tabs' Recebimento is SISJURI-derived
  and **no longer hand-fillable** (with `Resumo_Recebidas` transfers applied
  upstream). Manual per-area recebimento is rejected by the API and ignored by
  the assembler.
- **`Resumo_Recebidas` transfers** modeled as `area_transfers` (origem→destino
  deltas, net 0) overlaid on the base — new `app/manual/transfers.py` +
  `area_transfers` table. These small cross-area reclassifications are still
  finance-entered (no DB rule), but the *base* is now automatic.
- **Distribuição de Lucros extras** block surfaced in `base_resultado` (Bônus
  equipe, DL Extraordinária, DL excedente sócios/MV, Repasse Cacione), values
  from optional snapshot `distribuicao_extras`, blank otherwise.
- **Budget granularity:** `BudgetEntry.monthly_amounts` (optional 12-value array)
  → workbook per-month Orçado; `monthly_budget(entries, month=...)` selects it;
  `budgets.monthly_amounts` jsonb column + API accepts/returns it. On a
  legacy/canonical key collision the entry with monthly detail wins (so an
  imported granular budget is never shadowed by an old annual seed).
- **Budget import from workbook:** `app/budget/workbook_import.py` +
  `scripts/import_budget.py` parse the `DRE 2026` sheet (per-area Custo equipe,
  institucional Recebimento/Despesas/Imposto/Amortização/Reserva) into
  `BudgetEntry`s with 12-month detail, upserted on (client,ano,area,line) so the
  **manual budget API still works** (imported lines refresh in place, manual
  lines under other keys are preserved). MBC 2026 imported (2026-07-03); the 4
  legacy annual-only seed rows were removed.
- **Meta dashboard:** new `meta_dashboard` tab (annual goal 8.060.000, monthly
  goal, this-month attainment, 12-month table) via `assemble_meta`.

Still manual (no verified DB rule): the `area_transfers` and
`distribuicao_extras`.

### Per-area Custo equipe — automation frontier (2026-07-07)

> **Direction correction.** The end goal is **full automation**: the client
> should do the *least* manual work possible. The workbook / dashboard /
> Demonstrativo are **development aids only** (ground-truth to validate against),
> **not** monthly inputs — nothing we ship may assume they arrive each month.
> Per the operating rule, we **assume automation is possible and only accept a
> manual artifact once impossibility is 100% proven.**
>
> The **workbook importer below mirrors the monthly workbook**, so it does NOT
> reduce their manual work and is **not** the automation path. It is retained
> only as an **offline validation harness** (it ties to the dashboard to the
> centavo) and a temporary fallback.
>
> **PROVEN full-automatable (2026-07-07 probe).** The read-only probe
> (`ops/sisjuri-agent/probe_distribuicao_area.sql`, results in
> `docs/SISJURI_QUERIES.md` §11) confirmed per-area Custo equipe is **fully
> derivable from SISJURI with no monthly manual input**: `FINANCE.LANCAMENTO`
> books Distribuição Mensal Fixa (`030.010.0010`) per **lawyer (`COD_ADVG`) ×
> area (`SIGLADEST` cost-center)**, ties to the centavo (Σ 172.129,96 Feb), and
> **encodes cross-area splits in the DB** (Beatriz BBX split 518,40 Contencioso /
> 7.537,40 Econômico — the "Aurelio ÷2" pattern, but booked at payment time). So
> a **future lawyer's split flows through automatically**. Next: wire the
> corrected extract (drop the bad `LANCHISTORICO` filter; fold distribuição by
> `SIGLADEST`→area into `custo_equipe_prof`), validate the three area subtotals
> to the centavo, then **remove the workbook importer** as a data path.

#### Validation harness / temporary fallback: workbook ledger importer
A **second workbook
sample** (`Fechamento MBC 05.2026.xlsx`, alongside the earlier `02.2026`)
confirmed the `Base_Resultado Mensal_V2` **structure is stable across months** —
every section header (`Custo equipe - {area}`, `Participação/comissão`,
`Repasse`, `Despesas Área`, `Despesas Institucional`, `Total saídas`) matches;
only per-lawyer rows churn as staff change, and each still follows the
`{Nome} - {TipoConta}` convention. The `05.2026` edition even formalized the
rateio into a named block (`Despesa para ratear` / `Equipe` / `Comissão` /
`CHECK`, rows 207-214), confirming the rule is deliberate.

- **`app/closing/ledger_import.py`** — pure, label-driven parser. Locates section
  anchors by column-A label (robust to row insertion) and reads their **cached
  values** (never the formulas — sidesteps the manual `=12500-C8`, `=3182.83/2`
  per-lawyer splits, which Excel has already resolved into the subtotal). Emits
  per-area `custo_equipe`, `comissao` (Participação+Repasse), `despesas_equipe`
  (Despesas Área). Derives per-area **Despesa Institucional** via the workbook
  rateio: `desp_inst[area] = (DespInstTotal − ΣDespesasÁrea) × (CE[area]/ΣCE)`.
- **`scripts/import_ledger.py`** — reads the workbook `Base_Resultado` sheet and
  merges a `ledger` block into each competence month's snapshot
  (read-modify-write, preserving all SISJURI data). Imports every month present
  in the sheet (columns C..N).
- **`dre.py` wired**: `RealizadoInputs.from_snapshot` reads the `ledger` block;
  when present it **overrides** the SISJURI `custo_area` per-area Custo equipe
  (the two do NOT reconcile — SISJURI is a raw DB aggregation, the ledger is the
  hand-maintained figure the client dashboard uses) and drives Comissão /
  Despesas Equipe / the derived Despesa Institucional. `_area_rows` prefers the
  ledger; manual entry remains the fallback for months with no ledger.
- **Parity: verified to the centavo** against the client dashboard `MBC Resultado
  Jan a Mai 2026.pdf` (YTD Jan–Mai): Contencioso Custo equipe 372.279,42 (dash
  372,3K), Despesas Equipe 11.996,28 (12,0K), Despesa Institucional 170.869,75
  (170,9K); Econômico/Arbitragem Custo equipe 389.116,53 / 282.414,08 (389,1K /
  282,4K). Institucional Faturamento/Receita still tie to the sacred numbers.
- **Institutional row-198 map SOLVED (account-keyed).** `probe_inst_csv.sql`
  dumped `FINANCE.VW_RESULTADO_MENSAL_DET` as CONTA3-keyed rows; reconciled to the
  centavo against Fechamento MBC 02.2026 + 05.2026. Workbook "Despesas
  Institucional" (row 198) = sum of 10 families (Ocupação, Telecom, Despesas
  Gerais, Consultoria, Salários Adm, Administrativas, Invest. Prospecção, Gestão
  do Conhecimento, Endomarketing, Informática); Impostos + Distribuição de Lucros
  + area lines are excluded. The verified account→family overrides now live in
  `workbook_layouts.py::section_for(nome_pai, id_conta)` (keyed on stable CONTA3
  codes, e.g. Contabilidade 020.040.0050→Consultoria, Seguros 020.060.0040→
  Ocupação). Locked by `tests/test_workbook_layouts.py`. The residual ≈5–7k
  workbook drift is line-attributed to a manual annualization layer
  (Administrativas/Gestão/Endomkt) that is NOT in the DB month — see
  `docs/HANDOFF_DRE_AUTOMATION.md` Appendix B. These become optional manual inputs
  now that the workbook is going away.

**Demonstrativo Resultado Profissional** (`..._AR_20260623_....pdf`): the
LegalDesk report the client now uses to allocate per-area recebimento — it
replaced the workbook's `Resumo_Recebidas` + `FATURAS Analitico` tabs (both
absent from `05.2026`). Per client direction it is used as **cross-validation**
of our already-verified SISJURI-derived per-area recebimento, not (yet) wired as
an ingestion source.

### Operator steps to finish the deploy
1. Apply the new DDL in Supabase (`area_transfers` table + `budgets.
   monthly_amounts` column + earlier `manual_actuals` — see `app/db/schema.sql`).
2. Update the on-server `extract.sql` and **re-run the backfill** so snapshots
   carry `recebimento_area`, `faturamento_area`, `faturas_analitico`
   (see "When to re-run the backfill" below).
3. Optionally verify `FAT_FATURA` columns with `probe_faturas_analitico.sql`
   before trusting `faturas_analitico`.
4. **Import the per-area ledger** so area tabs match the dashboard:
   `python -m scripts.import_ledger --workbook "reference/workbook/Fechamento MBC 05.2026.xlsx"
   --client mbc --ano 2026` (idempotent; merges a `ledger` block into each
   month's snapshot). Re-run whenever a new monthly workbook arrives.

### Test counts (as of last update)
- Backend: **224 passing** (`cd backend && pytest`). +6 on 2026-07-14: bonus_equipe
  from 030.010.0010 (2), Nacional/Moedas tabs (4), SectionKey count. Earlier +26 on 2026-07-13:
  live SISJURI validation — custo equipe 2 fixes, comissão null fix + area-tab
  display, R$1 tolerance (8 verification tests), Vale-ADM + FGTS reclass,
  comissão/imposto label fix, margin-blanking, and **T5 despesas at líquido +
  desdobramento** (`test_despesas_liquido.py` + 2 integration tests).
- Frontend: **52 passing** (`cd frontend && npm run test`).

### Production (EasyPanel + Supabase) — live 2026-06-22
- **Frontend:** https://rumo-frontend.xem1qi.easypanel.host
- **Backend API:** https://rumo-backend.xem1qi.easypanel.host (`/api/health` → 200)
- **Supabase:** project `skrwptamwbhwaiwwhrqj` — `schema.sql` applied, seed run (`mbc` + `demo` clients, three users).
- **EasyPanel:** project `rumo`, services `backend` + `frontend` (GitHub `femito1/rumo` @ `main`, Dockerfiles in `backend/` + `frontend/`).
- **Auth:** production uses Supabase (`USE_FAKE_REPO=0`). Dev zero-setup toggle still available locally.
- Env templates: `backend/.env.production.example`, `frontend/.env.production.example`.

---

## 3. Architecture at a glance

```
rumo/
├── backend/            FastAPI service (Python)
│   ├── app/
│   │   ├── main.py         app + CORS + router wiring + /api/health
│   │   ├── config.py       env-driven Settings.from_env()
│   │   ├── auth/           passwords (argon2), tokens (JWT)
│   │   ├── tenancy/        User/Client models, Repository, SupabaseRepository
│   │   ├── db/             schema.sql (clients + users)
│   │   ├── sources/        base (SectionKey/DayRange/Source), legaldesk,
│   │   │                   fixture, juritis (placeholder), legaldesk_client
│   │   ├── closing/        period, builder, layouts, available, provider
│   │   └── api/            deps, providers, auth_router, clients_router,
│   │                       closing_router
│   ├── tests/          pytest (unit + API + recorded-fixture integration)
│   ├── scripts/seed.py idempotent Supabase seeding
│   └── Dockerfile, pyproject.toml
├── frontend/           React + TS + Vite SPA
│   └── src/{app,features/{auth,clients,closing},lib,components,styles}
│       + Dockerfile, nginx.conf
├── .github/workflows/ci.yml
├── docker-compose.yml
├── PROJECT_STATUS.md   (this file)
├── CLAUDE.md           agent operating guide
├── docs/               LEGALDESK.md, DESIGN.md
└── reference/workbook/ ground-truth xlsx + Postman (not runtime)
```

Data flow: `provider`/`provider_config` on a client → ordered `Source`s →
`ClosingProvider.build_closing(period, day_range)` → provider-agnostic
`ClosingPayload` → SPA renders it regardless of upstream source.

---

## 4. Verified facts preserved (SACRED — never silently regress)

Source of truth: `docs/LEGALDESK.md`. Locked by backend tests
against the recorded fixture `backend/tests/fixtures/legaldesk_2026_05.json`:

- `recebimento_bruto('2026-05')` ≈ **415.927,84** (98 rows)
- `faturamento_bruto('2026-05')` ≈ **719.988,05** (97 rows)
- **53** distinct invoices in May 2026
- Historicals: jan/2026 = **279.821,07** · fev/2026 = **319.233,58**
- `RateioFaturaProfissionalViews` rows are **duplicated** — de-dup by
  `(FaturaNumero, ProfissionalSigla)`.
- Workbook year is **2026** (not 2025). OData **v3** syntax.

If a change moves any of these numbers, it is a bug until proven otherwise.

---

## 5. Juritis-readiness (the defining constraint)

> **UPDATE 2026-07-01 — may be partly obsolete.** The institutional expenses this
> section assumes live only in TOTVS Backoffice were found in the **SISJURI Oracle
> DB** (`FINANCE` schema), readable today via the bridge server. See
> `docs/SISJURI_DB.md` §"Full-closing coverage". A `FinanceDbSource` could supply
> the expense side without waiting for the Juritis API. Revisit the paths below
> in light of that. Reconciliation of exact per-line DRE definitions is still open.

> **SUPERSEDED (2026-07-10, client-confirmed): there is NO Juritis/TOTVS API and
> none is planned.** The only non-LegalDesk source is the SISJURI Oracle DB (see
> §0 and §6b). The `JuritisSource` placeholder stays as a generic seam but will
> never be backed by an API. The paths below are kept for historical context only.

The Juritis / TOTVS Backoffice API ~~is coming but its shape is **unknown**~~. The
data layer is built so integrating it is a localized change, never a frontend or
contract rewrite. When access arrives, pick one path:

1. **Additive** — add `JuritisSource` supplying the institutional-expense
   SectionKeys; merge fills previously-MANUAL lines. LegalDesk untouched.
2. **Partial override** — Juritis supplies some sections LegalDesk also did;
   `merge_policy` sets per-section precedence (later source wins).
3. **Full replacement** — a client's provider lists `[JuritisSource]` instead
   of `[LegalDeskSource]`. LegalDesk stays for clients still on it.

In all three, the API contract and the SPA are unchanged: cells just carry a
different `origin` tag (`juritis` instead of `manual`).

---

## 6. Known limitations / tech debt

Non-blocking items found during review. Fix opportunistically; add new ones here.

- **Login timing oracle (low):** login compares password only when the user
  exists, so response timing can hint whether an email is registered. Acceptable
  for a small known user set; mitigate later with a constant-time dummy verify.
- **`DayRange` calendar validation gap (low):** `DayRange.within` trusts the
  caller's day bounds; it does not reject impossible days (e.g. day 31 in a
  30-day month) beyond basic ISO formatting. The closing endpoint clamps to the
  month, so impact is limited, but explicit validation would be cleaner.
- **`FixtureSource` is not representative:** demo numbers are arbitrary; do not
  use them to reason about real behavior or in screenshots shown to clients.
- **JWT secret length warning in tests:** test secrets are short and trigger a
  PyJWT `InsecureKeyLengthWarning`. Production secret comes from env and must be
  ≥ 32 bytes.
- **`docker compose up` needs `backend/.env`:** compose references
  `env_file: ./backend/.env`. Copy `backend/.env.example` → `backend/.env`
  before `up`. The `.env` is gitignored and must never be committed.

## 6b. SISJURI direct DB access (discovered 2026-07-01)

An **Oracle 19c** database behind SISJURI is reachable **read-only** through the
authorized Windows bridge server `MBC-LDESK01` (the Power BI gateway host). It
contains the **`LDESK`** schema (601 tables) — the same LegalDesk data RUMO pulls
via OData — and **`SSJR`** (704 tables) of SISJURI core data. Confirmed: real
`SELECT` on `LDESK` billing tables, 98 months of history (2018-05 → 2026-06),
53 May-2026 invoices matching the sacred `faturas_emitidas`. This opens an
**audit / fallback / alternative-`Source`** path to the API. Details, schema map,
and the (hard-won) `sqlplus`-over-RDP invocation recipe live in
`docs/SISJURI_DB.md`; the implementation-ready SQL per DRE line and the egress
options live in `docs/SISJURI_QUERIES.md`. The DB and RDP credentials used during
discovery were shared out-of-band and **must be rotated**; never commit them.

**Now partially wired (2026-07-02).** Full closing proven sourceable from the DB
via three objects + one fixed formula: revenue (`GERENC_VW_POSFIN_RESULT*`),
expenses gross/competence (`GERENC_LANCAMENTORESUMO`), pró-labore gross
(`CONTASPAGAR.CPGNVALORBASE`), and reserva de bônus = 10% da margem líquida
(finance-confirmed). Built so far:

- **On-server agent** `ops/sisjuri-agent/{extract.sql, run-agent.ps1}` — pure
  PowerShell + the existing `sqlplus` (no Python on the box), emits one JSON
  snapshot per competence month, TLS-1.2 outbound POST. Verified on the server:
  `closing_2026-02.json` (recebimento 319.233,58; 30 expense accounts).
- **Egress = Option A** (server pushes to VPS): `POST /api/ingest` (bearer-token,
  `INGEST_TOKEN`) stores snapshots via the snapshot store.
- **Snapshots persist in Supabase (2026-07-03).** `sisjuri_snapshots`
  (`client_id, ano_mes, payload jsonb`, PK `(client_id, ano_mes)`) is now the
  durable, multi-tenant source of truth — the whole financial dataset lives in
  Postgres alongside `budgets`/`manual_actuals`, not on the VPS disk.
  `SupabaseSnapshotStore` is selected in prod; the filesystem `SnapshotStore`
  (`SNAPSHOT_DIR`) remains the `USE_FAKE_REPO`/local-dev fallback and gained
  client scoping (with a legacy clientless-filename read fallback). `client_id`
  flows through `/api/ingest` (`meta.client_id`, default `"mbc"`) and the closing
  read path (`client.id`). The agent stamps `meta.client_id`. A one-time
  token-protected `POST /api/ingest/migrate-fs-to-supabase` copied the existing
  30 months (2024-01 → 2026-06) into Supabase; verified the closing endpoint now
  reads from Supabase with the sacred numbers intact.
- **`app/sources/sisjuri_db.py`** (`SisjuriDbSource`) consumes a snapshot and
  emits `SectionKey`s, encoding the pró-labore-gross and bonus-reserve rules.
  Tested against a recorded fixture (`tests/fixtures/sisjuri_2026_02.json`).
- **`ClosingProvider`** now has a `legaldesk+sisjuri` mode: composes
  `LegalDeskSource` (KPIs) with `SisjuriDbSource` in augment mode (institucional),
  preserving the sacred numbers.
- **LIVE on EasyPanel (2026-07-02):** `POST /api/ingest` is deployed and verified
  end-to-end — 401 without/with-wrong token, 422 on missing `meta.ano_mes`, 200 on
  the real Feb-2026 snapshot, persisted to a named volume `sisjuri-snapshots` →
  `/data/snapshots` (survives redeploys). **Root-cause fix:** the `backend` service
  was building via **Nixpacks** (wrong start cmd `python -m rumo-backend` → boot
  crash / 502); switched `build.type` to **`dockerfile`** so it uses the tested
  `backend/Dockerfile` (`uvicorn app.main:app`). `INGEST_TOKEN` is set in the
  EasyPanel backend env (not committed).
- **SCHEDULED & LIVE (2026-07-02):** `RUMO-SISJURI-Agent` runs daily at 06:00 on
  MBC-LDESK01 for the previous full month, extracts, and pushes to the VPS.
  Verified `LastTaskResult=0` (2026-06 snapshot uploaded). Constraints found on
  that box: `bia4u` is **not** a local admin, so env vars are **User-scope** and
  the task **runs as `bia4u`** (not SYSTEM). "Run whether logged on or not"
  needed the *Log on as a batch job* right, which an admin granted to `bia4u`
  (error `2147943785` until then). `register-task.ps1` now has `-StorePassword`
  (run-as-user) and `-AsSystem` modes.
- **Agent upload:** must send the body as **UTF-8 bytes** with an explicit
  charset (fixed in `run-agent.ps1`); a plain string body 400s on FastAPI,
  especially with accented account names.
- **Still TODO:** rotate the DB/RDP credentials that were shared in chat.

---

## 6c. Workbook mirror + manual budget (2026-07-02)

The deployed closing page now mirrors the MBC workbook DRE structure and adds a
manually-entered Orçado (budget) for Orçado × Realizado variance. Built:

- **DRE engine `app/closing/dre.py`** — a canonical DRE line-key registry
  (`faturamento`, `custos_diretos`, `despesas_indiretas`, `resultado_bruto`,
  `margem_bruta`, `impostos`, `amortizacao`, `resultado_liquido`,
  `margem_liquida`, `reserva_bonus`) shared by the SISJURI source, the budget
  domain and the frontend. `assemble_dre_sections` computes the **Institucional**
  block plus three area blocks (Contencioso/Economico/Arbitragem) and
  `areas_sintetico`, each row carrying `orcado | realizado | variacao | desvio%`.
  It **recomputes** from clean sources (not the workbook cells, which have
  `#REF!`s). Reserva de bônus = 10% da margem líquida; amortização = fixed
  monthly institutional installment.
- **`SisjuriDbSource` expanded** — emits rich, grouped expense detail
  (`INSTITUCIONAL_ANO`, section subtotal + indented sub-accounts) plus
  `RATEIO_MENSAL` (per-area team cost + per-lawyer rateio), prolabore (gross/net)
  and distribuição tables. The assembled DRE owns `INSTITUCIONAL`.
- **Budget domain `app/budget/`** — `budgets` Supabase table
  (`client_id, ano, area, line_key, annual_amount`; DDL in `app/db/schema.sql`),
  `BudgetRepository` (supabase + in-memory seeded), annual granularity split
  evenly to monthly. `BudgetSource` emits the `ORCAMENTO_2026` reference tab.
- **Budget API** — `GET/PUT /api/clients/{id}/budget?ano=YYYY`, guarded by
  `require_client_access` (ADMIN + that client's CLIENT may edit). Validates
  area/line keys. Seeded placeholder budget (Meta 8.060.000/ano) for MBC 2026.
- **Provider composition** — `legaldesk+sisjuri` now composes
  LegalDesk → SisjuriDb → Budget → **Assembler** (last, overrides). Headline KPIs
  (`resultado_bruto`, `margem_bruta`, `resultado_liquido`, `margem_liquida`,
  `reserva_bonus`) are lifted from the assembled DRE into the `kpis` map. When no
  snapshot exists the DRE still renders with `snapshot_missing: true`.
- **Frontend** — new KPI cards (with `formatPercent`/`formatNumber` and a
  `KpiCard format` prop); `RichTabView` renders DRE percent columns, section/total
  rows and indented sub-accounts; a PT-BR **missing-data banner**
  ("Dados institucionais ainda não importados para este mês") on institucional/DRE
  tabs; a **budget editor** panel (`BudgetEditor` + `useBudget` hook in its own
  module) for ADMIN and CLIENT. Spinner already existed. New rich tabs export via
  the existing `exportClosing.ts` automatically.
- **Backfill** — `ops/sisjuri-agent/backfill.ps1` loops 2024-01 → last closed
  month calling `run-agent.ps1` per month (one-shot catch-up; the daily task
  keeps recent months fresh). Documented in the agent README.
- **MBC provider** — the fixture/demo MBC client is now `legaldesk+sisjuri`. The
  **prod `clients.provider` for MBC must be set to `legaldesk+sisjuri`** for this
  to show live.

**Tests:** backend 95 passing (new: DRE assembler math/variance/margins,
BudgetSource, budget repo/API auth boundary, provider composition with all four
sources, snapshot_missing flag; sacred-number lock still green). Frontend 44
passing (new: `formatPercent`/`formatNumber`, DRE percent + grouped/indent
rendering + banner, BudgetEditor). Backend `ruff`+`mypy` clean; frontend
`lint`+`typecheck` clean.

**Operator TODO before this is fully live:**
1. Apply the `budgets` DDL (`backend/app/db/schema.sql`) to Supabase.
2. Set MBC's `clients.provider = 'legaldesk+sisjuri'` in Supabase.
3. Deploy backend+frontend (GitHub → EasyPanel, Dockerfile build).
4. Run `backfill.ps1` once on MBC-LDESK01, then verify a few months via
   `GET /api/ingest/{ano_mes}/summary`.

---

## 7. Future plans / phases (out of v1, noted not precluded)

- Implement `JuritisSource` once the API is available (see §5).
- Evolution API (WhatsApp) closing notifications.
- Password-reset emails; self-serve client onboarding UI.
- Per-request audit logging for ADMIN cross-client access.

---

## 8. Run / test / deploy

See `README.md`. Quality gates: backend `ruff` + `mypy` + `pytest`; frontend `lint` +
`typecheck` + `vitest`. Update this file when status changes.

---

## 9. Conventions (enforced)

- **TDD:** a failing test precedes every new function/endpoint.
- **Secrets:** never committed or shipped; always from env / `.env.example`.
- **Sacred numbers:** the verified LegalDesk totals (§4) must not regress.
- **UI is PT-BR**, money formatted as `R$ 415.927,84`.
- **New data sources** implement the `Source` protocol and emit `SectionKey`s;
  they never touch the API contract or the SPA.
- **Tenancy boundary is server-side.** Hiding a frontend button is never the
  security boundary; `require_client_access` is.
- Conventional, focused commits.
