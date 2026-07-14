-- probe_nacional_moedas.sql  (T8 — the per-invoice faturamento lists)
-- GOAL: find the DB source for the workbook 'Nacional' and 'Moedas' tabs — a
-- per-INVOICE list (16 cols): Docto, Cliente(id), Razão Social, Histórico,
-- Fatura#, Número Nota Fiscal, Data Emissão, Vencimento, Data Recebimento,
-- Moeda (R/E/U), Valor Honorários, Valor Despesas, Valor Total Fatura,
-- Valor Total, Valor Recebido, Honorários(convertido p/ BRL nas moedas estrangeiras).
--
-- Known (docs/SISJURI_DB.md): LDESK.FAT_FATURA has NUMERO, SITUACAO, DATA_EMISSAO,
-- DATA_CANCELAMENTO, VALOR_HONORARIOS, VALOR_DESCONTO, VALOR_DESPESAS,
-- VALOR_DESPESAS_TRIB, ID_ESCRITORIO, ID_PROFISSIONAL_RESP. It LACKS payment date,
-- líquido and moeda — so Nacional/Moedas need extra columns/joins we must discover.
-- Cliente name is behind CAD_CLIENTE->CAD_PESSOA (a 2-hop we have NOT verified).
-- This probe verifies: (1) full FAT_FATURA column list incl. any moeda/cliente/
-- vencimento/recebimento columns; (2) the cliente-name join path; (3) a currency
-- lookup; (4) one real May invoice row end-to-end so we can map every workbook col.
-- Read-only. Single-line statements, pipe-tagged where multi-row.
SET DEFINE OFF
SET PAGESIZE 0
SET LINESIZE 32767
SET LONG 100000
SET TRIMOUT ON
SET FEEDBACK OFF
SET HEADING OFF
WHENEVER SQLERROR CONTINUE

PROMPT #A FAT_FATURA full column list (hunt moeda / cliente / vencimento / recebimento / nota)
SELECT 'A|'||column_id||'|'||column_name||'|'||data_type
  FROM ALL_TAB_COLUMNS WHERE owner='LDESK' AND table_name='FAT_FATURA' ORDER BY column_id;

PROMPT #B FAT_FATURA columns whose NAME hints moeda/cliente/venc/receb/nota/valor
SELECT 'B|'||column_name||'|'||data_type
  FROM ALL_TAB_COLUMNS WHERE owner='LDESK' AND table_name='FAT_FATURA'
   AND ( UPPER(column_name) LIKE '%MOEDA%' OR UPPER(column_name) LIKE '%CURR%'
      OR UPPER(column_name) LIKE '%CLIENTE%' OR UPPER(column_name) LIKE '%PESSOA%'
      OR UPPER(column_name) LIKE '%VENC%' OR UPPER(column_name) LIKE '%RECEB%'
      OR UPPER(column_name) LIKE '%PAGAMENTO%' OR UPPER(column_name) LIKE '%QUITA%'
      OR UPPER(column_name) LIKE '%NOTA%' OR UPPER(column_name) LIKE '%NF%'
      OR UPPER(column_name) LIKE '%HISTOR%' OR UPPER(column_name) LIKE '%CASO%'
      OR UPPER(column_name) LIKE '%RAZAO%' OR UPPER(column_name) LIKE '%VALOR%' )
 ORDER BY column_name;

PROMPT #C One real May-2026 invoice header (by DATA_EMISSAO) — all columns, first row
-- Shows the actual values so we can map workbook columns to FAT_FATURA columns.
SELECT 'C|'||NUMERO||'|emis='||TO_CHAR(DATA_EMISSAO,'YYYY-MM-DD')
       ||'|hon='||TO_CHAR(VALOR_HONORARIOS)||'|desp='||TO_CHAR(VALOR_DESPESAS)
       ||'|desc='||TO_CHAR(VALOR_DESCONTO)||'|sit='||NVL(SITUACAO,'?')
  FROM LDESK.FAT_FATURA
 WHERE DATA_EMISSAO >= DATE '2026-05-01' AND DATA_EMISSAO < DATE '2026-06-01'
   AND ROWNUM <= 5 ORDER BY 1;

PROMPT #D Is there a moeda column anywhere? Search ALL LDESK tables for MOEDA/CURRENCY cols
SELECT 'D|'||table_name||'.'||column_name||'|'||data_type
  FROM ALL_TAB_COLUMNS WHERE owner='LDESK'
   AND (UPPER(column_name) LIKE '%MOEDA%' OR UPPER(column_name) LIKE '%CURRENC%')
 ORDER BY table_name, column_name;

PROMPT #E CAD_CLIENTE + CAD_PESSOA column lists (the cliente-name 2-hop)
SELECT 'E|CAD_CLIENTE|'||column_id||'|'||column_name||'|'||data_type
  FROM ALL_TAB_COLUMNS WHERE owner='LDESK' AND table_name='CAD_CLIENTE' ORDER BY column_id;
SELECT 'E2|CAD_PESSOA|'||column_id||'|'||column_name||'|'||data_type
  FROM ALL_TAB_COLUMNS WHERE owner='LDESK' AND table_name='CAD_PESSOA' ORDER BY column_id;

PROMPT #F Does POSFIN_RESULTFAT carry MOEDA / cliente / recebimento? (it has ID_CASO+VALOR1)
SELECT 'F|'||column_name||'|'||data_type
  FROM ALL_TAB_COLUMNS WHERE owner='LDESK' AND table_name='GERENC_VW_POSFIN_RESULTFAT'
 ORDER BY column_id;

PROMPT #G Faturamento total May via FAT_FATURA honorarios (cross-check vs sacred 719.988,05)
SELECT 'G|hon_sum='||TO_CHAR(ROUND(SUM(VALOR_HONORARIOS),2))
       ||'|desp_sum='||TO_CHAR(ROUND(SUM(VALOR_DESPESAS),2))
       ||'|n='||COUNT(*)
  FROM LDESK.FAT_FATURA
 WHERE DATA_EMISSAO >= DATE '2026-05-01' AND DATA_EMISSAO < DATE '2026-06-01';

PROMPT #END
EXIT
