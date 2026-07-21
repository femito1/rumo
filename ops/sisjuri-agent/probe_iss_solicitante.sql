-- probe_iss_solicitante.sql  (2026-07-21, linted)
-- JGS's two ISS units differ ONLY in LANCSOLICITANTE (MAM vs JGS). Hypothesis: the
-- area of each ISS rateio unit = the home area of its LANCSOLICITANTE (requester),
-- not the profD. Test across ALL Jan ISS rows: dump profD + solicitante + the
-- solicitante's home grupo. If grouping by solicitante-home reproduces the workbook
-- 4,5/5,5/4 split, ISS is 100% DB-derivable. Read-only.
SET DEFINE OFF
SET PAGESIZE 0
SET LINESIZE 32767
SET TRIMOUT ON
SET FEEDBACK OFF
SET HEADING OFF
SET SQLBLANKLINES ON
WHENEVER SQLERROR CONTINUE

PROMPT #N Every Jan ISS row: profD, solicitante, solicitante home grupo, DESNITEM
SELECT 'N|profD='||NVL(l.LANCPROFDEST,'-')
       ||'|solic='||NVL(l.LANCSOLICITANTE,'-')
       ||'|solicGrupo='||NVL(gs.NOME,'(none)')
       ||'|profDGrupo='||NVL(gp.NOME,'(none)')
       ||'|item='||NVL(TO_CHAR(l.DESNITEM),'-')
       ||'|val='||TO_CHAR(l.LANNVALOR) AS out
  FROM FINANCE.LANCAMENTO l
  LEFT JOIN LDESK.CAD_PROFISSIONAL ps ON ps.SIGLA = l.LANCSOLICITANTE
  LEFT JOIN LDESK.CAD_GRUPOJURIDICO gs ON gs.ID_GRUPOJURIDICO = ps.ID_GRUPOJURIDICO
  LEFT JOIN LDESK.CAD_PROFISSIONAL pp ON pp.SIGLA = l.LANCPROFDEST
  LEFT JOIN LDESK.CAD_GRUPOJURIDICO gp ON gp.ID_GRUPOJURIDICO = pp.ID_GRUPOJURIDICO
 WHERE l.PCTCNUMEROCONTADEST='030.010.0160'
   AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-02-01'
 ORDER BY l.LANCSOLICITANTE, l.LANCPROFDEST;

PROMPT #O ISS totals grouped by SOLICITANTE home area (does it = workbook 4,5/5,5/4?)
SELECT 'O|solicArea='||NVL(gs.NOME,'(none)')
       ||'|total='||TO_CHAR(ROUND(SUM(l.LANNVALOR),2))
       ||'|n='||COUNT(*) AS out
  FROM FINANCE.LANCAMENTO l
  LEFT JOIN LDESK.CAD_PROFISSIONAL ps ON ps.SIGLA = l.LANCSOLICITANTE
  LEFT JOIN LDESK.CAD_GRUPOJURIDICO gs ON gs.ID_GRUPOJURIDICO = ps.ID_GRUPOJURIDICO
 WHERE l.PCTCNUMEROCONTADEST='030.010.0160'
   AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-02-01'
 GROUP BY gs.NOME
 ORDER BY gs.NOME;

PROMPT #END
EXIT
