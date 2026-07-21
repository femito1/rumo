# SISJURI Database — direct DB access (discovered 2026-07-01)

> **Audience:** engineers evaluating a DB-backed alternative/audit path to the
> LegalDesk OData API. For the API itself see `docs/LEGALDESK.md`; for current
> status see `PROJECT_STATUS.md`. **Sacred numbers still live in
> `docs/LEGALDESK.md` §4 and win.**
>
> **Secrets:** this file contains **no** credentials. The DB user/password and
> the Windows RDP password used during discovery were shared out-of-band and
> **must be rotated**. Never commit them.

## TL;DR

SISJURI has **no API**, but its data lives in an **Oracle 19c** database that is
reachable — read-only — through the authorized Windows bridge server
`MBC-LDESK01` (the same host that runs the Power BI gateway). The DB contains an
**`LDESK` schema (601 tables)** that is the LegalDesk data RUMO already consumes
via OData, plus an **`SSJR` schema (704 tables)** of SISJURI core data. This is a
viable path to **audit** the sacred numbers, act as a **fallback** source, or
back a future `Source` implementation.

## Known account facts — CHECK THIS BEFORE PROBING (living index)

> **Read this table first.** It exists so we stop re-discovering the same DB
> facts. If you learn a new account→meaning→destination fact from a probe, **add a
> row here in the same commit.** Values are 2026 monthly examples (validation aids),
> NOT sacred; the *mapping* is the durable part.

### Institutional row-198 (Base_Resultado "Despesas Institucional")

Row 198 = sum of 10 families (Ocupação, Telecomunicações, Despesas Gerais,
Consultoria, Salários Administração, Administrativas, Investimentos em Prospecção,
Gestão do Conhecimento, Endomarketing, Informática). **Excludes** Impostos (row
168), Distribuição de Lucros (191), Despesas para Clientes (82). Area lines are
surfaced per-area (rows 204-206) **and** kept in the family totals. Authoritative
book = **05.2026** (boss-confirmed; 02.2026 uses an older layout). Full account map
+ formula proof: `HANDOFF_DRE_AUTOMATION.md` Appendix B/C. Encoded in
`app/closing/workbook_layouts.py::section_for` (keyed on stable CONTA3 codes).

| account (CONTA3) | meaning | workbook destination |
|------------------|---------|----------------------|
| `020.010.*` | Aluguel/Condomínio/Energia/IPTU | Ocupação |
| `020.010.0050` | Manutenção e Conservação | → Despesas Gerais |
| `020.020.*` | Telecom | Telecomunicações |
| `020.030.*` | Despesas Gerais | Despesas Gerais |
| `020.030.0150` | Relacionamento Institucional (Flores/Presentes) | → Endomarketing |
| `020.040.0010` | Serviços de Informática | → Informática (Suporte) |
| `020.040.0030` | Terceirização Limpeza (no area) | → Despesas Gerais (Limpeza e Copeira) |
| `020.040.0050` | Contabilidade | → Consultoria |
| `020.040.0060` | Servidor Externo | → Informática (Data Center) |
| `020.050.*` | Salários Administração (NO Vale account here) | Salários Administração |
| `020.050.0050/0060/0070/0160` | INSS/FGTS/IR/e-Social ADM | → Impostos (row 168, OUT of 198) |
| `020.060.0010/0020` | Assinaturas/Associações | Administrativas (STAY; also per-area) |
| `020.060.0040` | Seguros | → Ocupação (Seguro Locação) |
| `020.070.*` | Financeiras | → Administrativas |
| `020.080.0030` | Estacionamento (clientes) | → Despesas Gerais |
| `020.080.0050/0060` | Vale Ref/Transp (area staff, tiny, area-tagged) | → Salários Adm (area) |
| `020.090.*` | Investimento em Prospecção | Investimentos em Prospecção |
| `020.090.0040` | Eventos e Happy Hour | → Endomarketing (05 book "Eventos Internos") |
| `020.110.0010` | Participação Externa (comissões), area-level via ID_GRUPOJURIDICO | Comissão block (kind='area', OUT of 198) |
| `030.010.0120` | Participação Interna (comissões), **per-lawyer via `CONTASPAGAR.COD_ADVG`** — NÃO via `LANCAMENTO.LANCPROFDEST` (é NULL nessas linhas; a sigla só aparece no histórico "Comissão EHF"). Mai EHF 2.128,06 → Econômico. Foi o que zerava `comissao_deriv` (2026-07-13 probe). | Comissão block (kind='lawyer', folded by home area/rateio) |
| `030.010.0080` | Participação E — sempre vazio (não lido) | — |
| `040.010.*` | Marketing / Assessoria de Imprensa | → Consultoria |
| `040.030.*` | Investimentos:Consultoria Adm/Financeira | → Consultoria |
| `040.040.*` | Licenças/Micros/Impressoras | Informática |
| `040.050.*` | Biblioteca | → Gestão do Conhecimento |
| `030.010.0180` | **Cursos / Treinamento Jurídico** | → **Gestão do Conhecimento** (lifted OUT of Custo Equipe; area-tagged part only) |
| `150.000.0000` (`150.%`, real leaf `150.010.0010`) | **Bônus individuais dos funcionários** (Lucros/Bônus) | → Base_Resultado "Distribuição de Lucros extras" > **"Bônus equipe"** (POINT 16). **POINT 17 AUTOMATIZADO POR NÓS (2026-07-14, `probe_socio_split` + `probe_socio_split_validate`) — NÃO é tarefa do RUMO.** ⭐ **Flag estrutural achado: `LDESK.CAD_PROFISSIONAL.SOCIO`** ('S'/'N'). AM/DC/RB=**S**, MV=**N** — o DB separa os 3 sócios núcleo do Martim, igual ao workbook. ⚠ **FONTE CORRIGIDA:** os lançamentos 150.* vivem em **`FINANCE.LANCAMENTO`** (por `LANDDATA`), **NÃO** em `GERENC_LANCAMENTORESUMO` (retornava NULL/vazio — era o bug do `bonus_equipe`). Fev `FINANCE.LANCAMENTO` 150.% = **94.696,15** (FSM 22.596,95 + EHF 21.047,83 + BMP 16.300,57 + IAC 15.773,11 + BBX 12.903,36 + ASG 6.074,33), todas siglas **SOCIO='N'** (150.* já é só funcionário). Extract agora: `bonus_equipe` = Σ `FINANCE.LANCAMENTO` 150.% EXCLUINDO qualquer sigla SOCIO='S' (2º token do histórico "Bônus <SIGLA> ..."; hoje no-op, future-proof); **MAIS `bonus_equipe_030`** = bônus de funcionário lançado em `030.010.0010` (JGS 7.009,84, histórico "Bônus JGS referente a 2025"). Soma fev = **101.705,84** = workbook `D192` ao centavo. NULL quando não há lançamentos (linha em branco). Cliente confirmou: DL extras ~1×/ano em FEVEREIRO → maio = 0 é CORRETO. **DL excedente dos sócios** = `030.010.0010` histórico "DL excedente `<SIGLA>` - Reserva", split pelo flag SOCIO: `dl_excedente_socios` (SOCIO='S', ≠MV) **jan = 164.477,34** (AM 70.790,94 + DC 46.843,20 + RB 46.843,20 = Base_Resultado **D193** exato) + `dl_excedente_mv` (Martim) **mar = 6.627** (= **D194** exato). Ambos os blocos novos no `extract.sql`; `dre.py` funde as chaves top-level no bloco de extras (distribuicao_extras explícito ainda vence). Ver [[dl-extras-bonus-rules]]. |
| `500.010.DC/RB/EHF` (histórico "Convênio Médico dependentes"/"Débito pessoal ... upgrade") | **Convênio extra por advogado** — upgrade/dependentes que o advogado paga, deduzido da DL dele (NÃO é despesa do escritório) | **PROVADO (2026-07-14 probe_convenio_extra_dl):** constante Jan–Mai — **DC 3.796,78 · RB 5.151,75 · EHF 1.398,01** (via `LANCAMENTO.LANNVALOR`, `LANCPROFDEST` NULL → sigla vem do sufixo da conta `500.010.<SIGLA>`). Aurélio/AM: o extra já está embutido na base `030.010.0110` (4.774,27), não em 500.010. Base convênio 0110 por sigla (mai) confirmada: DC 1.736,14, BBX 1.269,46, RB 3.427,58, AM 4.774,27, EHF 2.122,30 etc. **Wire:** subtrair este valor da DL do sócio correspondente. Ver [[transitoria-desdobramento-mechanism]]. |
| `LDESK.DB_VW_FATURASEMI_REC` (view) | **Faturas emitidas + recebimento, com moeda** — a fonte das abas **Nacional** (BRL) e **Moedas** (EUR/USD) | **RESOLVIDO + VALIDADO AO CENTAVO (2026-07-14).** `FAT_FATURA` cru NÃO serve (mai 774.917,10, 53 linhas incl. cancelada `SITUACAO='C'`, ≠ sacred). A view **`DB_VW_FATURASEMI_REC`** bounded by `DATA` (emissão) no mês soma `VALOR_HONORARIOS_NAC` = **719.988,05 = sacred faturamento_bruto('2026-05') EXATO**, split R$ 708.659,18 (72) + US$ 11.328,87 (3). Colunas: `NUMERO, CLIENTE, CASO, ID_CASO, ID_CLIENTE, DATA, DATA_VENCIMENTO, DATA_RECEBIMENTO, ID_MOEDA, SIGLA_MOEDA, SIGLA_MOEDA_NACIONAL, VALOR_HONORARIOS(+_NAC), VALOR_DESPESAS(+_NAC), CR_HON(+_NAC), CR_DESP(+_NAC)`. ⚠ É per-invoice-LINE (n=75 p/ ~53 faturas; fatura 4143 tem 6 linhas de 678=4.068) → o extract faz **`GROUP BY NUMERO`** p/ o grão per-fatura do workbook (o sacred cross-check prova que as linhas são reais, não fan-out). Bloco `faturas_moeda` no `extract.sql`; backend `assemble_faturas_moeda` divide Nacional (moeda==moeda_nac) vs Moedas. Nota Fiscal + Razão Social ficam no `FAT_FATURA` (via `ID_FATURA`) se precisar depois. |

