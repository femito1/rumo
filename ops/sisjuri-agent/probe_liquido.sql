-- probe_liquido.sql
-- THE unlock: the workbook books LÍQUIDO (net of retained 3rd-party tax); our
-- extract reads BRUTO (CPGNVALORBASE). Confirmed vs Pagtos maio: Contabilidade
-- bruto 8570 -> líquido 8042.94 (= workbook exact); Suporte Totvs (Juritis
-- 030? no, 020.040.0010) bruto 3108.97 -> líquido 2917.77 (= workbook exact);
-- Terceirização Limpeza bruto 3984.15 -> líquido 3346.68 (= workbook exact).
-- FIND the net column / the retained-tax rows in the DB so we can book líquido.
SET DEFINE OFF
SET PAGESIZE 0
SET LINESIZE 32767
SET LONG 100000
SET TRIMOUT ON
SET FEEDBACK OFF
SET HEADING OFF
WHENEVER SQLERROR CONTINUE

PROMPT #A ALL columns of FINANCE.CONTASPAGAR (look for a net/liquido/valor column)
SELECT 'A|'||COLUMN_NAME||'|'||DATA_TYPE
  FROM ALL_TAB_COLUMNS
 WHERE OWNER='FINANCE' AND TABLE_NAME='CONTASPAGAR'
 ORDER BY COLUMN_ID;

PROMPT #B For the Ozai Contabilidade payment (May, bruto 8570), dump ALL numeric columns
-- Find the row and show every value column so we can spot 8042.94 or 527.06.
SELECT 'B|'||cp.PCTCNUMEROCONTA||'|VALORBASE='||TO_CHAR(cp.CPGNVALORBASE)
       ||'|'||SUBSTR(REPLACE(NVL(cp.CPGCHISTORICO,' '),'|','/'),1,30)
  FROM FINANCE.CONTASPAGAR cp
 WHERE cp.CPGDVECTO >= DATE '2026-05-01' AND cp.CPGDVECTO < DATE '2026-06-01'
   AND UPPER(cp.CPGCHISTORICO) LIKE '%OZAI%'
 ORDER BY cp.CPGNVALORBASE DESC;

PROMPT #C CPDESDOBRAMENTO / CPDESDOBRAMENTOPG columns (retained-tax desdobramento?)
SELECT 'C|'||TABLE_NAME||'|'||COLUMN_NAME||'|'||DATA_TYPE
  FROM ALL_TAB_COLUMNS
 WHERE OWNER='FINANCE' AND TABLE_NAME IN ('CPDESDOBRAMENTO','CPDESDOBRAMENTOPG')
 ORDER BY TABLE_NAME, COLUMN_ID;

PROMPT #D Retained-tax rows (300.010.* Valor Agregado de Terceiros) tied to May, per conta
SELECT 'D|'||NVL(l.PCTCNUMEROCONTADEST,'?')||'|'||SUBSTR(REPLACE(NVL(MAX(l.LANCHISTORICO),' '),'|','/'),1,30)||'|'||TO_CHAR(ROUND(SUM(l.LANNVALOR),2))||'|n='||COUNT(*)
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST LIKE '300.010.%'
   AND l.LANDDATA >= DATE '2026-05-01' AND l.LANDDATA < DATE '2026-06-01'
 GROUP BY l.PCTCNUMEROCONTADEST
 ORDER BY 1;

PROMPT #E VW_RESULTADO_MENSAL_DET: is there a column that is NET (vs VALOR=gross)?
SELECT 'E|'||COLUMN_NAME||'|'||DATA_TYPE
  FROM ALL_TAB_COLUMNS
 WHERE OWNER='FINANCE' AND TABLE_NAME='VW_RESULTADO_MENSAL_DET'
 ORDER BY COLUMN_ID;

PROMPT #END
EXIT
