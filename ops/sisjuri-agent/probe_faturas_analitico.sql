-- Probe v2: FAT_FATURA lacks payment date / liquido / caso, so faturas_analitico
-- must be built on GERENC_VW_POSFIN_RESULTFAT (has ID_CASO + VALOR1 + ANO_MES).
-- G0 lists that view's real columns; G1 dumps one row so we can map fatura#,
-- cliente, valor, date. Read-only. Single-line statements (paste-safe).
SET DEFINE OFF
SET PAGESIZE 200
SET LINESIZE 400
SET FEEDBACK OFF
WHENEVER SQLERROR CONTINUE
PROMPT === G0) POSFIN_RESULTFAT columns ===
SELECT column_name, data_type FROM ALL_TAB_COLUMNS WHERE owner='LDESK' AND table_name='GERENC_VW_POSFIN_RESULTFAT' ORDER BY column_id;
PROMPT === G1) one full POSFIN_RESULTFAT row (Fev 2026) ===
SELECT * FROM LDESK.GERENC_VW_POSFIN_RESULTFAT WHERE ANO_MES='2026-02' AND ROWNUM=1;
PROMPT === G2) CAD_CASO columns (for cliente/nome join) ===
SELECT column_name, data_type FROM ALL_TAB_COLUMNS WHERE owner='LDESK' AND table_name='CAD_CASO' ORDER BY column_id;
PROMPT === DONE ===
EXIT