### Post-meeting facts (2026-07-10) — see `docs/MEETING_2026-07-10.md` for full detail

- **Imposto do DRE = 15% do Recebimento** (número sacred do LegalDesk), NÃO a soma
  do razão `050.010.*`. Maio: 0,15 × 415.928 = 62.389,20 (bate: Bruto 100.327 −
  Imposto 62.389 − Amort 8.117 = Líquido 29.821).
- **Amortização = 8.117,00/mês** (fixo). **Reserva de bônus = 10% do Resultado
  Líquido** (por área). **Custo direto = Custo equipe + Participação + Comissão.**
- **`050.010.*` "Impostos - Tributos" (TIPO O)** = IRRF/PIS/COFINS/CSLL/ISS — visão
  de caixa/competência; **não** é a linha de imposto do DRE.
- **Contas Transitórias = uma CLASSE de contas (não um hub único).** Corrigido pelo
  cliente 2026-07-13. `PLANO CONTAS` lista (TIPO B): `200.010.0010` Transitória de
  **Pagamentos**, `.0020` Receitas, `.0030` Saldos Iniciais, `.0050` **Desdobramento
  após Pagamento**, `.0060` Acerto, `200.020.0030` Repasse Sócios; e `300.010.*`
  **Valor Agregado** (IRRF/INSS/ISS/PIS/COFINS/CSLL/Convênio de terceiros). Um
  pagamento cai na transitória e o **sistema o DESDOBRA** (rebucket) nas contas de
  despesa reais. A instrução de cada desdobramento vive no campo **`ORIENTAÇÃO`** de
  cada linha `FINANCE.LANCAMENTO`/`CONTASPAGAR` ("desdobramento - histórico",
  "suporte totvs", "suporte informática", "conta iss", "imposto terceiros", "não
  lançar"…), NÃO numa tabela de rateio estática (coluna Rateio do plano = 'N' p/ todas
  as 278 contas — o export não a carrega). É o "contas transitórias + desdobramento"
  do chefe: **o dado ESTÁ no DB**, chaveado por ORIENTAÇÃO/histórico.
  - Mapa desdobramento maio (Pagtos maio, `Conta Destino` × `ORIENTAÇÃO`, `Valor
    Bruto`): `Serviços de Informática` → "suporte informática" 2.040,00 / "suporte
    totvs" 3.108,97 / "vamos ajustar" 4.504,12; `200.010.0010` VR/VT Mensal 3.326,94
    (Vale-ADM, ver T4); Licenças de Uso de Software 3.880,50 (+"não terá lanç" 3.461,48).
    ⚠ O split que o workbook mostra (Informática Suporte Totvs 2.917,77) NÃO bate com o
    mês de pagamento (3.108,97) — há **alocação multi-mês/accrual** no desdobramento;
    reproduzir exige modelar o accrual, não só reetiquetar o mês. (Salários-Adm e as 7
    outras famílias já batem ao centavo; faltam Informática −1.553 e Despesas Gerais.)
- **`200.010.*` Transitórias** e **`300.010.*` Valor Agregado** = contas de
  desdobramento automático (impostos de terceiros, VR/VT, associações etc.).
- **Recebimento por área** = Demonstrativo Gerencial por Profissional (LegalDesk):
  Contencioso + Econômico + (Arbitragem + **Ambiental**) + **Não Alocados** = total.
- **Contas `Grupo='S'`** (plano de contas) = as despesas que o sistema **rateia por
  área automaticamente** (Associações, Prospecção, Eventos/HH, Cursos, Material
  Gráfico, Distribuição Fixa…). O `Contas a Pagar` traz a coluna `Grupo`
  (ECT/EDE/ESP/ADM) já preenchida — usar essa, não rebucket à mão.
- **`Pagtos maio.XLS.xlsx` = FINANCE.CONTASPAGAR detalhado**: colunas úteis
  `Conta Destino`, `Valor Bruto`, `Valor Base`, `Grupo`(área), `Profissional
  Destino`, `ORIENTAÇÃO`, `Histórico`. Plano de contas completo em `/tmp/plano_contas.csv`.

### Workbook targets (regra dura) — fonte, layout e números (2026-07-10)

A **regra dura** (`backend/app/closing/verification.py`) exige que toda célula
Realizado bata com o workbook (±R$1,00 — tolerância elevada de R$0,01 em
2026-07-13 porque **o workbook arredonda muitas células para reais inteiros**
enquanto o DB carrega centavos; ex.: Mai Recebimento = 415928 no book vs
415927,84 sacred. O drift máx. em células diretamente deriváveis, Jan–Mai, é
R$0,16; um bug real é ordens de grandeza maior) ou fique em branco. Esses alvos foram
extraídos do workbook **autoritativo** `Fechamento MBC 05.2026.xlsx`, aba
**`Areas Sintetico atualizado`**, e congelados em
`backend/app/closing/workbook_targets_2026.json` (regenerar com
`python backend/scripts/build_workbook_targets.py`). **Nada lê o .xlsx em runtime.**

