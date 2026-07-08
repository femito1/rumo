-- Probe: Comissão (Participação + Repasse) — retire Base_Resultado ledger.
-- Workbook Feb 2026 ground truth (test_ledger_import.py): Comissão is ~always
--   zero, with two known exceptions: Feb Econômico 1.500,00; May Econômico
--   2.128,06. Line 3454 of the past chat showed EHF 030.010.0120 May 2.128,06 —
--   so 0120 (Participação I) is almost certainly the source. Confirm here and
--   catalogue 0080 (Participação E) content too, Jan..Mai. Also scan every
--   nearby 030.010.* account with non-trivial values that could be missing
--   Comissão sources.
-- Ground truth per area, per month (workbook cached):
--   Contencioso: 0 every month
--   Econômico:   Jan 0 · Feb 1500 · Mar 0 · Apr 0 · Mai 2128,06
--   Arbitragem:  0 every month
SET DEFINE OFF
SET PAGESIZE 2000
SET LINESIZE 340
SET FEEDBACK ON
COL prof FORMAT A6
COL conta FORMAT A16
COL mes FORMAT A7
COL hist FORMAT A60
WHENEVER SQLERROR CONTINUE

PROMPT === 1. 030.010.0080 (Participação E) monthly totals + per-lawyer, Jan..Mai ===
SELECT TO_CHAR(l.LANDDATA,'YYYY-MM') mes, l.LANCPROFDEST prof,
       ROUND(SUM(l.LANNVALOR),2) net, COUNT(*) n,
       SUBSTR(MAX(l.LANCHISTORICO),1,60) hist
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST='030.010.0080'
   AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-06-01'
 GROUP BY TO_CHAR(l.LANDDATA,'YYYY-MM'), l.LANCPROFDEST
 ORDER BY mes, prof;

PROMPT === 2. 030.010.0120 (Participação I) monthly totals + per-lawyer, Jan..Mai ===
SELECT TO_CHAR(l.LANDDATA,'YYYY-MM') mes, l.LANCPROFDEST prof,
       ROUND(SUM(l.LANNVALOR),2) net, COUNT(*) n,
       SUBSTR(MAX(l.LANCHISTORICO),1,60) hist
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST='030.010.0120'
   AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-06-01'
 GROUP BY TO_CHAR(l.LANDDATA,'YYYY-MM'), l.LANCPROFDEST
 ORDER BY mes, prof;

PROMPT === 3. Same via CONTASPAGAR (gross basis) — is 2128.06 also here? ===
SELECT TO_CHAR(cp.CPGDVECTO,'YYYY-MM') mes, cp.PCTCNUMEROCONTA conta,
       cp.COD_ADVG prof, ROUND(SUM(cp.CPGNVALORBASE),2) base,
       COUNT(*) n, SUBSTR(MAX(cp.CPGCHISTORICO),1,60) hist
  FROM FINANCE.CONTASPAGAR cp
 WHERE cp.PCTCNUMEROCONTA IN ('030.010.0080','030.010.0120')
   AND cp.CPGDVECTO >= DATE '2026-01-01' AND cp.CPGDVECTO < DATE '2026-06-01'
 GROUP BY TO_CHAR(cp.CPGDVECTO,'YYYY-MM'), cp.PCTCNUMEROCONTA, cp.COD_ADVG
 ORDER BY mes, conta, prof;

PROMPT === 4. Scan ALL 030.010.* with nonzero magnitude Jan..Mai — is there another Comissão-like account? ===
-- Any account other than 0010/0110/0130/0140/0050 (already claimed by Custo equipe)
-- with material amounts. Filters "known" accounts out.
SELECT r.ID_CONTA, MAX(r.NOME_CONTA) nome, r.ANO_MES,
       ROUND(SUM(r.VALOR),2) total, COUNT(*) n
  FROM LDESK.GERENC_LANCAMENTORESUMO r
 WHERE r.ID_CONTA LIKE '030.010.%'
   AND r.ID_CONTA NOT IN ('030.010.0010','030.010.0050','030.010.0110',
                           '030.010.0130','030.010.0140')
   AND r.ANO_MES BETWEEN '2026-01' AND '2026-05'
 GROUP BY r.ID_CONTA, r.ANO_MES
 HAVING ABS(SUM(r.VALOR)) > 0.01
 ORDER BY r.ANO_MES, r.ID_CONTA;

PROMPT === 5. Same scan across LANCAMENTO destination (in case the resumo hides some) ===
SELECT l.PCTCNUMEROCONTADEST conta, TO_CHAR(l.LANDDATA,'YYYY-MM') mes,
       ROUND(SUM(l.LANNVALOR),2) net, COUNT(*) n
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST LIKE '030.010.%'
   AND l.PCTCNUMEROCONTADEST NOT IN ('030.010.0010','030.010.0050','030.010.0110',
                                       '030.010.0130','030.010.0140')
   AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-06-01'
 GROUP BY l.PCTCNUMEROCONTADEST, TO_CHAR(l.LANDDATA,'YYYY-MM')
 HAVING ABS(SUM(l.LANNVALOR)) > 0.01
 ORDER BY mes, conta;

PROMPT === 6. What was 030.010.0080 Feb 1500,00? By caso/cliente/histórico ===
-- Feb Econ Comissão = 1500; if 0080 has 1500 Feb somewhere, this shows who/why.
SELECT l.LANCPROFDEST prof, l.SIGLADEST sigla, l.PCTCNUMEROCONTADEST conta,
       ROUND(l.LANNVALOR,2) net, TO_CHAR(l.LANDDATA,'YYYY-MM-DD') dt,
       SUBSTR(l.LANCHISTORICO,1,100) hist
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST IN ('030.010.0080','030.010.0120')
   AND l.LANDDATA >= DATE '2026-02-01' AND l.LANDDATA < DATE '2026-03-01'
 ORDER BY l.LANDDATA;

EXIT
