-- probe_iss_jgs_dup.sql  (v3 — 2026-07-21, linted)
-- =====================================================================
-- Prove JGS's TWO Jan ISS postings carry a DB differentiator (the Arb/Econ split
-- that makes the workbook tie to the centavo), or confirm they're identical.
--
-- v3: NO XMLTYPE(alias) (v2 hit ORA-00904 — that needs an object table). Instead
-- dump the full column list (#J) and every KNOWN scalar column of both JGS rows
-- explicitly (#K), all TO_CHAR'd so nothing throws. Linted with lint_probe.py
-- (sqlglot, oracle dialect) before sending: ORDER BY targets real expressions.
--
-- SAFE: read-only. No positional ORDER BY beyond col 1. No object-type calls.
SET DEFINE OFF
SET PAGESIZE 0
SET LINESIZE 32767
SET TRIMOUT ON
SET FEEDBACK OFF
SET HEADING OFF
SET SQLBLANKLINES ON
WHENEVER SQLERROR CONTINUE

PROMPT ============================================================
PROMPT #J All FINANCE.LANCAMENTO column names+types (so #K covers the real columns)
PROMPT ============================================================
SELECT 'J|'||COLUMN_NAME||'|'||DATA_TYPE AS out
  FROM ALL_TAB_COLUMNS
 WHERE OWNER='FINANCE' AND TABLE_NAME='LANCAMENTO'
 ORDER BY COLUMN_NAME;

PROMPT ============================================================
PROMPT #K Both JGS Jan ISS rows, every KNOWN scalar column TO_CHAR'd (spot the diff)
PROMPT ============================================================
PROMPT Compare the two output lines field-by-field; any differing field = the area signal.
SELECT 'K|rid='||ROWIDTOCHAR(l.ROWID)
       ||'|dt='||TO_CHAR(l.LANDDATA,'YYYY-MM-DD')
       ||'|val='||TO_CHAR(l.LANNVALOR)
       ||'|ctaO='||NVL(l.PCTCNUMEROCONTAORG,'-')
       ||'|ctaD='||NVL(l.PCTCNUMEROCONTADEST,'-')
       ||'|profO='||NVL(l.LANCPROFORG,'-')
       ||'|profD='||NVL(l.LANCPROFDEST,'-')
       ||'|sigO='||NVL(l.SIGLAORG,'-')
       ||'|sigD='||NVL(l.SIGLADEST,'-')
       ||'|casoO='||NVL(TO_CHAR(l.LANNCASOORG),'-')
       ||'|casoD='||NVL(TO_CHAR(l.LANNCASODEST),'-')
       ||'|cliO='||NVL(TO_CHAR(l.LANNCLIENTEORG),'-')
       ||'|cliD='||NVL(TO_CHAR(l.LANNCLIENTEDEST),'-')
       ||'|h='||SUBSTR(l.LANCHISTORICO,1,60) AS out
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST='030.010.0160'
   AND l.LANCPROFDEST='JGS'
   AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-02-01'
 ORDER BY ROWIDTOCHAR(l.ROWID);

PROMPT ============================================================
PROMPT #L ISS posting COUNT per LANCPROFDEST per quarter (who is doubled, when)
PROMPT ============================================================
SELECT 'L|'||TO_CHAR(l.LANDDATA,'YYYY-MM')
       ||'|prof='||NVL(l.LANCPROFDEST,'-')
       ||'|n='||COUNT(*)
       ||'|sum='||TO_CHAR(ROUND(SUM(l.LANNVALOR),2)) AS out
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST='030.010.0160'
   AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-08-01'
 GROUP BY TO_CHAR(l.LANDDATA,'YYYY-MM'), l.LANCPROFDEST
 HAVING COUNT(*) > 1
 ORDER BY TO_CHAR(l.LANDDATA,'YYYY-MM'), l.LANCPROFDEST;

PROMPT #END
EXIT