Layout verificado da aba (1-based):
- Linha 1 = cabeçalho de mês; cada mês ocupa 4 colunas (Orçado | Realizado |
  Variação | Desvio%). **Colunas Realizado: Jan=3, Fev=7, Mar=11, Abr=15, Mai=19.**
- Bloco Institucional: `4` Receita(recebimento), `6` **Custos Diretos** (=nossa
  linha "Custo equipe" = equipe+comissão), `13` Despesas Indiretas(despesas),
  `25` Resultado Bruto, `28` Impostos(=15% receb), `29` Amortização(8.117),
  `30` Resultado Líquido, `32` Bonus(=10% líquido, segue o sinal).
- Blocos por área começam em: **Contencioso=35, Econômico=53, Arbitragem=71**;
  dentro do bloco Receita=+1, Custo Equipe=+4, Resultado Bruto=+8.

Alvos Institucional Realizado (05.2026, ao centavo):

| mês | Recebimento | Custos Diretos | Desp. Indir. | Result. Bruto | Imposto | Result. Líq. | Bônus |
|----:|------------:|---------------:|-------------:|--------------:|--------:|-------------:|------:|
| Jan | 279 821,07 | 211 242,68 | 100 181,41 | −31 603,02 | 41 973,16 | −81 693,18 | −8 169,32 |
| Fev | 319 233,58 | 218 453,74 | 95 047,39 | 5 732,45 | 47 885,04 | −50 269,59 | −5 026,96 |
| Mar | 612 501,76 | 198 079,41 | 101 968,90 | 312 453,45 | 91 875,26 | 212 461,19 | 21 246,12 |
| Abr | 238 327,46 | 209 572,83 | 110 156,11 | −81 401,48 | 35 749,12 | −125 267,60 | −12 526,76 |
| Mai | 415 928,00 | 210 089,46 | 105 511,43 | 100 327,11 | 62 389,20 | 29 820,91 | 2 982,09 |

Alvos Custo equipe por área (05.2026):

| mês | Contencioso | Econômico | Arbitragem |
|----:|------------:|----------:|-----------:|
| Jan | 73 576,32 | 75 653,19 | 62 013,17 |
| Fev | 76 342,35 | 78 817,05 | 61 794,34 |
| Mar | 72 845,49 | 76 049,97 | 49 183,94 |
| Abr | 75 374,05 | 79 160,08 | 55 038,69 |
| Mai | **74 141,21** | **79 436,24** | 54 383,94 |

Alvos Recebimento por área (05.2026): Mai Contencioso 240 445, Econômico 166 876,
Arbitragem 41 860 (Arbitragem já **inclui Ambiental**; "Não Alocados" não entra nas
áreas — fica só no total). Meses anteriores no JSON.

> Nota: o `Bonus` do workbook é 10% do Resultado Líquido **mesmo quando negativo**
> (Jan −8 169,32 = 0,10×−81 693,18); nosso `bonus_reserve` faz o mesmo.
> O `custos_diretos` da linha institucional já embute Participação/Comissão, por
> isso o alvo Fev (218 453,74) = Σ custo equipe áreas (216 953,74) + comissão (1 500).

### Vale Refeição/Transporte source — `FINANCE.LANCAMENTO`, `500.010.<SIGLA>`

CORRECTED after live probing (probe_vale_find.sql, 2026-07-08):

- **NOT** on `030.010.0100/0220` (those have **zero** rows by `LANDDATA` in 2026).
- **NOT** in `CONTASPAGAR` (only a tiny `500.010.AM` custas line).
- There is **no `ID_GRUPOJURIDICODEST` column** on `LANCAMENTO`; the cost-center is
  **`SIGLADEST`** and the professional is **`LANCPROFDEST`** (both often NULL on
  these rows). Date axis that matches the workbook = **`LANDDATA`**.
- The Vale lives in **`FINANCE.LANCAMENTO`** on **`500.010.<SIGLA>`** with historico
  `Vale transporte` (bundles Refeição+Transporte). Siglas seen: **JVO** (Contencioso
  — an AREA lawyer → per-area Custo Equipe), **MLA** and **VSR** (administrative).

Reconciliation status (workbook Salários-Adm Vale = row 122 Ref + row 123 Transp):

| month | wb Vale-ADM | MLA+VSR (500.010) | +other Vale postings | ties? |
|------:|------------:|------------------:|---------------------:|:-----:|
| Jan | 1 127,96 | 1 092,44 | — | ~ (Δ35,52) |
| Feb | 1 351,88 | 1 351,88 (MLA only) | — | **yes** |
| Mar | 3 983,22 | 2 249,32 | 3 335,76 | no |
| Abr | 3 421,36 | 2 230,56 | — | no |
| Mai | 3 326,94 | 1 121,94 | 2 090,04 | no |

**RESOLVED (2026-07-10) via `Pagtos maio.XLS.xlsx` (= CONTASPAGAR detail):** Vale-ADM
is booked to **`200.010.0010 Transitória de Pagamentos`** with `ORIENTAÇÃO=
"desdobramento - histórico"`, identified by the **histórico text** — May rows:
`"Pagamento de VR Mensal para Jo..."` = **2.719,90** (= wb `G122` Vale Refeição-ADM)
and `"Pagamento de VT Mensal para Jo..."` = **607,04** (= wb `G123` Vale Transporte).
So it was never a `500.010`/`030.*` posting — it is a **transitory payment unfolded
(desdobramento)**, keyed by histórico `%VR %`/`%VT %`/`Vale ... Mensal para`.
Extract from `CONTASPAGAR`/`LANCAMENTO` on `200.010.0010` filtered by that histórico.
(The earlier MLA/VSR `500.010` table below was a red herring for the ADM total, though
those siglas ARE administrative.)

**⭐ CORRECTION (2026-07-21, `lancextrato de contas.xls` = raw Extrato de Contas, May):**
the claim (memo `vale-adm-not-in-db-jan-mar-decision`) that "who inside the VR/VT bundle is
ADM vs área is NOT stored in the DB" is **WRONG**. The transitória `200.010.0010` unfolds the
VR/VT **Mensal parent** (2.719,90 + 607,04) into **per-person destination accounts**:
`500.010.MLA` (783,70+262,64), `500.010.JVO` (968,10+268,80), `500.010.VSR` (75,60), plus a
`020.030.0060` slice (968,10). The ADM-vs-área split IS in the DB — it is the **destination
account** (`PCTCNUMEROCONTADEST`, NOT `LANCPROFDEST`/`SIGLADEST`, which are NULL on these rows).
The prior probe summed the wrong leg. ⚠ The same VR/VT slice ALSO appears in `400.010.0040
Repasse` (the double-entry counter-leg) — do NOT sum both or you double-count. The correct
Vale-ADM = the **VR/VT Mensal parent** (positive leg). `probe_janapr_reconcile.sql` #1 verifies
this per month for Jan–Apr. See `docs/FINDINGS_2026-07-21-manuais-refutados.md`.

### The `500.010.<SIGLA>` personal-debit namespace (DO NOT re-discover)

Per-professional personal debits keyed by SIGLA in `FINANCE.CONTASPAGAR`
(`PCTCNUMEROCONTA LIKE '500.010.%'`, gross in `CPGNVALORBASE`, memo in
`CPGCHISTORICO`). **This is where ADM Vale Refeição/Transporte lives** — there is NO
Vale account under `020.050.*` and no Vale in the summarised S/I views.

