-- probe_inst_csv.sql
-- Emit institutional _DET (TIPO S+I) as pipe-delimited rows keyed on the STABLE
-- numeric account codes (CONTA1/2/3 + LANNCODIG), plus titles for readability and
-- SETOR + ORCAMENTO. One "DATA|" line per (month, account, setor); no column
-- wrapping so a machine can parse it losslessly. Accents in TITULOx are a console
-- artifact only; we key on the numeric CONTAx, never on the accented text.
SET DEFINE OFF
SET PAGESIZE 0
SET LINESIZE 32767
SET LONG 100000
SET TRIMOUT ON
SET FEEDBACK OFF
SET HEADING OFF
SET VERIFY OFF
WHENEVER SQLERROR CONTINUE

PROMPT #COLS ano_mes|tipo|conta1|titulo1|conta2|titulo2|conta3|titulo3|setor|orcamento|valor|n
SELECT 'DATA|'||ANO_MES
       ||'|'||TIPO
       ||'|'||CONTA1||'|'||TITULO1
       ||'|'||CONTA2||'|'||TITULO2
       ||'|'||CONTA3||'|'||TITULO3
       ||'|'||NVL(SETOR,'')
       ||'|'||NVL(TO_CHAR(SUM(ORCAMENTO)),'')
       ||'|'||TO_CHAR(ROUND(SUM(VALOR),2))
       ||'|'||COUNT(*)
  FROM FINANCE.VW_RESULTADO_MENSAL_DET
 WHERE ANO_MES BETWEEN '2026-01' AND '2026-05'
   AND TIPO IN ('S','I')
 GROUP BY ANO_MES, TIPO, CONTA1, TITULO1, CONTA2, TITULO2, CONTA3, TITULO3, NVL(SETOR,'')
 ORDER BY ANO_MES, TIPO, CONTA2, CONTA3, NVL(SETOR,'');

PROMPT #END
EXIT
