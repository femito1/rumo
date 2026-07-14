-- probe_faturas_moeda_validate.sql
-- Validate the exact SELECT that the new extract.sql 'faturas_moeda' block runs,
-- BEFORE trusting it in the daily extract (a bad column name would break the whole
-- extract via WHENEVER SQLERROR EXIT FAILURE). Confirms columns parse + sane data.
-- Read-only. May 2026.
SET DEFINE OFF
SET PAGESIZE 0
SET LINESIZE 32767
SET LONG 100000
SET TRIMOUT ON
SET FEEDBACK OFF
SET HEADING OFF
WHENEVER SQLERROR CONTINUE

PROMPT #A Row count + honorarios_nac sum for May emission (Nacional=R + Moedas foreign)
SELECT 'A|n='||COUNT(*)
       ||'|hon_nac_sum='||TO_CHAR(ROUND(SUM(v.VALOR_HONORARIOS_NAC),2))
       ||'|recebido_nac_sum='||TO_CHAR(ROUND(SUM(v.CR_HON_NAC),2))
  FROM LDESK.DB_VW_FATURASEMI_REC v
 WHERE v.DATA >= DATE '2026-05-01' AND v.DATA < DATE '2026-06-01';

PROMPT #B Split by moeda sigla (how many BRL vs foreign) May
SELECT 'B|'||NVL(v.SIGLA_MOEDA,'?')||'|n='||COUNT(*)||'|hon_nac='||TO_CHAR(ROUND(SUM(v.VALOR_HONORARIOS_NAC),2))
  FROM LDESK.DB_VW_FATURASEMI_REC v
 WHERE v.DATA >= DATE '2026-05-01' AND v.DATA < DATE '2026-06-01'
 GROUP BY v.SIGLA_MOEDA ORDER BY 1;

PROMPT #C First 6 rows end-to-end (the exact projected columns) May
SELECT 'C|'||v.NUMERO||'|'||SUBSTR(NVL(v.CLIENTE,'?'),1,22)||'|'||NVL(v.SIGLA_MOEDA,'?')
       ||'|emis='||TO_CHAR(v.DATA,'YYYY-MM-DD')
       ||'|venc='||TO_CHAR(v.DATA_VENCIMENTO,'YYYY-MM-DD')
       ||'|receb='||TO_CHAR(v.DATA_RECEBIMENTO,'YYYY-MM-DD')
       ||'|hon='||TO_CHAR(ROUND(v.VALOR_HONORARIOS,2))
       ||'|hon_nac='||TO_CHAR(ROUND(v.VALOR_HONORARIOS_NAC,2))
       ||'|cr_hon='||TO_CHAR(ROUND(v.CR_HON,2))
  FROM LDESK.DB_VW_FATURASEMI_REC v
 WHERE v.DATA >= DATE '2026-05-01' AND v.DATA < DATE '2026-06-01'
   AND ROWNUM <= 6 ORDER BY v.NUMERO;

PROMPT #END
EXIT
