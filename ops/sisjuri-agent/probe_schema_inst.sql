-- Probe: SCHEMA DISCOVERY for the institutional lines (Despesa Institucional
-- total + Despesas Área) that did not reconcile from the account rollups.
-- Hypotheses to test — DO NOT GIVE UP:
--  (H1) A management/DRE grouping table maps DB accounts -> the workbook families
--       (Ocupação/Consultoria/Informática...) that differ from NOME_CONTA_PAI.
--  (H2) PLANOCONTAS has extra hierarchy levels (PCTNNIVEL) or a "conta gerencial"
--       column that groups accounts the workbook way.
--  (H3) A per-area rateio table (like CAD_RATEIO_GRUPO for lawyers) drives the
--       Associações "=total/3" split into areas.
--  (H4) GERENC_LANCAMENTORESUMO / LANCAMENTO carry columns we never inspected
--       (subarea, second cost-center, rateio flag).
SET DEFINE OFF
SET PAGESIZE 5000
SET LINESIZE 200
SET FEEDBACK ON
COL table_name FORMAT A45
COL column_name FORMAT A32
COL data_type FORMAT A18
COL owner FORMAT A10
WHENEVER SQLERROR CONTINUE

PROMPT === H4a. FULL column list of GERENC_LANCAMENTORESUMO ===
SELECT column_name, data_type, data_length
  FROM ALL_TAB_COLUMNS
 WHERE table_name='GERENC_LANCAMENTORESUMO'
 ORDER BY column_id;

PROMPT === H4b. FULL column list of FINANCE.LANCAMENTO ===
SELECT column_name, data_type, data_length
  FROM ALL_TAB_COLUMNS
 WHERE table_name='LANCAMENTO' AND owner='FINANCE'
 ORDER BY column_id;

PROMPT === H2a. FULL column list of FINANCE.PLANOCONTAS ===
SELECT column_name, data_type, data_length
  FROM ALL_TAB_COLUMNS
 WHERE table_name='PLANOCONTAS' AND owner='FINANCE'
 ORDER BY column_id;

PROMPT === H2b. PLANOCONTAS hierarchy for 020.* and 040.* (levels + parents) ===
SELECT PCTCNUMEROCONTA, PCTNNIVEL, PCTCNUMEROCONTAPAI, SUBSTR(PCTCTITULO,1,40) titulo
  FROM FINANCE.PLANOCONTAS
 WHERE PCTCNUMEROCONTA LIKE '020.%' OR PCTCNUMEROCONTA LIKE '040.%'
 ORDER BY PCTCNUMEROCONTA;

PROMPT === H1. Hunt candidate grouping / DRE / rateio tables+views by name ===
SELECT owner, table_name FROM ALL_TABLES
 WHERE (UPPER(table_name) LIKE '%DRE%' OR UPPER(table_name) LIKE '%GERENC%'
        OR UPPER(table_name) LIKE '%RESULT%' OR UPPER(table_name) LIKE '%RATEIO%'
        OR UPPER(table_name) LIKE '%GRUPOCONTA%' OR UPPER(table_name) LIKE '%CONTAGRUPO%'
        OR UPPER(table_name) LIKE '%CONTA_GER%' OR UPPER(table_name) LIKE '%DEMONST%'
        OR UPPER(table_name) LIKE '%CLASSIF%')
   AND owner IN ('LDESK','FINANCE','SSJR')
 ORDER BY owner, table_name;

PROMPT === H1b. Same for VIEWS ===
SELECT owner, view_name FROM ALL_VIEWS
 WHERE (UPPER(view_name) LIKE '%DRE%' OR UPPER(view_name) LIKE '%RESULT%'
        OR UPPER(view_name) LIKE '%RATEIO%' OR UPPER(view_name) LIKE '%DEMONST%'
        OR UPPER(view_name) LIKE '%GERENC%' OR UPPER(view_name) LIKE '%CLASSIF%')
   AND owner IN ('LDESK','FINANCE','SSJR')
 ORDER BY owner, view_name;

PROMPT === H3. Does GERENC_LANCAMENTORESUMO carry a SUBAREA/second-grupo column with data? ===
-- Peek any *AREA*/*GRUPO*/*SUBAREA*/*RATEIO*/*CLASSIF* columns' distinct values Feb.
SELECT column_name FROM ALL_TAB_COLUMNS
 WHERE table_name='GERENC_LANCAMENTORESUMO'
   AND (UPPER(column_name) LIKE '%AREA%' OR UPPER(column_name) LIKE '%GRUPO%'
        OR UPPER(column_name) LIKE '%RATEIO%' OR UPPER(column_name) LIKE '%CLASSIF%'
        OR UPPER(column_name) LIKE '%GEREN%' OR UPPER(column_name) LIKE '%CENTRO%')
 ORDER BY column_id;

PROMPT === H1c. What columns does the resumo expose vs raw — is there a NOME_CONTA_GERENCIAL? ===
SELECT DISTINCT column_name FROM ALL_TAB_COLUMNS
 WHERE table_name LIKE 'GERENC_%' AND owner='LDESK'
   AND (UPPER(column_name) LIKE '%NOME%' OR UPPER(column_name) LIKE '%CONTA%'
        OR UPPER(column_name) LIKE '%TIPO%' OR UPPER(column_name) LIKE '%GRUPO%')
 ORDER BY column_name;

EXIT
