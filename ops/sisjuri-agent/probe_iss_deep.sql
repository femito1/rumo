-- probe_iss_deep.sql  (2026-07-21)
-- =====================================================================
-- EXHAUSTIVE test of the hypothesis: the workbook's per-area ISS split is
-- NOT manual — ISS (a tax on billed services) follows the ÁREA OF THE CASE/MATTER
-- it was charged on, so a lawyer who bills across areas gets ISS in each. The
-- rolled-up GERENC_LANCAMENTORESUMO collapses every ISS row to the lawyer's HOME
-- group (that's why both JGS rows showed grupo=Arbitragem). The RAW
-- FINANCE.LANCAMENTO should carry the real per-posting caso/cliente/area.
--
-- Target to reproduce (Jan, workbook "ISS Trimestral" formulas):
--   Contencioso 4,5u=1.719,72 | Econômico 5,5u=2.101,88 | Arbitragem 4u=1.528,64  (u=382,16)
-- Fixed home payers give Conten 3,5 / Econ 4,5 / Arb 3; the 3 "free" units are
-- JCT (1) + JGS (2), and the workbook needs +1 to EACH area — i.e. JCT and JGS's
-- two units land in three DIFFERENT areas. If ISS-follows-case is real, the raw
-- ledger will SHOW those three units in three different case-areas.
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
PROMPT #A RAW FINANCE.LANCAMENTO ISS rows (Jan) — every column that could carry area
PROMPT ============================================================
PROMPT dest acct, prof org/dest, sigla org/dest, caso, cliente, value, histórico:
SELECT 'A|'||TO_CHAR(l.LANDDATA,'YYYY-MM-DD')
       ||'|profO='||NVL(l.LANCPROFORG,'-')||'|profD='||NVL(l.LANCPROFDEST,'-')
       ||'|sigO='||NVL(l.SIGLAORG,'-')||'|sigD='||NVL(l.SIGLADEST,'-')
       ||'|caso='||NVL(TO_CHAR(l.LANNCASODEST),'-')
       ||'|cli='||NVL(TO_CHAR(l.LANNCLIENTEDEST),'-')
       ||'|val='||TO_CHAR(ROUND(l.LANNVALOR,2))
       ||'|h='||SUBSTR(l.LANCHISTORICO,1,45) AS out
  FROM FINANCE.LANCAMENTO l
 WHERE (l.PCTCNUMEROCONTADEST='030.010.0160' OR l.PCTCNUMEROCONTAORG='030.010.0160')
   AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-02-01'
 ORDER BY l.LANNVALOR, l.LANDDATA;

PROMPT ============================================================
PROMPT #B Each ISS posting resolved to CASE AREA (LANNCASODEST -> CAD_CASO -> área)
PROMPT ============================================================
PROMPT If ISS-follows-case is real, grouping by case-area reproduces 4,5/5,5/4:
SELECT 'B|caseArea='||NVL(a.NOME,'(sem caso/area)')
       ||'|total='||TO_CHAR(ROUND(SUM(l.LANNVALOR),2))
       ||'|n='||COUNT(*) AS out
  FROM FINANCE.LANCAMENTO l
  LEFT JOIN LDESK.CAD_CASO c ON c.ID_CASO = l.LANNCASODEST
  LEFT JOIN LDESK.CAD_AREAJURIDICA a ON a.ID_AREAJURIDICA = c.ID_AREAJURIDICA
 WHERE l.PCTCNUMEROCONTADEST='030.010.0160'
   AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-02-01'
 GROUP BY a.NOME
 ORDER BY a.NOME;

PROMPT ============================================================
PROMPT #C Who is JCT? profile + home grupo
PROMPT ============================================================
SELECT 'C|sigla='||NVL(p.SIGLA,'-')
       ||'|nome='||SUBSTR(NVL(p.NOME,'-'),1,40)
       ||'|grupo='||NVL(g.NOME,'-')
       ||'|socio='||NVL(p.SOCIO,'-') AS out
  FROM LDESK.CAD_PROFISSIONAL p
  LEFT JOIN LDESK.CAD_GRUPOJURIDICO g ON g.ID_GRUPOJURIDICO = p.ID_GRUPOJURIDICO
 WHERE p.SIGLA IN ('JCT','JGS');

PROMPT ============================================================
PROMPT #D JGS's TWO ISS rows side by side — do caso/cliente/area DIFFER between them?
PROMPT ============================================================
SELECT 'D|val='||TO_CHAR(ROUND(l.LANNVALOR,2))
       ||'|caso='||NVL(TO_CHAR(l.LANNCASODEST),'-')
       ||'|cli='||NVL(TO_CHAR(l.LANNCLIENTEDEST),'-')
       ||'|caseArea='||NVL(a.NOME,'-')
       ||'|h='||SUBSTR(l.LANCHISTORICO,1,55) AS out
  FROM FINANCE.LANCAMENTO l
  LEFT JOIN LDESK.CAD_PROFISSIONAL p ON p.ID_PROFISSIONAL = l.LANCPROFDEST
  LEFT JOIN LDESK.CAD_CASO c ON c.ID_CASO = l.LANNCASODEST
  LEFT JOIN LDESK.CAD_AREAJURIDICA a ON a.ID_AREAJURIDICA = c.ID_AREAJURIDICA
 WHERE l.PCTCNUMEROCONTADEST='030.010.0160'
   AND p.SIGLA='JGS'
   AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-02-01'
 ORDER BY l.LANNVALOR;

PROMPT ============================================================
PROMPT #E Fallback: if LANNCASODEST is null, does the ISS row carry a caso/area on the ORG side?
PROMPT ============================================================
SELECT 'E|profD='||NVL(l.LANCPROFDEST,'-')
       ||'|casoD='||NVL(TO_CHAR(l.LANNCASODEST),'-')
       ||'|cliD='||NVL(TO_CHAR(l.LANNCLIENTEDEST),'-')
       ||'|orgAcct='||NVL(l.PCTCNUMEROCONTAORG,'-')
       ||'|val='||TO_CHAR(ROUND(l.LANNVALOR,2)) AS out
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST='030.010.0160'
   AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-02-01'
 ORDER BY l.LANCPROFDEST, l.LANNVALOR;

PROMPT #END
EXIT
