-- probe_vale_folha.sql
-- The accounting ledger has NO ADM Vale account (020.050.* has none; a name search
-- for 'VALE' finds only tiny area-tagged 020.080.*). Yet the workbook Salários
-- Administração carries Vale Refeição-ADM + Vale Transporte every month, and that
-- Vale is EXACTLY the Salários-Adm residual (Feb 1.351,88 / May 3.326,94).
-- Hypothesis: the Vale postings live in FINANCE.CONTASPAGAR with 'Vale'/'Refeição'/
-- 'Transporte' in CPGCHISTORICO, under a 020.050.* or 030.* account, filtered out of
-- the S/I summarised view. Find them.
--
-- Targets to hit (Vale Ref-ADM / Vale Transporte, Jan..Mai):
--   829.80/1014.20/2766.00/2766.00/2719.90  and  298.16/337.68/1217.22/655.36/607.04
SET DEFINE OFF
SET PAGESIZE 0
SET LINESIZE 32767
SET TRIMOUT ON
SET FEEDBACK OFF
SET HEADING OFF
WHENEVER SQLERROR CONTINUE

PROMPT #A CONTASPAGAR postings whose historico mentions VALE/REFEI/TRANSPORTE, Jan..Mai
PROMPT #A cols: ano_mes|conta|historico(<=40)|n|bruto|base|liquido
SELECT 'A|'||TO_CHAR(cp.CPGDVECTO,'YYYY-MM')
       ||'|'||NVL(cp.PCTCNUMEROCONTA,'?')
       ||'|'||SUBSTR(REPLACE(NVL(cp.CPGCHISTORICO,' '),'|','/'),1,40)
       ||'|'||COUNT(*)
       ||'|'||TO_CHAR(ROUND(SUM(cp.CPGNVALORBRUTO),2))
       ||'|'||TO_CHAR(ROUND(SUM(cp.CPGNVALORBASE),2))
       ||'|'||TO_CHAR(ROUND(SUM(cp.CPGNVALORLIQUIDO),2))
  FROM FINANCE.CONTASPAGAR cp
 WHERE cp.CPGDVECTO >= DATE '2026-01-01' AND cp.CPGDVECTO < DATE '2026-06-01'
   AND ( UPPER(cp.CPGCHISTORICO) LIKE '%VALE%'
      OR UPPER(cp.CPGCHISTORICO) LIKE '%REFEI%'
      OR UPPER(cp.CPGCHISTORICO) LIKE '%TRANSPORTE%' )
 GROUP BY TO_CHAR(cp.CPGDVECTO,'YYYY-MM'), cp.PCTCNUMEROCONTA,
          SUBSTR(REPLACE(NVL(cp.CPGCHISTORICO,' '),'|','/'),1,40)
 ORDER BY 1;

PROMPT #B Same but grouped only by account+month (compact totals to match wb Vale)
SELECT 'B|'||TO_CHAR(cp.CPGDVECTO,'YYYY-MM')||'|'||NVL(cp.PCTCNUMEROCONTA,'?')
       ||'|'||TO_CHAR(ROUND(SUM(cp.CPGNVALORLIQUIDO),2))
       ||'|liq  base='||TO_CHAR(ROUND(SUM(cp.CPGNVALORBASE),2))
  FROM FINANCE.CONTASPAGAR cp
 WHERE cp.CPGDVECTO >= DATE '2026-01-01' AND cp.CPGDVECTO < DATE '2026-06-01'
   AND ( UPPER(cp.CPGCHISTORICO) LIKE '%VALE%'
      OR UPPER(cp.CPGCHISTORICO) LIKE '%REFEI%'
      OR UPPER(cp.CPGCHISTORICO) LIKE '%TRANSPORTE%' )
 GROUP BY TO_CHAR(cp.CPGDVECTO,'YYYY-MM'), cp.PCTCNUMEROCONTA
 ORDER BY 1;

PROMPT #END
EXIT
