-- probe_janapr_reconcile.sql  (v2 — 2026-07-21)
-- =====================================================================
-- Jan-Apr 2026 reconciliation of the three families the NOTA_CLIENTE calls
-- "lançamentos manuais": Vale-ADM, Associações (020.060.0020), DL extras.
--
-- v2 FIXES (v1 tripped two SQL*Plus gotchas):
--   * NO line may END in a hyphen — a trailing "-" is SQL*Plus line-continuation,
--     so a "PROMPT ... ---" ate the SELECT that followed it (SP2-0734). All PROMPT
--     headers below end in ":" or a letter.
--   * #1b used "ORDER BY 1,2" on a single concatenated column (ORA-01785); fixed.
--   * SET SQLBLANKLINES ON so blank lines inside a statement don't terminate it.
--
-- v1 LIVE RESULTS worth keeping in view (workbook targets in parens):
--   #1a Vale-ADM parent: jan 2090,24 (1127,96) feb 2601,28 (1351,88)
--       mar 3440,12 (3983,22) abr 3421,36 (3421,36 TIE) mai 3326,94 (3326,94 TIE)
--   #2a Associações: jan 2800,06 feb/mar/abr 7109,73 (constant!) mai 2822,06 (TIE)
--   #4 inst despesas GROSS: within ~4,6k of every month's row-198 target.
-- Hypothesis this v2 tests: Jan/Feb Vale differs only because the OLD workbook
-- hand-split vale into an ADM row + an área row (r26/27, filled jan/feb, empty
-- mar+); the DB carries the full parent AND the per-person destination (MLA/VSR
-- =ADM, JVO=área lawyer), so the split is DB-derivable — arguably more correct.
--
-- SAFE: read-only SELECTs. Pipe-delimited, block-prefixed output.
SET DEFINE OFF
SET PAGESIZE 0
SET LINESIZE 32767
SET TRIMOUT ON
SET FEEDBACK OFF
SET HEADING OFF
SET SQLBLANKLINES ON
WHENEVER SQLERROR CONTINUE

PROMPT ============================================================
PROMPT #1 VALE-ADM per month
PROMPT ============================================================
PROMPT targets jan 1127,96 fev 1351,88 mar 3983,22 abr 3421,36 mai 3326,94
PROMPT [1b] per-person desdobramento legs (500.010.SIGLA + the 020.030.0060 slice) by month.
PROMPT These sum to the #1a parent. MLA/VSR=ADM, JVO=area lawyer (Contencioso):
SELECT '1b|'||TO_CHAR(l.LANDDATA,'YYYY-MM')
       ||'|dest='||NVL(l.PCTCNUMEROCONTADEST,'?')
       ||'|val='||TO_CHAR(ROUND(SUM(l.LANNVALOR),2))
       ||'|n='||COUNT(*) AS out
  FROM FINANCE.LANCAMENTO l
 WHERE l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-06-01'
   AND ( UPPER(l.LANCHISTORICO) LIKE '%VALE REFEI%'
      OR UPPER(l.LANCHISTORICO) LIKE '%VALE TRANSP%'
      OR UPPER(l.LANCHISTORICO) LIKE '%VR MENSAL%'
      OR UPPER(l.LANCHISTORICO) LIKE '%VT MENSAL%' )
   AND ( l.PCTCNUMEROCONTADEST LIKE '500.010.%'
      OR l.PCTCNUMEROCONTADEST = '020.030.0060' )
 GROUP BY TO_CHAR(l.LANDDATA,'YYYY-MM'), l.PCTCNUMEROCONTADEST
 ORDER BY 1;