- **Vale (histórico `%VALE%`/`%REFEI%`/`%TRANSP%`):** area-lawyer siglas → per-area
  Custo Equipe (JVO Feb 1.249,40 → Contencioso). **ADM/non-area siglas → workbook
  Salários Administração** (row 116, inside row 198). `500.010.MLA` Feb = 1.351,88 =
  EXACTLY the workbook Feb Vale-ADM (Ref 1.014,20 + Transp 337,68). The custo-equipe
  extract *excludes* MLA as "ex-lawyer"; the institutional side must *include* it.
- **Convênio dependente** (`%CONVÊNIO%dependente%`): personal debt, NOT Custo equipe.
- **GPS/INSS s/ folha** `178,31`: reciprocal of the gross-vs-net pró-labore gap; do
  NOT add as Custo equipe (double-count).

### Other durable facts

- Gross "de folha" (pró-labore etc.) = `FINANCE.CONTASPAGAR.CPGNVALORBASE`, NOT the
  net `VALOR` in the resumo view. Keys: `COD_ADVG`, `PCTCNUMEROCONTA`,
  `CPGCHISTORICO`, `CPGDVECTO` (competence/vencimento).
- Reserva de bônus = 10% da margem líquida (fixed, all months).
- `RateioFaturaProfissionalViews` duplicates rows — de-dup by
  `(FaturaNumero, ProfissionalSigla)` before summing.
- `FINANCE.VW_RESULTADO_MENSAL_DET` carries `LANNCODIG`, `CONTA1/2/3`,
  `TITULO1/2/3`, `SETOR`, `ORCAMENTO` — the account-keyed institutional detail.

## Access path (authorized — through the server, not direct)

```
SISJURI Oracle 19c
  host 172.16.237.9 : 1521   (private OCI VCN — NOT reachable from the internet)
  SERVICE_NAME cdbp01_pdb1.submbc.vcnmbc.oraclevcn.com
        ^  Oracle 11g client + sqlplus  (System DSN "sisjuri")
        |
  MBC-LDESK01   Windows Server 2012 R2   (RDP; only host with a route to the DB)
        |
        v  Power BI On-Premises Data Gateway (PBIEgwService, running)
   Power BI cloud
```

- The DB host is a **private VCN address**: only `MBC-LDESK01` can reach it, which
  is why all access must go **through the server**.
- Oracle client home: `C:\oracle11\app\product\11.2.0\client_1`
  (`bin\sqlplus.exe`, `bin\tnsping.exe`).
- TNS aliases in `...\network\admin\tnsnames.ora`: `SISJURI` / `CDBP01_PDB1`
  (the 19c PDB, used by the DSN), plus `SISJURI11` / `PROD11` on `172.16.237.31`
  (older Oracle 11 hosts — not used here).

## Credential & privileges (as discovered)

- DB user **`RGN`** — provided out-of-band. **Rotate it.**
- Privileges: `CREATE SESSION` only, **no roles**. Despite that, it has **real
  SELECT** on `LDESK` application tables (confirmed by returning row counts, not
  just catalog visibility). Treat as **read-only**; only ever run `SELECT`.

## Schema inventory (18 owners; application data in bold)

| Owner | Tables | What it is |
| --- | ---: | --- |
| **SSJR** | 704 | SISJURI core (agenda, faturamento, fiscal SPED, SAPC contencioso, DBM CRM, compras) |
| **LDESK** | 601 | **LegalDesk** model (`CAD_*`, `FAT_*`, `JUR_*`, `GERENC_*`, `CONTR_*`) — the RUMO source |
| RCR | 353 | module (TBD) |
| SAPC | 221 | SAP connector / contencioso |
| FINANCE | 89 | financial |
| SYNC | 25 | replication/sync |
| SEGURANCA | 11 | security/users |
| CUSTOM / LDESK_CUSTOM / LIXO | 2 / 1 / 1 | custom / scratch |
| SYS, SYSTEM, MDSYS, XDB, CTXSYS, APEX_220200, FOEX_210100 | — | Oracle internals (ignore) |

## Key billing tables (LDESK) and confirmed shape

Row counts (2026-07-01) and the columns that matter for the monthly closing:

| Table | Rows | Notable columns |
| --- | ---: | --- |
| `LDESK.FAT_FATURA` | 4,249 | `NUMERO`, `SITUACAO`, `DATA_EMISSAO`, `DATA_CANCELAMENTO`, `VALOR_HONORARIOS`, `VALOR_DESCONTO`, `VALOR_DESPESAS`, `VALOR_DESPESAS_TRIB`, `ID_ESCRITORIO`, `ID_PROFISSIONAL_RESP` |
| `LDESK.FAT_FATURA_PROF` | 9,798 | invoice x professional |
| `LDESK.FAT_RATEIOFATURA_PROF` | 19,812 | `ID_FATURA`, `ID_PROFISSIONAL`, `ID_CASO`, `ID_CLIENTE`, **`VALOR_FATURADO`**, **`VALOR_TRABALHADO`**, **`ANO_MES`** (`'YYYY-MM'`), `ID_ESCRITORIO` |
| `LDESK.FAT_TIMESHEET` | 55,925 | timesheets |
| `LDESK.CAD_PROFISSIONAL` | 69 | professionals |

Data characteristics:

- **Single tenant** in this instance: one `ID_ESCRITORIO`
  (`5B041D9E-98E9-68F1-A6E1-8C4DB3FE939A`) owns all rows.
- **Continuous history: 98 competence months, 2018-05 -> 2026-06.**
- `FAT_RATEIOFATURA_PROF` is **clean at the PK level** (raw rows == distinct
  `ID_RATEIOFATURA_PROF`). The duplication warned about in `CLAUDE.md` /
  `docs/LEGALDESK.md` comes from the **API view** `RateioFaturaProfissionalViews`,
  not this base table — querying the DB directly avoids that gotcha.

## Cross-check vs. the sacred numbers (2026-05)

Sacred (from `docs/LEGALDESK.md` §4, locked by `test_legaldesk_source.py`):

- `receita_honorarios` (recebimento_bruto) = **415.927,84**
- `faturamento_realizado` (faturamento_bruto) = **719.988,05**
- `faturas_emitidas` = **53**

DB observations so far:

- `FAT_FATURA` by `DATA_EMISSAO` 2026-05 = **53 invoices** -> **matches** `faturas_emitidas`.
- `FAT_RATEIOFATURA_PROF` 2026-05 = **286 rows** -> **matches** the documented
  rateio row count (and 53 distinct invoices).
- The money headlines (415.927,84 / 719.988,05) come from the OData entities
  `PosicaoFinanceiraResultadoRecebimentoViews` / `...FaturamentoViews`
  (sum of `Valor1` for the `AnoMes`). Mapping these to their underlying
  Oracle view/table is **in progress** (search `all_objects` in `LDESK`/`SSJR`
  for `%POSICAO%` / `%RESULTADO%` / `%RECEB%` / `%FATURAMENTO%`).

## Reliable sqlplus invocation (hard-won)

The RDP console **collapses pasted newlines** and PowerShell **mangles
connect-string arguments** (`@`, parentheses). Two robust patterns:

### A. One-liner (easiest — no base64, no multi-line paste)

Everything on ONE line; SQL line breaks are PowerShell backtick-n; password is
double-double-quoted; `CONNECT` lives inside the SQL file:

