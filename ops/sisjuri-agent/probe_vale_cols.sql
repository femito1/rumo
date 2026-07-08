-- probe_vale_cols.sql
-- Do NOT guess LANCAMENTO columns. First dump the real column list, then pull the
-- Vale rows using only columns we can confirm here. probe_vale_hunt.sql referenced
-- SIGLADEST / ID_GRUPOJURIDICODEST but the live table rejected ID_GRUPOJURIDICODEST
-- (ORA-00904) — so we inventory first.
SET DEFINE OFF
SET PAGESIZE 0
SET LINESIZE 32767
SET TRIMOUT ON
SET FEEDBACK OFF
SET HEADING OFF
WHENEVER SQLERROR CONTINUE

PROMPT #COLS all columns of FINANCE.LANCAMENTO (name|type)
SELECT 'COL|'||column_name||'|'||data_type
  FROM ALL_TAB_COLUMNS
 WHERE table_name = 'LANCAMENTO' AND owner = 'FINANCE'
 ORDER BY column_id;

PROMPT #COLSDEST columns of LANCAMENTO whose name contains GRUPO or SIGLA or SETOR or DEST
SELECT 'DST|'||column_name||'|'||data_type
  FROM ALL_TAB_COLUMNS
 WHERE table_name = 'LANCAMENTO' AND owner = 'FINANCE'
   AND ( column_name LIKE '%GRUPO%' OR column_name LIKE '%SIGLA%'
      OR column_name LIKE '%SETOR%' OR column_name LIKE '%DEST%' )
 ORDER BY column_name;

PROMPT #A raw Vale rows 030.010.0100/0220 Jan..Mai (safe cols only: conta, historico, valor)
SELECT 'A|'||TO_CHAR(l.LANDDATA,'YYYY-MM')
       ||'|'||l.PCTCNUMEROCONTADEST
       ||'|'||SUBSTR(REPLACE(NVL(l.LANCHISTORICO,' '),'|','/'),1,50)
       ||'|'||TO_CHAR(ROUND(l.LANNVALOR,2))
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST IN ('030.010.0100','030.010.0220')
   AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-06-01'
 ORDER BY TO_CHAR(l.LANDDATA,'YYYY-MM'), l.PCTCNUMEROCONTADEST;

PROMPT #C monthly total per Vale account (no grouping cols needed)
SELECT 'C|'||TO_CHAR(l.LANDDATA,'YYYY-MM')||'|'||l.PCTCNUMEROCONTADEST
       ||'|'||TO_CHAR(ROUND(SUM(l.LANNVALOR),2))||'|n='||COUNT(*)
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST IN ('030.010.0100','030.010.0220')
   AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-06-01'
 GROUP BY TO_CHAR(l.LANDDATA,'YYYY-MM'), l.PCTCNUMEROCONTADEST
 ORDER BY TO_CHAR(l.LANDDATA,'YYYY-MM'), l.PCTCNUMEROCONTADEST;

PROMPT #END
EXIT