PROMPT [1c] EVERY vale line jan..abr with full histórico (see the wording per month):
SELECT '1c|'||TO_CHAR(l.LANDDATA,'YYYY-MM-DD')
       ||'|org='||NVL(l.PCTCNUMEROCONTAORG,'?')
       ||'|dest='||NVL(l.PCTCNUMEROCONTADEST,'?')
       ||'|val='||TO_CHAR(ROUND(l.LANNVALOR,2))
       ||'|'||SUBSTR(l.LANCHISTORICO,1,75) AS out
  FROM FINANCE.LANCAMENTO l
 WHERE l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-05-01'
   AND ( UPPER(l.LANCHISTORICO) LIKE '%VALE%'
      OR UPPER(l.LANCHISTORICO) LIKE '%REFEI%'
      OR UPPER(l.LANCHISTORICO) LIKE '%VR MENSAL%'
      OR UPPER(l.LANCHISTORICO) LIKE '%VT MENSAL%' )
   AND ( l.PCTCNUMEROCONTADEST LIKE '500.010.%'
      OR l.PCTCNUMEROCONTADEST = '200.010.0010'
      OR l.PCTCNUMEROCONTADEST = '020.030.0060' )
 ORDER BY 1;

PROMPT ============================================================
PROMPT #2 ASSOCIACOES 020.060.0020 per month
PROMPT ============================================================
PROMPT workbook totals jan 1400,19 fev 3829,42 mar 4046,82 abr 4046,82 mai 2822,06
PROMPT [2b] every line jan..abr with date + value + setor + histórico (diagnose the constant 7109,73):
SELECT '2b|'||TO_CHAR(l.LANDDATA,'YYYY-MM-DD')
       ||'|val='||TO_CHAR(ROUND(l.LANNVALOR,2))
       ||'|setor='||NVL(l.SIGLADEST,'?')
       ||'|'||SUBSTR(l.LANCHISTORICO,1,90) AS out
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST='020.060.0020'
   AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-05-01'
   AND l.LANNVALOR <> 0
 ORDER BY 1;

PROMPT ============================================================
PROMPT #3 DL EXTRAS per month
PROMPT ============================================================
PROMPT [3a] Bônus 150.% by month (expect ~fev only):
SELECT '3a|'||TO_CHAR(l.LANDDATA,'YYYY-MM')
       ||'|bonus_150='||TO_CHAR(ROUND(SUM(l.LANNVALOR),2))
       ||'|n='||COUNT(*) AS out
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST LIKE '150.%'
   AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-06-01'
 GROUP BY TO_CHAR(l.LANDDATA,'YYYY-MM')
 ORDER BY 1;

PROMPT [3b] 030.010.0010 lines mentioning Bônus / excedente / Reserva / Cacione, by month:
SELECT '3b|'||TO_CHAR(l.LANDDATA,'YYYY-MM-DD')
       ||'|val='||TO_CHAR(ROUND(l.LANNVALOR,2))
       ||'|sig='||NVL(l.SIGLADEST,'?')
       ||'|'||SUBSTR(l.LANCHISTORICO,1,70) AS out
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST='030.010.0010'
   AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-06-01'
   AND ( UPPER(l.LANCHISTORICO) LIKE '%BONUS%'
      OR UPPER(l.LANCHISTORICO) LIKE '%B_NUS%'
      OR UPPER(l.LANCHISTORICO) LIKE '%EXCEDENTE%'
      OR UPPER(l.LANCHISTORICO) LIKE '%RESERVA%'
      OR UPPER(l.LANCHISTORICO) LIKE '%CACIONE%' )
 ORDER BY 1;

PROMPT ============================================================
PROMPT #5 Workbook area-split of Vale: is r26/27 (area) filled jan/feb only?
PROMPT ============================================================
PROMPT [5] ALL 500.010 vale legs by SIGLA across jan..mai (classify ADM vs area by sigla):
SELECT '5|'||NVL(l.PCTCNUMEROCONTADEST,'?')
       ||'|jan..mai_total='||TO_CHAR(ROUND(SUM(l.LANNVALOR),2))
       ||'|n='||COUNT(*) AS out
  FROM FINANCE.LANCAMENTO l
 WHERE l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-06-01'
   AND ( UPPER(l.LANCHISTORICO) LIKE '%VALE REFEI%'
      OR UPPER(l.LANCHISTORICO) LIKE '%VALE TRANSP%'
      OR UPPER(l.LANCHISTORICO) LIKE '%VR MENSAL%'
      OR UPPER(l.LANCHISTORICO) LIKE '%VT MENSAL%' )
   AND l.PCTCNUMEROCONTADEST LIKE '500.010.%'
 GROUP BY l.PCTCNUMEROCONTADEST
 ORDER BY 1;

PROMPT #END
EXIT
