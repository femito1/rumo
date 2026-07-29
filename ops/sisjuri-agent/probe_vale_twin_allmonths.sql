-- probe_vale_twin_allmonths.sql
-- QUESTION: does the extract's new "exclude rows having a 500.010.<SIGLA> twin"
-- rule produce the workbook's ADM-only Vale for EVERY month of 2026, or only for
-- May/June (the two we proved by hand)?
--
-- WHY THIS EXISTS. `vale_adm` sums FINANCE.LANCAMENTO on the transitória
-- 200.010.0010 whose histórico matches VR/VT-Mensal. That total is ADM-only in
-- some months and ADM+lawyers in others, because finance books it in two shapes:
--   May  — ONE lump pair (VR 2.719,90 + VT 607,04 = 3.326,94), no 500.010.*
--          counterpart. All ADM. Ties workbook G122+G123.
--   June — the transitória MIRRORS per-person 500.010.<SIGLA> lines:
--          JVO 1.283,00 + VSR 1.100,60 (lawyers) + MLA 1.333,12 (ADM) = 3.716,72,
--          and the workbook types only 1.333,12 (H122+H123).
-- Leaving the lawyers in double-counts them (they are already in per-área Custo
-- equipe via custo_equipe_area) and inflates every área's Despesa Institucional
-- rateio share. June showed reserva -10.194,80 instead of -9.956,44 because of it.
--
-- A post-hoc "subtract Σ custo_equipe_area" fix was tried and REJECTED: it only
-- reproduces the workbook in Feb. Measured, extract − lawyers vs workbook:
--       Jan 1.092,44 vs 1.127,96  ✗
--       Feb 1.351,88 vs 1.351,88  ✓
--       Mar 1.240,92 vs 3.983,22  ✗
--       Abr     0,00 vs 3.421,36  ✗
--       Mai 2.014,44 vs 3.326,94  ✗
-- So the split MUST be structural (does a twin row exist?), not arithmetic.
--
-- WHAT TO DO WITH THE OUTPUT. Block C is the number the fixed extract will emit.
-- Compare it per month against the workbook's typed Vale-ADM (Base_Resultado
-- Mensal_V2 rows 122+123, month column):
--       Jan 1.127,96 | Feb 1.351,88 | Mar 3.983,22 | Abr 3.421,36
--       Mai 3.326,94 | Jun 1.333,12
-- Rows that tie ⇒ the twin rule is correct for that month. Rows that DON'T tie
-- are either (a) finance hand-typing a different number in the workbook, or
-- (b) a third bookkeeping shape we have not seen — bring those to Renata with the
-- block-A dump for that month rather than guessing a formula.
--
-- SAFE: read-only SELECTs. Columns verified against extract.sql (LANCHISTORICO,
-- LANDDATA, PCTCNUMEROCONTADEST, LANNVALOR).
SET DEFINE OFF
SET PAGESIZE 0
SET LINESIZE 32767
SET TRIMOUT ON
SET FEEDBACK OFF
SET HEADING OFF

PROMPT === BLOCK A: every VR/VT-Mensal line on the transitória, per month ===
PROMPT ano_mes|conta_dest|valor|historico
SELECT TO_CHAR(l.LANDDATA,'YYYY-MM') || '|' ||
       l.PCTCNUMEROCONTADEST || '|' ||
       TO_CHAR(l.LANNVALOR,'FM999999990.00') || '|' ||
       SUBSTR(l.LANCHISTORICO, 1, 90)
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST = '200.010.0010'
   AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-07-01'
   AND ( UPPER(l.LANCHISTORICO) LIKE '%VR MENSAL%'
      OR UPPER(l.LANCHISTORICO) LIKE '%VT MENSAL%'
      OR UPPER(l.LANCHISTORICO) LIKE '%VALE REFEI%MENSAL%'
      OR UPPER(l.LANCHISTORICO) LIKE '%VALE TRANSP%MENSAL%' )
 ORDER BY 1;

PROMPT
PROMPT === BLOCK B: the per-person 500.010.<SIGLA> Vale lines (the twins) ===
PROMPT ano_mes|conta_dest|sigla|valor|historico
SELECT TO_CHAR(l.LANDDATA,'YYYY-MM') || '|' ||
       l.PCTCNUMEROCONTADEST || '|' ||
       SUBSTR(l.PCTCNUMEROCONTADEST, 9) || '|' ||
       TO_CHAR(l.LANNVALOR,'FM999999990.00') || '|' ||
       SUBSTR(l.LANCHISTORICO, 1, 90)
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST LIKE '500.010.%'
   AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-07-01'
   AND ( UPPER(l.LANCHISTORICO) LIKE '%VR MENSAL%'
      OR UPPER(l.LANCHISTORICO) LIKE '%VT MENSAL%'
      OR UPPER(l.LANCHISTORICO) LIKE '%VALE REFEI%MENSAL%'
      OR UPPER(l.LANCHISTORICO) LIKE '%VALE TRANSP%MENSAL%' )
 ORDER BY TO_CHAR(l.LANDDATA,'YYYY-MM'), l.PCTCNUMEROCONTADEST;

PROMPT
PROMPT === BLOCK C: what the FIXED extract emits (twin-excluded), per month ===
PROMPT ano_mes|vale_adm_admonly|n_rows_kept|n_rows_dropped
SELECT m || '|' ||
       TO_CHAR(kept_sum,'FM999999990.00') || '|' || kept_n || '|' || dropped_n
  FROM (
    SELECT TO_CHAR(l.LANDDATA,'YYYY-MM') m,
           SUM(CASE WHEN tw.c IS NULL THEN l.LANNVALOR ELSE 0 END) kept_sum,
           SUM(CASE WHEN tw.c IS NULL THEN 1 ELSE 0 END) kept_n,
           SUM(CASE WHEN tw.c IS NULL THEN 0 ELSE 1 END) dropped_n
      FROM FINANCE.LANCAMENTO l
      LEFT JOIN (
            -- same-month 500.010.* row with the same histórico and |valor|
            SELECT DISTINCT TO_CHAR(p.LANDDATA,'YYYY-MM') m,
                   p.LANCHISTORICO h, ABS(p.LANNVALOR) v, 1 c
              FROM FINANCE.LANCAMENTO p
             WHERE p.PCTCNUMEROCONTADEST LIKE '500.010.%'
               AND p.LANDDATA >= DATE '2026-01-01' AND p.LANDDATA < DATE '2026-07-01'
           ) tw
        ON tw.m = TO_CHAR(l.LANDDATA,'YYYY-MM')
       AND tw.h = l.LANCHISTORICO
       AND ABS(ABS(l.LANNVALOR) - tw.v) < 0.005
     WHERE l.PCTCNUMEROCONTADEST = '200.010.0010'
       AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-07-01'
       AND ( UPPER(l.LANCHISTORICO) LIKE '%VR MENSAL%'
          OR UPPER(l.LANCHISTORICO) LIKE '%VT MENSAL%'
          OR UPPER(l.LANCHISTORICO) LIKE '%VALE REFEI%MENSAL%'
          OR UPPER(l.LANCHISTORICO) LIKE '%VALE TRANSP%MENSAL%' )
     GROUP BY TO_CHAR(l.LANDDATA,'YYYY-MM')
  )
 ORDER BY 1;
