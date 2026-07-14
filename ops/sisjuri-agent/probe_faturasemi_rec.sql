-- probe_faturasemi_rec.sql  (T8 follow-up — the correct Nacional/Moedas source)
-- probe_nacional_moedas showed raw FAT_FATURA is the wrong grain (May honorários
-- 774.917,10 incl. a cancelled invoice ≠ sacred 719.988,05) and lacks recebimento
-- date / cliente name / NF. The MOEDA-column sweep surfaced LDESK.DB_VW_FATURASEMI_REC
-- (has SIGLA_MOEDA + SIGLA_MOEDA_NACIONAL) — "faturas emitidas + recebimento with
-- currency", the exact shape of the workbook Nacional (BRL) / Moedas (EUR/USD) tabs.
-- Confirm its columns + one real row so we can map all 16 workbook columns:
--   Docto, Cliente(id), Razão Social, Histórico, Fatura#, Número Nota Fiscal,
--   Data Emissão, Vencimento, Data Recebimento, Moeda, Valor Honorários,
--   Valor Despesas, Valor Total Fatura, Valor Total, Valor Recebido, Honorários(BRL).
-- Read-only. Pipe-tagged single-line statements.
SET DEFINE OFF
SET PAGESIZE 0
SET LINESIZE 32767
SET LONG 100000
SET TRIMOUT ON
SET FEEDBACK OFF
SET HEADING OFF
WHENEVER SQLERROR CONTINUE

PROMPT #A DB_VW_FATURASEMI_REC full column list (map to the 16 workbook cols)
SELECT 'A|'||column_id||'|'||column_name||'|'||data_type
  FROM ALL_TAB_COLUMNS WHERE owner='LDESK' AND table_name='DB_VW_FATURASEMI_REC'
 ORDER BY column_id;

PROMPT #B Row count + is there an ANO_MES / emission-date filter column? sample distinct date cols
-- Peek at which date columns exist so we know how to bound a competence month.
SELECT 'B|datecol|'||column_name
  FROM ALL_TAB_COLUMNS WHERE owner='LDESK' AND table_name='DB_VW_FATURASEMI_REC'
   AND (data_type LIKE '%DATE%' OR data_type LIKE '%TIMESTAMP%' OR UPPER(column_name) LIKE '%DATA%'
        OR UPPER(column_name) LIKE '%ANO_MES%')
 ORDER BY column_name;

PROMPT #C Total honorários over the view for May emission (cross-check vs sacred 719.988,05)
-- Try common column names; whichever errors is skipped (WHENEVER SQLERROR CONTINUE).
SELECT 'C1|hon_by_SIGLA_MOEDA=R only'||'|'||TO_CHAR(ROUND(SUM(VALOR_HONORARIOS),2))||'|n='||COUNT(*)
  FROM LDESK.DB_VW_FATURASEMI_REC
 WHERE SIGLA_MOEDA_NACIONAL='R';

PROMPT #D One full sample row (any) so we see the real values end-to-end
SELECT * FROM LDESK.DB_VW_FATURASEMI_REC WHERE ROWNUM=1;

PROMPT #E Also dump DB_VW_FATURASEMI_REC + FATURASREC_CASO column names side by side (pick best)
SELECT 'E|FATURASREC_CASO|'||column_id||'|'||column_name||'|'||data_type
  FROM ALL_TAB_COLUMNS WHERE owner='LDESK' AND table_name='DB_VW_FATURASREC_CASO'
 ORDER BY column_id;

PROMPT #END
EXIT
