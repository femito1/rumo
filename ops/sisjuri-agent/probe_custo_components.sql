-- Probe: rebuild each lawyer's FULL Custo equipe components from SISJURI so we can
-- reconcile per-area Custo equipe to the ledger's per-lawyer figures to the centavo.
-- The ledger per-lawyer "Distribuição Mensal Fixa" is neither raw net (LANCAMENTO)
-- nor raw gross (CONTASPAGAR) for several lawyers (JGS/RB/DC), so we must see the
-- component accounts (distribuição + reajuste + pró-labore + convênio + bolsa …)
-- per lawyer, both net and gross. Read-only. Feb 2026.
SET DEFINE OFF
SET PAGESIZE 1000
SET LINESIZE 320
SET FEEDBACK ON
SET TRIMSPOOL ON
COL sigla FORMAT A6
COL conta FORMAT A16
COL nome_conta FORMAT A34
WHENEVER SQLERROR CONTINUE

PROMPT === A. NET per lawyer x account (all 030.010.* team-cost accounts), LANCAMENTO, Feb ===
SELECT l.COD_ADVG AS sigla, l.SIGLADEST AS cc, l.PCTCNUMEROCONTADEST AS conta,
       ROUND(SUM(l.LANNVALOR),2) AS net_valor, COUNT(*) n
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST LIKE '030.010.%'
   AND l.LANDDATA >= DATE '2026-02-01' AND l.LANDDATA < DATE '2026-03-01'
 GROUP BY l.COD_ADVG, l.SIGLADEST, l.PCTCNUMEROCONTADEST
 ORDER BY l.COD_ADVG, l.PCTCNUMEROCONTADEST;

PROMPT === B. GROSS per lawyer x account, CONTASPAGAR, Feb ===
SELECT cp.COD_ADVG AS sigla, cp.PCTCNUMEROCONTA AS conta,
       ROUND(SUM(cp.CPGNVALORBASE),2)   AS base,
       ROUND(SUM(cp.CPGNVALORBRUTO),2)  AS bruto,
       ROUND(SUM(cp.CPGNVALORLIQUIDO),2) AS liquido, COUNT(*) n
  FROM FINANCE.CONTASPAGAR cp
 WHERE cp.PCTCNUMEROCONTA LIKE '030.010.%'
   AND cp.CPGDVECTO >= DATE '2026-02-01' AND cp.CPGDVECTO < DATE '2026-03-01'
 GROUP BY cp.COD_ADVG, cp.PCTCNUMEROCONTA
 ORDER BY cp.COD_ADVG, cp.PCTCNUMEROCONTA;

PROMPT === C. Account catalogue for 030.010.* (names, so we can label components) ===
SELECT PCTCNUMEROCONTA AS conta, SUBSTR(PCTCNOME,1,40) AS nome
  FROM FINANCE.PLANOCONTAS
 WHERE PCTCNUMEROCONTA LIKE '030.010.%'
 ORDER BY PCTCNUMEROCONTA;

PROMPT === D. Grand totals to anchor (net vs gross) for account 030.010.0010 only ===
SELECT 'NET  030.010.0010' tag, ROUND(SUM(l.LANNVALOR),2) v
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST='030.010.0010'
   AND l.LANDDATA >= DATE '2026-02-01' AND l.LANDDATA < DATE '2026-03-01'
UNION ALL
SELECT 'GROSS 030.010.0010 (base)', ROUND(SUM(cp.CPGNVALORBASE),2)
  FROM FINANCE.CONTASPAGAR cp
 WHERE cp.PCTCNUMEROCONTA='030.010.0010'
   AND cp.CPGDVECTO >= DATE '2026-02-01' AND cp.CPGDVECTO < DATE '2026-03-01';

EXIT
