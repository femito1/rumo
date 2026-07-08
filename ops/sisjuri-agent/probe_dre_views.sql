-- Probe: the DB's OWN DRE engine (discovered via schema hunt). LegalDesk ships a
-- DB_* / VW_RESULTADO_* family that likely already computes the per-area DRE the
-- workbook replicates by hand. If any of these yields per-area Despesa
-- Institucional / Despesas Área to the centavo, we read it directly.
-- Workbook targets (Feb 2026): Despesa Inst total 95.047,39;
--   Despesas Área Cont 2.129,32 / Econ 3.296,07 / Arb 2.633,69.
SET DEFINE OFF
SET PAGESIZE 400
SET LINESIZE 220
SET FEEDBACK ON
COL column_name FORMAT A32
COL data_type FORMAT A16
WHENEVER SQLERROR CONTINUE

PROMPT === 1. Columns of DB_VW_DEMONSTRATIVO_RESULTADOS ===
SELECT column_name, data_type FROM ALL_TAB_COLUMNS
 WHERE table_name='DB_VW_DEMONSTRATIVO_RESULTADOS' AND owner='LDESK' ORDER BY column_id;

PROMPT === 2. Columns of DB_RESULTADO_AREA ===
SELECT column_name, data_type FROM ALL_TAB_COLUMNS
 WHERE table_name='DB_RESULTADO_AREA' AND owner='LDESK' ORDER BY column_id;

PROMPT === 3. Columns of FINANCE.VW_RESULTADO_MENSALCC (per centro de custo) ===
SELECT column_name, data_type FROM ALL_TAB_COLUMNS
 WHERE table_name='VW_RESULTADO_MENSALCC' AND owner='FINANCE' ORDER BY column_id;

PROMPT === 4. Columns of FINANCE.VW_RESULTADO_MENSAL_DET ===
SELECT column_name, data_type FROM ALL_TAB_COLUMNS
 WHERE table_name='VW_RESULTADO_MENSAL_DET' AND owner='FINANCE' ORDER BY column_id;

PROMPT === 5. Columns of DB_DRE_NIVEL and DB_DRE_TIPOS (the DRE line structure) ===
SELECT 'DB_DRE_NIVEL' tbl, column_name, data_type FROM ALL_TAB_COLUMNS
 WHERE table_name='DB_DRE_NIVEL' AND owner='LDESK'
UNION ALL
SELECT 'DB_DRE_TIPOS', column_name, data_type FROM ALL_TAB_COLUMNS
 WHERE table_name='DB_DRE_TIPOS' AND owner='LDESK'
 ORDER BY 1, column_name;

PROMPT === 6. Columns of GERENC_VW_PERC_GRUPOJURIDICO (candidate for the area split rule) ===
SELECT column_name, data_type FROM ALL_TAB_COLUMNS
 WHERE table_name='GERENC_VW_PERC_GRUPOJURIDICO' AND owner='LDESK' ORDER BY column_id;

PROMPT === 7. Columns of GERENC_LANCAMENTORESUMORATEIO (resumo WITH rateio applied!) ===
SELECT column_name, data_type FROM ALL_TAB_COLUMNS
 WHERE table_name='GERENC_LANCAMENTORESUMORATEIO' AND owner='LDESK' ORDER BY column_id;

EXIT
