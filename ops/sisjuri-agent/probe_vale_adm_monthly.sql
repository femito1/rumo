-- probe_vale_adm_monthly.sql
-- QUESTION: do Jan/Feb/Mar 2026 book Vale-ADM by a DIFFERENT rule than Apr/May?
--
-- Context (verified 2026-07-16, live snapshots vs the 05.2026 workbook):
--   The extract's ``vale_adm`` = Σ FINANCE.LANCAMENTO on 200.010.0010 whose
--   histórico matches VR/VT-Mensal. Per month, extract vs workbook Vale-ADM:
--       Jan  extract 2090.24  vs  wb 1127.96   (extract HIGHER +962.28)
--       Feb  extract 2601.28  vs  wb 1351.88   (extract HIGHER +1249.40)
--       Mar  extract 3440.12  vs  wb 3983.22   (extract LOWER  -543.10)
--       Abr  extract 3421.36  vs  wb 3421.36   (TIE)
--       Mai  extract 3326.94  vs  wb 3326.94   (TIE)
--   So Apr/May tie the DB; Jan–Mar don't. We want to know WHY: is the DB
--   transitória the complete, true Vale-ADM (and Jan–Mar were just hand-typed
--   differently by finance), OR is the extract filter missing/over-catching rows
--   in some months (a DB-capture bug, not a client hand-entry difference)?
--
-- This probe dumps EVERY 200.010.0010 line per month (Jan..May 2026) with its full
-- histórico + value, and separately the exact subset the extract's VR/VT filter
-- catches. Compare the two, and compare the filtered Σ to the workbook's typed
-- Vale-ADM above. If the filtered Σ == extract value every month (it should) and
-- the FULL 200.010.0010 set reveals extra VR/VT-like lines the filter skips (or
-- the workbook's typed number matches a hand-picked subset), that pinpoints the rule.
--
-- Output: one concatenated column per row, pipe-delimited, prefixed by block (A/B/C).
-- SAFE: read-only SELECTs. Columns verified against extract.sql (LANCHISTORICO,
-- LANDDATA, PCTCNUMEROCONTADEST, LANNVALOR, LANCPROFDEST, SIGLADEST).
SET DEFINE OFF
SET PAGESIZE 0
SET LINESIZE 32767
SET TRIMOUT ON
SET FEEDBACK OFF
SET HEADING OFF
WHENEVER SQLERROR CONTINUE

PROMPT #A Per-month Vale-ADM: FULL 200.010.0010 total vs the VR/VT-filtered subset (the extract rule)
-- For each month: (1) SUM of ALL 200.010.0010 lines, (2) SUM of only the VR/VT
-- lines the extract catches, (3) count of each. If (1) >> (2), the transitória
-- carries much more than Vale and the filter is right to be narrow; if (1) ~= (2),
-- Vale is essentially the whole transitória.
SELECT 'A|'||mth||'|all_total='||TO_CHAR(all_tot)||'|all_n='||all_n
       ||'|vrvt_total='||TO_CHAR(vrvt_tot)||'|vrvt_n='||vrvt_n
  FROM (
    SELECT TO_CHAR(l.LANDDATA,'YYYY-MM') mth,
           ROUND(SUM(l.LANNVALOR),2) all_tot,
           COUNT(*) all_n,
           ROUND(SUM(CASE WHEN ( UPPER(l.LANCHISTORICO) LIKE '%VR MENSAL%'
                              OR UPPER(l.LANCHISTORICO) LIKE '%VT MENSAL%'
                              OR UPPER(l.LANCHISTORICO) LIKE '%VALE REFEI%MENSAL%'
                              OR UPPER(l.LANCHISTORICO) LIKE '%VALE TRANSP%MENSAL%' )
                          THEN l.LANNVALOR ELSE 0 END),2) vrvt_tot,
           SUM(CASE WHEN ( UPPER(l.LANCHISTORICO) LIKE '%VR MENSAL%'
                        OR UPPER(l.LANCHISTORICO) LIKE '%VT MENSAL%'
                        OR UPPER(l.LANCHISTORICO) LIKE '%VALE REFEI%MENSAL%'
                        OR UPPER(l.LANCHISTORICO) LIKE '%VALE TRANSP%MENSAL%' )
                    THEN 1 ELSE 0 END) vrvt_n
      FROM FINANCE.LANCAMENTO l
     WHERE l.PCTCNUMEROCONTADEST='200.010.0010'
       AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-06-01'
     GROUP BY TO_CHAR(l.LANDDATA,'YYYY-MM')
  )
 ORDER BY 1;

PROMPT #B EVERY 200.010.0010 line Jan..May (date|value|profdest|sigladest|historico) — eyeball what VR/VT lines exist and whether the filter catches them all
SELECT 'B|'||TO_CHAR(l.LANDDATA,'YYYY-MM-DD')
       ||'|'||TO_CHAR(ROUND(l.LANNVALOR,2))
       ||'|'||NVL(l.LANCPROFDEST,'-')
       ||'|'||NVL(l.SIGLADEST,'-')
       ||'|'||SUBSTR(l.LANCHISTORICO,1,80)
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST='200.010.0010'
   AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-06-01'
   AND ( UPPER(l.LANCHISTORICO) LIKE '%VALE%'
      OR UPPER(l.LANCHISTORICO) LIKE '%VR %'
      OR UPPER(l.LANCHISTORICO) LIKE '%VT %'
      OR UPPER(l.LANCHISTORICO) LIKE '%REFEI%'
      OR UPPER(l.LANCHISTORICO) LIKE '%TRANSP%' )
 ORDER BY 1;

PROMPT #C ALL 200.010.0010 lines Jan..May regardless of histórico (so we see any Vale booked with an unexpected wording the VALE/VR/VT filter in #B would miss)
SELECT 'C|'||TO_CHAR(l.LANDDATA,'YYYY-MM-DD')
       ||'|'||TO_CHAR(ROUND(l.LANNVALOR,2))
       ||'|'||SUBSTR(l.LANCHISTORICO,1,90)
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST='200.010.0010'
   AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-06-01'
 ORDER BY 1;

PROMPT #END
EXIT