```powershell
$s="SET DEFINE OFF`nSET FEEDBACK ON`nWHENEVER SQLERROR CONTINUE`nCONNECT RGN/""<PASSWORD>""@(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=172.16.237.9)(PORT=1521))(CONNECT_DATA=(SERVICE_NAME=cdbp01_pdb1.submbc.vcnmbc.oraclevcn.com)))`n<SQL; statements end with ; and are separated by backtick-n>`nEXIT;";Set-Content C:\temp\q.sql $s -Encoding ASCII;& 'C:\oracle11\app\product\11.2.0\client_1\bin\sqlplus.exe' /nolog '@C:\temp\q.sql' *>&1 | Tee-Object C:\temp\out.txt
```

### B. Base64 delivery (immune to any paste mangling)

Encode a full `.ps1` to base64, then:

```powershell
$b='<BASE64>';[IO.File]::WriteAllText('C:\temp\probe.ps1',[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($b)));powershell -ExecutionPolicy Bypass -File C:\temp\probe.ps1 *>&1 | Tee-Object C:\temp\out.txt
```

Rules that make either work:
- `CONNECT` goes **inside** the `.sql`, password quoted (it contains `@`),
  **inline DESCRIPTOR** (no dependence on `tnsnames.ora` resolution quirks).
- Launch `sqlplus /nolog @file` — no special chars as shell args.
- `SET DEFINE OFF` / `SET SCAN OFF` so `&` is not treated as a substitution prompt.
- `Tee-Object` to a file so output can be retrieved with `Get-Content` if the
  console is hard to copy.

## Why this matters for RUMO

- **Audit**: independently verify the API's sacred numbers against raw DB rows.
- **Fallback / alternative**: a DB-backed `Source` (implementing
  `app/sources/base.py`) could supply the same `SectionKey`s if the API is
  unavailable — without touching the API contract or the SPA.
- **Reach**: `SSJR`/`FINANCE` may expose data the OData API does not.

## Open items

- Map `PosicaoFinanceiraResultado{Recebimento,Faturamento}Views` to their DB
  objects and reconcile the 415.927,84 / 719.988,05 totals.
- Confirm whether other tenants exist on the `SISJURI11` / `PROD11` instances.
- Decide if a `SisjuriDbSource` is worth building (vs. keeping OData primary).

## Full-closing coverage — the FINANCE schema (discovered 2026-07-01)

**Major finding:** the institutional expenses that `docs/LEGALDESK.md` declared
out-of-scope ("TOTVS Backoffice / ~65 manual lines") are **in this same Oracle
DB**, in a dedicated **`FINANCE`** schema that `RGN` can read. This means the DB
can, in principle, source the **entire** monthly closing — revenue *and*
institutional expenses — not just the LegalDesk billing side.

Evidence gathered against the MBC financial exports the client sent
(`reference/workbook/{PLANO CONTAS.XLS.xlsx, Pagtos maio.XLS.xlsx,
lancextrato de contas.xls}`):

| Client sheet | DB object (readable by RGN) | Rows |
| --- | --- | --- |
| `PLANO CONTAS` (chart of accounts, 279 lines) | `FINANCE.PLANOCONTAS` | 278 |
| `Pagtos maio` (payments) | `FINANCE.LANCAMENTO` (financial entries) | 36,093 |
| `lancextrato de contas` (Extrato de Contas ledger, 88 accounts) | built from `FINANCE.LANCAMENTO` + `FINANCE.PLANOCONTAS` | — |
| (payables) | `FINANCE.CONTASPAGAR` | 7,955 |

Also present: `FINANCE.{CONTASRECEBER, EXTRATO, GRUPOPLANOCONTAS,
PLANOCONTACONTABIL}` and many reporting views (`VW_EXTRATO`, `VW_LANCAMENTO`,
`VW_LANCAMENTOCONTABILIDADE`, `VW_RESCENTROCUSTO`, `VW_PLANOCONTASEXTRATO`, ...).
`FINANCE.EXTRATO` is **empty** (0 rows) here — the "Extrato de Contas" report is
derived from `LANCAMENTO`, not from the bank-reconciliation `EXTRATO` table.

### Data model — double-entry

`FINANCE.LANCAMENTO` is a **double-entry** ledger. Each row moves value between
two plano-de-contas accounts:

- `PCTCNUMEROCONTAORG`  — origin account (VARCHAR2, e.g. `200.010.0020`)
- `PCTCNUMEROCONTADEST` — destination account (e.g. `020.010.0010`)
- `LANNVALOR`  — value (NUMBER)
- `LANDDATA`   — entry date (DATE)
- `LANCHISTORICO` — free-text history
- `SIGLAORG` / `SIGLADEST` — professional sigla; `ESCRITORIOORG` / `ESCRITORIODEST`
- `GERADO_LD` — flag: generated by LegalDesk
- NB: `LANCAMENTO.CODIGO` is a currency/real-estimado flag ('R'), **not** the account.

`FINANCE.PLANOCONTAS` key columns:

- `PCTCNUMEROCONTA` — account code (`010.010.0010`) — join key to LANCAMENTO ORG/DEST
- `PCTCTITULO` — account title (e.g. `Aluguel`)
- `PCTCNUMEROCONTAPAI` — parent account (tree)
- `PCTNNIVEL` — level; flags `PCTCFLAGCP/CR/BANCO/RATEIO/...`

### Reproduce the "Extrato de Contas" ledger

Group May-2026 entries by **destination account** joined to the plano de contas:

```sql
SELECT p.PCTCNUMEROCONTA AS conta, p.PCTCTITULO AS titulo,
       COUNT(*) AS n, ROUND(SUM(l.LANNVALOR),2) AS total
  FROM FINANCE.LANCAMENTO l
  JOIN FINANCE.PLANOCONTAS p ON p.PCTCNUMEROCONTA = l.PCTCNUMEROCONTADEST
 WHERE l.LANDDATA >= DATE '2026-05-01' AND l.LANDDATA < DATE '2026-06-01'
 GROUP BY p.PCTCNUMEROCONTA, p.PCTCTITULO
 ORDER BY p.PCTCNUMEROCONTA;
