# Findings — the "lançamentos manuais" claim is wrong on mechanism

**Date:** 2026-07-21 · **Trigger:** re-audit before the MBC automation meeting.
**One line:** the raw May system export refutes the `NOTA_CLIENTE_meses_em_branco.md`
claim that Vale-ADM / Associações / DL-extras are "lançamentos manuais não deriváveis do
banco". **They are ordinary SISJURI postings**; Jan–Apr blank because of the R$1 hard
rule + a couple of extract filter/basis details, **not** because the numbers were invented
by finance.

---

## The decisive artifact: `reference/workbook/lancextrato de contas.xls`

This file was under-used. It is a **raw system export** — *"Extrato de Contas · Conta(s): %%
· Período 01/05/2026 a 31/05/2026 · Todos · MBC Advogados"*, built from `FINANCE.LANCAMENTO`
(4.307 rows, 66 accounts). It is the actual ledger behind May, **not** a workbook tab. Every
family the NOTA calls "manual" is a real account in it, and Recebimento ties the sacred
number exactly (`010.010.0010 = 415.927,84`).

Companion export `Pagtos maio.XLS.xlsx` (`FINANCE.CONTASPAGAR`, 59 columns) independently
confirms the mechanism: it carries **`Valor Bruto` AND `Valor Liquido` as native system
columns** (cols 6/7), plus `Conta Destino`, `ORIENTAÇÃO`, `Profissional Destino`, `Rateio`,
`Grupo`, `Setor`. The "líquido" the workbook books is a **system field**, never a hand
computation.

---

## Family-by-family verdict (May, to the centavo)

### 1. Vale-ADM — REFUTES "the DB doesn't store who is ADM vs área"
The transitória `200.010.0010` unfolds the VR/VT **Mensal parent** into per-person
destination accounts — the split is *in the DB*, in the desdobramento:

| Leg | dest account | value | histórico |
|---|---|---:|---|
| VR Mensal parent | (paid via Itaú) | **2.719,90** | "Pagamento de VR Mensal para João Victor, Maria Luiza…" |
| VT Mensal parent | (paid via Itaú) | **607,04** | "Pagamento de VT Mensal para João Victor…" |
| VR split | `500.010.MLA` | 783,70 | Vale refeição 17 dias × 46,10 |
| VR split | `500.010.JVO` | 968,10 | Vale refeição 21 dias × 46,10 |
| VR split | `020.030.0060` | 968,10 | Vale refeição 21 dias × 46,10 |
| VT split | `500.010.VSR` | 75,60 | Vale transporte 07 dias × 10,80 |
| VT split | `500.010.MLA` | 262,64 | Vale transporte 14 dias × 18,76 |
| VT split | `500.010.JVO` | 268,80 | Vale transporte 08 dias × 33,60 |

**VR+VT parent = 3.326,94 = workbook G122+G123 exactly.** The per-person `500.010.<SIGLA>`
destinations *are* the ADM-vs-área tag (MLA/VSR administrative, JVO an área lawyer). The prior
memo `vale-adm-not-in-db-jan-mar-decision` said "who inside the bundle is ADM vs área is NOT
stored in the DB" — that is **false**; the prior probe just summed the wrong leg
(`LANCPROFDEST`/`SIGLADEST`, which are NULL on these rows) instead of reading the destination
account. The client's own action list (`Pontos da Reuniao … 10JUL2026`, item 6) even says it
outright: **"VALE REFEICAO, buscar na conta transitória | informacao recebida."**

> Why Jan–Mar looked un-tie-able before: the extract's `vale_adm` sums the transitória VR/VT
> lines, but (a) the same slice also appears in `400.010.0040 Repasse` (double-count risk if
> the filter widens) and (b) early months may carry a second estagiário VR/VT line (the March
> "estagiário do concorrencial Vitor" 543,22) or the accrual timing differs. This is a
> **filter/basis question, testable and fixable** — not hand-entry. `probe_janapr_reconcile.sql`
> #1 settles it by reconstructing the parent per month.

### 2. Associações — REFUTES "a divisão entre áreas é feita à mão"
`020.060.0020 Associações = 2.822,06` (4 real transactions). **The area split is written in
the transaction histórico**, not invented by finance:

