-- probe_recebimento_area_basis.sql
-- ★ BIGGEST GAP (2026-07-14): the per-area DRE tabs are mostly BLANK because the
-- DB per-area recebimento (cash, case->área, Σ = sacred 415.927,84) does NOT match
-- the workbook per-area target (Σ = 449.181 — 33k MORE than cash received):
--   Contencioso 205.157 vs 240.445 (+35.288) · Econômico 162.473 vs 166.876 · Arbitragem 48.298 vs 41.860
-- The +33k over cash means the workbook allocates per-área on a DIFFERENT basis than
-- "cash received per case's área" — almost certainly a COMPETÊNCIA / faturado basis
-- (the same reason the workbook despesas use a competência VW_RESULTADOS* view, not
-- the cash snapshot — see probe_resultados_views.sql). GOAL: find the DB source whose
-- per-área receita for MAY 2026 = 240.445 / 166.876 / 41.860 (Arbitragem incl.
-- Ambiental; "Não Alocados" EXCLUDED). Read-only. Pipe-tagged single-line output.
SET DEFINE OFF
SET PAGESIZE 0
SET LINESIZE 32767
SET LONG 100000
SET TRIMOUT ON
SET FEEDBACK OFF
SET HEADING OFF
WHENEVER SQLERROR CONTINUE

PROMPT #A Cash-basis baseline (what we already emit): RESULTREC by case->área, May
SELECT 'A|'||NVL(a.NOME,'(sem area)')||'|'||TO_CHAR(ROUND(SUM(r.VALOR1),2))
  FROM LDESK.GERENC_VW_POSFIN_RESULTREC r
  LEFT JOIN LDESK.CAD_CASO c ON c.ID_CASO = r.ID_CASO
  LEFT JOIN LDESK.CAD_AREAJURIDICA a ON a.ID_AREAJURIDICA = c.ID_AREAJURIDICA
 WHERE r.ANO_MES = '2026-05'
 GROUP BY NVL(a.NOME,'(sem area)')
 ORDER BY 1;

PROMPT #B Faturado-basis by case->área, May (competência candidate) — does it approach 449k split?
SELECT 'B|'||NVL(a.NOME,'(sem area)')||'|'||TO_CHAR(ROUND(SUM(f.VALOR1),2))
  FROM LDESK.GERENC_VW_POSFIN_RESULTFAT f
  LEFT JOIN LDESK.CAD_CASO c ON c.ID_CASO = f.ID_CASO
  LEFT JOIN LDESK.CAD_AREAJURIDICA a ON a.ID_AREAJURIDICA = c.ID_AREAJURIDICA
 WHERE f.ANO_MES = '2026-05'
 GROUP BY NVL(a.NOME,'(sem area)')
 ORDER BY 1;

PROMPT #C Faturado-SHARE applied to total recebimento (ex Não Alocados) — candidate rule
-- If the workbook = (each área's faturado share, excluding unallocated) x total recebimento.
WITH fat AS (
  SELECT NVL(a.NOME,'(sem area)') area, SUM(f.VALOR1) v
    FROM LDESK.GERENC_VW_POSFIN_RESULTFAT f
    LEFT JOIN LDESK.CAD_CASO c ON c.ID_CASO = f.ID_CASO
    LEFT JOIN LDESK.CAD_AREAJURIDICA a ON a.ID_AREAJURIDICA = c.ID_AREAJURIDICA
   WHERE f.ANO_MES='2026-05'
   GROUP BY NVL(a.NOME,'(sem area)')
), tot AS (
  SELECT SUM(VALOR1) rec FROM LDESK.GERENC_VW_POSFIN_RESULTREC WHERE ANO_MES='2026-05'
), fbase AS (
  SELECT SUM(v) fsum FROM fat WHERE area <> '(sem area)'
)
SELECT 'C|'||fat.area||'|'||TO_CHAR(ROUND(fat.v / fbase.fsum * tot.rec, 2))
  FROM fat, tot, fbase
 WHERE fat.area <> '(sem area)'
 ORDER BY 1;

PROMPT #D List all LDESK/FINANCE views whose name hints at per-área or demonstrativo result
SELECT 'D|'||OWNER||'.'||OBJECT_NAME||'|'||OBJECT_TYPE
  FROM ALL_OBJECTS
 WHERE OWNER IN ('LDESK','FINANCE','GERENC')
   AND OBJECT_TYPE IN ('VIEW','TABLE')
   AND ( OBJECT_NAME LIKE '%RESULT%' OR OBJECT_NAME LIKE '%DEMONSTR%'
      OR OBJECT_NAME LIKE '%PROFISSIONAL%' OR OBJECT_NAME LIKE '%AREA%' )
 ORDER BY 1;

PROMPT #E Demonstrativo-per-profissional candidate: any view carrying área + receita + profissional
-- Show columns of the most likely candidates so the next probe can query them by month.
SELECT 'E|'||TABLE_NAME||'|'||COLUMN_NAME||'|'||DATA_TYPE
  FROM ALL_TAB_COLUMNS
 WHERE OWNER IN ('LDESK','GERENC')
   AND ( TABLE_NAME LIKE '%DEMONSTR%' OR TABLE_NAME LIKE '%RESULTADO%PROF%'
      OR TABLE_NAME LIKE '%POSFIN%RESULT%' )
 ORDER BY TABLE_NAME, COLUMN_ID;

PROMPT #F Sub-área split of cash recebimento (in case área is being sub-divided differently), May
SELECT 'F|'||NVL(a.NOME,'(sem area)')||'|'||NVL(sa.NOME,'(sem sub)')||'|'||TO_CHAR(ROUND(SUM(r.VALOR1),2))
  FROM LDESK.GERENC_VW_POSFIN_RESULTREC r
  LEFT JOIN LDESK.CAD_CASO c ON c.ID_CASO = r.ID_CASO
  LEFT JOIN LDESK.CAD_AREAJURIDICA a ON a.ID_AREAJURIDICA = c.ID_AREAJURIDICA
  LEFT JOIN LDESK.CAD_AREAJURIDICA sa ON sa.ID_AREAJURIDICA = c.ID_SUBAREAJURIDICA
 WHERE r.ANO_MES = '2026-05'
 GROUP BY NVL(a.NOME,'(sem area)'), NVL(sa.NOME,'(sem sub)')
 ORDER BY 1,2;

PROMPT #END target per-área MAY: Contencioso 240445 / Econômico 166876 / Arbitragem(+Ambiental) 41860
