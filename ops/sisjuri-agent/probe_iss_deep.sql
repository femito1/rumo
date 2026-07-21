-- probe_iss_deep.sql  (v2 — 2026-07-21)
-- =====================================================================
-- Test: is the workbook's per-area ISS split DB-derivable (ISS follows the CASE
-- area of the billed service), or genuinely manual? GERENC rolls ISS to the
-- lawyer's HOME group (both JGS rows showed Arbitragem); the RAW FINANCE.LANCAMENTO
-- may carry the real per-posting case/area.
--
-- v2 FIXES (v1 hit two schema errors):
--   * CAD_PROFISSIONAL has no NOME column -> use SIGLA/grupo only.
--   * ORA-01722: some LANC*/LANN* columns aren't the type assumed, and CAD_CASO's
--     key is likely a GUID string (like ID_GRUPOJURIDICO) not a number, so the
--     join coerced and failed. v2 (a) DISCOVERS the real columns first, and
--     (b) TO_CHAR-wraps every projected field so nothing can throw. The case
--     join is deferred until #F tells us the right key.
--
-- SAFE: read-only. Pipe-delimited, block-prefixed. No trailing-hyphen PROMPTs.
SET DEFINE OFF
SET PAGESIZE 0
SET LINESIZE 32767
SET TRIMOUT ON
SET FEEDBACK OFF
SET HEADING OFF
SET SQLBLANKLINES ON
WHENEVER SQLERROR CONTINUE

PROMPT ============================================================
PROMPT #F1 FINANCE.LANCAMENTO columns mentioning CASO / CLIENTE / GRUPO / AREA / SETOR
PROMPT ============================================================
SELECT 'F1|'||COLUMN_NAME||'|'||DATA_TYPE||'('||DATA_LENGTH||')' AS out
  FROM ALL_TAB_COLUMNS
 WHERE OWNER='FINANCE' AND TABLE_NAME='LANCAMENTO'
   AND ( COLUMN_NAME LIKE '%CASO%' OR COLUMN_NAME LIKE '%CLIENTE%'
      OR COLUMN_NAME LIKE '%GRUPO%' OR COLUMN_NAME LIKE '%AREA%'
      OR COLUMN_NAME LIKE '%SETOR%' OR COLUMN_NAME LIKE '%PROF%' )
 ORDER BY COLUMN_NAME;

PROMPT ============================================================
PROMPT #F2 LDESK.CAD_CASO key/area columns (find the join key type + area column)
PROMPT ============================================================
SELECT 'F2|'||COLUMN_NAME||'|'||DATA_TYPE||'('||DATA_LENGTH||')' AS out
  FROM ALL_TAB_COLUMNS
 WHERE OWNER='LDESK' AND TABLE_NAME='CAD_CASO'
   AND ( COLUMN_NAME LIKE '%ID%' OR COLUMN_NAME LIKE '%CASO%'
      OR COLUMN_NAME LIKE '%AREA%' OR COLUMN_NAME LIKE '%NUMERO%'
      OR COLUMN_NAME LIKE '%CODIGO%' )
 ORDER BY COLUMN_NAME;

PROMPT ============================================================
PROMPT #A RAW FINANCE.LANCAMENTO ISS rows (Jan) — all fields TO_CHAR'd (cannot throw)
PROMPT ============================================================
SELECT 'A|'||TO_CHAR(l.LANDDATA,'YYYY-MM-DD')
       ||'|profO='||NVL(TO_CHAR(l.LANCPROFORG),'-')
       ||'|profD='||NVL(TO_CHAR(l.LANCPROFDEST),'-')
       ||'|sigO='||NVL(TO_CHAR(l.SIGLAORG),'-')
       ||'|sigD='||NVL(TO_CHAR(l.SIGLADEST),'-')
       ||'|casoD='||NVL(TO_CHAR(l.LANNCASODEST),'-')
       ||'|cliD='||NVL(TO_CHAR(l.LANNCLIENTEDEST),'-')
       ||'|val='||TO_CHAR(ROUND(l.LANNVALOR,2))
       ||'|h='||SUBSTR(l.LANCHISTORICO,1,45) AS out
  FROM FINANCE.LANCAMENTO l
 WHERE (l.PCTCNUMEROCONTADEST='030.010.0160' OR l.PCTCNUMEROCONTAORG='030.010.0160')
   AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-02-01'
 ORDER BY l.LANNVALOR, l.LANDDATA;

PROMPT ============================================================
PROMPT #C Who is JCT / JGS? sigla + home grupo + sócio flag (no NOME column)
PROMPT ============================================================
SELECT 'C|sigla='||NVL(p.SIGLA,'-')
       ||'|grupo='||NVL(g.NOME,'-')
       ||'|socio='||NVL(p.SOCIO,'-') AS out
  FROM LDESK.CAD_PROFISSIONAL p
  LEFT JOIN LDESK.CAD_GRUPOJURIDICO g ON g.ID_GRUPOJURIDICO = p.ID_GRUPOJURIDICO
 WHERE p.SIGLA IN ('JCT','JGS');

PROMPT ============================================================
PROMPT #G ISS grouped by SIGLADEST cost-center (the tag despesas_equipe_area uses)
PROMPT ============================================================
PROMPT SIGLADEST may carry ECT/EDE/ESP per posting even when GERENC rolls to home:
SELECT 'G|sigD='||NVL(TO_CHAR(l.SIGLADEST),'(null)')
       ||'|total='||TO_CHAR(ROUND(SUM(l.LANNVALOR),2))
       ||'|n='||COUNT(*) AS out
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST='030.010.0160'
   AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-02-01'
 GROUP BY l.SIGLADEST
 ORDER BY l.SIGLADEST;

PROMPT #END
EXIT
