-- probe_iss_jgs_dup.sql  (2026-07-21)
-- =====================================================================
-- The per-professional ISS rateio ties the workbook TOTAL and Contencioso; the
-- Econ/Arb split ties IFF JGS's TWO Jan units split Arb/Econ. We must prove that
-- split is DB-derivable, not assumed. The two JGS rows looked identical in the
-- columns dumped so far. This probe dumps EVERY column of both JGS ISS rows (and
-- all Jan ISS rows) so we can see ANY differentiator: ROWID, primary key, ORG
-- side accounts/prof, grupo id, cost-center, sequence, doc number, etc.
--
-- SAFE: read-only. No trailing-hyphen PROMPTs.
SET DEFINE OFF
SET PAGESIZE 0
SET LINESIZE 32767
SET LONG 4000
SET TRIMOUT ON
SET FEEDBACK OFF
SET HEADING OFF
SET SQLBLANKLINES ON
WHENEVER SQLERROR CONTINUE

PROMPT ============================================================
PROMPT #J All columns of FINANCE.LANCAMENTO (names+types) so we know what exists
PROMPT ============================================================
SELECT 'J|'||COLUMN_NAME||'|'||DATA_TYPE AS out
  FROM ALL_TAB_COLUMNS
 WHERE OWNER='FINANCE' AND TABLE_NAME='LANCAMENTO'
 ORDER BY COLUMN_ID;

PROMPT ============================================================
PROMPT #K The TWO JGS Jan ISS rows, EVERY scalar column via XML (spot the differentiator)
PROMPT ============================================================
PROMPT If any column differs between the two rows, that is the DB area signal.
SELECT 'K|'||ROWIDTOCHAR(l.ROWID)||'|'||
       SUBSTR(XMLTYPE(DBMS_XMLGEN.GETXML(
         'SELECT * FROM FINANCE.LANCAMENTO WHERE ROWID='''||ROWIDTOCHAR(l.ROWID)||''''
       )).getClobVal(), 1, 3500) AS out
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST='030.010.0160'
   AND l.LANCPROFDEST='JGS'
   AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-02-01';

PROMPT ============================================================
PROMPT #L Count of ISS postings per LANCPROFDEST per quarter (who is doubled, when)
PROMPT ============================================================
PROMPT JGS doubled in Jan (2025-Q2 ISS) but single in Apr/Jul — the count encodes area-seats.
SELECT 'L|'||TO_CHAR(l.LANDDATA,'YYYY-MM')
       ||'|prof='||NVL(l.LANCPROFDEST,'-')
       ||'|n='||COUNT(*)
       ||'|sum='||TO_CHAR(ROUND(SUM(l.LANNVALOR),2)) AS out
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST='030.010.0160'
   AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-08-01'
 GROUP BY TO_CHAR(l.LANDDATA,'YYYY-MM'), l.LANCPROFDEST
 HAVING COUNT(*) > 1
 ORDER BY 1,2;

PROMPT #END
EXIT
