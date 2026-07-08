-- probe_vale_500.sql
-- BREAKTHROUGH: the ADM Vale lives in the 500.010.<SIGLA> personal-debit namespace.
-- SISJURI_QUERIES.md already recorded: 500.010.MLA "Vale refeição / Vale transporte"
-- = 1.351,88 (Feb) = EXACTLY the workbook Feb Vale-ADM total (Ref 1014.20 + Transp
-- 337.68). It was excluded from per-area Custo Equipe as an "ex-lawyer"; but the
-- workbook routes it (and any other non-area/ADM sigla Vale) into Salários
-- Administração. Confirm this reconstructs the ADM Vale for every month.
--
-- Workbook Vale-ADM totals (Ref+Transp): 1127.96/1351.88/3983.22/3421.36/3326.94
SET DEFINE OFF
SET PAGESIZE 0
SET LINESIZE 32767
SET TRIMOUT ON
SET FEEDBACK OFF
SET HEADING OFF
WHENEVER SQLERROR CONTINUE

PROMPT #A ALL 500.010.* postings Jan..Mai (conta/sigla, historico, month, valor)
SELECT 'A|'||TO_CHAR(cp.CPGDVECTO,'YYYY-MM')
       ||'|'||NVL(cp.PCTCNUMEROCONTA,'?')
       ||'|'||SUBSTR(REPLACE(NVL(cp.CPGCHISTORICO,' '),'|','/'),1,44)
       ||'|'||TO_CHAR(ROUND(SUM(cp.CPGNVALORBASE),2))
  FROM FINANCE.CONTASPAGAR cp
 WHERE cp.CPGDVECTO >= DATE '2026-01-01' AND cp.CPGDVECTO < DATE '2026-06-01'
   AND cp.PCTCNUMEROCONTA LIKE '500.010.%'
 GROUP BY TO_CHAR(cp.CPGDVECTO,'YYYY-MM'), cp.PCTCNUMEROCONTA,
          SUBSTR(REPLACE(NVL(cp.CPGCHISTORICO,' '),'|','/'),1,44)
 ORDER BY 1, 2;

PROMPT #B 500.010.* VALE only (historico VALE/REFEI/TRANSP), per sigla per month
SELECT 'B|'||TO_CHAR(cp.CPGDVECTO,'YYYY-MM')
       ||'|'||NVL(cp.PCTCNUMEROCONTA,'?')
       ||'|'||TO_CHAR(ROUND(SUM(cp.CPGNVALORBASE),2))
  FROM FINANCE.CONTASPAGAR cp
 WHERE cp.CPGDVECTO >= DATE '2026-01-01' AND cp.CPGDVECTO < DATE '2026-06-01'
   AND cp.PCTCNUMEROCONTA LIKE '500.010.%'
   AND ( UPPER(cp.CPGCHISTORICO) LIKE '%VALE%'
      OR UPPER(cp.CPGCHISTORICO) LIKE '%REFEI%'
      OR UPPER(cp.CPGCHISTORICO) LIKE '%TRANSP%' )
 GROUP BY TO_CHAR(cp.CPGDVECTO,'YYYY-MM'), cp.PCTCNUMEROCONTA
 ORDER BY 1, 2;

PROMPT #C Monthly TOTAL of 500.010.* Vale (all siglas) vs wb Vale-ADM target
SELECT 'C|'||TO_CHAR(cp.CPGDVECTO,'YYYY-MM')
       ||'|allsiglas='||TO_CHAR(ROUND(SUM(cp.CPGNVALORBASE),2))
  FROM FINANCE.CONTASPAGAR cp
 WHERE cp.CPGDVECTO >= DATE '2026-01-01' AND cp.CPGDVECTO < DATE '2026-06-01'
   AND cp.PCTCNUMEROCONTA LIKE '500.010.%'
   AND ( UPPER(cp.CPGCHISTORICO) LIKE '%VALE%'
      OR UPPER(cp.CPGCHISTORICO) LIKE '%REFEI%'
      OR UPPER(cp.CPGCHISTORICO) LIKE '%TRANSP%' )
 GROUP BY TO_CHAR(cp.CPGDVECTO,'YYYY-MM')
 ORDER BY 1;

PROMPT #END
EXIT