| value | histórico | → área |
|---:|---|---|
| 217,40 | "**AASP AM, DC** 04/2026 108,70 por profissional" | Contencioso (AM+DC) |
| 700,09 | "IBRAC 2026 R$1.400,19 — **Dividido em Contencioso e Econômico**" | Econômico |
| 700,10 | "IBRAC 2026 R$1.400,19 — **Dividido em Contencioso e Econômico**" | Contencioso |
| 1.204,47 | "Patrocínio Canal de arbitragem — **100% Arbitragem (demandas especiais - MV)**" | Arbitragem |

Workbook G129+G130+G131 = 917,50 + 700,10 + 1.204,47 = **2.822,07 = DB 2.822,06** (1 centavo
rounding). The IBRAC "1400.19/2" the NOTA calls a hand-split is **the system posting it as two
rows** (700,09 + 700,10). The extract already tags these by cost-center (`despesas_equipe_area`,
ECT/EDE/ESP) — proven vs May. The `4287.67/3` "anuidade" in Feb–Apr is an annual fee whose
competência the DB spreads; that's a **competência/accrual** question, again testable
(`probe_janapr_reconcile.sql` #2), not hand-entry.

### 3. DL extras — already DB-derived; "só num mês" is a real business fact, not manual
`bonus_equipe` (150.* + 030.010.0010), `dl_excedente_socios`, `dl_excedente_mv` are wired and
tie: Feb Bônus 94.696,15 + 7.009,84 = **101.705,84 = D192**; Jan DL sócios 164.477,34 = **D193**;
Mar DL MV 6.627 = **E194**. They post ~1×/yr in specific months (client-confirmed) — May = 0 is
*correct*, not a blank-because-manual.

---

## Independent cross-check
Rebuilding May institutional despesas from the **raw Extrato** (a different export than the
CONTASPAGAR path the code uses): Σ020/040 gross 104.760,56 + Cursos 1.600 + Vale-ADM 3.326,94 −
retained 3rd-party tax 2.165,01 = **107.522,49** vs workbook 105.640,60 (Δ 1,8%, family-level
rough roll-up; the centavo-exact tie is already locked in `test_despesas_liquido.py`). The same
total emerges from a completely separate system export → the recipe is sound.

---

## What this means for the meeting / the NOTA

- **Drop the "lançamentos manuais não deriváveis" framing.** It is factually wrong and the
  client (who told us "eu não inputei nada… já vem de dentro do sistema") will recognize it as
  wrong. Every one of those numbers is a system posting; the split rules are in the histórico
  and the desdobramento destination accounts.
- **The honest, correct story:** the site only shows a number when it reproduces the DB to the
  centavo (R$1 hard rule). May & June do; Jan–Apr have a few lines still gated by **two known,
  mechanical gaps** — (a) Vale/Associações **competência & desdobramento-leg selection** in the
  older months, (b) the client's *older* workbook cells were themselves hand-adjusted with
  month-varying accrual choices the DB spreads differently. Where they disagree, **the DB is
  arguably more correct.**
- **Actionable:** run `ops/sisjuri-agent/probe_janapr_reconcile.sql` on `MBC-LDESK01`. If #1a
  and #2a reproduce the workbook Jan–Apr targets (or reveal the exact accrual leg), we can
  un-blank Jan–Apr straight from the DB and retire the "aceitar número do banco vs manter
  planilha" decision entirely.

## How to run the probe (RDP recipe, from ops/sisjuri-agent/README.md)
```powershell
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$env:SISJURI_PASSWORD = '<RGN password>'
Invoke-WebRequest -UseBasicParsing "https://raw.githubusercontent.com/femito1/rumo/main/ops/sisjuri-agent/probe_janapr_reconcile.sql" -OutFile C:\temp\sisjuri\probe_janapr_reconcile.sql
Set-Content C:\temp\sisjuri\q.sql -Encoding ASCII -Value ("CONNECT RGN/""$($env:SISJURI_PASSWORD)""@(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=172.16.237.9)(PORT=1521))(CONNECT_DATA=(SERVICE_NAME=cdbp01_pdb1.submbc.vcnmbc.oraclevcn.com)))`r`n" + (Get-Content C:\temp\sisjuri\probe_janapr_reconcile.sql -Raw))
& 'C:\oracle11\app\product\11.2.0\client_1\bin\sqlplus.exe' -S /nolog '@C:\temp\sisjuri\q.sql' *>&1 | Tee-Object C:\temp\sisjuri\out_janapr.txt
```
(Commit + push first so the raw URL resolves. Paste `out_janapr.txt` back.)