```

This returns all 88 accounts with the right titles (Aluguel, Condomínio, IPTU,
Salários, INSS, FGTS, Distribuição Mensal Fixa, Consultoria, COFINS, per-
professional `500.010.*`, etc.). Spot-check: DEST `020.010.0010 Aluguel` =
**27.477,67**, which matches the genuine Aluguel line in the client's ledger
export. (A naive re-sum of the `.xls` mis-parses because of the report's
blank/merged rows; the DB figure is the clean source of truth.)

### Coverage matrix (workbook tabs -> source)

| Workbook data family | Source | DB objects |
| --- | --- | --- |
| Revenue: honorários / recebimento / faturamento | API today; **also DB** | `LDESK.FAT_FATURA`, `PosicaoFinanceira*` (mapping TBD) |
| Rateio por profissional / por caso | API today; **also DB** | `LDESK.FAT_RATEIOFATURA_PROF` |
| Faturas / centro de custo | API today; **also DB** | `LDESK.FAT_FATURA` (+ rateio caso) |
| **Institutional expenses (aluguel, salários, INSS/FGTS, impostos, distribuições, CAPEX)** | **was MANUAL/TOTVS — now DB** | `FINANCE.LANCAMENTO` + `FINANCE.PLANOCONTAS` |
| Chart of accounts / DRE scaffold | **DB** | `FINANCE.PLANOCONTAS` (278) |
| Payables / receivables | **DB** | `FINANCE.CONTASPAGAR` (7,955), `FINANCE.CONTASRECEBER` |

**Implication:** the `PROJECT_STATUS.md` §5 assumption that institutional
expenses require a future Juritis/TOTVS integration may be **obsolete** — the
data is reachable now via this DB. This warrants revisiting the Juritis plan and
considering a `FinanceDbSource` alongside `LegalDeskSource`.

### Open reconciliation items

- Whether the closing wants **DEST-only**, **ORG-net**, or **cash-account
  (100.*)** views per line (the double-entry means each value appears on both
  sides). Match the workbook's DRE definitions before trusting per-line totals.
- Confirm the ledger's competence vs. cash-date convention (`LANDDATA` vs
  `LANDDATADESP`).

## DRE reconciliation nuance (2026-07-01) — data is present, but 3 transforms apply

Reading the workbook's core DRE tab `Base_Resultado Mensal_V2` against the DB
shows the closing is **not** a raw account dump. Three transforms sit between the
DB ledger and the workbook lines. The DB has all the data; a `FinanceDbSource`
must replicate these:

1. **Competence (accrual) vs cash (payment) basis.** Workbook `Aluguel` Jan =
   `26.384,63` (competence base); the DB/ledger payment is `27.477,67` (cash, with
   monetary correction, competence Abr/2026). So `SUM(LANNVALOR) by LANDDATA month`
   != the workbook line. Competence likely comes from the `Competência: MM/AAAA`
   text in `LANCHISTORICO` (or `LANDDATADESP`), not the payment date `LANDDATA`.
2. **Per-professional x cost-center breakdown.** DRE lines are grouped as
   `Custo equipe - {Contencioso, Econômico, Arbitragem e Compliance}`, then
   `Ocupação`, etc., each split per professional (`... - Convenio Medico`,
   `- Distribuição Mensal`, `- Pro labore`). DB can do this via
   `LANCAMENTO.SIGLADEST` + `PCTCNUMEROCONTADEST` and the `500.010.<SIGLA>`
   accounts, **plus** a professional->cost-center mapping the workbook encodes by hand.
3. **Line taxonomy.** Plano-de-contas accounts must be mapped to the workbook's
   DRE line labels.

**Today these leaf values are hardcoded** in `Base_Resultado Mensal_V2` (the audit
counts 58 hardcoded cells; only subtotals are `SUM()` formulas). That is the
manual step the client's ledger export currently feeds — and the step a DB source
could automate.

**Conclusion:** there is **no missing data source** for the closing — revenue and
all institutional expenses are in the DB. Remaining work to automate is
*modeling* (competence assignment, cost-center map, line taxonomy), not *access*.

## Sacred-number reconciliation — EXACT MATCH (2026-07-01)

The two headline sacred totals were reconciled **to the centavo, including row
counts**, straight from the DB. Source views (behind the OData
`PosicaoFinanceiraResultado*Views`):

- Recebimento: `LDESK.GERENC_VW_POSFIN_RESULTREC`
- Faturamento: `LDESK.GERENC_VW_POSFIN_RESULTFAT`
- Aggregation: `SUM(VALOR1)` filtered by `ANO_MES = 'YYYY-MM'` (note underscore).

| Metric | Sacred (docs/LEGALDESK.md §4) | DB result | Rows |
| --- | --- | --- | --- |
| recebimento_bruto 2026-05 | 415.927,84 | **415.927,84** | 98 (match) |
| faturamento_bruto 2026-05 | 719.988,05 | **719.988,05** | 97 (match) |
| recebimento 2026-01 | 279.821,07 | **279.821,07** | 89 |
| recebimento 2026-02 | 319.233,58 | **319.233,58** | 92 |

Verification query:

```sql
SELECT ROUND(SUM(VALOR1),2) total, COUNT(*) n
  FROM LDESK.GERENC_VW_POSFIN_RESULTREC WHERE ANO_MES = '2026-05';  -- 415927.84 / 98
SELECT ROUND(SUM(VALOR1),2) total, COUNT(*) n
  FROM LDESK.GERENC_VW_POSFIN_RESULTFAT WHERE ANO_MES = '2026-05';  -- 719988.05 / 97
