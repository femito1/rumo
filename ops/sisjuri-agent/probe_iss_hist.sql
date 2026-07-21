-- probe_iss_hist.sql  (2026-07-21)
-- =====================================================================
-- THE decisive ISS probe. The raw ISS rows carry NO caso/cliente/setor — just a
-- flat 382,16 per lawyer (profD) and a histórico truncated at 45 chars reading
-- "ISS trimestral 2025- 2º TRIM - rateado para...". The system RECORDS the
-- apportionment target in that text. Get the FULL histórico for every ISS row,
-- all quarter months (Jan/Apr/Jul), so we can read where each 382,16 unit is
-- "rateado para" — especially JGS's TWO Jan units (workbook books one to
-- Arbitragem, one to Econômico). If the histórico names the area/lawyer, the
-- split is 100% DB-derivable from the text.
--
-- SAFE: read-only. Full histórico via SUBSTR(...,1,220). No trailing-hyphen PROMPTs.
SET DEFINE OFF
SET PAGESIZE 0
SET LINESIZE 32767
SET TRIMOUT ON
SET FEEDBACK OFF
SET HEADING OFF
SET SQLBLANKLINES ON
WHENEVER SQLERROR CONTINUE

PROMPT ============================================================
PROMPT #H FULL histórico of every ISS (030.010.0160) posting, Jan/Apr/Jul 2026
PROMPT ============================================================
PROMPT Read "rateado para ___" — does it name the destination area/lawyer per unit?
SELECT 'H|'||TO_CHAR(l.LANDDATA,'YYYY-MM')
       ||'|profD='||NVL(TO_CHAR(l.LANCPROFDEST),'-')
       ||'|val='||TO_CHAR(ROUND(l.LANNVALOR,2))
       ||'|H='||SUBSTR(l.LANCHISTORICO,1,220) AS out
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST='030.010.0160'
   AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-08-01'
 ORDER BY l.LANDDATA, l.LANCPROFDEST, l.LANNVALOR;

PROMPT ============================================================
PROMPT #I Just JGS's rows, full histórico, all quarters (the split-defining lawyer)
PROMPT ============================================================
SELECT 'I|'||TO_CHAR(l.LANDDATA,'YYYY-MM-DD')
       ||'|val='||TO_CHAR(ROUND(l.LANNVALOR,2))
       ||'|H='||SUBSTR(l.LANCHISTORICO,1,240) AS out
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST='030.010.0160'
   AND l.LANCPROFDEST='JGS'
   AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-08-01'
 ORDER BY l.LANDDATA, l.LANNVALOR;

PROMPT #END
EXIT