```

Related views also present (same `GERENC_VW_POSFIN_*` family): `_FATURA`,
`_COBRANCA`, `_ADIANTAMENTO`, `_DESPINC`, `_PENDENCIA`, `_RESUMODESP`,
`_RESUMOPROF`, plus base table `LDESK.GERENC_POSICAOFINANCEIRA`.

### Bottom line

Every input to the monthly closing is present in the DB and, where a locked
figure exists, **reconciles exactly**:

- Headline recebimento/faturamento — exact (this section).
- 53 distinct invoices (May 2026) — matched (`LDESK.FAT_FATURA`).
- 286 rateio-por-profissional rows — matched (`LDESK.FAT_RATEIOFATURA_PROF`).
- Full institutional-expense ledger (88 accounts) — present
  (`FINANCE.LANCAMENTO` + `FINANCE.PLANOCONTAS`); Aluguel line exact.

Remaining work to automate is **modeling** (competence assignment, cost-center
map, DRE line taxonomy — see previous section), **not data access**. A
`FinanceDbSource` / `SisjuriDbSource` reading these objects can supply the entire
closing.

## Algorithmic proof: DB values -> workbook DRE lines (2026-07-01)

We reproduced individual workbook DRE lines algorithmically from raw
`FINANCE.LANCAMENTO` rows. This proves the closing is *computable* from the DB,
not merely that the data exists.

### The professional/cost-center dimensions

- `COD_ADVG` = the **individual professional** sigla (`AM`, `DC`, `BBX`, `IAC`, ...).
- `SIGLADEST` = the **cost-center group** (`ECT`=Contencioso, `EDE`=Econômico,
  `ESP`=Arbitragem/Compliance).
- `PCTCNUMEROCONTADEST` = plano-de-contas account (e.g. `030.010.0010`
  Distribuição, `030.010.0130` Pró-labore).
- `LANCHISTORICO` = free text that distinguishes sub-types (e.g.
  "Distribuição Fixa Líquida Mensal" vs "DL excedente ... Reserva").

### Associates — exact, direct formula

`workbook line = SUM(LANNVALOR)` grouped by `COD_ADVG` (+ `SIGLADEST`) on account
`030.010.0010`, for the month. Verified exact for January 2026:

| Prof (COD_ADVG) | Group | DB total | Workbook "Distribuição Mensal Fixa" |
| --- | --- | --- | --- |
| BBX | EDE | 7.019 | 7.019 ✓ |
| BMP | EDE | 7.003 | 7.003 ✓ |
| ASG | EDE | 3.579 | 3.579 ✓ |
| IAC | ECT | 14.039 | 14.039 ✓ |
| FSM | ESP | 11.799 | 11.799 ✓ |
| EMC | ESP | 4.699 | 4.699 ✓ |
| MV  | ESP | 23.379 | 23.379 ✓ |

(8 associate lines matched to the centavo.)

### Partners (sócios) — decomposition rule, also exact

Partner rows on `030.010.0010` carry **two sub-types** distinguished by
`LANCHISTORICO`, and the fixed part is **split evenly across the partner's
cost-centers**. Example — AM (Aurelio), January 2026:

| Account | Group | Value | Histórico | Maps to workbook |
| --- | --- | --- | --- | --- |
| 030.010.0010 | EDE | 23.379 | "Distribuição Fixa Líquida Mensal" | **Distribuição Fixa**: 23.379 / 2 groups = **11.689,5** per group ✓ (workbook r7 Contencioso = r38 Econômico = 11.689,5) |
| 030.010.0010 | ECT | 70.790,94 | "DL excedente ... Reserva" | profit/reserve line (NOT the fixed-distribution row — correctly excluded) |
| 030.010.0130 | — | 1.442,69 | "Pró labore mês atual" | Pró-labore line |

So the rule is: **filter by account + histórico sub-type, then split the fixed
distribution across the professional's cost-centers.** That reproduces the
workbook's separate Distribuição / Pró-labore / Excedente lines exactly.

> **Client-confirmed (2026-07-10):** a professional who works in **two areas is
> ALWAYS split 50/50** between them (custo de equipe + comissão). Fixed rule, never
> case-by-case. When the DB posts a partner's fixed distribution against multiple
> cost-centers, the even split IS this rule; a two-area lawyer with a single
> posting must still be halved across the two areas. See `PROJECT_STATUS.md` §0.

### What this proves

- Revenue KPIs: exact (`GERENC_VW_POSFIN_RESULT*`).
- Per-professional expense/distribution lines: reproduced exactly from
  `FINANCE.LANCAMENTO` (associates directly; partners via the account +
  histórico + cost-center-split rule).
- Therefore the **entire DRE is derivable from the DB**. The only "logic" needed
  is the taxonomy: (account, histórico sub-type) -> workbook line, plus the
  partner fixed-distribution split and competence-month assignment. This is
  exactly what a `FinanceDbSource` would encode.

### Caveat / next validation

- Formalize the (account, histórico) -> line map for all ~65 expense lines
  (some sub-types are identified by free-text histórico; confirm whether a
  structured column/flag exists to avoid text matching).
- Confirm competence-month rule per line (payment date vs a competence tag).

## BREAKTHROUGH — `GERENC_LANCAMENTORESUMO` is the gross competence expense ledger (2026-07-01)

Earlier sections reconstructed expenses from `FINANCE.LANCAMENTO` (the **cash**,
**net** double-entry ledger) and hit a gross-vs-net gap on personnel lines. That
gap is now resolved: the workbook's expense side is built from a **different,
cleaner object** — the pre-aggregated LegalDesk management ledger.

### The table

`LDESK.GERENC_LANCAMENTORESUMO` — **11,803 rows**, one row per
`(ANO_MES, ID_CONTA, ID_PROFISSIONAL, ...)`. Key columns:

- `ANO_MES` (`'YYYY-MM'`) — **competence month** (accrual, not cash date)
- `ID_CONTA` / `NOME_CONTA` — DRE account (e.g. `030.010.0010 Distribuição Mensal Fixa`)
- `ID_CONTA_PAI` / `NOME_CONTA_PAI` — parent account (`030.010.0000 Custos com Pessoal Técnico`)
- `TIPO_CONTA` — `D` (despesa/institucional), `C` (custo pessoal), `I` (investimento)
- `VALOR` — **GROSS** amount (NUMBER) — this is the workbook figure, not the net cash figure
- `ID_GRUPOJURIDICO` — cost-center/area (join `LDESK.CAD_GRUPOJURIDICO.NOME`)
- `ID_PROFISSIONAL` — professional (populated for most accounts; **NULL for the
  distribution account 030.010.0010**, where the total is stored at account level)
- `ORIGEM` — all `'F'` in this data

### Why this is the right source

- **Gross, not net.** `VALOR = 23379` for Distribuição Mensal Fixa exactly equals
  the workbook's gross figure (e.g. Daniel Costa Caselta = 23.379; Martim Della
  Valle = 23.379; João Gabriel = 9.379). No gross-up derivation needed for the
  account-level DRE lines. (`FINANCE.LANCAMENTO` stores the *net/liquida* payment
  and would require adding back withholding — avoid it for the DRE.)
- **Competence-dated.** `ANO_MES` is the accrual month, matching the workbook's
  competence basis directly — no `LANCHISTORICO` date-parsing needed.
- **Account tree baked in.** `ID_CONTA` + `ID_CONTA_PAI` + `TIPO_CONTA` give the
  DRE line taxonomy for free.

### Feb-2026 account roll-up (verified against the workbook)

`SELECT ID_CONTA, TIPO_CONTA, SUM(VALOR) FROM LDESK.GERENC_LANCAMENTORESUMO
WHERE ANO_MES='2026-02' GROUP BY ...` returns 30 accounts in three families:

| Family | TIPO | Feb-2026 total | Meaning |
| --- | --- | ---: | --- |
| `020.*` | D | 68.771,58 | institutional/admin (Aluguel 21.707,78, Contabilidade 7.804,05, Associações 7.109,73, ...) |
| `030.*` | C | 215.310,35 | personnel (Distribuição 172.129,96, Convênio 19.177,71, Pró-labore 17.312,28, INSS-Jur 3.890,40, Bolsa 2.800) |
| `040.*` | I | 30.913,70 | investments (Consultoria 14.705,80, Licenças 16.207,90) |
| **Total** | | **314.995,63** | vs workbook "Total saídas" 318.368,21 |

Individual account lines match the workbook's realized figures (Aluguel,
Condomínio, IPTU, Contabilidade, Consultoria, Licenças, etc.).

### The complete DRE assembles from TWO DB sources

| DRE side | DB source | Grain | Status |
| --- | --- | --- | --- |
| **Revenue** (recebimento / faturamento) | `LDESK.GERENC_VW_POSFIN_RESULTREC` / `_RESULTFAT` | `ANO_MES`, `SUM(VALOR1)` | **EXACT to the centavo** (415.927,84 / 719.988,05) |
| **Expenses** (institutional + personnel + investments) | `LDESK.GERENC_LANCAMENTORESUMO` | `ANO_MES` x `ID_CONTA` (gross, competence) | account-level **matches**; grand total within ~0,3% (gaps below) |

This is far simpler than the `FINANCE.LANCAMENTO` reconstruction: two
management-ledger objects, both keyed by `ANO_MES`, both already gross/competence.

### Two remaining, well-bounded gaps (Feb-2026 total diff ≈ 3.372,58)

1. **Pró-labore net vs gross.** The resumo stores pró-labore **net**
   (`030.010.0130` = 1.442,69 per professional, 12 people = 17.312,28); the
   workbook shows **gross 1.621** per person. Per-person diff 178,31 = INSS/IRRF
   withholding. Options: (a) add back withholding, (b) accept the resumo net if
   the closing definition allows, or (c) source gross from the folha. For the
   *account-level DRE* the resumo value is internally consistent; the 1.621 is a
   per-person supporting-detail figure.
2. **"Distribuição de Lucros extras" / "Bônus equipe" (Feb 101.705,84).** This
   line is **NOT** in `GERENC_LANCAMENTORESUMO` (no bônus/lucros account; value
   not found). In the workbook DRE it aligns with **"Reserva bônus" = 10% of
   Resultado Líquido** — i.e. a **formula-derived appropriation of profit**, not a
   booked cost. Treat as a computed line (result x reserve %), confirm the exact
   rule with finance, rather than sourcing it.

Also: the **per-partner distribution split** (who gets which slice of the
172.129,96) is not in the resumo (`ID_PROFISSIONAL` is NULL on `030.010.0010`).
The **account total is exact**; the per-partner detail, if the closing needs it,
comes from `FINANCE.LANCAMENTO` (net, by `COD_ADVG`) — but the DRE headline does
not require it.

### Honest bottom line (supersedes the optimistic "everything, zero gaps")

- **Revenue:** 100% in the DB, exact.
- **Expenses (institutional + personnel + investments), account-level, gross,
  competence, monthly:** in ONE table (`GERENC_LANCAMENTORESUMO`), account lines
  match the workbook.
- **Genuinely not sourced from these tables:** (a) the pró-labore net->gross
  add-back (small, = withholding), and (b) the profit-bonus/lucros-extras line
  (appears formula-derived: 10% reserve on net result). Both are **bounded and
  explainable**, not "missing data across dozens of manual lines."

So: automation is viable end-to-end. The closing = revenue views + expense resumo
+ two small rules (pró-labore gross-up if required; bonus-reserve formula). That
is a defensible, precise claim to take to the boss — materially stronger than the
prior "reconstruct from the cash ledger" plan.

## Lacunas resolvidas — respostas do financeiro MBC (2026-07-02)

As duas pendências abertas na seção anterior foram **fechadas** com as respostas do
financeiro da MBC e uma verificação no banco.

### Lacuna 1 (pró-labore bruto x líquido) — RESOLVIDA, e no banco

Financeiro: *"lançamos o bruto já para contemplar o valor com INSS... tem a
possibilidade de pegar em detalhes do lançamento, no campo valor base"*.

Confirmado no banco: o bruto está em **`FINANCE.CONTASPAGAR.CPGNVALORBASE`**.
Para os 12 pró-labores de fev/2026 (conta `030.010.0130`, histórico
"Pró labore mês atual"):

- `CPGNVALORBASE`     = **1.621,00**  ← BRUTO (valor da planilha)
- `CPGNVALORLIQUIDO`  = **1.442,69**  ← líquido (o que aparecia no resumo)

Ou seja, **não precisa de folha nem de parametrização manual**: o bruto já existe
no banco. Regra: para pró-labore (e provavelmente outras linhas de pessoal com
retenção), usar `CPGNVALORBASE` de `CONTASPAGAR`, não o `VALOR` líquido do resumo.
Chaves úteis em `CONTASPAGAR`: `COD_ADVG` (profissional), `PCTCNUMEROCONTA`
(conta), `CPGCHISTORICO` (histórico), `CPGDVECTO` (vencimento/competência),
`CPGDDATADESP` (data despesa), `CPGNVALORBRUTO`/`CPGNVALORBASE`/`CPGNVALORLIQUIDO`.
(Obs.: neste dado `CPGNVALORBRUTO` repetiu o líquido; o campo correto para o bruto
"de folha" é **`CPGNVALORBASE`**.)

### Lacuna 2 (bônus / distribuição de lucros extras) — RESOLVIDA como fórmula fixa

Financeiro: *"distribuição de lucros e reserva de bônus são coisas diferentes... a
reserva de bônus vamos demonstrar sendo 10% da margem líquida... a fórmula é fixa
para todos os meses"*.

Portanto:
- **Reserva de bônus = 10% da margem líquida** — **fórmula fixa, todos os meses**.
  É um **cálculo derivado do resultado**, não um lançamento a buscar no banco.
- **Distribuição de lucros** é **outra coisa** (não confundir com a reserva de
  bônus). Tratar separadamente; confirmar a origem/definição da distribuição de
  lucros quando essa linha precisar ser reproduzida.

### Situação final da cobertura

Com isto, o fechamento é **totalmente automatizável a partir do banco** + uma
fórmula fixa:

| DRE | Fonte | Observação |
| --- | --- | --- |
| Receita (recebimento/faturamento) | `LDESK.GERENC_VW_POSFIN_RESULTREC/FAT` | exato ao centavo |
| Despesas por conta (bruto, competência) | `LDESK.GERENC_LANCAMENTORESUMO` | linhas por conta batem |
| Pró-labore **bruto** (e retenções de pessoal) | `FINANCE.CONTASPAGAR.CPGNVALORBASE` | bruto 1.621 confirmado |
| Reserva de bônus | **fórmula fixa** = 10% da margem líquida | não é lançamento |
| Distribuição de lucros | a confirmar (é diferente da reserva de bônus) | fora da reserva de bônus |

Não há mais lacuna de **acesso a dados**. O que resta é modelagem: taxonomia
conta→linha do DRE, escolha de `CPGNVALORBASE` (bruto) vs resumo (líquido) nas
linhas de pessoal, e aplicar a fórmula fixa da reserva de bônus.

### Custo equipe por área — estado e o que falta extrair (2026-07-10)

A linha "Custo equipe" por área deve bater os alvos do workbook (ver tabela em
"Workbook targets"). Hoje o cálculo local usa `snapshot["custo_equipe_deriv"]`
(componentes por advogado) + `rateio_grupo` (CAD_RATEIO_GRUPO %) + `home_area`
(sigla→grupo), com fallback para `custo_area`. **Não temos um snapshot real de
maio localmente** — o único fixture SISJURI é `sisjuri_2026_02.json`, que só traz
o `custo_area` antigo (ruidoso). Drift medido nesse fixture vs alvo Fev 05.2026:

| área | `custo_area` (fixture) | alvo wb Fev | Δ |
|------|-----------------------:|------------:|----:|
| Contencioso | 49 941,93 | 76 342,35 | −26 400,42 |
| Econômico | 94 571,59 | 78 817,05 | +15 754,54 |
| Arbitragem | 70 796,83 | 61 794,34 | +9 002,49 |

Ou seja: o `custo_area` cru **não serve**; precisamos do bloco
`custo_equipe_deriv` (por advogado, contas `030.010.*`) + `rateio_grupo` +
`home_area` **extraídos do SISJURI para o mês-alvo** e então validar contra os
alvos. Regra de split confirmada: advogado em duas áreas **divide 50/50**
(`build_area_splits`/`derive_area_custo_equipe` já implementam isso). Enquanto o
extract correto não vier, a **regra dura mantém a célula em branco** (nunca um
número errado) — comportamento coberto por
`test_hard_rule_uses_workbook_targets_for_the_month`.

**AÇÃO (RDP):** rodar o extract `ops/sisjuri-agent/extract.sql` para o mês-alvo e
salvar o snapshot; conferir por área contra a tabela de alvos. Só então as células
saem do branco.

### Custo equipe por área — RESOLVIDO ao centavo com dados reais de maio (2026-07-13)

Validado o snapshot real de 2026-05 (Supabase) contra os alvos do workbook. As três
áreas batem **exatamente** com duas correções na derivação (`dre.py`):

1. **Vale (`custo_equipe_area`, postings `500.010.<SIGLA>`) NÃO entra no custo de
   equipe por área.** Prova: Vale do JVO = 1.236,90 = resíduo exato do Contencioso.
   Vale pertence à transitória/Salários-ADM (`200.010.0010`), não ao custo direto.
   Bug atual: `all_rows = deriv_rows + custo_equipe_area` em `RealizadoInputs.from_snapshot`.
2. **Convênio médico (`030.010.0110`) usa a "Parte MBC" (de `convenio_memo.parsed_valor`),
   não o valor bruto lançado.** Prova: substituir o `0110` pela Parte MBC zera o
   resíduo de +1.459,69 do Econômico. O extract já emite `convenio_memo`
   (sigla, parsed_valor, raw_memo) exatamente para isso; o assembler ignora hoje.

Resultado (maio): Contencioso 74.141,21 · Econômico 79.436,24 · Arbitragem 54.383,94
(todos = alvo). Total custo equipe 207.961,39; + comissão 2.128,07 = Custos Diretos
210.089,46 (alvo exato).

Componentes de `custo_equipe_deriv` por conta (maio): `030.010.0010` (pró-labore/
distribuição) 166.323,80 · `030.010.0110` (convênio médico, usar Parte MBC) 20.266,29
· `030.010.0130` 17.831,00 · `030.010.0140` 5.000,00.

### Comissão — `comissao_deriv` voltou `null` em maio (2026-07-13) — INVESTIGAR

O bloco `comissao_deriv` do extract retornou `null` para maio. A comissão implícita
de maio é **2.128,07** (Custos Diretos 210.089,46 − custo equipe 207.961,39). Provável
filtro de data/JOIN zerando o SELECT (externa `020.110.0010` por grupo + interna
`030.010.0120` por `LANCPROFDEST`). Ver `probe_comissao.sql`.
